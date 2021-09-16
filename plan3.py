# import numpy as np
import glob, os, sys
import datetime
from plan_io import *

class Satellite:
  def __init__(self, NORAD, ephem):
    self.NORAD = NORAD
    self.ephem = ephem

# p1 = Person("John", 36)


#  Main begin here------------------------------------------------------------------------------------------
# 36581 = HA 235508.25 -071108.39   0.00 8x10 @173600-173900
# 26853 = HA 235420.60 -040736.63   0.00 8x10 @173900-174200
# 38022 = HA 232759.36 -130207.99   0.00 8x10 @174200-174500
# 95151 = HA 233142.64 -032121.09   0.00 8x10 @174500-174800
# 95243 = HA 225529.90 -070816.10   0.00 8x10 @174800-175100
# 96132 = HA 223619.08 -084226.46   0.00 8x10 @175100-175400
# 95170 = HA 222828.70 -102552.50   0.00 8x10 @175400-175700
# 95157 = HA 222713.16 -044818.07   0.00 8x10 @175700-180000
# 95213 = HA 222441.20 -051617.45   0.00 8x10 @180000-180300
# 95215 = HA 220929.90 -071139.06   0.00 8x10 @180300-180600
# 95226 = HA 214543.41 -053029.86   0.00 8x10 @180600-180900

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


obj = read_planed_objects('planed_objects.txt')


# vtlist = glob.glob("*.vt")
geo_list = []

alleph = []
for sat in obj:
    filename_vt = 'vt/' + sat.strip() + '.vt'
    filename_va = 'va/' + sat.strip() + '.va'
    if os.path.isfile(filename_vt):
        ephem = read_vt(filename_vt)
        # alleph.append(ephem)
        geo_list.append(Satellite(sat, ephem))
    elif os.path.isfile(filename_va):
        ephem = read_va(filename_va)
        # alleph.append(ephem)
        geo_list.append(Satellite(sat, ephem))
    else:
        print 'cant find ' + sat.strip() + " vt or va ephemeris file"

geo_list.sort(key=lambda x: x.ephem[0][8], reverse=False) # sort satellites by HA

for sat in geo_list:
    print sat.NORAD, "--> HA ", sat.ephem[0][7], "####->", sat.ephem[0][8] 

# print obj
import datetime
ndate = datetime.datetime.now().strftime("%Y%m%d")

f = open('object_' + C + '_' + ndate +'.list', 'w')
# last_T = calc_T_twilight()
last_T = datetime.datetime(year=2021, month=9, day=14, hour=18, minute=0, second=0)

# print last_T 
# last_T = last_T - datetime.timedelta(days=1)  # ---------------------------------------<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
print "start date =" 
print last_T
f.write("# Start T = " + str(last_T) + "\n")

print "start..."
for ser in range(0, 1):
    print "ser#", ser+1
    for sat in geo_list:
        T1 = alleph[z][k][1].replace(":", "")
        T2 = addT(T1, t_ser + t_move)  # time for frames capture + move telescope to next point
        f.write(sat.NORAD + ' = ' + flag + ' ' + ra + '  ' + dec + '  ' + mag + ' ' + str_v_plan + T1 + '-' + T2 + '\n')


f.close()
