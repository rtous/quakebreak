import json
from obspy.core import read
from quakenet.data_io import load_catalog
from obspy.core.utcdatetime import UTCDateTime
import argparse
import os
import fnmatch
import seisobs #https://github.com/d-chambers/seisobs
import sys 
import csv
#from sklearn.neighbors.nearest_centroid import NearestCentroid

class Catalog():

    def __init__(self):
        self.events = []
   
    def import_sfiles(self, input_metadata_dir):
        #This imports a nordic format sfile into our own catalog object
        print ("[preprocessing metadata] \033[94m INFO:\033[0m Remember that sfiles need to have names such as 01-1259-00M.S201804")
        metadata_files = [file for file in os.listdir(input_metadata_dir) if
            fnmatch.fnmatch(file, "*")]
        print "[preprocessing metadata] List of metadata files to anlayze: ", metadata_files

        #centroids = np.array([[10.33908571, -68.01505714], [8.246, -72.21366667], [10.352, -62.472]]) #centroids
        #centroid_numbers = np.array([0, 1, 2])
        #nearest_centroid_model = NearestCentroid()
        #nearest_centroid_model.fit(centroids, centroid_numbers)

        for metadata_file in metadata_files:
            #WARNING: Nordic Format lines start with a whitespace and have 80 characters
            #NORDIC FORMAT: http://seis.geus.net/software/seisan/node240.html
            #See fields here: https://docs.obspy.org/packages/autogen/obspy.core.event.event.Event.html#obspy.core.event.event.Event
            #1. Process metadata
            print("[preprocessing metadata] Reading metadata file "+os.path.join(input_metadata_dir, metadata_file))
            obspyCatalogMeta = seisobs.seis2cat(os.path.join(input_metadata_dir, metadata_file)) 
            
            if len(obspyCatalogMeta.events) == 0 :
                print ("[preprocessing metadata] \033[91m ERROR!!\033[0m Cannot process metadata sfile "+os.path.join(input_metadata_dir, metadata_file))
                sys.exit(0)

            #print("[preprocessing metadata] Imported sfile "+str(obspyCatalogMeta.events[0]))
            eventOriginTime = obspyCatalogMeta.events[0].origins[0].time
            lat = obspyCatalogMeta.events[0].origins[0].latitude
            lon = obspyCatalogMeta.events[0].origins[0].longitude
            depth = obspyCatalogMeta.events[0].origins[0].depth
            if len(obspyCatalogMeta.events[0].magnitudes) > 0:
                mag = obspyCatalogMeta.events[0].magnitudes[0].mag
            else:
                mag = -1 #TODO
            #cluster = nearest_centroid_model.predict([[lat, lon]])[0]
            #e = Event(eventOriginTime, lat, lon, depth, mag, cluster)
            eventid = obspyCatalogMeta.events[0].resource_id.id
            e = Event(eventOriginTime, lat, lon, depth, mag, eventid)
            self.events.append(e)
            print("APPEND")
            for pick in obspyCatalogMeta.events[0].picks:
                if pick.phase_hint == 'P':
                    station_code = pick.waveform_id.station_code
                    d = Detection(station_code, pick.time)
                    e.detections.append(d)
                    print(pick.waveform_id.get_seed_string())
            #for comment in sobspyCatalogMeta.events[0].comment:
            #    print("COMMENT:"+comment)

            #print("ID:")
            #print obspyCatalogMeta.events[0].resource_id.id
            #print obspyCatalogMeta.events[0].event_descriptions
            #for desc in obspyCatalogMeta.events[0].event_descriptions:
            #    print("DESC:"+str(desc.text))
            #print("CATALOG:"+obspyCatalogMeta.description)
            #print("COMMENTS:")
            #for ccomment in obspyCatalogMeta.comments:
            #    print("ccomment:"+ccomment)
            #print("CATALOG:"+obspyCatalogMeta.description)
            #print obspyCatalogMeta.resource_id.get_referred_object()
            #print obspyCatalogMeta.creation_info.agency_uri



    def import_txt(self, input_txtfile_path):
        #This imports a summary containing only locations and origin times for events in txt with tab delimiters
        print("[preprocessing metadata] Reading metadata file "+input_txtfile_path)
        with open(input_txtfile_path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter="\t", skipinitialspace=True)
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
                    line_count += 1
                else:
                    line_count += 1
                    year = int(row[0].strip())
                    month = int(row[1])
                    day = int(row[2])
                    hour = int(row[3])
                    minute = int(row[4])
                    sec = int(float(row[5]))
                    lat = float(row[6])
                    lon = float(row[7])
                    depth = float(row[8])
                    print(str(year)+","+str(month)+","+str(day)+","+str(hour)+","+str(minute)+","+str(sec)+","+str(lat)+","+str(lon)+","+str(depth))
                    eventOriginTime = UTCDateTime(year=year, month=month, day=day, hour=hour, minute=minute, second=sec)
                    e = Event(eventOriginTime, lat, lon, depth)
                    self.events.append(e)
                    

    #def export_json(self, path):
    #    with open(path, 'w') as f:
    #        s = json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
    #        json.dump(s, f)

    def export_json(self, path):
        with open(path, 'w') as f:
            jevents = {"events":[]}  
            for e in self.events:
                print("FOUND EVENT")
                jevent = {"detections":[]}
                jevent["eventOriginTime"] = str(e.eventOriginTime)
                jevent["lat"] = e.lat
                jevent["lon"] = e.lon
                jevent["depth"] = e.depth
                jevent["mag"] = e.mag
                jevent["eventid"] = e.eventid

                #jevent["cluster"] = e.cluster
                for d in e.detections:
                    jevent["detections"].append({"station":d.station, "ptime":str(d.ptime)})
                jevents["events"].append(jevent)
            json.dump(jevents, f, indent=4)

    def export_javascript(self, path):
        with open(path, 'w') as f:
            i = 0
            for e in self.events:
                f.write("t"+str(i)+": {\n")
                f.write("center: {lat: "+str(e.lat)+", lng:"+str(e.lon)+"},\n")
                f.write("population: "+str(e.mag)+"\n")
                f.write("},\n")
                i = i + 1

    def import_json(self, path):
        with open(path) as f:  
            jdata = json.load(f)
            for jevent in jdata['events']:
                #e = Event(UTCDateTime(jevent['eventOriginTime']), jevent['lat'], jevent['lon'], jevent['depth'], jevent['mag'], jevent['cluster'])
                e = Event(UTCDateTime(jevent['eventOriginTime']), jevent['lat'], jevent['lon'], jevent['depth'], jevent['mag'], jevent['eventid'])
                self.events.append(e)
                for jdetection in jevent['detections']:
                    d = Detection(jdetection['station'], UTCDateTime(jdetection['ptime']))
                    e.detections.append(d)

    def getPtime(self, window_start, window_end, station):
        event, detection = self.getDetection(window_start, window_end, station)
        if detection is not None:
            return detection.ptime
        else:
            return None

    def getLatLongDepth(self, window_start, window_end, station):
        event, detection = self.getDetection(window_start, window_end, station)
        return event.lat, event.lon, event.depth

    def getDetection(self, window_start, window_end, station):
        res = None
        for e in self.events:
            for d in e.detections:
                if ((d.station == station) and (d.ptime >= window_start) and (d.ptime <= window_end)):
                    return e, d
        return None, None

    def getLocations(self, depth=True):
        locations = []
        for e in self.events:
            locations.append([e.lat, e.lon, e.depth])
            if depth:
                print(str(e.lat)+","+str(e.lon)+","+str(e.depth))
            else:
                print(str(e.lat)+","+str(e.lon))
        return locations

class Event():
    #def __init__(self, eventOriginTime, lat, lon, depth, mag, cluster):
    def __init__(self, eventOriginTime, lat, lon, depth, mag, eventid):
        self.eventOriginTime = eventOriginTime
        self.lat = lat
        self.lon = lon
        self.depth = depth
        self.detections = [] 
        self.mag = mag
        self.eventid = eventid

        #self.cluster = cluster

class Detection():
    def __init__(self, station, ptime):
        self.station = station
        self.ptime = ptime

if __name__ == "__main__":
    print ("\033[92m******************** CATALOG TOOL *******************\033[0m ")
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_path", type=str)
    parser.add_argument("--output_path", type=str)
    args = parser.parse_args()
    if not os.path.exists(os.path.dirname(args.output_path)):
        os.makedirs(os.path.dirname(args.output_path))
    c = Catalog()
    #c.import_sfiles(args.input_path)
    #c.export_json(args.output_path)
    c.import_json(args.input_path)
    c.export_javascript(args.output_path)


    

        