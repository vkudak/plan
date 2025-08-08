import argparse

from skyfield.api import EarthSatellite, wgs84, load

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

# Check Python version
if sys.version_info[0] < 3 and sys.version_info[1] < 8:
    raise Exception(f"You are using Python {sys.version}. Must be using Python 3.8 or higher")


parser = argparse.ArgumentParser(description='Plan of GSO observation')
parser.add_argument('-c', '--config', help='Specify config file', required=False)
parser.add_argument('-o', '--objects', help='Specify file with objects', required=False)
args = vars(parser.parse_args())

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
site_lat = conf_res["site_lat"]
site_lon = conf_res["site_lon"]
site_elev = conf_res["site_elev"]
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
min_sat_h = conf_res["min_sat_h"]

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

mag = "0.00"
eph = load('de421.bsp')
site = wgs84.latlon(site_lat, site_lon, site_elev)
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
ts = load.timescale()
for sat in obj:
    # print(sat)
    for tle in TLE:
        if int(sat) == tle[-1]:
            # print(sat)

            tle[1] = fix_checksum(tle[1])  # fix checksum !!!!
            tle[2] = fix_checksum(tle[2])

            satellite = EarthSatellite(tle[1], tle[2], tle[0], ts)

            try:
                my_sat = Satellite(norad=sat, tle=tle,
                                    priority=0, sat=satellite, block=False,
                                    planed=[0] * series)
                my_sat.calc_pos(site, start_T, eph)
                geo_list.append(my_sat)
            except Exception as E:
                print(E, E.args)
                age = ts.now() - satellite.epoch
                print(
                    f"WARNING: Skip satellite {sat}, TLE too old "
                    f"for predictions: {age} days."
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
geo_list.sort(key=lambda x: x.ha_sort.hours, reverse=False)  # sort satellites by HA

# print(geo_list[-1].norad)
# print start_T
# start_T = start_T - datetime.timedelta(days=1)  # ----------------------<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
print("Start date = %s" % start_T.utc_datetime().strftime("%Y/%m/%d %H:%M:%S"))
print("End date = %s" % end_T.utc_datetime().strftime("%Y/%m/%d %H:%M:%S"))

f.write("# Start T = " + start_T.utc_datetime().strftime("%Y-%m-%d %H:%M:%S.%f") + "\n")

print("Start...")
flag = C
T1 = start_T
# series = 2


for ser in range(0, series):
    print("##################---Ser #%i" % (ser + 1))
    for msat in geo_list:
        msat.calc_pos(site, T1, eph)
    geo_list.sort(key=lambda x: x.ha_sort.hours, reverse=False)  # sort satellites by HA  !!!!!!


    f.write("# series N = %i \n" % (ser + 1))
    if ser > 0:
        T1 = T1 + timedelta(0, t_between_ser)
    for i in range(0, len(geo_list)):
        if geo_list[i].planed[ser] == 0:
            if (geo_list[i] == geo_list[0]) and (geo_list[i].priority == 0) and (ser > 0):
                T2 = T1 + timedelta(0, t_ser + t_move + 90)  # add time for safe move to first sat in series
            else:
                T2 = T1 + timedelta(0, t_ser + t_move)  # 0 days and N seconds
                # t_ser + t_move ---> time for frames capture + move telescope to next point
            if T1 > end_T:
                print_park(f, T1, park_ra, park_dec, t_exp, exp_wait)
                f.close()
                print("#####\nFinish. Sunrise, h_sun=%i..." % h_sun)
                sys.exit()
            T1_s = T1.utc_datetime().strftime("%H%M%S")
            T2_s = T2.utc_datetime().strftime("%H%M%S")

            # print(T1_s, T2_s)

            # # Deren.date = T1.utc_datetime().strftime("%Y/%m/%d %H:%M:%S")
            # ra, ha, dec = geo_list[i].calc_pos(site, T1)
            # # print("here...", ha, geo_list[i].HA)
            # # ra, dec = geo_list[i].sat.ra, geo_list[i].sat.dec

            geo_list[i].calc_pos(site, T1, eph)
            # print(geo_list[i].norad, T1.utc_datetime().strftime("%Y-%m-%d %H:%M:%S.%f"),  geo_list[i].pos['dec'])
            # ra_speed, dec_speed = calc_geo_speed(geo_list[i], site, T1, eph, flag=C)
            if flag == 'HA':
                ra_speed,dec_speed = geo_list[i].pos['hadec_speed']
            else:
                ra_speed,dec_speed = geo_list[i].pos['radec_speed']

            # !!!!!!!!!!!!!!!!!!!!!

            moon_sep = geo_list[i].pos['m_sep']
            # moon_sep = geo_list[i].calc_moon_sep(site, T1)
            # geo_list[i].calc_pos(site, T1)

            if (geo_list[i].pos['alt'].degrees > min_sat_h) and (T1 < end_T) and (moon_sep.degrees > float(moon_dist)):
                # if geo_list[i].sat.at(T1).is_sunlit(eph):
                if geo_list[i].pos['sunlit']:
                    # geo_list[i].calc_pos(site, T1)
                    ha = geo_list[i].pos["ha"]
                    dec = geo_list[i].pos["dec"]
                    ha_s, dec_s = corr_ha_dec_s(ha, dec)

                    # if geo_list[i].norad == '23855':
                    #     # geo_list[i].calc_pos(site, T1)
                    #     print(site)
                    #     print(geo_list[i].norad, T1.utc_datetime().strftime("%Y-%m-%d %H:%M:%S.%f"), geo_list[i].pos['dec'])
                    #     geo_list[i].calc_pos(site, T1)
                    #     print(geo_list[i].norad, T1.utc_datetime().strftime("%Y-%m-%d %H:%M:%S.%f"), geo_list[i].pos['dec'])

                    # print("here", geo_list[i].norad)

                    write_plan(
                        file=f,
                        tracking=tracking,
                        min_track_speed=min_track_speed,
                        ra_speed=ra_speed,
                        dec_speed=dec_speed,
                        geo = geo_list[i],
                        flag = flag,
                        T1_s = T1_s,
                        T2_s = T2_s,
                        str_v_plan = str_v_plan
                    )

                    geo_list[i].planed[ser] = 1
                else:  # eclipsed
                    geo_list[i].priority = geo_list[i].priority + 1
                    print("Satellite %s in series %i is eclipsed." % (geo_list[i].norad, ser+1))
                    if debug:
                        f.write("# %s is eclipsed skipping..\n" % geo_list[i].norad)
                    x = 1
                    sat = geo_list[i]
                    found = False
                    while not sat.pos['sunlit'] or sat.planed[ser] == 1:
                        if i + x <= len(geo_list)-1:
                            sat = geo_list[i+x]
                            pos = sat.calc_pos(site, T1, eph)
                            ha = pos["ha"]
                            dec = pos["dec"]
                            if sat.pos['sunlit']:
                                found = True
                        else:
                            break
                        x = x + 1

                    if found:
                        if debug:
                            f.write(f"# changed to {sat.norad} \n")

                        # geo_list[i].calc_pos(site, T1)
                        ha_s, dec_s = corr_ha_dec_s(ha, dec)
                        print(f"Changed to {sat.norad}")
                        # ra_speed, dec_speed = calc_geo_speed(sat, site, T1, eph, flag=C)
                        if flag == 'HA':
                            ra_speed, dec_speed = geo_list[i].pos['hadec_speed']
                        else:
                            ra_speed, dec_speed = geo_list[i].pos['radec_speed']

                        write_plan(
                            file=f,
                            tracking=tracking,
                            min_track_speed=min_track_speed,
                            ra_speed=ra_speed,
                            dec_speed=dec_speed,
                            geo=sat, # geo_list[i + x - 1],
                            flag=flag,
                            T1_s=T1_s,
                            T2_s=T2_s,
                            str_v_plan=str_v_plan
                        )
                        geo_list[i + x - 1].planed[ser] = 1
            else:
                geo_list[i].priority = geo_list[i].priority + 1
                if debug:
                    f.write("# skip satellite %s, h= %s, Moon sep=%s\n" %
                            (geo_list[i].norad, str(geo_list[i].pos['alt']), str(moon_sep)))
                if geo_list[i].pos['alt'].degrees < min_sat_h:
                    print("Skip satellite %s in series %i, because of small elevation - h=%s" %
                          (geo_list[i].norad, ser+1, geo_list[i].pos['alt'].dstr(format='{0:+>1}{1:02}:{2:02}:{3:02}')))
                if moon_sep.degrees < float(moon_dist):
                    print("Skip satellite %s in series %i, because of Moon sep = %s" %
                          (geo_list[i].norad, ser+1, moon_sep.dstr(format='{0}{1:02}:{2:02}:{3:02} degrees')))
                T2 = T1

            # CHECK if some unplanned satellites are available now...
            # print (i, len(geo_list)-1)
            added = False
            if i == len(geo_list)-1:
                # print("HERE NOW!!!!!!!!!!!!!!!!!!!")
                for j in range(0, len(geo_list)):
                    # ha = geo_list[j].calc_pos(site, T1)['ha']
                    if (geo_list[j].planed[ser] == 0) and (geo_list[j].pos['sunlit']) and \
                            (geo_list[j].pos["alt"].degrees > min_sat_h) and (moon_sep.degrees < float(moon_dist)):
                        T1 = T2
                        T2 = T1 + timedelta(0, t_ser + t_move)
                        T1_s = T1.utc_datetime().strftime("%H%M%S")
                        T2_s = T2.utc_datetime().strftime("%H%M%S")

                        geo_list[j].calc_pos(site, T1, eph)
                        ha_s, dec_s = corr_ha_dec_s(geo_list[j].pos["ha"], geo_list[j].pos["dec"])
                        print(f"Satellite {geo_list[j].norad} is out of eclipse, added to the end of series {ser + 1}")
                        # ra_speed, dec_speed = calc_geo_speed(geo_list[i], site, T1, eph, flag=C)
                        if flag == 'HA':
                            ra_speed, dec_speed = geo_list[j].pos['hadec_speed']
                        else:
                            ra_speed, dec_speed = geo_list[j].pos['radec_speed']

                        write_plan(
                            file=f,
                            tracking=tracking,
                            min_track_speed=min_track_speed,
                            ra_speed=ra_speed,
                            dec_speed=dec_speed,
                            geo=geo_list[j],
                            flag=flag,
                            T1_s=T1_s,
                            T2_s=T2_s,
                            str_v_plan=str_v_plan
                        )
                        geo_list[j].planed[ser] = 1
                        added = True
            ###
            if (geo_list[i].pos["alt"].degrees > min_sat_h) and (moon_sep.degrees > float(moon_dist)) and (not added):
                T1 = T2
            if added:
                T1 = T2
if park:
    print_park(f, T1, park_ra, park_dec, t_exp, exp_wait)
print(f"#####\nFinish. {series} series calculated.")
f.close()
