import configparser
import argparse
import sys
import os

STRING = 0
INT = 1
FLOAT = 2
BOOLEAN = 3

class Config(object):

    def __init__(self, args):
        if args.config_file_path is not None:
            if not os.path.isfile(args.config_file_path):
                print ("[config] \033[91m ERROR!!\033[0m Config file not found: "+args.config_file_path)
                sys.exit(0)
            config = configparser.ConfigParser()
            config.read(args.config_file_path)  
        else:
            config = None
        default_config = configparser.ConfigParser()
        default_config.read("config_default.ini")   
        self.read_attribute('debug', BOOLEAN, default_config, config, args)

        #preprocessing
        self.read_attribute('filterfreq', BOOLEAN, default_config, config, args)
        self.read_attribute('sampling_rate', INT, default_config, config, args)
        self.read_attribute('window_size', INT, default_config, config, args)
        self.read_attribute('pwave_window', INT, default_config, config, args)
        self.read_attribute('window_stride', INT, default_config, config, args)
        self.read_attribute('window_avoid_negatives_before', INT, default_config, config, args)
        self.read_attribute('window_avoid_negatives_after', INT, default_config, config, args)
        self.n_traces = 0
        self.read_attribute('component_Z', BOOLEAN, default_config, config, args)
        if self.component_Z:
            self.n_traces = self.n_traces + 1 
        self.read_attribute('component_N', BOOLEAN, default_config, config, args)
        if self.component_N:
            self.n_traces = self.n_traces + 1
        self.read_attribute('component_E', BOOLEAN, default_config, config, args)
        if self.component_E:
            self.n_traces = self.n_traces + 1
        if self.n_traces == 0:
            print ("[config] \033[91m ERROR!!\033[0m 0 number of components selected. You need to specify at least component_Z = true, component_N = true or component_E = true")
            sys.exit(0)
        self.read_attribute('mean_velocity', FLOAT, default_config, config, args)
        self.read_attribute('mseed_dir', STRING, default_config, config, args)
        self.read_attribute('mseed_event_dir', STRING, default_config, config, args)
        self.read_attribute('mseed_noise_dir', STRING, default_config, config, args)
        self.read_attribute('png_dir', STRING, default_config, config, args)
        self.read_attribute('png_event_dir', STRING, default_config, config, args)
        self.read_attribute('png_noise_dir', STRING, default_config, config, args)
        self.read_attribute('output_tfrecords_dir_positives', STRING, default_config, config, args)
        self.read_attribute('output_tfrecords_dir_negatives', STRING, default_config, config, args)
        
        #tfrecords
        self.read_attribute('random_seed', INT, default_config, config, args)
        self.read_attribute('balance', BOOLEAN, default_config, config, args)

        #model
        self.read_attribute('model', STRING, default_config, config, args)
        self.read_attribute('num_conv_layers', INT, default_config, config, args)
        self.read_attribute('conv_stride', INT, default_config, config, args)
        self.read_attribute('num_fc_layers', INT, default_config, config, args)
        self.read_attribute('fc_size', INT, default_config, config, args)
        self.read_attribute('pooling', BOOLEAN, default_config, config, args)
        self.read_attribute('n_clusters', INT, default_config, config, args)
        self.read_attribute('pooling_window', INT, default_config, config, args)
        self.read_attribute('pooling_stride', INT, default_config, config, args)
        self.read_attribute('ksize', INT, default_config, config, args)

        #training
        self.read_attribute('learning_rate', FLOAT, default_config, config, args)
        self.read_attribute('batch_size', INT, default_config, config, args)
        self.win_size = int((self.window_size * self.sampling_rate) + 1)
        self.read_attribute('display_step', INT, default_config, config, args)
        self.read_attribute('n_threads', INT, default_config, config, args)
        self.n_epochs = None
        self.regularization = 1e-3
        self.read_attribute('resume', BOOLEAN, default_config, config, args)
        self.read_attribute('profiling', BOOLEAN, default_config, config, args)
        self.read_attribute('add', INT, default_config, config, args)
        self.read_attribute('checkpoint_step', INT, default_config, config, args)
        self.read_attribute('max_checkpoint_step', INT, default_config, config, args)
        self.read_attribute('window_step_predict', INT, default_config, config, args)
        self.read_attribute('save_sac', BOOLEAN, default_config, config, args)

    def read_attribute(self, attribute, type, default_config, config, args):
        value = None

        #Check if the attribute has been passed as argument.
        #WARNING: If the argument is optional, ensure that argsparse did not assign a default value.
        #e.g. Use default=argparse.SUPPRESS
        if hasattr(args, attribute):
            value = getattr(args, attribute)
            if type == BOOLEAN: 
                value = bool(value) #We use int arguments as booleans are not properly supported by argparse
            print_info(attribute, value, True)
        elif config is not None and config.has_option('main', attribute):
            value = read_attribute_from_config_file(attribute, type, config)
            print_info(attribute, value, True)
        elif default_config.has_option('main', attribute):   
            value = read_attribute_from_config_file(attribute, type, default_config) 
            print_info(attribute, value, False)
        else:
            print("ERROR: Attribute "+attribute+" not found in config files neither in arguments.")
            sys.exit(0)
        setattr(self, attribute, value)


def read_attribute_from_config_file(attribute, type, config):     
    value = None
    if type == STRING:
        value = config.get('main', attribute)
    elif type == INT:
        value = config.getint('main', attribute)
    elif type == FLOAT:
        value = config.getfloat('main', attribute)
    elif type == BOOLEAN:
        value = config.getboolean('main', attribute)
    else:
        print("ERROR (config.py): Type "+type+" not valid.")
        sys.exit(0)
    return value

def print_info(attribute, value, overwritten):
    sys.stdout.write("[\033[94mCONFIG\033[0m] "+str(attribute)+" = "+str(value))
    if overwritten:
        sys.stdout.write("\033[94m (OVERWRITTEN)\033[0m")
    sys.stdout.write("\n")
