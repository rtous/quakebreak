# quakebreak

## About this repository

*CURRENT STATUS/ACTIVITY: Under construction, not sure if it will be finished.*

*CURRENT STATUS/USABILITY: Usable as example code, not as a tool (not finished).*

This repository provides tools to split seismograms into windows for their usage in machine learning datasets. It is a component of the UPC-UCV project, related to the application of deep neural networks to the automated analysis of seismograms. More specifically, this repository is part of the preprocessing tools, used to generate the datasets to train and test the models.  

## Prerequisites

The repository has been created with Python 3.7 and has not been tested with previous versions.

It is convenient to activate a python virtual environment before installing the dependencies:

	python3 -m venv VirtualEnvs/myVirtualEnv
	source VirtualEnvs/myVirtualEnv/bin/activate


## Input

1. Catalog: A seismic catalog in Nordic format, typically obtained from [SEISAN](https://www.geosig.com/files/GS_SEISAN_9_0_1.pdf), the seismic analysis software suite. 

2. Waveforms: A set of .mseed files.

## Test

get_windows.py \
	--debug 1 \
	--window_size 10 \
	--window_stride 10 \
	--raw_data_dir input/datos5/mseed \
	--catalog_path input/datos5/select.out \
	--prep_data_dir output/datos5/10 \
	--station BENV

## TODO

- Packaging as a command line tool

## Troubleshooting

Error:

	Error reading Nordic Format file: 'str' object has no attribute 'close'

Error from obspy when trying to read Nordic but the file it's not there
