#!/bin/bash
cd /home/scout
git clean -fd sessions/
git pull origin master
source venv/bin/activate
pip install -r requirements.txt -q
systemctl restart scout
echo "Scout deployed."
