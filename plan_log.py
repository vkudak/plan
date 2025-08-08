import os
import sys
import glob
import logging
from datetime import datetime, timedelta
import argparse

from skyfield.api import EarthSatellite, wgs84, load

from plan_io import *  # Твої функції читання config, планування, тощо


def setup_logger():
    # Створюємо папку logs, якщо немає
    if not os.path.exists('logs'):
        os.makedirs('logs')

    log_filename = datetime.now().strftime('%y%m%d_%H%M%S') + '.log'
    log_path = os.path.join('logs', log_filename)

    logger = logging.getLogger('plan_logger')
    logger.setLevel(logging.DEBUG)

    # Файл хендлер — все DEBUG і вище
    fh = logging.FileHandler(log_path, encoding='utf-8')
    fh.setLevel(logging.DEBUG)

    # Формат логів: час, рівень, повідомлення
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)

    logger.addHandler(fh)

    return logger


def main():
    logger = setup_logger()

    # Перевірка Python версії
    if sys.version_info < (3, 8):
        print(f"You are using Python {sys.version}. Must be Python 3.8 or higher.")
        sys.exit(1)

    parser = argparse.ArgumentParser(description='Plan of GSO observation')
    parser.add_argument('-c', '--config', help='Specify config file', required=False)
    parser.add_argument('-o', '--objects', help='Specify file with objects', required=False)
    args = vars(parser.parse_args())

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
    C = conf_res["plan_type"]
    h_sun = conf_res["h_sun"]
    series = conf_res["series"]
    t_move = conf_res["t_move"]
    t_exp = conf_res["t_exp"]
    n_frames = conf_res["n_frames"]
    exp_wait = conf_res["exp_wait"]
    t_between_ser = conf_res["t_between_ser"]
    min_track_speed = conf_res["min_track_speed"]
    min_sat_h = conf_res["min_sat_h"]

    park_ra = conf_res['park_ra']
    park_dec = conf_res['park_dec']

    tracking = conf_res['track']
    band = conf_res["band"]
    if band == "None":
        band = None

    moon_ph = moon_phase()
    print(f"Moon phase is {moon_ph:.1f} %")
    logger.info(f"Moon phase is {moon_ph:.1f} %")

    moon_dist = "10"
    if moon_ph < 50:
        moon_dist = str(conf_res["moon_dist1"])
    elif moon_ph > 50:
        moon_dist = str(conf_res["moon_dist2"])
    print(f"Moon distance will be {moon_dist} degrees")
    logger.info(f"Moon distance will be {moon_dist} degrees")

    t_ser = n_frames * (t_exp + 3 + exp_wait)

    if band is None or band == "":
        str_v_plan = f"{n_frames}x{t_exp}:{exp_wait} @"
    else:
        str_v_plan = f"{n_frames}x{t_exp}:{exp_wait}*{band} @"

    ndate = datetime.now().strftime("%Y%m%d")
    f = open('object_' + C + '_' + ndate + '.list', 'w')

    for k, v in conf_res.items():
        f.write(f"# {k} = {v}\n")
    f.write("#\n")

    eph = load('de421.bsp')
    site = wgs84.latlon(site_lat, site_lon, site_elev)
    start_T, end_T = calc_t_twilight(site, h_sun=h_sun)

    obj = read_planed_objects(objects_file)
    print(f"Satellites to plan = {len(obj)}")
    logger.info(f"Satellites to plan = {len(obj)}")

    if not os.path.isdir('tle'):
        print("Error !!!! No TLE files in 'tle' directory")
        logger.error("No TLE files in 'tle' directory")
        sys.exit(1)

    try:
        tle_file_list = glob.glob('tle//*.txt')
        TLE = read_tle(tle_file_list)
        print("TLE read successfully")
        logger.info("TLE read successfully")
    except Exception as e:
        print(f"Error reading TLE files: {e}")
        logger.error(f"Error reading TLE files: {e}")
        sys.exit(1)

    geo_list = []
    bad_sat = []
    ts = load.timescale()

    for sat in obj:
        for tle in TLE:
            if int(sat) == tle[-1]:
                tle[1] = fix_checksum(tle[1])
                tle[2] = fix_checksum(tle[2])

                satellite = EarthSatellite(tle[1], tle[2], tle[0], ts)

                try:
                    my_sat = Satellite(norad=sat, tle=tle,
                                       priority=0, sat=satellite, block=False,
                                       planed=[0] * series)
                    my_sat.calc_pos(site, start_T, eph)
                    geo_list.append(my_sat)
                except Exception as E:
                    logger.warning(f"Skip satellite {sat}, TLE too old or error: {E}")
                    bad_sat.append(sat)

    for bad in bad_sat:
        obj.remove(bad)

    for sat in obj:
        if not any(ge.norad == sat for ge in geo_list):
            logger.warning(f"Satellite {sat} has no TLE data")

    print(f"Satellites planned = {len(geo_list)}")
    logger.info(f"Satellites planned = {len(geo_list)}")

    geo_list.sort(key=lambda x: x.ha_sort.hours)

    print(f"Start date = {start_T.utc_datetime().strftime('%Y/%m/%d %H:%M:%S')}")
    print(f"End date = {end_T.utc_datetime().strftime('%Y/%m/%d %H:%M:%S')}")

    logger.info(f"Start date = {start_T.utc_datetime().strftime('%Y/%m/%d %H:%M:%S')}")
    logger.info(f"End date = {end_T.utc_datetime().strftime('%Y/%m/%d %H:%M:%S')}")

    f.write("# Start T = " + start_T.utc_datetime().strftime("%Y-%m-%d %H:%M:%S.%f") + "\n")

    print("Start...")

    # --- Основний цикл ---
    T1 = start_T

    for ser in range(series):
        logger.info(f"##################--- Series #{ser + 1}")

        for msat in geo_list:
            msat.calc_pos(site, T1, eph)

        geo_list.sort(key=lambda x: x.ha_sort.hours)

        f.write(f"# series N = {ser + 1}\n")

        if ser > 0:
            T1 = T1 + timedelta(seconds=t_between_ser)
            logger.info(f"Series {ser + 1} start time adjusted by {t_between_ser} seconds")

        for i, sat in enumerate(geo_list):
            if sat.planed[ser] == 0:
                if (i == 0) and (sat.priority == 0) and (ser > 0):
                    T2 = T1 + timedelta(seconds=t_ser + t_move + 90)
                else:
                    T2 = T1 + timedelta(seconds=t_ser + t_move)

                if T1 > end_T:
                    print_park(f, T1, park_ra, park_dec, t_exp, exp_wait)
                    f.close()
                    logger.info(f"Finish. Sunrise reached at {T1.utc_datetime().strftime('%Y-%m-%d %H:%M:%S')}, h_sun={h_sun}")
                    sys.exit()

                T1_s = T1.utc_datetime().strftime("%H%M%S")
                T2_s = T2.utc_datetime().strftime("%H%M%S")

                sat.calc_pos(site, T1, eph)

                if C == 'HA':
                    ra_speed, dec_speed = sat.pos['hadec_speed']
                else:
                    ra_speed, dec_speed = sat.pos['radec_speed']

                moon_sep = sat.pos['m_sep']

                if (sat.pos['alt'].degrees > min_sat_h) and (T1 < end_T) and (moon_sep.degrees > float(moon_dist)):
                    if sat.pos['sunlit']:
                        write_plan(
                            file=f,
                            tracking=tracking,
                            min_track_speed=min_track_speed,
                            ra_speed=ra_speed,
                            dec_speed=dec_speed,
                            geo=sat,
                            flag=C,
                            T1_s=T1_s,
                            T2_s=T2_s,
                            str_v_plan=str_v_plan
                        )
                        sat.planed[ser] = 1
                        logger.info(f"Planned satellite {sat.norad} at {T1.utc_datetime().strftime('%Y-%m-%d %H:%M:%S')}, alt={sat.pos['alt'].degrees:.2f}, moon_sep={moon_sep.degrees:.2f}")
                    else:
                        sat.priority += 1
                        logger.info(f"Satellite {sat.norad} in series {ser + 1} is eclipsed")
                        found = False
                        x = 1
                        while not found and (i + x < len(geo_list)):
                            alt_sat = geo_list[i + x]
                            alt_sat.calc_pos(site, T1, eph)
                            if alt_sat.pos['sunlit'] and alt_sat.planed[ser] == 0:
                                found = True
                            else:
                                x += 1
                        if found:
                            alt_sat = geo_list[i + x]
                            logger.info(f"Changed planning to satellite {alt_sat.norad}")
                            if C == 'HA':
                                ra_speed, dec_speed = alt_sat.pos['hadec_speed']
                            else:
                                ra_speed, dec_speed = alt_sat.pos['radec_speed']

                            write_plan(
                                file=f,
                                tracking=tracking,
                                min_track_speed=min_track_speed,
                                ra_speed=ra_speed,
                                dec_speed=dec_speed,
                                geo=alt_sat,
                                flag=C,
                                T1_s=T1_s,
                                T2_s=T2_s,
                                str_v_plan=str_v_plan
                            )
                            alt_sat.planed[ser] = 1
                        else:
                            logger.info(f"No replacement found for eclipsed satellite {sat.norad}")
                else:
                    sat.priority += 1
                    if debug:
                        logger.info(f"Skipping satellite {sat.norad} in series {ser + 1} due to altitude {sat.pos['alt'].degrees:.2f} or moon separation {moon_sep.degrees:.2f}")
                    if sat.pos['alt'].degrees < min_sat_h:
                        logger.info(f"Skip satellite {sat.norad} due to low elevation: {sat.pos['alt'].degrees:.2f} deg")
                    if moon_sep.degrees < float(moon_dist):
                        logger.info(f"Skip satellite {sat.norad} due to moon separation: {moon_sep.degrees:.2f} deg")
                    T2 = T1

                added = False
                if i == len(geo_list) - 1:
                    for j, sat_j in enumerate(geo_list):
                        if (sat_j.planed[ser] == 0) and sat_j.pos['sunlit'] and (sat_j.pos["alt"].degrees > min_sat_h) and (moon_sep.degrees > float(moon_dist)):
                            T1 = T2
                            T2 = T1 + timedelta(seconds=t_ser + t_move)
                            T1_s = T1.utc_datetime().strftime("%H%M%S")
                            T2_s = T2.utc_datetime().strftime("%H%M%S")
                            sat_j.calc_pos(site, T1, eph)
                            logger.info(f"Satellite {sat_j.norad} is out of eclipse, added to end of series {ser + 1}")

                            if C == 'HA':
                                ra_speed, dec_speed = sat_j.pos['hadec_speed']
                            else:
                                ra_speed, dec_speed = sat_j.pos['radec_speed']

                            write_plan(
                                file=f,
                                tracking=tracking,
                                min_track_speed=min_track_speed,
                                ra_speed=ra_speed,
                                dec_speed=dec_speed,
                                geo=sat_j,
                                flag=C,
                                T1_s=T1_s,
                                T2_s=T2_s,
                                str_v_plan=str_v_plan
                            )
                            sat_j.planed[ser] = 1
                            added = True
                            break

                if (sat.pos["alt"].degrees > min_sat_h) and (moon_sep.degrees > float(moon_dist)) and (not added):
                    T1 = T2
                if added:
                    T1 = T2

    if park:
        print_park(f, T1, park_ra, park_dec, t_exp, exp_wait)
    logger.info(f"Finished. {series} series calculated.")
    f.close()


if __name__ == "__main__":
    main()
