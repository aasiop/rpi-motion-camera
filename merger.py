import os
import subprocess
from collections import defaultdict
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

INPUT_DIR = os.path.join(os.getenv("PROJECT_PATH"), "recordings")
OUTPUT_DIR = os.path.join(os.getenv("PROJECT_PATH"), "merged")
TMP_DIR = os.getenv("TEMP_DIR")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TMP_DIR, exist_ok=True)

#date in format YYYY-MM-DD
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

groups = defaultdict(list)

print(f"Finding files from: {yesterday}")

#load files
for file in os.listdir(INPUT_DIR):
    if not file.endswith(".mp4"):
        continue

    name = os.path.splitext(file)[0]

    #expected format:
    #recording_2026-06-24_08-28-58.mp4
    parts = name.rsplit("_", 2)

    if len(parts) != 3:
        print(f"Skiping... (incorrect name): {file}")
        continue

    _, date_part, _ = parts

    #only files from yesterday
    if date_part != yesterday:
        continue

    groups[date_part].append(os.path.join(INPUT_DIR, file))

if not groups:
    print(f"No files from {yesterday}")
    exit(0)

#Merge and delete
for date, files in groups.items():
    files.sort()

    list_file = os.path.join(TMP_DIR, f"list_{date}.txt")

    with open(list_file, "w") as f:
        for file in files:
            f.write(f"file '{file}'\n")

    output_file = os.path.join(OUTPUT_DIR, f"merged_{date}.mp4")

    print(f"Merging files from {date} ({len(files)})")

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_file,
        "-c", "copy",
        output_file
    ]

    result = subprocess.run(cmd)

    #Delete only after merging
    if result.returncode == 0:
        print(f"Merged successfully. Deleting {len(files)} files.")

        for file in files:
            try:
                os.remove(file)
            except Exception as e:
                print(f"Can't delete {file}: {e}")
    else:
        print(f"ffmpeg error, day {date}.")
print("DONE!")
