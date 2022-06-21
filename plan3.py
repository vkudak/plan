# import numpy as np
# import glob, os, sys
# import datetime
# import ephem
from plan_io import *
import glob
# https://rhodesmill.org/skyfield/earth-satellites.html  ?????
# https://github.com/brandon-rhodes/python-sgp4  !!!!!!!!


#  Main begin here------------------------------------------------------------------------------------------
# 36581 = HA 235508.25 -071108.39   0.00 8x10 @173600-173900
# 26853 = HA 235420.60 -040736.63   0.00 8x10:30 @173900-174200

# print "------Twilight (h_sun=-10)--"
# print calc_T_twilight()
# print "--------------------------"

def print_park(T1, file):
    if park:
        T1_s = T1.strftime("%H%M%S")
        T2 = T1 + datetime.timedelta(0, 30)
        T2_s = T2.strftime("%H%M%S")
        str_v_plan_p = str(1) + "x" + str(t_exp) + " @"
        file.write('park  = ' + "HA" + ' ' + '194821.45  -064724.7' + '  ' + mag + ' '
                                    + str_v_plan_p + T1_s + '-' + T2_s + '   ' + '\n')
        # park  = HA 194818.02  -064718.6  0.00 7x12.0:30 @011036-011251


debug = False  # True
park = True
C = 'HA'  # HA
h_sun = -10
series = 5
t_move = 40
t_exp = 12.0
n_frames = 7
exp_wait = 30 #30  # interval between frames
t_between_ser = 0  # 60 * 5 seconds dead time between series
# t_miz_ser = 3.6*60*60

t_ser = n_frames * (t_exp + 3 + exp_wait)  # 3 - readout, 
str_v_plan = str(n_frames) + "x" + str(t_exp) + ":" + str(exp_wait) + " @" 

ndate = datetime.datetime.now().strftime("%Y%m%d")
f = open('object_' + C + '_' + ndate + '.list', 'w')
start_T, end_T = calc_T_twilight(h_sun=h_sun)
# start_T = datetime.datetime(year=2021, month=9, day=14, hour=18, minute=0, second=0)

obj = read_planed_objects('planed_objects.txt')
print("Satellites to plan = %i " % len(obj))
if not os.path.isdir('tle'):
    print("Error !!!! No TLE files in 'tle' directory")
    sys.exit()
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
    # print(sat)
    for tle in TLE:
        if int(sat) == tle[-1]:
            # print(sat)

            tle[1] = fix_checksum(tle[1])  # fix checksum !!!!
            tle[2] = fix_checksum(tle[2])

            geo = ephem.readtle(tle[0], tle[1], tle[2])
            Deren.date = start_T.strftime("%Y/%m/%d %H:%M:%S")  # "2021/09/17 18:00:00" #'2003/3/23 H:M:S'
            geo.compute(Deren)
            ha = ephem.hours(Deren.sidereal_time() - geo.ra)  # -12 to +12.
            #                                                 To convert 0-24 do + h<0 : geo.ra + ephem.degrees("360.0")
            # if ha < 0:
            #     ha = ephem.hours(Deren.sidereal_time() - geo.ra + ephem.degrees("360.0"))
            # print("NORAD=", sat, "DATE=", Deren.date,
            #       ', ST=', Deren.sidereal_time(),
            #       "RA=", geo.ra,
            #       "HA=", ha, geo.eclipsed)
            geo_list.append(Satellite(NORAD=sat, HA=ha, TLE=tle, priority=0, geo=geo, block=False, planed=[0] * series))
            # geo_list[-1].planed = [0] * series

for sat in obj:
    eps = True
    for ge in geo_list:
        if sat == ge.NORAD:
            eps = False
    if eps:
        print("Warning !!!!  Satellite %s has no TLE data" % sat)

print("Satellites planned = %i" % len(geo_list))
geo_list.sort(key=lambda x: x.HA, reverse=False)  # sort satellites by HA

# print(geo_list[-1].NORAD)
# print start_T
# start_T = start_T - datetime.timedelta(days=1)  # ----------------------<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
print("Start date = %s" % start_T.strftime("%Y/%m/%d %H:%M:%S"))
print("End date = %s" % end_T.strftime("%Y/%m/%d %H:%M:%S"))

f.write("# Start T = " + str(start_T) + "\n")

print("Start...")
flag = C
T1 = start_T
# series = 2
for ser in range(0, series):
    print("##################---Ser #%i" % (ser + 1))
    # geo_list.sort(key=lambda x: x.HA, reverse=False)  # sort satellites by HA  !!!!!!
    # sort again !!!!!!!!!!!!!!!!!!!!!!!!!
    for v in range(0, len(geo_list)):
        Deren.date = T1.strftime("%Y/%m/%d %H:%M:%S")
        geo_list[v].geo.compute(Deren)
        ha = ephem.hours(Deren.sidereal_time() - geo_list[v].geo.ra)  # -12 to +12.
        ha2 = ha
        if ha > ephem.hours("12:00:00"):
            ha2 = ephem.hours(Deren.sidereal_time() - geo_list[v].geo.ra - ephem.degrees("360.0"))
        if ha < ephem.hours("-12:00:00"):
            ha2 = ephem.hours(Deren.sidereal_time() - geo_list[v].geo.ra + ephem.degrees("360.0"))
        # print(ha, ha2, ha > ephem.hours("12:00:00"))
        geo_list[v].HA = ha2
    geo_list.sort(key=lambda x: x.HA, reverse=False)  # sort satellites by HA  !!!!!!
    #
    # for v in range(0, len(geo_list)):
    #     print(v, geo_list[v].NORAD, geo_list[v].HA)
    # ###############################################################

    f.write("# series N = %i \n" % (ser + 1))
    if ser > 0:
        T1 = T1 + + datetime.timedelta(0, t_between_ser)
    for i in range(0, len(geo_list)):
        # print(i, geo_list[i].NORAD, geo_list[i].geo.eclipsed, geo_list[i].geo.alt)
        # sat = geo_list[i]
        if geo_list[i].planed[ser] == 0:
            if (geo_list[i] == geo_list[0]) and (geo_list[i].priority == 0) and (ser > 0):
                T2 = T1 + datetime.timedelta(0, t_ser + t_move + 90)  # add time for safe move to first sat in series
            else:
                T2 = T1 + datetime.timedelta(0, t_ser + t_move)  # 0 days and N seconds
                # t_ser + t_move ---> time for frames capture + move telescope to next point
            if T1 > end_T:
                print_park(T1, f)
                f.close()
                print("#####\nFinish. Sunrise, h_sun=%i..." % h_sun)
                sys.exit()
            mag = "0.00"
            T1_s = T1.strftime("%H%M%S")
            T2_s = T2.strftime("%H%M%S")

            Deren.date = T1.strftime("%Y/%m/%d %H:%M:%S")
            ha = geo_list[i].calc(Deren)
            # print("here...", ha, geo_list[i].HA)
            ra, dec = geo_list[i].geo.ra, geo_list[i].geo.dec
            moon_sep = geo_list[i].calc_moon_angle(Deren)
            if (geo_list[i].geo.alt > ephem.degrees("10")) and (T1 < end_T) and (moon_sep > ephem.degrees("10")):
                if not geo_list[i].geo.eclipsed:
                    ha_s, dec_s = corr_ha_dec_s(ha, geo_list[i].geo.dec)
                    f.write(geo_list[i].NORAD + ' = ' + flag + ' ' + ha_s + '  ' + dec_s + '  ' + mag + ' '
                            + str_v_plan + T1_s + '-' + T2_s + '   ' + '\n')
                    # geo_list[i].block = True
                    geo_list[i].planed[ser] = 1
                else:  # eclipsed
                    geo_list[i].priority = geo_list[i].priority + 1
                    print("Satellite %s in series %i is eclipsed." % (geo_list[i].NORAD, ser+1))
                    if debug:
                        f.write("# %s is eclipsed skipping..\n" % geo_list[i].NORAD)
                    x = 1
                    sat = geo_list[i]
                    found = False
                    while sat.geo.eclipsed or sat.planed[ser] == 1:
                        if i + x <= len(geo_list)-1:
                            sat = geo_list[i+x]
                            Deren.date = T1.strftime("%Y/%m/%d %H:%M:%S")
                            ha = sat.calc(Deren)
                            ra, dec = sat.geo.ra, sat.geo.dec
                            if not sat.geo.eclipsed:
                                found = True
                            # print(sat.NORAD, sat.geo.eclipsed)
                        else:
                            break
                        x = x + 1

                    if found:
                        if debug:
                            f.write("# changed to %s \n" % sat.NORAD)

                        # T1 = T2
                        # T2 = T1 + datetime.timedelta(0, t_ser + t_move)
                        # T1_s = T1.strftime("%H%M%S")
                        # T2_s = T2.strftime("%H%M%S")
                        ha_s, dec_s = corr_ha_dec_s(ha, dec)
                        print("Changing it to %s"% sat.NORAD)
                        f.write(sat.NORAD + ' = ' + flag + ' ' + ha_s + '  ' + dec_s + '  ' + mag + ' '
                                + str_v_plan + T1_s + '-' + T2_s + '   ' + '\n')
                        # geo_list[i + x - 1].block = True
                        geo_list[i + x - 1].planed[ser] = 1
            else:
                geo_list[i].priority = geo_list[i].priority + 1
                if debug:
                    f.write("# skip satellite %s, h= %s, Moon sep=%s\n" %
                            (geo_list[i].NORAD, str(geo_list[i].geo.alt), str(moon_sep)))
                if geo_list[i].geo.alt < ephem.degrees("10"):
                    print("Skip satellite %s in series %i, because of small elevation - h= %s" %
                          (geo_list[i].NORAD, ser+1, str(geo_list[i].geo.alt)))
                    # T1 = T2
                    # T2 = T1 + datetime.timedelta(0, t_ser + t_move)
                if moon_sep < ephem.degrees("10"):
                    print("Skip satellite %s in series %i, because of Moon sep = %s" %
                          (geo_list[i].NORAD, ser+1, str(moon_sep)))

            # CHECK if some unplanned satellites are available now...
            # print (i, len(geo_list)-1)
            added = False
            if i == len(geo_list)-1:
                # print("HERE NOW!!!!!!!!!!!!!!!!!!!")
                for j in range(0, len(geo_list)):
                    Deren.date = T1.strftime("%Y/%m/%d %H:%M:%S")
                    ha = geo_list[j].calc(Deren)
                    # print(j, geo_list[j].planed[ser], geo_list[j].geo.eclipsed)
                    if (geo_list[j].planed[ser] == 0) and (not geo_list[j].geo.eclipsed) and \
                            (geo_list[j].geo.alt > ephem.degrees("10")):
                        T1 = T2
                        T2 = T1 + datetime.timedelta(0, t_ser + t_move)
                        T1_s = T1.strftime("%H%M%S")
                        T2_s = T2.strftime("%H%M%S")
                        ha_s, dec_s = corr_ha_dec_s(ha, geo_list[j].geo.dec)
                        print("Satellite %s is out of eclipse, added to the end of series %i " %
                              (geo_list[j].NORAD, ser + 1))
                        f.write(geo_list[j].NORAD + ' = ' + flag + ' ' + ha_s + '  ' + dec_s + '  ' + mag + ' '
                                + str_v_plan + T1_s + '-' + T2_s + '   ' + '\n')
                        geo_list[j].planed[ser] = 1
                        added = True
            ###
            if (geo_list[i].geo.alt > ephem.degrees("10")) and (moon_sep > ephem.degrees("10")) and (not added):
                T1 = T2
            if added:
                T1 = T2
print_park(T1, f)
print("#####\nFinish. %i series calculated." % series)
f.close()
