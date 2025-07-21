"""
Run this script in SharpCap Pro to start calculated plan.
Connect to camera and telescope manually before running the script
"""

import time
from datetime import datetime, timezone
import os
import configparser

# ---------------------- Load Config ----------------------
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), "config_SharpCap_plan.ini"))

observer_longitude = float(config["observer"]["longitude"])
plan_file_path = config["files"]["plan_file"]
log_dir = config["files"]["log_dir"]

# ---------------------- Logging ----------------------
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, f"log_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.txt")
log_file = open(log_file_path, "a")

def log(msg):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    log_file.write(full_msg + "\n")
    log_file.flush()

# ---------------------- Parsing ----------------------
def parse_ha_dec(coord_str):
    parts = coord_str.strip().split(':')
    sign = -1 if parts[0].startswith('-') else 1
    h = abs(float(parts[0]))
    m = float(parts[1])
    s = float(parts[2])
    return sign * (h + m / 60 + s / 3600)

def parse_plan(file_path):
    targets = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line == '' or line.startswith('#'):
                continue
            try:
                parts = line.split()
                obj_id = parts[0]
                ha_str = parts[2].split('(')[0]
                dec_str = parts[3].split('(')[0]
                ha = parse_ha_dec(ha_str)
                dec = parse_ha_dec(dec_str)
                ha_rate = float(parts[3].split('(')[1].rstrip(')')) if '(' in parts[3] else 0.0
                dec_rate = float(parts[4].split('(')[1].rstrip(')')) if '(' in parts[4] else 0.0
                exposure_str = parts[5]  # format: "10x12.0:0"
                count = int(exposure_str.split('x')[0])
                exp = float(exposure_str.split('x')[1].split(':')[0])
                pause = float(exposure_str.split(':')[1])
                interval = parts[6].replace('@', '')
                start_utc = datetime.strptime(interval[:6], "%H%M%S").time()
                stop_utc = datetime.strptime(interval[7:], "%H%M%S").time()
                targets.append((obj_id, ha, dec, ha_rate, dec_rate, start_utc, stop_utc, count, exp, pause))
            except Exception as e:
                log(f"[WARN] Failed to parse line: {line} ({e})")
    return targets

# ---------------------- Time helpers ----------------------
def get_lst(longitude):
    now = datetime.now(timezone.utc)
    days = (now - datetime(now.year, 1, 1)).total_seconds() / 86400.0
    gmst = 6.697374558 + 0.06570982441908 * days + 1.00273790935 * now.hour + now.minute / 60.0 + now.second / 3600.0
    lst = (gmst * 15 + longitude) % 360
    return lst / 15.0  # in hours

def ha_dec_to_ra(ha, lst):
    ra = (lst - ha) % 24.0
    return ra

# ---------------------- Capture Function ----------------------
def perform_capture(camera, mount, target):
    obj_id, ha, dec, ha_rate, dec_rate, t_start, t_stop, count, exp, pause = target

    now = datetime.now(timezone.utc).time()
    log(f"[INFO] Starting capture for {obj_id} at {now}")

    # Обчислюємо RA
    lst = get_lst(observer_longitude)
    ra = ha_dec_to_ra(ha, lst)

    # Наведення
    mount.Tracking = True
    mount.SlewToCoordinates(ra, dec)
    while mount.Slewing:
        time.sleep(0.5)

    log(f"[INFO] Slewed to RA={ra:.4f}, DEC={dec:.4f}")

    if abs(ha_rate) > 0.0 or abs(dec_rate) > 0.0:
        # Not TESTED !!!
        log(f"Setting custom tracking rates: dRA={ha_rate:.3f}h/s, dDEC={dec_rate:.3f}°/s")
        mount.Tracking = False
        mount.RightAscensionRate = ha_rate * 15.0  # години/секунду в градуси/секунду
        mount.DeclinationRate = dec_rate
        mount.Tracking = True
    else:
        log("Using normal tracking mode")
        # mount.RightAscensionRate = 0.0
        # mount.DeclinationRate = 0.0
        mount.Tracking = True

    # Встановлення експозиції
    camera.Controls.Exposure.Value = exp
    log(f"[INFO] Set exposure = {exp}s")

    if pause == 0:
        log("[INFO] Using continuous capture mode")
        camera.StartCapture()
        while camera.Capturing:
            if camera.FramesCaptured >= count:
                camera.StopCapture()
                break
            time.sleep(0.1)
    else:
        for i in range(count):
            camera.CaptureSingleFrame()
            log(f"[INFO] Captured frame {i+1}/{count}")
            time.sleep(pause)

    log(f"[INFO] Capture complete for {obj_id}")

# ---------------------- Main Script ----------------------
targets = parse_plan(plan_file_path)
completed_targets = set()

camera = SharpCap.SelectedCamera
mount = SharpCap.Mounts.SelectedMount.AscomMount

now = datetime.now(timezone.utc).time()

# Перевірка, чи всі цілі вже у минулому
# target[6] = t_end
if all(target[6] < now for target in targets):
    log("[INFO] All targets are in the past. Exiting.")
    log_file.close()
    exit(0)

# Отримуємо останню ціль за часом
latest_target_idx = max(range(len(targets)), key=lambda i: targets[i][6])  # індекс цілі з найпізнішим t_stop

while True:
    now = datetime.now(timezone.utc).time()

    for idx, target in enumerate(targets):
        obj_id, ha, dec, t_start, t_stop, count, exp, pause = target

        if idx in completed_targets:
            continue

        if t_start <= now <= t_stop:
            perform_capture(camera, mount, target)
            completed_targets.add(idx)
            break  # не перевіряємо інші цілі під час зйомки

    if len(completed_targets) == len(targets):
        log("[INFO] All targets observed. Exiting.")
        break

    time.sleep(0.5)

log_file.close()
