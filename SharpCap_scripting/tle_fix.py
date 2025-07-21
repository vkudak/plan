"""
Correction of TLE checksums.
Usage: tle_fix.py tle_file.txt
Output: tle_file_corrected.txt
"""
import sys
import os

def compute_tle_checksum(line: str) -> str:
    total = 0
    for char in line[:68]:
        if char.isdigit():
            total += int(char)
        elif char == '-':
            total += 1
    return str(total % 10)


def fix_tle_checksums(input_path: str, output_path: str):
    corrected_norad_ids = []

    with open(input_path, "r") as infile, open(output_path, "w") as outfile:
        lines = infile.readlines()
        i = 0
        while i < len(lines):
            name_line = lines[i].rstrip()
            line1 = lines[i + 1].rstrip()
            line2 = lines[i + 2].rstrip()

            norad_id = line1[2:7]  # NORAD ID (5 цифр)

            checksum1 = compute_tle_checksum(line1)
            checksum2 = compute_tle_checksum(line2)

            was_corrected = False

            if line1[68] != checksum1:
                line1 = line1[:68] + checksum1
                was_corrected = True

            if line2[68] != checksum2:
                line2 = line2[:68] + checksum2
                was_corrected = True

            if was_corrected:
                corrected_norad_ids.append(norad_id)

            # Write corrected block
            outfile.write(name_line + "\n")
            outfile.write(line1 + "\n")
            outfile.write(line2 + "\n")

            i += 3

    # Summary
    if corrected_norad_ids:
        print("Виправлені контрольні суми для наступних NORAD ID:")
        for nid in corrected_norad_ids:
            print(" -", nid)
    else:
        print("Усі контрольні суми вже були правильні.")


# === Використання ===
input_file = sys.argv[1]
# print(os.path.filename(input_file.rstrip(os.sep)))
output_file = os.path.basename(input_file.rstrip(os.sep)).split('.')[0] + "_corrected.txt"

fix_tle_checksums(input_file, output_file)
