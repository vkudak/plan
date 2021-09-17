# import numpy as np
import glob, os, sys
import datetime
import ephem
from plan_io import *

class Satellite:
  def __init__(self, NORAD, HA, prio, TLE):
      self.NORAD = NORAD
      self.HA = HA
      self.prio = prio
      self.TLE = TLE


#  Main begin here------------------------------------------------------------------------------------------
# 36581 = HA 235508.25 -071108.39   0.00 8x10 @173600-173900
# 26853 = HA 235420.60 -040736.63   0.00 8x10 @173900-174200

# print "------Twilight (h_sun=-10)--"
# print calc_T_twilight()
# print "--------------------------"

C = 'HA'  # HA
t_move = 40
t_exp = 12.0
n_frames = 7
exp_wait = 30 # interval between frames
t_miz_ser = 3.6*60*60

t_ser = n_frames * (t_exp + 3 + exp_wait)  # 3 - readout, 
str_v_plan = str(n_frames) + "x" + str(t_exp) + ":" + str(exp_wait) + " @" 

ndate = datetime.datetime.now().strftime("%Y%m%d")
f = open('object_' + C + '_' + ndate +'.list', 'w')
# last_T = calc_T_twilight()
last_T = datetime.datetime(year=2021, month=9, day=14, hour=18, minute=0, second=0)

obj = read_planed_objects('planed_objects.txt')
TLE = read_tle("tle//tle_20210917.txt")

geo_list = []

Deren = ephem.Observer()
Deren.lon = str(22.299167)  # Note that lon should be in string format
Deren.lat = str(48.631639)  # Note that lat should be in string format
Deren.elev = 245 # Elevation in metres

for sat in obj:
    for tle in TLE:
        if int(sat) == tle[-1]:
            geo = ephem.readtle(tle[0], tle[1], tle[2])
            # print(last_T.strftime("%Y/%m/%d %H:%M:%S"))
            Deren.date = last_T.strftime("%Y/%m/%d %H:%M:%S") #'2003/3/23 H:M:S'
            geo.compute(Deren)

            ha = Deren.sidereal_time() - geo.ra + ephem.degrees('22.299167')
            print Deren.sidereal_time(), ephem.degrees('22.299167'), geo.ra , ha
            print type(Deren.sidereal_time()), type(ephem.degrees('22.299167')), type(geo.ra)

            sys.exit()

            # print(tle[-1], geo.ra, geo.dec, ha)
            geo_list.append(Satellite(sat, HA=ha, TLE=tle, prio=0))

# print len(geo_list)


# alleph = []
# for sat in obj:
#     filename_vt = 'vt/' + sat.strip() + '.vt'
#     filename_va = 'va/' + sat.strip() + '.va'
#     if os.path.isfile(filename_vt):
#         ephem = read_vt(filename_vt)
#         # alleph.append(ephem)
#         geo_list.append(Satellite(sat, ephem, prio=0))
#     elif os.path.isfile(filename_va):
#         ephem = read_va(filename_va)
#         # alleph.append(ephem)
#         geo_list.append(Satellite(sat, ephem, prio=0))
#     else:
#         print('cant find ' + sat.strip() + " vt or va ephemeris file")

# geo_list.sort(key=lambda x: x.ephem[0][8], reverse=False) # sort satellites by HA
geo_list.sort(key=lambda x: x.HA, reverse=False) # sort satellites by HA

for sat in geo_list:
    # print(sat.NORAD, "--> HA ", sat.ephem[0][7], "####->", sat.ephem[0][8])
    print(sat.NORAD, "--> HA ", sat.HA)

# print obj



# print last_T 
# last_T = last_T - datetime.timedelta(days=1)  # ---------------------------------------<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
print("start date =")
print(last_T)
f.write("# Start T = " + str(last_T) + "\n")

sys.exit()

print("start...")
for ser in range(0, 1):
    print("ser#", ser+1)
    for sat in geo_list:
        T1 = alleph[z][k][1].replace(":", "")
        T2 = addT(T1, t_ser + t_move)  # time for frames capture + move telescope to next point
        f.write(sat.NORAD + ' = ' + flag + ' ' + ra + '  ' + dec + '  ' + mag + ' ' + str_v_plan + T1 + '-' + T2 + '\n')


f.close()
