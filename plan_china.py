# import numpy as np
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
                UTCh, UTCm, UTCsec = UTCs.split(':')
                UTC = float(UTCh) + float(UTCm) / 60 + float(UTCsec) / 3600
                ephem.append((date, UTCs, UTC, RA.replace(" ", ""), DEC.replace(" ", ""), RAr, DECr, HA, mag.strip()))
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
                UTCh, UTCm, UTCsec = UTCs.split(':')
                UTC = float(UTCh) + float(UTCm) / 60
                ephem.append((date, UTCs, UTC, RA.replace(" ", ""), DEC.replace(" ", ""), RAr, DECr, HA, mag.strip()))
    return ephem



def read_plan(filename):
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
    date_part = datetime.datetime.strptime(date, '%Y-%m-%d')
    # hour = int(hh)
    # minuts = int((hh - hour) * 60)
    # sec = (minuts - ((hh - hour) * 60)) * 60
    hour, minuts, sec = hh.split(':')
    DT = datetime.datetime.combine(date_part, datetime.time(int(hour), int(minuts), int(sec)))
    return DT

#  Main begin here------------------------------------------------------------------------------------------
# 36581 = HA 235508.25 -071108.39   0.00 8x10 @173600-173900
# 26853 = HA 235420.60 -040736.63   0.00 8x10 @173900-174200
# 38022 = HA 232759.36 -130207.99   0.00 8x10 @174200-174500
# 95151 = HA 233142.64 -032121.09   0.00 8x10 @174500-174800
# 95243 = HA 225529.90 -070816.10   0.00 8x10 @174800-175100
# 96132 = HA 223619.08 -084226.46   0.00 8x10 @175100-175400
# 95170 = HA 222828.70 -102552.50   0.00 8x10 @175400-175700
# 95157 = HA 222713.16 -044818.07   0.00 8x10 @175700-180000
# 95213 = HA 222441.20 -051617.45   0.00 8x10 @180000-180300
# 95215 = HA 220929.90 -071139.06   0.00 8x10 @180300-180600
# 95226 = HA 214543.41 -053029.86   0.00 8x10 @180600-180900

# print "------Twilight (h_sun=-10)--"
# print calc_T_twilight()
# print "--------------------------"

C = 'HA'  # HA
t_move = 40
t_exp = 12.0
n_frames = 7
exp_wait = 30 # interval between frames
t_miz_ser = 3.6*60*60

t_ser = n_frames * (t_exp + 3 + exp_wait)  # 3 - readout, 
str_v_plan = str(n_frames) + "x" + str(t_exp) + ":" + str(exp_wait) + " @" 


obj = read_plan('planed_objects.txt')


# vtlist = glob.glob("*.vt")

alleph = []
for sat in obj:
    filename_vt = 'vt/' + sat.strip() + '.vt'
    filename_va = 'va/' + sat.strip() + '.va'
    if os.path.isfile(filename_vt):
        ephem = read_vt(filename_vt)
        alleph.append(ephem)
    elif os.path.isfile(filename_va):
        ephem = read_va(filename_va)
        alleph.append(ephem)
    else:
        print 'cant find ' + sat.strip() + " vt or va ephemeris file"

# print obj
ndate = datetime.datetime.now().strftime("%Y%m%d")

f = open('object_' + C + '_' + ndate +'_china.list', 'w')

last_T = calc_T_twilight()
# last_T = datetime.datetime(day=07, month=04, year=2021, hour=20, minute=00, second=00)
# print last_T 

# last_T = last_T - datetime.timedelta(days=1)  # ---------------------------------------<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
print "start date =" 
print last_T
f.write("# Start T = " + str(last_T) + "\n")

# print obj
# sys.exit()


def ser_print(last_T):
    for z in range(0, len(obj)):
        sat = obj[z]  # satname
        last_T = last_T + datetime.timedelta(seconds=( t_ser + t_move))
        # f.write('# dummy ' + ' ' + sat + '---------------------\n')
        # n = 1
        all_sat_pos = [i for i, x in enumerate(obj) if x == sat]  # position in list , if observed many series
        if len(all_sat_pos) == 1:
            n = 1
            ser = 1
        else:
            len(all_sat_pos) > 1
            ser = all_sat_pos.index(z) + 1
            n = 1

        for k in range(0, len(alleph[z]) - 1):
            T = alleph[z][k][2]
            date = alleph[z][k][0]
            UTCs = alleph[z][k][1]
            DT = fDT(date, UTCs)
            if last_T <= DT:  # T:
                if C == 'RA':
                    ra = alleph[z][k][3]
                else:
                    ra = alleph[z][k][-2]  # HA
                ra = ra.replace(" ", "")
                # print ra

                dec = alleph[z][k][4]
                mag = alleph[z][k][-1]

                ra_r = alleph[z][k][5]
                if C == 'RA':
                    ra_r = float(ra_r) / 60
                else:
                    ra_r = -1 * float(ra_r) / 60  # HA rate just in oposite side ????????????
                    if ra_r > 0:
                        ra_r = ra_r - 15.035
                    else:
                        ra_r = ra_r + 15.035
                ra_r = ('%+2.5f' % ra_r)

                dec_r = alleph[z][k][6]
                dec_r = float(dec_r) / 60
                dec_r = ('%+2.5f' % dec_r)

                T1 = alleph[z][k][1].replace(":", "")
                T2 = addT(T1, t_ser + t_move)  # time for frames capture + move telescope to next point

                # f.write('# ' + date + '  ' + UTCs + '\n')

                if C =='RA':
                    flag = 'F'
                else:
                    flag = 'HA'

                # print T1
                # print T2
                T2 = T2.split(".")[0]
                # print T2


                f.write(sat + ' = ' + flag + ' ' + ra + '  ' + dec +'  ' + mag +' ' + str_v_plan + T1 + '-' + T2 + '\n')
                # f.close()
                # sys.exit()
                # last_T = DT + datetime.timedelta(seconds=(45))
                n = n + 1
            if n > 1:  # number of frames
                break

# make 4 series
for sr in range(0, 20):
    if sr == 0:
        last_T = last_T
    else:
        last_T = last_T + datetime.timedelta(seconds=(t_miz_ser))
    ser_print(last_T)
    f.write("#\n")

f.close()
