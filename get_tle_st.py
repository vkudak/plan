import os
import datetime
from spacetrack import SpaceTrackClient

list_my = [
28358,
18570,
35943,
36582,
36868,
37948,
38091,
38977,
39079,
39285,
40258,
40505,
41105,
41238,
41384,
42907,
44035,
43867,
44457,
44903,
]


st = SpaceTrackClient('labLKD', 'lablkdSpace2013')

ndate = datetime.datetime.now().strftime("%Y%m%d")

data = st.tle_latest(norad_cat_id=list_my, ordinal=1, epoch='>now-30', format='3le')



if os.path.isdir('tle'):
	# fr = open("tle//tle_ckkp_" + ndate + ".txt", "w")
	fp_name = "tle//tle_ckkp_" + ndate + ".txt"
else:
	os.mkdir('tle')
	# fr = open("tle//tle_ckkp_" + ndate + ".txt", "w")
	fp_name = "tle//tle_ckkp_" + ndate + ".txt"



with open(fp_name, 'w') as fp:
	for line in data:
		fp.write(line)
