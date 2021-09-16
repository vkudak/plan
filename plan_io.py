import glob, os, sys
import datetime


def calc_T_twilight():
    import ephem
    # Make an observer
    fred = ephem.Observer()

    # PyEphem takes and returns only UTC times. 15:00 is noon in Fredericton
    fred.date = datetime.datetime.now()
    fred.date = fred.date.datetime().replace(hour=0, minute=0, second=0)  # GET DATE AT hh=0 mm=0 ss=0

    # Location of Fredericton, Canada
    fred.lon = str(22.299167)  # Note that lon should be in string format
    fred.lat = str(48.631639)  # Note that lat should be in string format

    # Elevation of Fredericton, Canada, in metres
    fred.elev = 205

    # To get U.S. Naval Astronomical Almanac values, use these settings
    fred.pressure = 0
    fred.horizon = '-0:34'

    # sunrise=fred.previous_rising(ephem.Sun()) #Sunrise
    # noon   =fred.next_transit   (ephem.Sun(), start=sunrise) #Solar noon
    # sunset =fred.next_setting   (ephem.Sun()) #Sunset

    # We relocate the horizon to get twilight times
    fred.horizon = '-12'  # -6=civil twilight, -12=nautical, -18=astronomical
    # beg_twilight=fred.previous_rising(ephem.Sun(), use_center=True) #Begin civil twilight
    end_twilight = fred.next_setting(ephem.Sun(), use_center=True)  # End civil twilight
    return end_twilight.datetime()


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