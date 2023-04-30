import glob, os, sys
import datetime
import ephem


class Satellite:
    def __init__(self, NORAD, HA, priority, TLE, geo, block, planed):
        self.NORAD = NORAD
        self.HA = HA  # HA at the first evening point
        self.priority = priority
        self.TLE = TLE
        self.geo = geo  # pyephem sat object
        self.block = block
        self.planed = planed  # []  # [planed in ser like [1, 0, 0]]

    def calc(self, site):
        self.geo.compute(site)
        ha_sort = ephem.hours(site.sidereal_time() - self.geo.ra)
        # print(ha_sort)
        self.HA = ha_sort
        if ha_sort < 0:
            # print(self.NORAD, str(ha_sort), str(ephem.hours(site.sidereal_time() - self.geo.ra + ephem.degrees("360.0"))))
            return ephem.hours(site.sidereal_time() - self.geo.ra + ephem.degrees("360.0"))  # -01 to 23 hour
        else:
            return ha_sort
        # self.HA = ha_sort
        # return ha

    def calc_moon_angle(self, site):
        self.geo.compute(site)
        sc = (self.geo.ra, self.geo.dec)
        moon = ephem.Moon()
        moon.compute(site)
        mc = (moon.ra, moon.dec)
        return ephem.separation(sc, mc)


def fix_checksum(line):
    """Return a new copy of the TLE `line`, with the correct checksum appended.

    This discards any existing checksum at the end of the line, if a
    checksum is already present.

    """
    return line[:68].ljust(68) + str(compute_checksum(line))


def compute_checksum(line):
    """Compute the TLE checksum for the given line."""
    return sum((int(c) if c.isdigit() else c == '-') for c in line[0:68]) % 10


def calc_T_twilight(h_sun=-12):
    import ephem
    # Make an observer
    fred = ephem.Observer()

    # PyEphem takes and returns only UTC times. 15:00 is noon in Fredericton
    fred.date = datetime.datetime.now()
    fred.date = fred.date.datetime().replace(hour=0, minute=0, second=0)  # GET DATE AT hh=0 mm=0 ss=0

    # Location of Fredericton, Canada
    fred.lon = str(22.453751)  # Note that lon should be in string format
    fred.lat = str(48.5635505)  # Note that lat should be in string format

    # Elevation of Fredericton, Canada, in metres
    fred.elev = 231

    # To get U.S. Naval Astronomical Almanac values, use these settings
    fred.pressure = 0
    fred.horizon = '-0:34'

    # sunrise=fred.previous_rising(ephem.Sun()) #Sunrise
    # noon   =fred.next_transit   (ephem.Sun(), start=sunrise) #Solar noon
    # sunset =fred.next_setting   (ephem.Sun()) #Sunset

    # We relocate the horizon to get twilight times
    fred.horizon = str(h_sun)#'-10'  # -6=civil twilight, -12=nautical, -18=astronomical
    # beg_twilight=fred.previous_rising(ephem.Sun(), use_center=True) #Begin civil twilight
    end_twilight = fred.next_setting(ephem.Sun(), use_center=True)  # End civil twilight
    start_twilight = fred.next_rising(ephem.Sun(), use_center=True)
    return end_twilight.datetime(), start_twilight.datetime() + datetime.timedelta(1, 0)


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


def T_to_dec(UTCs):
    h = UTCs[:2]
    m = UTCs[2:4]
    sec = UTCs[4:]
    UTC = float(h) + float(m) / 60 + float(sec) / 3600
    return UTC


def corr_ha_dec_s(ha, dec):
    ha_s = "%s" % ha
    ha_s = ha_s.replace(':', '')
    dec_s = "%s" % dec
    dec_s = dec_s.replace(':', '')

    # HA leading zero correction
    if len(ha_s.split(".")[0]) < 6:
        ha_s = "0"+"".join(ha_s)

    # DEC leading zero correction  -6 -> -06
    dec2 = float(dec_s)
    if abs(dec2) < 100000:
        if dec < 0:
            dec_s = list(dec_s)
            dec_s.insert(1, "0")
        else:
            dec_s = list(dec_s)
            dec_s.insert(0, "0")
        dec_s = "".join(dec_s)
    if dec2 > 0:
        dec_s = "+" + dec_s
    return ha_s, dec_s

def addT(UTCs, dt):
    # dt in sec
    # print addT('010503', 600)
    h = UTCs[:2]
    m = UTCs[2:4]
    sec = UTCs[4:]
    # print h, m, sec
    hi, mi, seci = int(h), int(m), int(sec)
    seci = seci + dt
    while seci > 59:
        seci = seci - 60
        mi = mi + 1

    while mi > 59:
        mi = mi - 60
        hi = hi + 1

    while hi > 23:
        hi = hi - 24

    sec = str(seci)
    if seci < 10:
        sec = '0' + sec
    m = str(mi)
    if mi < 10:
        m = '0' + m
    h = str(hi)
    if hi < 10:
        h = '0' + h

    UTCn = h + m + sec
    return UTCn


def fDT(date, hh):
    # combine date and UTC
    date_part = datetime.datetime.strptime(date, '%Y-%m-%d')
    # hour = int(hh)
    # minuts = int((hh - hour) * 60)
    # sec = (minuts - ((hh - hour) * 60)) * 60
    hour, minuts, sec = hh.split(':')
    DT = datetime.datetime.combine(date_part, datetime.time(int(hour), int(minuts), int(sec)))
    return DT

def moon_phase():
    date_str = datetime.datetime.now().strftime('%Y/%m/%d')
    moon = ephem.Moon(date_str)
    return moon.moon_phase * 100
