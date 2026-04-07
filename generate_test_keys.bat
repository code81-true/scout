@echo off
echo Generating 5 test keys on Scout server...
ssh root@178.104.57.52 "cd /home/scout && /home/scout/venv/bin/python access/keygen.py --test 5"
echo.
echo Downloading updated key list to your computer...
scp root@178.104.57.52:/home/scout/access/keys.txt C:\Users\Manmo\Projectns\scout\access\keys.txt
echo.
echo Done. Test keys are ready.
echo Open the file access\keys.txt to see all keys and their status.
pause
