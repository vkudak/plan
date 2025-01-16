import glob, os, sys
from datetime import datetime, timedelta

from skyfield import almanac
from skyfield.api import EarthSatellite, load, wgs84, utc
from skyfield.units import Angle


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

    # def norm_ha(self):
    #     ha = self.ha
    #     if ha.hours < 0:
    #         ha = ha.hours + Angle(hours=24).hours
    #         return Angle(hours=ha)
    #     else:
    #         return ha

    def calc_pos(self, site, t):
        # ha, dec,_ = self.sat.at(t).hadec()
        difference = self.sat - site
        topocentric = difference.at(t)
        ha, dec, _ = topocentric.hadec()
        ra, _, _ = topocentric.radec()
        alt, az, _ = topocentric.altaz()
        self.ha_sort = ha
        self.pos = {'ha':ha, 'dec':dec, 'ra':ra, 'alt':alt, 'az':az}
        return self.pos

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

        return sep.degrees
        # moon = eph["Moon"]
        # moon.compute(site)
        # mc = (moon.ra, moon.dec)
        # return ephem.separation(sc, mc)


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
    s = e.observe(sun).apparent()
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


def calc_geo_speed(msat, site, t0, flag):
    # Deren.date = T1.strftime("%Y/%m/%d %H:%M:%S")
    pos1 = msat.calc_pos(site, t0)
    ha1, ra1, dec1 = pos1["ha"], pos1["ra"], pos1["dec"]

    n_sec = 60
    # moment 2
    t2 = t0 + timedelta(seconds=n_sec)
    pos2 = msat.calc_pos(site, t2)
    ha2, ra2, dec2 = pos2["ha"], pos2["ra"], pos2["dec"]

    ra_speed = (ra2._degrees - ra1._degrees) * 60 * 60
    ha_speed = (ha2._degrees - ha1._degrees) * 60 * 60
    dec_speed = (dec2.degrees - dec1.degrees) * 60 * 60

    if flag == "HA":
        # ha_speed = (ha2 - ha) #/ 100
        return ha_speed / n_sec, dec_speed / n_sec
    else:
        # ra_speed = (ra2 - ra) #/ 100
        return ra_speed / n_sec, dec_speed / n_sec
