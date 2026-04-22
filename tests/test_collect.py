"""Tests for the /collect delivery flow — Sprint 2 edge cases.

Covers the six edge cases from Sprint 2 plus a no-regression happy path:
- A: token not found → "not valid" (404)
- D: returning user with one file done → valid status with pre-frozen button
- E: file missing on disk → Scout-register error page (404)
- F: already-downloaded re-request → Scout-register error page (410)
- G: rate-limited verify → 429 response (client surfaces to user separately)
- H: token case-insensitive lookup
- Happy path: correct key returns {valid: true}

Run from the project root:
    python -m unittest tests.test_collect -v
"""
from __future__ import annotations

import os
import sys
import unittest
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as scout_app  # noqa: E402
from scout.database import (  # noqa: E402
    _connect,
    create_delivery,
    mark_downloaded,
)


class CollectFlowTests(unittest.TestCase):
    """End-to-end tests against the Flask test client."""

    @classmethod
    def setUpClass(cls):
        scout_app.app.config["TESTING"] = True
        cls.client = scout_app.app.test_client()
        cls.test_tokens: list[str] = []
        cls.test_files: list[str] = []

    @classmethod
    def tearDownClass(cls):
        conn = _connect()
        for token in cls.test_tokens:
            conn.execute("DELETE FROM deliveries WHERE token = ?", (token,))
        conn.commit()
        conn.close()
        for path in cls.test_files:
            try:
                os.remove(path)
            except FileNotFoundError:
                pass

    def setUp(self):
        # Reset Flask-Limiter counters between tests so the rate-limit test
        # (G) does not poison later tests that also hit /verify.
        try:
            scout_app.limiter.reset()
        except Exception:
            pass

    # --- helpers ---

    def _make_token(self, key: str, expires_hours: int = 48,
                    portrait_downloaded: bool = False,
                    meridian_downloaded: bool = False) -> str:
        token = uuid.uuid4().hex
        expires_at = (datetime.now(timezone.utc)
                      + timedelta(hours=expires_hours)).isoformat()
        create_delivery(key, token, expires_at)
        if portrait_downloaded:
            mark_downloaded(token, "portrait")
        if meridian_downloaded:
            mark_downloaded(token, "meridian")
        self.__class__.test_tokens.append(token)
        return token

    def _make_stub_pdfs(self, key: str, date_str: str = "2099-01-01") -> None:
        """Write minimal valid PDFs into deliveries/ so the download routes
        find them. Registered for teardown cleanup."""
        pdf_bytes = (
            b"%PDF-1.4\n"
            b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\n"
            b"trailer<</Root 1 0 R/Size 4>>\n%%EOF\n"
        )
        for kind in ("portrait", "meridian"):
            path = os.path.join(
                scout_app.DELIVERIES_DIR,
                f"{key}_{date_str}_{kind}.pdf",
            )
            with open(path, "wb") as f:
                f.write(pdf_bytes)
            self.__class__.test_files.append(path)

    # --- A: token not found ---

    def test_A_token_not_found_shows_invalid_not_expired(self):
        """Typo or fabricated token → 'This link is not valid.' + 404.

        Before Sprint 2 this path rendered 'This link has expired.' which was
        misleading — the token was never valid, not expired.
        """
        r = self.client.get("/collect/nonexistenttoken9999zzz")
        self.assertEqual(r.status_code, 404)
        self.assertIn(b"This link is not valid", r.data)
        self.assertNotIn(b"This link has expired", r.data)

    # --- D: returning user with one file downloaded ---

    def test_D_returning_user_one_file_done_renders_valid_with_frozen_button(self):
        """User downloaded portrait earlier, closes tab, returns: page renders
        in valid state with portrait button pre-frozen (class 'done') and a
        returning-note visible near the top."""
        token = self._make_token(
            key="TEST-RETURN1",
            portrait_downloaded=True,
        )
        r = self.client.get(f"/collect/{token}")
        self.assertEqual(r.status_code, 200)
        body = r.data.decode()
        # Returning-user cue present
        self.assertIn("One document has already been collected", body)
        # Portrait button pre-frozen
        self.assertRegex(body, r'<a class="download-btn done"[^>]*id="portrait-btn"')
        # Meridian button still unfrozen (no 'done' class)
        self.assertRegex(body, r'<a class="download-btn\s*"[^>]*id="meridian-btn"')

    # --- E: file missing on disk ---

    def test_E_file_missing_on_disk_renders_error_page(self):
        """Delivery row exists but PDF file is not on disk → Scout-register
        HTML page (not raw text), HTTP 404."""
        token = self._make_token(key="TEST-MISSING")
        # Deliberately DO NOT call _make_stub_pdfs — file must be absent
        r = self.client.get(f"/collect/{token}/portrait")
        self.assertEqual(r.status_code, 404)
        self.assertIn(b"Something didn't arrive as it should", r.data)
        # Response is HTML, not plain text
        self.assertIn(b"<!DOCTYPE html", r.data)
        self.assertIn(b"Scout</div>", r.data)  # wordmark rendered

    # --- F: already-downloaded re-request ---

    def test_F_already_downloaded_rerequest_renders_error_page(self):
        """GET /collect/<token>/portrait after the portrait has been served
        once → Scout-register HTML page with 'already been collected' copy."""
        token = self._make_token(
            key="TEST-COLLECTED",
            portrait_downloaded=True,
        )
        self._make_stub_pdfs(key="TEST-COLLECTED")
        r = self.client.get(f"/collect/{token}/portrait")
        self.assertEqual(r.status_code, 410)
        self.assertIn(b"This document has already been collected", r.data)
        self.assertIn(b"<!DOCTYPE html", r.data)

    # --- G: rate-limit surfaces on /verify ---

    def test_G_verify_rate_limit_returns_429(self):
        """After 10 /verify POSTs in a minute, the 11th returns 429. The
        client-side handler surfaces this as a distinct muted message (not
        the shake animation which implies wrong key). Test verifies server
        side only."""
        token = self._make_token(key="TEST-RATELIMIT")
        # The 10/min limit is per-IP; test client IP is fixed per process.
        # If an earlier test consumed the limit, we might already be at 11 —
        # check both states.
        saw_429 = False
        for _ in range(12):
            r = self.client.post(
                f"/collect/{token}/verify",
                json={"key": "definitely-wrong"},
            )
            if r.status_code == 429:
                saw_429 = True
                break
        self.assertTrue(
            saw_429,
            "Expected a 429 within 12 rapid /verify attempts; limiter "
            "appears not to be firing.",
        )

    # --- H: token case-insensitive lookup ---

    def test_H_token_uppercase_still_routes_to_correct_delivery(self):
        """Email clients sometimes uppercase URLs. Tokens are uuid4().hex
        (lowercase). The route should normalise to lowercase before DB
        lookup — silent fix, the user never sees a problem."""
        token = self._make_token(key="TEST-CASEFIX")
        upper = token.upper()
        self.assertNotEqual(upper, token)
        r = self.client.get(f"/collect/{upper}")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Enter your session key to unlock", r.data)

    def test_H_token_uppercase_verify_route_also_normalises(self):
        """Same normalisation must apply to /verify and download routes so
        the whole flow works for an uppercased URL."""
        key = "TEST-CASEVERIFY"
        token = self._make_token(key=key)
        r = self.client.post(
            f"/collect/{token.upper()}/verify",
            json={"key": key},
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["valid"])

    # --- Happy path — no regression on existing flow ---

    def test_happy_path_correct_key_returns_valid_true(self):
        """No-regression: a correct key on a fresh token returns {valid: true}."""
        key = "TEST-HAPPYPATH"
        token = self._make_token(key=key)
        r = self.client.post(
            f"/collect/{token}/verify",
            json={"key": key},
        )
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertTrue(data["valid"])

    def test_happy_path_wrong_key_returns_valid_false(self):
        """No-regression: a wrong key returns {valid: false} without leaking info."""
        key = "TEST-HAPPYWRONG"
        token = self._make_token(key=key)
        r = self.client.post(
            f"/collect/{token}/verify",
            json={"key": "not-the-key"},
        )
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertFalse(data["valid"])
        # Response body is exactly {"valid": false} — no key leak, no hint.
        # Normalise whitespace so the test is independent of Flask's JSON formatter.
        import json as _json
        self.assertEqual(_json.loads(r.data.decode()), {"valid": False})
        self.assertNotIn(b"TEST-HAPPYWRONG", r.data)

    def test_expired_token_still_renders_expired(self):
        """No-regression: an expired token renders the expired view + 410."""
        token = self._make_token(
            key="TEST-EXPIRED",
            expires_hours=-1,  # already past
        )
        r = self.client.get(f"/collect/{token}")
        self.assertEqual(r.status_code, 410)
        self.assertIn(b"This link has expired", r.data)
        self.assertNotIn(b"This link is not valid", r.data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
