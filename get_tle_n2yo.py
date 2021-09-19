import os
from n2yo import n2yo
import datetime


list_ckkp = [
	11804,
	13954,
	14977,
	15264,
	16908,
	18340,
	18570,
	19751,
	22076,
	23088,
	23405,
	23455,
	26536,
	27386,
	27453,
	28358,
	28492,
	28809,
	29228,
	31792,
	32294,
	33105,
	34810,
	35943,
	36095,
	36124,
	36582,
	36868,
	37794,
	38707,
	38708,
	39079,
	39177,
	39186,
	39194,
	39227,
	39285,
	39375,
	39451,
	39452,
	39453,
	39635,
	39731,
	40010,
	40258,
	40353,
	40358,
	40360,
	40420,
	40505,
	40699,
	41121,
	41238,
	41240,
	41384,
	41386,
	41394,
	41465,
	41579,
	42798,
	42825,
	42907,
	42986,
	43032,
	43180,
	43181,
	43657,
	43866,
	43867,
	43876,
	43877,
	44421,
	44422,
	44423,
	44424,
	44457,
	44517,
	44547,
	44797,
	44835,
	47230,
	47305,
	47546,
	38858,
	41335,
	49069,
	43783,
	48865,
	43437
]


api_key = "Q3YSXZ-7MP4J6-5ASVKZ-2ONC" # Obtain an api key at https://www.n2yo.com/api/
latitude = 0.000 # decimal degree format
longitude = 0.000 # decimal degree format
altitude = 0

cl = n2yo.N2YO(api_key, latitude, longitude, altitude)

ndate = datetime.datetime.now().strftime("%Y%m%d")

if os.path.isdir('tle'):
	fr = open("tle//tle_ckkp_" + ndate + ".txt", "w")
else:
	os.mkdir('tle')
	fr = open("tle//tle_ckkp_" + ndate + ".txt", "w")

for sat in list_ckkp:
	try:
		res = cl.get_tle(sat)
		fr.write(res[0]["satname"] + "\n")
		fr.write(res[1] + "\n")
	except Exception as e:
		print('Error while retrieving TLE for ' + str(sat))
		pass
fr.close()
