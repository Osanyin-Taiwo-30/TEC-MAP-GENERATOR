# Add RMExtract to Python path
import sys
RMEXTRACT_PATH = '../RMextract' # dependent on this file being in this folder.
sys.path.append(RMEXTRACT_PATH)

from scipy.interpolate import RegularGridInterpolator
import numpy as np
import matplotlib.pyplot as plt
import os
import subprocess
import time
import urllib2

import getIONEX as ionex

#######################################################
# Downloading barely works, get your files from here! #
# ftp://cddis.gsfc.nasa.gov/gps/products/ionex        #
#######################################################

def get_ionex_file(year, day_of_year):
    day_formatted = "%03d" % day_of_year
    year_formatted = str(year)[-2:]

    igsg_file_name = "igsg{}0.{}i".format(day_formatted, year_formatted)
    igsg_file_name_z = igsg_file_name + ".Z"
    IONEX_DATASTORE = "ftp://cddis.gsfc.nasa.gov/gps/products/ionex/{}/{}/{}".format(year, day_formatted, igsg_file_name_z)
    ionex_file_path = IONEX_DATASTORE.format(year, )

    print IONEX_DATASTORE
    req = urllib2.Request(IONEX_DATASTORE)
    resp = urllib2.urlopen(req)
    with open(igsg_file_name_z, 'wb') as fp:
        fp.write(resp.read())

    cmd = "uncompress {}".format(igsg_file_name_z)
    p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    p.stdin.write('yes')
    time.sleep(1)

    return igsg_file_name

def generate_tec_map(path_to_ionex, hour_in_day):
    """
    Function to generate tec maps!
    """
    tec_struct = ionex.readTEC(path_to_ionex) # some data struct is returned from the library.
    tec_data = tec_struct[0]

    LAT_STEP_SIZE = 2.5
    LON_STEP_SIZE = 5.0

    MAX_LAT = 180
    MIN_LAT = 0

    MAX_LON = 360
    MIN_LON = 0

    hours = np.arange(0, 25, 2) # 24 hours, 2 hour steps
    lat_v = np.arange(MIN_LAT + LAT_STEP_SIZE, MAX_LAT, LAT_STEP_SIZE) # Starts at 2.5 degrees (87.5)
    lon_v = np.arange(MIN_LON, MAX_LON + LON_STEP_SIZE, LON_STEP_SIZE)
    interpolator = RegularGridInterpolator((hours, lat_v, lon_v), tec_data, bounds_error=False)

    tecs = np.zeros((len(lat_v), len(lon_v)))
    for i, lat in enumerate(lat_v):
        for j, lon in enumerate(lon_v):
            tec = interpolator(np.array([hour_in_day, lat, lon]))
            tecs[i, j] = tec

    AXIS_STEP = 5
    plt.figure(figsize=(36, 18))
    plt.title("TEC Map of {}".format(path_to_ionex))
    plt.ylabel("Latitude (degrees)")
    plt.yticks(range(len(lat_v))[::AXIS_STEP], lat_v[::AXIS_STEP]-90) # reverse the array so lats count down

    plt.xlabel("Longitude (degrees)")
    plt.xticks(range(len(lon_v))[::AXIS_STEP], lon_v[::AXIS_STEP]-180)

    heatmap = plt.pcolor(tecs)
    plt.colorbar()
    plt.show()
    
    return tecs

