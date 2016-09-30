from scipy.interpolate import RegularGridInterpolator
import numpy as np
import matplotlib.pyplot as plt
import os
import subprocess
import time
import urllib2

from RMextract import getIONEX as ionex

LAT_STEP_SIZE = 2.5
LON_STEP_SIZE = 5.0

MAX_LAT = 180
MIN_LAT = 0

MAX_LON = 360
MIN_LON = 0

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

def get_tec_for_lat_lon_idx(tecs, lat, lon, lat_step=LAT_STEP_SIZE, lon_step=LON_STEP_SIZE):
    lat_idx = int((lat + 90) / lat_step)
    lon_idx = int((lon + 180) / lon_step)
    return lat_idx, lon_idx    

def generate_tec_map(year, day_of_year, hour_in_day, lat_of_interest=0.0, lon_of_interest=0.0, plot=True):
    """
    Generates a tec map for a specific time. The returned array is sampled every 2.5 degrees in latitude and every
    5.0 degrees in longitude, as given in the IONEX files. 

    
    :param year: year for tec map
    :param day_in_year: day in the year (e.g. January 6th = 6, Febuary 1st = 32 (i think))
    :param hour_in_day: the hour of the tec map. Note this value is interpolated between 2 hour samples.
    :param lat_of_interest: the latitude you are interested in (-90 <= lat_of_interest <= 90 in degrees)
    :param lon_of_interest: the longitude you are interested in (-180 <= lat_of_interest <= 180 in degrees)
    :returns tec_value, tec_map: tuple of the actual TEC at a given lat long, and a numpy array of sampled TEC values.
    """
    path_to_ionex = get_ionex_file(year, day_of_year)

    tec_struct = ionex.readTEC(path_to_ionex) # some data struct is returned from the library.
    tec_data = tec_struct[0]

    hours = np.arange(0, 25, 2) # 24 hours, 2 hour steps
    lat_v = np.arange(MIN_LAT + LAT_STEP_SIZE, MAX_LAT, LAT_STEP_SIZE) # Starts at 2.5 degrees (87.5)
    lon_v = np.arange(MIN_LON, MAX_LON + LON_STEP_SIZE, LON_STEP_SIZE)
    interpolator = RegularGridInterpolator((hours, lat_v, lon_v), tec_data, bounds_error=False)

    tecs = np.zeros((len(lat_v), len(lon_v)))
    for i, lat in enumerate(lat_v):
        for j, lon in enumerate(lon_v):
            tec = interpolator(np.array([hour_in_day, lat, lon]))
            tecs[i, j] = tec
    
    def plot_tec_map():
        AXIS_STEP = 5
        plt.figure(figsize=(36, 18))
        plt.title("TEC Map of {} @ {} hours".format(path_to_ionex, hour_in_day))
        plt.ylabel("Latitude (degrees)")
        plt.yticks(range(len(lat_v))[::AXIS_STEP], lat_v[::AXIS_STEP]-90) # reverse the array so lats count down

        lat_idx, lon_idx = get_tec_for_lat_lon_idx(tecs, lat_of_interest, lon_of_interest)
        plt.annotate('Lat {} Lon {} (aprox)'.format(lat_of_interest, lon_of_interest), xy=(lon_idx, lat_idx), xytext=(lon_idx-5, lat_idx-5),
                arrowprops=dict(facecolor='white'),
        )


        plt.xlabel("Longitude (degrees)")
        plt.xticks(range(len(lon_v))[::AXIS_STEP], lon_v[::AXIS_STEP]-180)

        heatmap = plt.pcolor(tecs)
        plt.colorbar()
    
    if plot:
        plot_tec_map()
        print "Run matplotlib.pyplot.show() to see the TEC map!"
    
    lat, lon = get_tec_for_lat_lon_idx(tecs, lat_of_interest, lon_of_interest)
    tec_value = tecs[lat][lon]
    print "TEC Value ~= {}".format(tec_value)
    return tec_value, tecs