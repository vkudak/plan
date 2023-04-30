import configparser
import os
import datetime
import sys

from spacetrack import SpaceTrackClient

list_my = [
18570,
]

config = configparser.ConfigParser(inline_comment_prefixes="#")
try:
	config.read('config.ini')
	username = config.get('space_track', 'username')
	password = config.get('space_track', 'password')
except Exception as E:
	print("Error in INI file\n", E)
	sys.exit()

st = SpaceTrackClient(username, password)

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
