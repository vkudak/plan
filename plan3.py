# import numpy as np
import glob, os, sys
import datetime
import ephem
from plan_io import *
import glob
# https://rhodesmill.org/skyfield/earth-satellites.html  ?????


class Satellite:
    def __init__(self, NORAD, HA, priority, TLE, geo, block):
        self.NORAD = NORAD
        self.HA = HA  # HA at the first evening point
        self.priority = priority
        self.TLE = TLE
        self.geo = geo  # pyephem sat object
        self.block = block


#  Main begin here------------------------------------------------------------------------------------------
# 36581 = HA 235508.25 -071108.39   0.00 8x10 @173600-173900
# 26853 = HA 235420.60 -040736.63   0.00 8x10:30 @173900-174200

# print "------Twilight (h_sun=-10)--"
# print calc_T_twilight()
# print "--------------------------"

C = 'HA'  # HA
series = 3
t_move = 40
t_exp = 12.0
n_frames = 7
exp_wait = 30 # interval between frames
# t_miz_ser = 3.6*60*60

t_ser = n_frames * (t_exp + 3 + exp_wait)  # 3 - readout, 
str_v_plan = str(n_frames) + "x" + str(t_exp) + ":" + str(exp_wait) + " @" 

ndate = datetime.datetime.now().strftime("%Y%m%d")
f = open('object_' + C + '_' + ndate + '.list', 'w')
start_T, end_T = calc_T_twilight()
# start_T = datetime.datetime(year=2021, month=9, day=14, hour=18, minute=0, second=0)

obj = read_planed_objects('planed_objects.txt')
print("Satellites to plan =", len(obj))
if not os.path.isdir('tle'):
    print("no TLE files in 'tle' directory")
else:
    try:
        tle_file_list = glob.glob('tle//*.txt')
        TLE = read_tle(tle_file_list)
        print("TLE read successfully")
    except Exception as e:
        print(e.message, e.args)

geo_list = []

Deren = ephem.Observer()
Deren.lon = str(22.453751)  # Note that lon should be in string format
Deren.lat = str(48.5635505)  # Note that lat should be in string format
Deren.elev = 231  # Elevation in metres

for sat in obj:
    for tle in TLE:
        if int(sat) == tle[-1]:
            # print(sat)
            geo = ephem.readtle(tle[0], tle[1], tle[2])
            Deren.date = start_T.strftime("%Y/%m/%d %H:%M:%S")  # "2021/09/17 18:00:00" #'2003/3/23 H:M:S'
            geo.compute(Deren)
            ha = ephem.hours(Deren.sidereal_time() - geo.ra)  # -12 to +12.
            #                                                 To convert 0-24 do + ephem.degrees("360.0")
            # print("NORAD=", sat, "DATE=", Deren.date,
            #        ', ST=', Deren.sidereal_time(),
            #        "RA=", geo.ra,
            #        "HA=", ha, geo.eclipsed )
            geo_list.append(Satellite(sat, HA=ha, TLE=tle, priority=0, geo=geo, block=False))

print("Satellites planned =", len(geo_list) - 1)

geo_list.sort(key=lambda x: x.HA, reverse=False)  # sort satellites by HA

# print(geo_list[-1].NORAD)
# print start_T
# start_T = start_T - datetime.timedelta(days=1)  # ----------------------<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
print("Start date = ", start_T)
print("End date = ", end_T)

f.write("# Start T = " + str(start_T) + "\n")

print("start...")
flag = C
T1 = start_T
for ser in range(0, series):
    # print("ser#", ser+1)
    geo_list.sort(key=lambda x: x.HA, reverse=False)  # sort satellites by HA  !!!!!!
    f.write("# series N = %i \n" % (ser + 1))
    # change all BLOCK to False !!!!!!!!!!!!
    for i in range(0, len(geo_list)):
        geo_list[i].block = False
    for i in range(0, len(geo_list)):
        sat = geo_list[i]
        if not sat.block:
            if (sat == geo_list[0]) and (sat.priority == 0) and (ser > 0):
                T2 = T1 + datetime.timedelta(0, t_ser + t_move + 45)  # add time for safe move to first sat in ser
            else:
                T2 = T1 + datetime.timedelta(0, t_ser + t_move)  # 0 days and N seconds
                # t_ser + t_move ---> time for frames capture + move telescope to next point
            if T1 > end_T:
                print("Sunrise, h_sun -10...")
                f.close()
                sys.exit()

            Deren.date = T1.strftime("%Y/%m/%d %H:%M:%S")
            sat.geo.compute(Deren)
            if (sat.geo.elevation > 10) and (T1 < end_T):
                ra = sat.geo.ra
                ha = ephem.hours(Deren.sidereal_time() - sat.geo.ra + ephem.degrees("360.0"))
                dec = sat.geo.dec
                eclipsed = sat.geo.eclipsed

                if not eclipsed:
                    ha_s, dec_s = corr_ha_dec_s(ha, dec)
                    mag = "0.00"
                    T1_s = T1.strftime("%H%M%S")
                    T2_s = T2.strftime("%H%M%S")
                    # print("here we are", ha_s)
                    f.write(sat.NORAD + ' = ' + flag + ' ' + ha_s + '  ' + dec_s + '  ' + mag + ' '
                            + str_v_plan + T1_s + '-' + T2_s + '   ' + '# %s \n' % eclipsed)
                    geo_list[i].block = True
                else:  # eclipsed
                    geo_list[i].priority = geo_list[i].priority + 1
                    print(sat.NORAD, eclipsed)
                    x = 1
                    while eclipsed:
                        if i + x <= len(geo_list)-1:
                            sat = geo_list[i+x]

                            sat.geo.compute(Deren)
                            ra = sat.geo.ra
                            ha = ephem.hours(Deren.sidereal_time() - sat.geo.ra + ephem.degrees("360.0"))
                            dec = sat.geo.dec
                            eclipsed = sat.geo.eclipsed
                            print(sat.NORAD, eclipsed)
                        x = x + 1

                    print("changed to", sat.NORAD)

                    ha_s, dec_s = corr_ha_dec_s(ha, dec)
                    mag = "0.00"
                    T1_s = T1.strftime("%H%M%S")
                    T2_s = T2.strftime("%H%M%S")
                    # print("here we are", ha_s)
                    f.write(sat.NORAD + ' = ' + flag + ' ' + ha_s + '  ' + dec_s + '  ' + mag + ' '
                            + str_v_plan + T1_s + '-' + T2_s + '   ' + '# %s \n' % eclipsed)
                    geo_list[i + x - 1].block = True
            else:
                geo_list[i].priority = geo_list[i].priority + 1

        T1 = T2

f.close()
