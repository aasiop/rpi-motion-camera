import subprocess
import os
from dotenv import load_dotenv
from pathlib import Path

project_dir = Path(__file__).resolve().parent

load_dotenv()
hours,minutes = (os.getenv("MERGE_TIME", "6:00")).split(":")

cron = f'{minutes} {hours} * * * /usr/bin/python3 {project_dir}/merge.py >> {project_dir}/logs.log 2>&1'

#protection against adding another crontab job
current_crontab = subprocess.run(
    ["crontab", "-l"],
    capture_output=True,
    text=True
).stdout

if cron not in current_crontab:
    subprocess.run(
        f'(crontab -l 2>/dev/null; echo "{cron}") | crontab -',
        shell=True,
        check=True,
    )
else:
    print("Cronjob already added")