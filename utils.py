#!/usr/bin/env python
# -------------------------------------------------------------------
# File Name : utils.py
# Creation Date : 11-07-2018
# Last Modified : 11-07-2018 13:21:32 
# Author: Ruben Tous <rtous@ac.upc.edu>
# -------------------------------------------------------------------
""""
Common functions.
"""
import os
import setproctitle
import numpy as np
from quakenet.data_pipeline import DataWriter
import tensorflow as tf
from obspy.core import read
from quakenet.data_io import load_catalog
from obspy.core.utcdatetime import UTCDateTime
import fnmatch
import json
import argparse
from tqdm import tqdm
import time
import pandas as pd
import seisobs #https://github.com/d-chambers/seisobs
import config as config
import matplotlib.pyplot as plt
import obspy
import datetime as dt
from openquake.hazardlib.geo.geodetic import distance
import sys

def preprocess_stream(stream):
    stream = stream.detrend('constant')
    stream = stream.normalize()

    #if filterfreq:
    #    stream = stream.taper(max_percentage=0.05, type="hann")
    #    stream = stream.filter("bandpass", freqmin = 0.5, freqmax = 10.0)
    return stream

def filter_stream(stream):
    #stream = stream.taper(max_percentage=0.05, type="hann")
    stream = stream.filter("bandpass", freqmin = 0.5, freqmax = 10.0)
    return stream

def obspyDateTime2PythonDateTime(odt):
    return dt.datetime(odt.year, odt.month, odt.day, odt.hour, odt.minute, odt.second)

def check_stream(stream, cfg, check_n_traces=True): 
    if check_n_traces and len(stream) != cfg.n_traces:
        if cfg.debug:
            print ("[check stream] \033[93m WARNING!!\033[0m Only "+str(len(stream))+" channels.")
        return False
    if stream[0].stats.sampling_rate != 100.0:
        if cfg.debug:
            print ("[check stream] \033[93m WARNING!!\033[0m Wrong sampling rate ("+str(stream[0].stats.sampling_rate)+").")
        return False

    theoretical_data_size = 0
    data_size = 0
    for i in range(len(stream)):
        theoretical_data_size = theoretical_data_size + cfg.win_size
        data_size = data_size + len(stream[i].data)

    #data_size = len(stream[0].data) + len(stream[1].data) + len(stream[2].data)

    if data_size != theoretical_data_size:
        if cfg.debug:
            print ("[check stream] \033[93m WARNING!!\033[0m Not enough data points  ("+str(data_size)+").")
        return False 
    return True

def fetch_window_data(stream, cfg):
    """fetch data from a stream window and dump in np array"""
    data = np.empty((cfg.win_size, cfg.n_traces))
    for i in range(cfg.n_traces):
        data[:, i] = stream[i].data.astype(np.float32)
    data = np.expand_dims(data, 0)
    return data

def select_components(stream, cfg):
    """fetch data from a stream window and dump in np array"""
    stream_select = None
    if cfg.component_Z:
        stream_select = stream.select(component="Z")
        if len(stream_select) == 0:
            print ("[utils.select_components] \033[91m ERROR!!\033[0m Selected component is empty (trying to extract three components tfrecords with mseed with just 1?).")
            sys.exit(0)
        #print ("[check select_components] component Z selected.")
    if cfg.component_N:
        #print ("[check select_components] component N selected.")
        streamN = stream.select(component="N")
        if len(streamN) == 0:
            print ("[utils.select_components] \033[91m ERROR!!\033[0m Selected component is empty (trying to extract three components tfrecords with mseed with just 1?).")
            sys.exit(0)
        if stream_select == None:
            stream_select = streamN
        else:
            stream_select += streamN
    if cfg.component_E:
        #print ("[check select_components] component E selected.")
        streamE = stream.select(component="E")
        if len(streamE) == 0:
            print ("[utils.select_components] \033[91m ERROR!!\033[0m Selected component is empty (trying to extract three components tfrecords with mseed with just 1?).")
            sys.exit(0)
        if stream_select == None:
            stream_select = streamE
        else:
            stream_select += streamE
    return stream_select

def isPositiveKnownP(window_start, window_end, cat):
    isPositive = False
    for i in range(0, len(cat.start_time)):
        event_start_time = UTCDateTime(cat.start_time[i])
        event_end_time = UTCDateTime(cat.end_time[i])
        if (event_start_time >= UTCDateTime(window_start)) and (event_end_time <= UTCDateTime(window_end)):# and (cat.end_time[0] <= win[0].stats.endtime):
            isPositive = True
    return isPositive

def isPositiveEstimatedP(window_start, window_end, cat, stationLAT, stationLONG, stationDEPTH, mean_velocity):
    isPositive = False
    for i in range(0, len(cat.start_time)):
        event_start_time = UTCDateTime(cat.start_time[i]) + travel_time(cat.lat[i], cat.long[i], cat.prof[i], stationLAT, stationLONG, stationDEPTH, mean_velocity)
        event_end_time = UTCDateTime(cat.end_time[i]) + travel_time(cat.lat[i], cat.long[i], cat.prof[i], stationLAT, stationLONG, stationDEPTH, mean_velocity)
        if (event_start_time >= UTCDateTime(window_start)) and (event_end_time <= UTCDateTime(window_end)):# and (cat.end_time[0] <= win[0].stats.endtime):
            isPositive = True
    return isPositive

#def save_json(data, path):
#    with open(path, 'w') as outfile:  
#        json.dump(data, outfile)

def travel_time(lat, long, depth, stationLAT, stationLONG, stationDEPTH, mean_velocity):
    #print("long ="+str(long)+", lat ="+str(lat)+", depth ="+str(depth)+", stationLONG ="+str(stationLONG)+", stationLAT ="+str(stationLAT));
    distance_to_station = distance(long, lat, depth, stationLONG, stationLAT, stationDEPTH)
    #distance_to_station = distance(long, lat, 0, stationLONG, stationLAT, 0)
    #distance in km
    #print("distance_to_station = "+str(distance_to_station)+" km")
    travel_time = (distance_to_station/mean_velocity)*3600
    #print("travel_time = "+str(travel_time)+"s")
    return travel_time

def station_coordinates(station, stations):
    stationLAT = None
    stationLONG = None
    stationDEPTH = None
    for i in range(0, len(stations.code)):
        if station == stations.code[i]:
            stationLAT = stations.latitude[i]
            stationLONG = stations.longitude[i]
            stationDEPTH = stations.elevation[i]
    return stationLAT, stationLONG, stationDEPTH

def getPtime(window_start, window_end, cat, stationLAT, stationLONG, stationDEPTH, mean_velocity):
    timeP = None
    eventTime = None
    for i in range(0, len(cat.start_time)):
        event_start_time = UTCDateTime(cat.start_time[i]) + travel_time(cat.lat[i], cat.long[i], cat.prof[i], stationLAT, stationLONG, stationDEPTH, mean_velocity)
        event_end_time = UTCDateTime(cat.end_time[i]) + travel_time(cat.lat[i], cat.long[i], cat.prof[i], stationLAT, stationLONG, stationDEPTH, mean_velocity)
        if (event_start_time >= UTCDateTime(window_start)) and (event_end_time <= UTCDateTime(window_end)):# and (cat.end_time[0] <= win[0].stats.endtime):
            timeP = event_start_time
            eventTime = UTCDateTime(cat.start_time[i])
    return timeP, eventTime

def getPtimeFromObsPyCat(obspyCatalogMeta, station):
    print("getPtimeFromObsPyCat for station "+station)
    timeP = None
    for pick in obspyCatalogMeta.events[0].picks:
        print("Found pick")
        if pick.phase_hint == 'P':
            station_code = pick.waveform_id.station_code
            print("Found P for station "+station_code)
            if station == station_code:
                timeP = pick.time
                break
    return timeP

def fileNameWithoutExtension(fileName):
    return os.path.splitext(fileName)[0]