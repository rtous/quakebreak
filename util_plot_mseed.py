#!/usr/bin/env python
# -------------------------------------------------------------------
# File Name : convert_stream_to_tfrecords.py
# Creation Date : 09-12-2016
# Last Modified : Mon Jan  9 13:21:32 2017
# Author: Thibaut Perol <tperol@g.harvard.edu>
# -------------------------------------------------------------------
#TODO: Generating windows is embarassingly parallel. This can be speed up
""""
Load a stream, preprocess it, and create windows in tfrecords to be
fed to ConvNetQuake for prediction
NB: Use max_windows to create tfrecords of 1 week or 1 month
NB2: This convert a stream into ONE tfrecords, this is different
from create_dataset_events and create_dataset_noise that output
multiple tfrecords of equal size used for training.
e.g.,
./bin/preprocess/convert_stream_to_tfrecords.py \
--stream_path data/streams/GSOK029_7-2014.mseed \
--output_dir  data/tfrecord \
--window_size 10 --window_step 11 \
--max_windows 5000
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

#OUTPUT_DIR = "output"

def preprocess_stream(stream):
    stream = stream.detrend('constant')
    return stream.normalize()

def main(args):
    # Create dir to store the plot
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    if os.path.isdir(args.stream_path):
        processDirectory(args)
    else:
        processSingleFile(args.stream_path, args) 

def processDirectory(args):
    files = [file for file in os.listdir(args.stream_path) if
                    fnmatch.fnmatch(file, "*.mseed")]
    for file in files:
        processSingleFile(os.path.join(args.stream_path, file), args)

def processSingleFile(file, args):
    # Load stream
    stream_path = file
    stream_file = os.path.split(stream_path)[-1]
    print "+ Loading Stream {}".format(stream_file)
    stream = read(stream_path)
    print '+ Preprocessing stream'
    stream = preprocess_stream(stream)

    total_time = stream[-1].stats.endtime - stream[0].stats.starttime
    print "total time {}s".format(total_time)

    #debug: plot all
    stream.plot(outfile=os.path.join(args.output_dir, os.path.basename(stream_path)+".png"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stream_path",type=str, required=True,
                        help="path to mseed to analyze")
    parser.add_argument("--output_dir",type=str, required=True)
    args = parser.parse_args()
    main(args)
