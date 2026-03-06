import argparse
import configparser
import os
import sys

from n2yo import n2yo
import datetime
from tqdm import tqdm
import requests
import json
from astropy.time import Time
from plan_io import read_planed_objects

def get_from_satcheck(id, fr, max_mean_motion=99999):
	t = Time.now()
	
	url = 'https://satchecker.cps.iau.org/tools/get-nearest-tle/'
	params = {'id': str(id),
	          'id_type': 'catalog',
	          'epoch': str(t.jd) #'2461105'
	        }
	
	r = requests.get(url, params=params)
	# print(json.dumps(r.json(), indent=4))
	r = r.json()[0]
	
	if r['tle_data'] and (float(r['tle_data'][0]['tle_line1'].split()[-2]) < max_mean_motion): 
		fr.write(r['tle_data'][0]['satellite_name'] + "\n" + 
				 r['tle_data'][0]['tle_line1'] + "\n" + 
				 r['tle_data'][0]['tle_line2'] + "\n"
				)
		return 'found'
	    # return(r['tle_data'][0]['satellite_name'], 
			  #  r['tle_data'][0]['tle_line1'],
	    #        r['tle_data'][0]['tle_line2']
			  # )
	else:
	    return None


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

max_mm = 7 # max mean motion

miss = []
for sat in tqdm(list_my):
	try:
		res = cl.get_tle(sat)

		if res[1] != '':
			mean_motion = float(res[1].split()[-2])
			if mean_motion < max_mm:
				fr.write(res[0]["satname"] + "\n")
				ll = res[1].split('\r\n')
				fr.write(ll[0] + "\n" + ll[1] + "\n")
			else:
				print(f'Mean motion too big, skipping {sat}')
		else:
			rr = get_from_satcheck(sat, fr, max_mm)
			if rr is None
				miss.append(sat)
	except Exception as e:
		print('Error while retrieving TLE for ' + str(sat))
		# print(repr(e))
		pass

if miss:
	print(f'No TLE for object {miss}')
fr.close()
