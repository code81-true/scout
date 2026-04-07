@echo off
echo Generating 10 new keys on Scout server...
ssh root@178.104.57.52 "cd /home/scout && /home/scout/venv/bin/python keys_generate.py 10"
echo.
echo Downloading updated key list to your computer...
scp root@178.104.57.52:/home/scout/access/keys.txt C:\Users\Manmo\Projectns\scout\access\keys.txt
echo.
echo Done. New keys are ready.
echo Open the file access\keys.txt to see all keys and their status.
pause
