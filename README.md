# quakebreak

## input


cat select1.out >> select.out
cat select2.out >> select.out

## test

python step1_preprocess1_get_windows.py \
	--debug 1 \
	--window_size 10 \
	--window_stride 10 \
	--raw_data_dir input/datos5/mseed \
	--catalog_path output/datos5/select.out \
	--prep_data_dir output/datos5/10 \
	--station BENV

## TODO

falten imports (obspy, matplotlib)
falta passar a package

## Troubleshooting
Error:

	Error reading Nordic Format file: 'str' object has no attribute 'close'

Error from obspy when trying to read Nordic but the file it's not there
