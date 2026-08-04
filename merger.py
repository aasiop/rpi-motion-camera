import os
import subprocess
from collections import defaultdict
from datetime import datetime, timedelta

INPUT_DIR = "/srv/NAS/monitoring/Nagrania"
OUTPUT_DIR = "/srv/NAS/monitoring/scalone"
TMP_DIR = "/tmp/ffmpeg_merge"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TMP_DIR, exist_ok=True)

# Data wczorajsza w formacie YYYY-MM-DD
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

groups = defaultdict(list)

print(f"Szukam plików z dnia: {yesterday}")

# Wczytanie plików
for file in os.listdir(INPUT_DIR):
    if not file.endswith(".mp4"):
        continue

    name = os.path.splitext(file)[0]

    # oczekiwany format:
    # nagranie_2026-06-24_08-28-58.mp4
    parts = name.rsplit("_", 2)

    if len(parts) != 3:
        print(f"Pomijam (zła nazwa): {file}")
        continue

    _, date_part, _ = parts

    # Tylko pliki z poprzedniego dnia
    if date_part != yesterday:
        continue

    groups[date_part].append(os.path.join(INPUT_DIR, file))

if not groups:
    print(f"Brak plików z dnia {yesterday}")
    exit(0)

# Scalanie + usuwanie
for date, files in groups.items():
    files.sort()

    list_file = os.path.join(TMP_DIR, f"list_{date}.txt")

    with open(list_file, "w") as f:
        for file in files:
            f.write(f"file '{file}'\n")

    output_file = os.path.join(OUTPUT_DIR, f"merged_{date}.mp4")

    print(f"Łączenie dnia {date} ({len(files)} plików)")

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

    # Usuwanie tylko po udanym scaleniu
    if result.returncode == 0:
        print(f"Scalono poprawnie. Usuwam {len(files)} plików.")

        for file in files:
            try:
                os.remove(file)
            except Exception as e:
                print(f"Nie mogę usunąć {file}: {e}")
    else:
        print(f"Błąd ffmpeg dla dnia {date} — pliki pozostają.")

print("Gotowe")
