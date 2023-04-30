# import numpy as np
# import glob, os, sys
# import datetime
# import ephem
import configparser
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


def read_config():
    config = configparser.ConfigParser(inline_comment_prefixes="#")

    if os.path.isfile('config.ini'):
        try:
            config.read('config.ini')

            c_debug = config.getboolean('global', 'debug', fallback=False)

            c_plan_type = config.get("options", 'plan_type', fallback="HA")
            c_h_sun = config.getfloat('options', 'h_sun', fallback=-12)
            c_series = config.getint('options', 'series', fallback=7)
            c_t_move = config.getint('options', 't_move', fallback=40)
            c_t_exp = config.getfloat('options', 't_exp', fallback=12)
            c_n_frames = config.getint('options', 'n_frames', fallback=10)
            c_exp_wait = config.getfloat('options', 'exp_wait', fallback=0)
            c_t_between_ser = config.getfloat('options', 't_between_ser', fallback=300)

            c_park = config.getboolean('park', 'park', fallback=True)
            c_park_ra= config.get("park", 'park_RA', fallback="194821.45")
            c_park_dec = config.get("park", 'park_DEC', fallback="-084724.7")

            c_moon1 = config.getfloat('Moon', 'dist1', fallback=30)
            c_moon2 = config.getfloat('Moon', 'dist2', fallback=40)

            return {'debug': c_debug,
                    'plan_type': c_plan_type,
                    'h_sun': c_h_sun,
                    'series': c_series,
                    't_move': c_t_move,
                    't_exp': c_t_exp,
                    'n_frames': c_n_frames,
                    'exp_wait': c_exp_wait,
                    't_between_ser': c_t_between_ser,
                    'park': c_park,
                    'park_ra': c_park_ra,
                    'park_dec': c_park_dec,
                    'moon_dist1': c_moon1,
                    'moon_dist2': c_moon2,
                    }

        except Exception as E:
            print("Error in INI file\n", E)
            sys.exit()
    else:
        print("Error. Cant find config_sat.ini")
        sys.exit()


def print_park(T1, file, park_ra, park_dec):
    if park:
        T1_s = T1.strftime("%H%M%S")
        T2 = T1 + datetime.timedelta(0, 30)
        T2_s = T2.strftime("%H%M%S")
        park_radec = park_ra + "  " + park_dec
        str_v_plan_p = str(1) + "x" + str(t_exp) + " @"
        file.write('park  = ' + "HA" + ' ' + park_radec + '  ' + mag + ' '
                                    + str_v_plan_p + T1_s + '-' + T2_s + '   ' + '\n')
        # file.write('park  = ' + "HA" + ' ' + '194821.45  -084724.7' + '  ' + mag + ' '
        #                             + str_v_plan_p + T1_s + '-' + T2_s + '   ' + '\n')
        # park  = HA 194818.02  -064718.6  0.00 7x12.0:30 @011036-011251


# debug = False  # True
# park = True
# C = 'HA'  # HA
# h_sun = -12
# series = 7
# t_move = 40
# t_exp = 12.0
# n_frames = 10
# exp_wait = 0 #20 #30  # interval between frames
# t_between_ser = 30*10  # 60 * 5 seconds dead time between series
# # t_miz_ser = 3.6*60*60


conf_res = read_config()

debug = conf_res["debug"]
park = conf_res["park"]
C = conf_res["plan_type"]  # HA
h_sun = conf_res["h_sun"]
series = conf_res["series"]
t_move = conf_res["t_move"]
t_exp = conf_res["t_exp"]
n_frames = conf_res["n_frames"]
exp_wait = conf_res["exp_wait"]  # 20 #30  # interval between frames
t_between_ser = conf_res["t_between_ser"]  # 30*10  # 60 * 5 seconds dead time between series

park_ra = conf_res['park_ra']
park_dec = conf_res['park_dec']


moon_ph = moon_phase()
print(f"Moon phase is {moon_phase():.1f} %")

moon_dist = "10"
if moon_ph < 50:
    moon_dist = str(conf_res["moon_dist1"])  # "30"
elif moon_ph > 50:
    moon_dist = str(conf_res["moon_dist2"])  # "40"
print(f"Moon distance will be {moon_dist} degrees")

t_ser = n_frames * (t_exp + 3 + exp_wait)  # 3 - readout, 
str_v_plan = str(n_frames) + "x" + str(t_exp) + ":" + str(exp_wait) + " @" 

ndate = datetime.datetime.now().strftime("%Y%m%d")
f = open('object_' + C + '_' + ndate + '.list', 'w')
start_T, end_T = calc_T_twilight(h_sun=h_sun)
# start_T = datetime.datetime(year=2023, month=2, day=9, hour=22, minute=0, second=0)

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
                print_park(T1, f, park_ra, park_dec)
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
            if (geo_list[i].geo.alt > ephem.degrees("10")) and (T1 < end_T) and (moon_sep > ephem.degrees(moon_dist)):
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
print_park(T1, f, park_ra, park_dec)
print("#####\nFinish. %i series calculated." % series)
f.close()
