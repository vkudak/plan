import argparse
import configparser
import os
import datetime
import sys

from spacetrack import SpaceTrackClient

from plan_io import read_planed_objects

# list_my = [
#     18570,
# ]

parser = argparse.ArgumentParser(description='Get TLE from Space-track')
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
    username = config.get('space_track', 'username')
    password = config.get('space_track', 'password')
except Exception as E:
    print("Error in INI file\n", E)
    sys.exit()

st = SpaceTrackClient(username, password)

ndate = datetime.datetime.now().strftime("%Y%m%d")
list_my = read_planed_objects(objects_file)
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
