# import numpy as np
# import glob, os, sys
# import datetime
# import ephem
import argparse
import configparser

from astropy.coordinates import Angle
from skyfield.api import EarthSatellite, load, wgs84, Topos, N, W, E, S
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


parser = argparse.ArgumentParser(description='Plan of GSO observation')
parser.add_argument('-c', '--config', help='Specify config file', required=False)
parser.add_argument('-o', '--objects', help='Specify file with objects', required=False)
args = vars(parser.parse_args())


def read_config(conf_file):
    """
    :param conf_file: name of config file
    :return: dict of parameters
    """
    config = configparser.ConfigParser(inline_comment_prefixes="#")

    if os.path.isfile(conf_file):
        try:
            config.read(conf_file)

            c_debug = config.getboolean('global', 'debug', fallback=False)

            c_plan_type = config.get("options", 'plan_type', fallback="HA")
            c_h_sun = config.getfloat('options', 'h_sun', fallback=-12)
            c_series = config.getint('options', 'series', fallback=7)
            c_t_move = config.getint('options', 't_move', fallback=40)
            c_t_exp = config.getfloat('options', 't_exp', fallback=12)
            c_n_frames = config.getint('options', 'n_frames', fallback=10)
            c_exp_wait = config.getint('options', 'exp_wait', fallback=0)
            c_t_between_ser = config.getfloat('options', 't_between_ser', fallback=300)
            c_track = config.getboolean('options', 'track', fallback=False)
            c_min_track_speed = config.getfloat('options', 'min_track_speed', fallback=0.1)
            c_band = config.get("options", 'filter', fallback=None)

            c_park = config.getboolean('park', 'park', fallback=True)
            c_park_ra = config.get("park", 'park_RA', fallback="194821.45")
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
                    "track": c_track,
                    "min_track_speed": c_min_track_speed,
                    "band": c_band,
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


if args["config"]:
    config_name = args["config"]
else:
    print("Search for configuration in default filename - config.ini")
    config_name = "config.ini"

if args["objects"]:
    objects_file = args["objects"]
else:
    print("Search for targets in default filename - planed_objects.txt")
    objects_file = "planed_objects.txt"

conf_res = read_config(conf_file=config_name)

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
min_track_speed = conf_res["min_track_speed"]

park_ra = conf_res['park_ra']
park_dec = conf_res['park_dec']

tracking = conf_res['track']
band = conf_res["band"]
if band == "None":
    band = None

moon_ph = moon_phase()
print(f"Moon phase is {moon_phase():.1f} %")

moon_dist = "10"
if moon_ph < 50:
    moon_dist = str(conf_res["moon_dist1"])  # "30"
elif moon_ph > 50:
    moon_dist = str(conf_res["moon_dist2"])  # "40"
print(f"Moon distance will be {moon_dist} degrees")

t_ser = n_frames * (t_exp + 3 + exp_wait)  # 3 - readout,

if band is None or band == "":
    str_v_plan = f"{n_frames}x{t_exp}:{exp_wait} @"
else:
    str_v_plan = f"{n_frames}x{t_exp}:{exp_wait}*{band} @"


ndate = datetime.now().strftime("%Y%m%d")
f = open('object_' + C + '_' + ndate + '.list', 'w')

for k, v in conf_res.items():
    f.write(f"# {k} = {v}\n")
f.write("#\n")


site = wgs84.latlon(48.5635505, 22.453751, 231)
[start_T, end_T] = calc_t_twilight(site,  h_sun=h_sun)
# print(start_T.utc)
# print(end_T.utc)
# print(calc_T_twilight())

# start_T = datetime.datetime(year=2023, month=2, day=9, hour=22, minute=0, second=0)

obj = read_planed_objects(objects_file)
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

bad_sat = []
for sat in obj:
    # print(sat)
    for tle in TLE:
        if int(sat) == tle[-1]:
            # print(sat)

            tle[1] = fix_checksum(tle[1])  # fix checksum !!!!
            tle[2] = fix_checksum(tle[2])

            ts = load.timescale()
            satellite = EarthSatellite(tle[1], tle[2], tle[0], ts)

            try:
                # geocentric = satellite.at(t)
                difference = satellite - site
                topocentric = difference.at(start_T)
                # ra, dec, distance = topocentric.radec()
                ha, dec, distance = topocentric.hadec()
                # print(sat, ha.hours)
                ha = ha.hours

                # geo.compute(Deren)
                # ha = ephem.hours(Deren.sidereal_time() - geo.ra)  # -12 to +12.
                geo_list.append(
                                Satellite(norad=sat, ha=ha, tle=tle,
                                          priority=0, sat=satellite, block=False,
                                          planed=[0] * series)
                )
            except Exception as E:
                # print(E, E.args)
                age = ts.now() - satellite.epoch
                print(
                    f"WARNING: Skip satellite {sat}, TLE too old "
                    f"for predictions: {age.days} days."
                )
                bad_sat.append(sat)


for bad in bad_sat:
    # remove satellites with problems in TLE
    obj.remove(bad)

for sat in obj:
    eps = True
    for ge in geo_list:
        if sat == ge.norad:
            eps = False
    if eps:
        print("WARNING: Satellite %s has no TLE data" % sat)


print("Satellites planned = %i" % len(geo_list))
geo_list.sort(key=lambda x: x.ha, reverse=False)  # sort satellites by HA

# print(geo_list[-1].norad)
# print start_T
# start_T = start_T - datetime.timedelta(days=1)  # ----------------------<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
print("Start date = %s" % start_T.utc_datetime().strftime("%Y/%m/%d %H:%M:%S"))
print("End date = %s" % end_T.utc_datetime().strftime("%Y/%m/%d %H:%M:%S"))

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
        ha, dec = geo_list[v].calc_hadec(site, T1)
        # ha = ephem.hours(Deren.sidereal_time() - geo_list[v].geo.ra)  # -12 to +12.
        ha2 = ha

        #  angle(hours=-1.5).hstr(format='{0}{1:02}:{2:02}:{3:02}')
        # https://rhodesmill.org/skyfield/api-units.html

        if ha._degrees > Angle(hours=12)._degrees: #ephem.hours("12:00:00"):
            ha2 = ha - Angle(degrees=360.0)
        if ha._degrees < Angle(hours=-12)._degrees: #ephem.hours("-12:00:00"):
            ha2 = ha + Angle(degrees=360.0)
        # print(ha, ha2, ha > ephem.hours("12:00:00"))
        geo_list[v].ha = ha2
    geo_list.sort(key=lambda x: x.ha._degrees, reverse=False)  # sort satellites by HA  !!!!!!
    #
    # for v in range(0, len(geo_list)):
    #     print(v, geo_list[v].norad, geo_list[v].HA)
    # ###############################################################

    f.write("# series N = %i \n" % (ser + 1))
    if ser > 0:
        T1 = T1 + timedelta(0, t_between_ser)
    for i in range(0, len(geo_list)):
        # print(i, geo_list[i].norad, geo_list[i].geo.eclipsed, geo_list[i].geo.alt)
        # sat = geo_list[i]
        if geo_list[i].planed[ser] == 0:
            if (geo_list[i] == geo_list[0]) and (geo_list[i].priority == 0) and (ser > 0):
                T2 = T1 + timedelta(0, t_ser + t_move + 90)  # add time for safe move to first sat in series
            else:
                T2 = T1 + timedelta(0, t_ser + t_move)  # 0 days and N seconds
                # t_ser + t_move ---> time for frames capture + move telescope to next point
            if T1 > end_T:
                print_park(T1, f, park_ra, park_dec)
                f.close()
                print("#####\nFinish. Sunrise, h_sun=%i..." % h_sun)
                sys.exit()
            mag = "0.00"
            T1_s = T1.utc_datetime().strftime("%H%M%S")
            T2_s = T2.utc_datetime().strftime("%H%M%S")

            # Deren.date = T1.utc_datetime().strftime("%Y/%m/%d %H:%M:%S")
            ha = geo_list[i].calc(site, T1)
            # print("here...", ha, geo_list[i].HA)
            ra, dec = geo_list[i].sat.ra, geo_list[i].sat.dec
            ra_speed, dec_speed = calc_geo_speed(geo=geo_list[i], site=site, date=T1, flag=C)

            # !!!!!!!!!!!!!!!!!!!!!

            moon_sep = geo_list[i].calc_moon_angle(Deren)
            if (geo_list[i].geo.alt > ephem.degrees("10")) and (T1 < end_T) and (moon_sep > ephem.degrees(moon_dist)):
                if not geo_list[i].geo.eclipsed:
                    ha_s, dec_s = corr_ha_dec_s(ha, geo_list[i].geo.dec)
                    if tracking and (abs(ra_speed) > min_track_speed or abs(dec_speed) > min_track_speed):
                        my_line = (f"{geo_list[i].norad} = {flag} {ha_s}"
                                   f"({ra_speed:3.2f})  {dec_s}({dec_speed:3.2f}) "
                                   f"{mag} {str_v_plan}{T1_s}-{T2_s}\n"
                                   )
                        f.write(my_line)
                    else:
                        my_line = f"{geo_list[i].norad} = {flag} {ha_s}  {dec_s} {mag} {str_v_plan}{T1_s}-{T2_s}\n"
                        f.write(my_line)
                        # f.write(geo_list[i].norad + ' = ' + flag + ' ' + ha_s + '  ' + dec_s + '  ' + mag + ' '
                        #         + str_v_plan + T1_s + '-' + T2_s + '   ' + '\n')
                    # geo_list[i].block = True
                    geo_list[i].planed[ser] = 1
                else:  # eclipsed
                    geo_list[i].priority = geo_list[i].priority + 1
                    print("Satellite %s in series %i is eclipsed." % (geo_list[i].norad, ser+1))
                    if debug:
                        f.write("# %s is eclipsed skipping..\n" % geo_list[i].norad)
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
                            # print(sat.norad, sat.geo.eclipsed)
                        else:
                            break
                        x = x + 1

                    if found:
                        if debug:
                            f.write("# changed to %s \n" % sat.norad)

                        # T1 = T2
                        # T2 = T1 + datetime.timedelta(0, t_ser + t_move)
                        # T1_s = T1.strftime("%H%M%S")
                        # T2_s = T2.strftime("%H%M%S")
                        ha_s, dec_s = corr_ha_dec_s(ha, dec)
                        print("Changing it to %s"% sat.norad)
                        ra_speed, dec_speed = calc_geo_speed(geo=sat, site=Deren, date=Deren.date, flag=C)
                        if tracking and (abs(ra_speed)> min_track_speed or abs(dec_speed) > min_track_speed):
                            f.write(
                                (f"{sat.norad} = {flag} {ha_s}({ra_speed:3.2f})  "
                                 f"{dec_s}({dec_speed:3.2f}) {mag} {str_v_plan}{T1_s}-{T2_s}\n")
                            )
                        else:
                            f.write(f"{sat.norad} = {flag} {ha_s}  {dec_s} {mag} {str_v_plan}{T1_s}-{T2_s}\n")
                            # sat.norad + ' = ' + flag + ' ' + ha_s + '  ' + dec_s + '  ' + mag + ' '
                            #     + str_v_plan + T1_s + '-' + T2_s + '   ' + '\n')
                        # geo_list[i + x - 1].block = True
                        geo_list[i + x - 1].planed[ser] = 1
            else:
                geo_list[i].priority = geo_list[i].priority + 1
                if debug:
                    f.write("# skip satellite %s, h= %s, Moon sep=%s\n" %
                            (geo_list[i].norad, str(geo_list[i].geo.alt), str(moon_sep)))
                if geo_list[i].geo.alt < ephem.degrees("10"):
                    print("Skip satellite %s in series %i, because of small elevation - h= %s" %
                          (geo_list[i].norad, ser+1, str(geo_list[i].geo.alt)))
                    # T1 = T2
                    # T2 = T1 + datetime.timedelta(0, t_ser + t_move)
                if moon_sep < ephem.degrees(moon_dist):
                    print("Skip satellite %s in series %i, because of Moon sep = %s" %
                          (geo_list[i].norad, ser+1, str(moon_sep)))
                T2 = T1

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
                            (geo_list[j].geo.alt > ephem.degrees("10")) and (moon_sep < ephem.degrees(moon_dist)):
                        T1 = T2
                        T2 = T1 + datetime.timedelta(0, t_ser + t_move)
                        T1_s = T1.strftime("%H%M%S")
                        T2_s = T2.strftime("%H%M%S")
                        ha_s, dec_s = corr_ha_dec_s(ha, geo_list[j].geo.dec)
                        print("Satellite %s is out of eclipse, added to the end of series %i " %
                              (geo_list[j].norad, ser + 1))
                        ra_speed, dec_speed = calc_geo_speed(geo=geo_list[i], site=Deren, date=Deren.date, flag=C)
                        if tracking and (abs(ra_speed)> min_track_speed or abs(dec_speed) > min_track_speed):
                            f.write(
                                (f"{geo_list[j].norad} = {flag} {ha_s}({ra_speed:3.2f})  "
                                 f"{dec_s}({dec_speed:3.2f}) {mag} {str_v_plan}{T1_s}-{T2_s}\n"
                                 )
                            )
                        else:
                            f.write(
                                f"{geo_list[j].norad} = {flag} {ha_s}  {dec_s} {mag} {str_v_plan}{T1_s}-{T2_s}\n")
                            # f.write(geo_list[j].norad + ' = ' + flag + ' ' + ha_s + '  ' + dec_s + '  ' + mag + ' '
                            #         + str_v_plan + T1_s + '-' + T2_s + '   ' + '\n')
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
