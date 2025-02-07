import glob, os, sys
from datetime import datetime, timedelta
import configparser

from skyfield import almanac
from skyfield.api import load, utc
from skyfield.units import Angle


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
            c_site_lat = config.getfloat('site', 'site_lat')
            c_site_lon = config.getfloat('site', 'site_lon')
            c_site_elev = config.getfloat('site', 'site_elev')

            c_plan_type = config.get("options", 'plan_type', fallback="HA")
            c_min_sat_h = config.getfloat('options', 'min_sat_h', fallback=10)
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
                    'site_lat': c_site_lat,
                    'site_lon': c_site_lon,
                    'site_elev': c_site_elev,
                    'plan_type': c_plan_type,
                    'min_sat_h': c_min_sat_h,
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


class Satellite:
    def __init__(self, norad, priority, tle, sat, block, planed):
        self.norad = norad
        self.ha_sort = 0  # HA at the first evening point
        self.pos = {}
        self.priority = priority
        self.tle = tle
        self.sat = sat  # sat object
        self.block = block
        self.planed = planed  # []  # [planed in ser like [1, 0, 0]]

    def calc_pos(self, site, t, eph):
        moon = eph['Moon']
        earth = eph['Earth']

        # ICRF
        difference = self.sat - site
        topocentric = difference.at(t)

        # Barycenter
        # ssb_bluffton = earth + site
        # ssb_satellite = earth + self.sat
        # topocentric = ssb_bluffton.at(t).observe(ssb_satellite).apparent()
        # # topocentric = ssb_bluffton.at(t).observe(ssb_satellite)

        ha, _, _ = topocentric.hadec()
        ra, dec, _ = topocentric.radec(epoch='date')
        alt, az, _ = topocentric.altaz()
        self.ha_sort = ha

        # calc Moon separation
        # eph = load('de421.bsp')

        m = earth.at(t).observe(moon)
        sep = topocentric.separation_from(m)

        # is in sunlight
        sunlit = self.sat.at(t).is_sunlit(eph)

        # Calc geo track speed
        n_sec = 60
        t2 = t + timedelta(seconds=n_sec) # moment 2
        topocentric2 = difference.at(t2)
        # topocentric2 = ssb_bluffton.at(t2).observe(ssb_satellite).apparent()
        # topocentric2 = ssb_bluffton.at(t2).observe(ssb_satellite)
        ha2, _, _ = topocentric2.hadec()
        ra2, dec2, _ = topocentric2.radec(epoch='date')

        # ha1, ra1, dec1 = ha, ra, dec

        ra_speed = (ra2._degrees - ra._degrees) * 60 * 60
        ha_speed = (ha2._degrees - ha._degrees) * 60 * 60
        dec_speed = (dec2.degrees - dec.degrees) * 60 * 60

        hadec_speed = (ha_speed / n_sec, dec_speed / n_sec)
        radec_speed = (ra_speed / n_sec, dec_speed / n_sec)

        self.pos = {'ha':ha, 'dec':dec, 'ra':ra, 'alt':alt, 'az':az, 'm_sep':sep, 'sunlit':sunlit,
                    'hadec_speed':hadec_speed, 'radec_speed':radec_speed
                    }
        return self.pos

    def calc_sat_phase(self, site, t):
        """
        # https://github.com/skyfielders/python-skyfield/discussions/607
        Calculate phase angle of Satellite
        site: Observation point load.wgs84() object
        t: Time
        return: Satellite phase angle
        """
        eph = load('de421.bsp')
        earth = eph['earth']
        sun = eph['sun']

        ssb_obs = earth + site
        ssb_satellite = earth + self.sat
        # sun_position = s.at(t).observe(sun)
        # earth_position = s.at(t).observe(earth)
        # phase_angle = sun_position.separation_from(earth_position)

        topocentric_sat_obs = ssb_satellite.at(t).observe(ssb_obs).apparent()
        topocentric_sat_sun = ssb_satellite.at(t).observe(sun).apparent()
        phase_angle = topocentric_sat_obs.separation_from(topocentric_sat_sun)
        return phase_angle.degrees


    def calc_moon_sep(self, site, t):
        # ra, _ , dec = self.calc_pos(site, time)
        # sc = (ra, dec)
        eph = load('de421.bsp')
        moon = eph['Moon']
        earth = eph['Earth']

        difference = self.sat - site
        topocentric = difference.at(t)

        # dif_moon = moon - site
        # top_moon = dif_moon.at(time)
        m = earth.at(t).observe(moon)

        sep = topocentric.separation_from(m)

        # https://rhodesmill.org/skyfield/api-position.html#skyfield.positionlib.ICRF.separation_from
        # https://rhodesmill.org/skyfield/examples.html
        # print(sep.degrees)
        # sys.exit()

        return sep


def fix_checksum(line):
    """Return a new copy of the TLE `line`, with the correct checksum appended.

    This discards any existing checksum at the end of the line, if a
    checksum is already present.

    """
    return line[:68].ljust(68) + str(compute_checksum(line))


def compute_checksum(line):
    """Compute the TLE checksum for the given line."""
    return sum((int(c) if c.isdigit() else c == '-') for c in line[0:68]) % 10


def calc_t_twilight(site, h_sun=-12):
    """
    Calculate twilight time according to h_sun
    site: observational site. Create by api.Topos(lat, lon, elevation_m=elv) or api.wgs84(lat, lon, elevation_m=elv)
    h_sun: elevation of Sun below horizon. Default is -12 degrees.
    """
    ts = load.timescale()
    eph = load('de421.bsp')
    observer = eph['Earth'] + site

    now = datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=utc)
    next_midnight = midnight + timedelta(days=2)
    t0 = ts.from_datetime(midnight)
    t1 = ts.from_datetime(next_midnight)

    t_set, y = almanac.find_settings(observer, eph['Sun'], t0, t1, horizon_degrees=h_sun)
    t_rise, y = almanac.find_risings(observer, eph['Sun'], t0, t1, horizon_degrees=h_sun)
    return t_set[0], t_rise[1]


def read_tle(file_list):
    TLE = []
    for filename in file_list:
        with open(filename, 'r') as infile:
            lines = []
            for line in infile:
                lines.append(line)
                if len(lines) == 3:
                    NORAD = int(lines[2].split()[1])
                    epoch = float(lines[1].split()[3])
                    lines.append(NORAD)

                    # check dublicate
                    dublic = False
                    for x in range(0, len(TLE)):
                        if int(TLE[x][2].split()[1]) == NORAD:
                            dublic = True
                            if epoch > float(TLE[x][1].split()[3]):
                                TLE.pop(x)
                                # print("deleting N", x)
                                TLE.append(lines)
                    if dublic == False:
                        TLE.append(lines)
                    # end check

                    lines = []
    return TLE


def read_vt(filename):
    f = open(filename, 'r')
    ephem = []
    for line in f:
        if len(line) > 84:
            l = line.split()
            if len(l) > 12:
                # print len(l)
                date, UTCs, RA, DEC = l[0], l[1], l[2] + ' ' + l[3] + ' ' + l[4], l[5] + ' ' + l[6] + ' ' + l[7]
                RAr, DECr, HA, mag = l[8], l[9], l[10] + ' ' + l[11] + ' ' + l[12], '   ' + l[-1]
                
                HA_deg = (int(l[10]) + int(l[11])/60.0 + float(l[12])/3600.0)*15
                if HA_deg > 180:
                    HA_deg = HA_deg - 360
                
                UTCh, UTCm, UTCsec = UTCs.split(':')
                UTC = float(UTCh) + float(UTCm) / 60 + float(UTCsec) / 3600
                ephem.append((date, UTCs, UTC, RA.replace(" ", ""), DEC.replace(" ", ""), RAr, DECr, HA, HA_deg, mag.strip()))
    return ephem


def read_va(filename):
    f = open(filename, 'r')
    ephem = []
    for line in f:
        if (len(line) > 124) and (line[0]not in ["=", " "]):
            # print line
            l = line.split()
            if len(l) > 12:
                # print len(l)
                date, UTCs, RA, DEC = "20" + l[0], l[1] + ":00", l[4] + ' ' + l[5] + ' ' + l[6], l[7] + ' ' + l[8] + ' ' + l[9]
                RAr, DECr, HA, mag = l[10], l[11], l[12] + ' ' + l[13] + ' ' + l[14], '   ' + l[-3]

                HA_deg = (int(l[12]) + int(l[13])/60.0 + float(l[14])/3600.0)*15
                if HA_deg > 180:
                    HA_deg = HA_deg - 360
                
                UTCh, UTCm, UTCsec = UTCs.split(':')
                UTC = float(UTCh) + float(UTCm) / 60
                ephem.append((date, UTCs, UTC, RA.replace(" ", ""), DEC.replace(" ", ""), RAr, DECr, HA, mag.strip()))
    return ephem


def read_planed_objects(filename):
    obj = []
    f = open(filename, 'r')
    for line in f:
        if line[0] not in ["#"]:
            obj.append(line.split()[0].strip())
    return obj


# def T_to_dec(UTCs):
#     h = UTCs[:2]
#     m = UTCs[2:4]
#     sec = UTCs[4:]
#     UTC = float(h) + float(m) / 60 + float(sec) / 3600
#     return UTC


def corr_ha_dec_s(ha, dec):
    if ha.hours < 0:
        ha = ha.hours + Angle(hours=24).hours
        ha = Angle(hours=ha)
    ha_s = ha.hstr(format='{0}{1:02}{2:02}{3:02}.{4:0{5}}')
    dec_s = dec.dstr(format='{0:+>1}{1:02}{2:02}{3:02}.{4:0{5}}')

    return ha_s, dec_s

# def addT(UTCs, dt):
#     # dt in sec
#     # print addT('010503', 600)
#     h = UTCs[:2]
#     m = UTCs[2:4]
#     sec = UTCs[4:]
#     # print h, m, sec
#     hi, mi, seci = int(h), int(m), int(sec)
#     seci = seci + dt
#     while seci > 59:
#         seci = seci - 60
#         mi = mi + 1
#
#     while mi > 59:
#         mi = mi - 60
#         hi = hi + 1
#
#     while hi > 23:
#         hi = hi - 24
#
#     sec = str(seci)
#     if seci < 10:
#         sec = '0' + sec
#     m = str(mi)
#     if mi < 10:
#         m = '0' + m
#     h = str(hi)
#     if hi < 10:
#         h = '0' + h
#
#     UTCn = h + m + sec
#     return UTCn


# def fDT(date, hh):
#     # combine date and UTC
#     date_part = datetime.strptime(date, '%Y-%m-%d')
#     # hour = int(hh)
#     # minuts = int((hh - hour) * 60)
#     # sec = (minuts - ((hh - hour) * 60)) * 60
#     hour, minutes, sec = hh.split(':')
#     dt = datetime.combine(date_part, time(int(hour), int(minutes), int(sec)))
#     return dt


def moon_phase():
    """
    Get Moon phase and illumination percents for NOW
    """
    ts = load.timescale()
    now = datetime.now()
    now = now.replace(tzinfo=utc)
    t = ts.from_datetime(now)

    eph = load('de421.bsp')
    sun, moon, earth = eph['sun'], eph['moon'], eph['earth']

    e = earth.at(t)
    # s = e.observe(sun).apparent()
    m = e.observe(moon).apparent()

    # _, slon, _ = s.frame_latlon(ecliptic_frame)
    # _, mlon, _ = m.frame_latlon(ecliptic_frame)
    # phase = (mlon.degrees - slon.degrees) % 360.0

    percent = 100.0 * m.fraction_illuminated(sun)

    # print('Phase (0°–360°): {0:.1f}'.format(phase))
    # print('Percent illuminated: {0:.1f}%'.format(percent))

    return percent


# def deg_to_float(deg):
#     return float(math.degrees(deg))


def calc_geo_speed(msat, site, t0, eph, flag):
    # Deren.date = T1.strftime("%Y/%m/%d %H:%M:%S")
    pos1 = msat.calc_pos(site, t0, eph)
    ha1, ra1, dec1 = pos1["ha"], pos1["ra"], pos1["dec"]

    n_sec = 60
    # moment 2
    t2 = t0 + timedelta(seconds=n_sec)
    pos2 = msat.calc_pos(site, t2, eph)
    ha2, ra2, dec2 = pos2["ha"], pos2["ra"], pos2["dec"]

    msat.calc_pos(site, t0, eph) # set t0 position

    ra_speed = (ra2._degrees - ra1._degrees) * 60 * 60
    ha_speed = (ha2._degrees - ha1._degrees) * 60 * 60
    dec_speed = (dec2.degrees - dec1.degrees) * 60 * 60

    if flag == "HA":
        # ha_speed = (ha2 - ha) #/ 100
        return ha_speed / n_sec, dec_speed / n_sec
    else:
        # ra_speed = (ra2 - ra) #/ 100
        return ra_speed / n_sec, dec_speed / n_sec


def write_plan(file, tracking, min_track_speed, ra_speed, dec_speed, geo, flag, T1_s, T2_s, str_v_plan):
    mag = "0.00"
    ha, dec = geo.pos["ha"], geo.pos['dec']
    ha_s, dec_s = corr_ha_dec_s(ha, dec)
    if tracking and (abs(ra_speed) > min_track_speed or abs(dec_speed) > min_track_speed):
        my_line = (f"{geo.norad} = {flag} {ha_s}"
                   f"({ra_speed:>+4.2f})  {dec_s}({dec_speed:>+4.2f}) "
                   f"{mag} {str_v_plan}{T1_s}-{T2_s}\n"
                   )
        file.write(my_line)
    else:
        my_line = f"{geo.norad} = {flag} {ha_s:<16}  {dec_s:<16} {mag} {str_v_plan}{T1_s}-{T2_s}\n"
        file.write(my_line)


def print_park(file, t1, park_ra, park_dec, t_exp, exp_wait):
    mag = "0.00"
    t1_s = t1.utc_datetime().strftime("%H%M%S")
    t2 = t1 + timedelta(0, 30)
    t2_s = t2.utc_datetime().strftime("%H%M%S")
    str_v_plan_p = f" 1x{t_exp:3.1f}:{exp_wait} @"
    file.write(f"park  = HA {park_ra:<16}  {park_dec:<16} {mag} {str_v_plan_p}{t1_s}-{t2_s}\n")
