import argparse
import configparser
import os
import sys

from n2yo import n2yo
import datetime
from tqdm import tqdm

from plan_io import read_planed_objects


# list_my = [
# 	11804,
# ]

parser = argparse.ArgumentParser(description='Get TLE from n2yo')
parser.add_argument('-c', '--config', help='Specify config file', required=False)
parser.add_argument('-o', '--objects', help='Specify file with objects', required=False)
args = vars(parser.parse_args())

if args["config"]:
    config_name = args["config"]
else:
    config_name = "config.ini"

if args["objects"]:
    objects_file = args["objects"]
else:
    objects_file = "planed_objects.txt"

config = configparser.ConfigParser(inline_comment_prefixes="#")
try:
	config.read(config_name)
	api = config.get('n2yo', 'api_key')
except Exception as E:
	print("Error in INI file\n", E)
	sys.exit()

api_key = api  # Obtain an api key at https://www.n2yo.com/api/
latitude = 0.000  # decimal degree format
longitude = 0.000  # decimal degree format
altitude = 0

cl = n2yo.N2YO(api_key, latitude, longitude, altitude)

ndate = datetime.datetime.now().strftime("%Y%m%d")

if os.path.isdir('tle'):
	fr = open("tle//tle_ckkp_" + ndate + ".txt", "w")
else:
	os.mkdir('tle')
	fr = open("tle//tle_ckkp_" + ndate + ".txt", "w")

list_my = read_planed_objects(objects_file)

for sat in tqdm(list_my):
	try:
		res = cl.get_tle(sat)
		fr.write(res[0]["satname"] + "\n")
		ll = res[1].split('\r\n')
		fr.write(ll[0] + "\n" + ll[1] + "\n")
	except Exception as e:
		print('Error while retrieving TLE for ' + str(sat))
		pass
fr.close()
