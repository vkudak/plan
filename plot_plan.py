import argparse
import sys

import numpy as np
from astropy import units as u
from astropy.coordinates import Angle
from datetime import datetime, timedelta
from matplotlib import pyplot as plt
import matplotlib.dates as mdates



def read_plan(filename):
    res = {"norad":[], "ra":[], "dec":[], "b_time":[]}
    for line in open(filename, "r"):
        li = line.strip()
        if not li.startswith("#") or li.startswith(" "):
            # print(li.split())
            norad, _, _, ra, dec, _, _, b_time = li.split()
            res["norad"].append(norad)

            ra = ra.split("(")[0]
            ra = ra[:2] + ":" + ra[2:]
            ra = ra[:5] + ":" + ra[5:]
            ra = Angle(ra + "hours")

            dec = dec.split("(")[0]
            dec = dec[:3] + ":" + dec[3:]
            dec = dec[:6] + ":" + dec[6:]
            dec = Angle(dec + "degrees")

            res["ra"].append(ra.hour)
            res["dec"].append(dec.degree)
            btime = b_time[1:].split("-")[0]
            btime = datetime.strptime('2020-01-01 ' + btime, '%Y-%d-%m %H%M%S')
            if btime < datetime(2020, 1, 1, 16, 0, 0):
                btime = btime + timedelta(days=1)

            res["b_time"].append(btime)
    return res


parser = argparse.ArgumentParser(description='Plan plotter')
parser.add_argument('plan_file', type=str, help='Specify file with plan')
args = parser.parse_args()

# r = read_plan("object_HA_20240819.list")

if not args.plan_file:
    sys.exit("Not enough parameters. Enter path")

r = read_plan(args.plan_file)

plt.rcParams["figure.figsize"] = (12, 6)
fig, axs = plt.subplots(2, 1, sharex=True)
axs[0].plot(r["b_time"], r["ra"], "ko-", label="RA/HA", linewidth=1, markersize=5)
axs[0].set_ylabel("RA/HA (hours)")
axs[0].set_xlabel("Time (UTC)")
axs[0].tick_params(axis='both',direction='in')


axs[1].plot(r["b_time"], r["dec"], "ko-", label="DEC", linewidth=1, markersize=5)
axs[1].set_xlabel("Time (UTC)")
axs[1].set_ylabel("DEC (degrees)")
myFmt = mdates.DateFormatter('%H')
axs[1].xaxis.set_major_formatter(myFmt)
axs[1].tick_params(axis='both',direction='in')

plt.tight_layout()
plt.show()
# print(r)
