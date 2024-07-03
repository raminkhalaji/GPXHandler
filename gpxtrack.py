

import math
import random
import numpy as np

from datetime import datetime, timedelta, timezone

from scipy import signal
from scipy import interpolate

import utm

import gpxpy
import gpxpy.gpx as GPX


# CONSTANTS
EARTH_RADIUS = 6371000
GARMIN_HANDYGPS = 'GARMIN_HANDYGPS'
IPHONE_WICILOC = 'IPHONE_WIKILOC'
ALPINE_QUEST = 'ALPINE_QUEST'


'''
TrackPoint3D Class
'''
class TrackPoint3D:

    # Members
    name:str
    long:float
    lat:float
    elevation:float
    timestamp:datetime
    description:str
    comment:str

    # Calculated Vars
    speed:float
    density:float


    def __init__(self, name:str = '', lat:float=0, long:float=0, elev:float=0, timestamp:datetime=None, description:str=' ', comment:str=' ', speed:float=None):
        self.name = name
        self.long = long
        self.lat = lat
        self.elevation = elev
        self.timestamp = timestamp        
        self.description = description
        self.comment = comment
        self.speed = speed


    def to_utm(self):
        easting, northing, _, _ = utm.from_latlon(self.lat, self.long)
        return easting, northing
    

    def distance2D_to(self, other)->float:
        if isinstance(other, TrackPoint3D):

            pt1 = self.to_utm()
            pt2 = other.to_utm()

            return math.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)
        else:
            return None
    
    
    def attract_to(self, other, weight:float, preserve_elevation:True):
        if isinstance(other, TrackPoint3D):

            result_point = self

            result_point.lat = (1-weight)*self.lat + weight*other.lat
            result_point.long = (1-weight)*self.long + weight*other.long

            if not preserve_elevation:
                result_point.elevation = (1-weight)*self.elevation + weight*other.elevation

            return result_point


    def deltatime(self, other)->timedelta:
        if isinstance(other, TrackPoint3D):
            return (self.timestamp - other.timestamp)
        else:
            return None
        
    
    def deltatime_seconds(self, other) -> float:
        if isinstance(other, TrackPoint3D):
            return self.deltatime(other).total_seconds()
        else:
            return None
        
    
    def set_timestamp(self, new_timestamp:datetime):
        if not new_timestamp.tzinfo:
            self.timestamp = datetime(new_timestamp.year,
                                        new_timestamp.month,
                                        new_timestamp.day,
                                        new_timestamp.hour,
                                        new_timestamp.minute,
                                        new_timestamp.second,
                                        tzinfo=timezone.utc)
        else:
            self.timestamp = new_timestamp
        
    
    def time_shift(self, delta:timedelta):
        if self.timestamp:
            self.timestamp = self.timestamp + delta
        else:
            self.timestamp = None

    
    def regulate(self):
        
        # ROUND VALUES
        self.lat = round(self.lat, 6)
        self.long = round(self.long, 6)
        self.elevation = round(self.elevation, 1)

        # REGULATE TIME
        if not self.timestamp.tzinfo:
                self.timestamp = datetime(self.timestamp.year,
                                          self.timestamp.month,
                                          self.timestamp.day,
                                          self.timestamp.hour,
                                          self.timestamp.minute,
                                          self.timestamp.second,
                                          tzinfo=timezone.utc)


    # TO STRING
    def __str__(self) -> str:
        return f'{self.name}, Lat:{self.lat}, Long:{self.long}, Elev:{self.elevation}, Time:{datetime.strftime(self.timestamp, "%H:%M:%S")}'



'''
Tracklog Class
'''
class Tracklog:

    gpx_name:str
    gpx_time:str
    gpx_creator:str
    gpx_version:str
    gpx_nsmap:dict[str, str]
    gpx_schema_locations:list[str]

    gpx_link:str
    gpx_link_text:str
    gpx_link_type:str

    copyright_year:str
    copyright_license:str
    copyright_author:str

    author_name:str
    author_link:str
    author_link_text:str
    author_link_type:str
    author_email:str

    track_name:str
    track_comment:str
    track_desc:str

    waypoints:list[TrackPoint3D]
    trackpoints:list[TrackPoint3D]


    def __init__(self, gpx_path:str = None):

        self.waypoints = []
        self.trackpoints = []

        if gpx_path is not None:
            self.import_gpx(gpx_path)


    @staticmethod
    def read_csv_(csv_path:str, pid_field:int=0, lat_field:int=1, long_field:int=2, elev_field:int=None, desc_field:int = None)->list[TrackPoint3D]:
        
        points_list:list[TrackPoint3D] = []

        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            
            end_of_file = False

            while not end_of_file:
                line = csvfile.readline()

                if line != '':
                    
                    parts = line.split(',')
                    
                    try:
                        if pid_field:
                            pid = str(parts[pid_field])
                        else:
                            pid='tkpt'

                        if lat_field:
                            lat = float(parts[lat_field])
                        else:
                            lat= None

                        if long_field:
                            long = float(parts[long_field])
                        else:
                            long = None

                        if elev_field:
                            elev = float(parts[elev_field])
                        else:
                            elev = 0

                        if desc_field:
                            desc = parts[desc_field]
                        else:
                            desc = ' '

                        if long and lat:
                            pt3D = TrackPoint3D(pid, lat, long, elev, None, desc)
                            points_list.append(pt3D)
                    
                    except:
                        pass
            
                else:
                    end_of_file = True        

            if len(points_list) > 0:
                return points_list
            else:
                return None


    # IMPORT CSV
    def import_csv(self, csv_path:str, as_trackpoints:bool=True,
                    pid_field:int=0, lat_field:int=1, long_field:int=2, elev_field:int=None, desc_field:int = None
                   ):

        resultlist = Tracklog.read_csv_(csv_path, pid_field, lat_field, long_field, elev_field, desc_field)
        
        if as_trackpoints:
            self.trackpoints = resultlist
        else:
            self.waypoints = resultlist


    # IMPORT GPX
    def import_gpx(self, gpx_path:str):

        waypoints_list:list[TrackPoint3D] = []
        trackpoints_list:list[TrackPoint3D] = []

        with open(gpx_path, 'r', encoding='utf-8') as gpxfile:
            
            gpxdata = gpxpy.parse(gpxfile)

            self.gpx_creator = gpxdata.creator
            self.gpx_name = gpxdata.name
            self.gpx_link = gpxdata.link
            self.gpx_link_text = gpxdata.link_text
            self.gpx_nsmap = gpxdata.nsmap
            self.gpx_schema_locations = gpxdata.schema_locations
            self.gpx_version = gpxdata.version

            self.track_name = gpxdata.tracks[0].name
            self.track_comment = gpxdata.tracks[0].comment
            self.track_desc = gpxdata.tracks[0].description


            # READ WAyPOINTS
            waypoint_index = 1
            for point in gpxdata.waypoints:

                pt3D = TrackPoint3D(
                    name = f'wpt{waypoint_index:4}',
                    lat = point.latitude,
                    long = point.longitude,
                    elev = point.elevation,
                    timestamp = point.time                    
                )

                waypoints_list.append(pt3D)
                waypoint_index += 1

            # READ TRACKPOINTS
            trackpoint_index = 1
            for track in gpxdata.tracks:
                for segment in track.segments:            
                    for point in segment.points:
                        
                        pt3D = TrackPoint3D(
                            name = f'trkpt{trackpoint_index:4}',
                            lat = point.latitude,
                            long = point.longitude,
                            elev = point.elevation,
                            timestamp = point.time
                        )

                        trackpoints_list.append(pt3D)
                        trackpoint_index += 1
        
        self.waypoints = waypoints_list
        self.trackpoints = trackpoints_list
    

    # CHECK IF THE TRACK IS NOT EMPTY
    def is_empty(self)->bool:
        if len(self.trackpoints) > 0:
            return False
        else:
            return True
        
    
    # CHECK IF THE TRACK HAS TIMESTAMP
    def has_timestamp(self):
        if self.is_empty():
            return False
        
        if self.trackpoints[0].timestamp:
            return True
        else:
            return False


    #GET LENGTH
    def track_length(self, from_index:int = None, to_index:int = None)->float:
        
        n_trackpoints = len(self.trackpoints)

        if  n_trackpoints < 2:
            return 0
        
        if not from_index or from_index < 0:
            from_index = 0
        
        if not to_index or to_index > n_trackpoints:
            to_index = n_trackpoints


        total_length = 0
        
        for index in range(from_index + 1, to_index):
            segment_length = self.trackpoints[index].distance2D_to(self.trackpoints[index-1])
            total_length += segment_length

        return total_length


    def reconstruct(self, n_nodes:int, interpolation_type = 'linear'):
        
        n_trackpoints = len(self.trackpoints)

        if n_trackpoints > 2:

            xdata = np.arange(0, n_trackpoints)
            latdata = np.array([pt.lat for pt in self.trackpoints])
            longdata = np.array([pt.long for pt in self.trackpoints])
            elevdata = np.array([pt.elevation for pt in self.trackpoints])
            # timestampdata = np.array([pt.timestamp for pt in self.trackpoints])

            lat_intp = interpolate.interp1d(xdata, latdata, interpolation_type)
            long_intp = interpolate.interp1d(xdata, longdata, interpolation_type)
            elev_intp = interpolate.interp1d(xdata, elevdata, interpolation_type)
            # timestamp_intp = interpolate.interp1d(xdata, timestampdata, interpolation_type)

            new_xdata = np.linspace(0, n_trackpoints, n_nodes, endpoint=False)

            new_latdata = lat_intp(new_xdata)
            new_longdata = long_intp(new_xdata)
            new_elevdata = elev_intp(new_xdata)
            # new_timestampdata = timestamp_intp(new_xdata)

            self.trackpoints = []
            for i in range(len(new_latdata)):
                self.trackpoints.append(TrackPoint3D(f'trkpt{i}',new_latdata[i], new_longdata[i], new_elevdata[i]))



    def update_speed(self):

        if self.is_empty():
            return None
        
        if len(self.trackpoints) < 2:
            print('Not Enough Data to Calculate Speed')
            return None

        if not self.has_timestamp():
            print('No Timestamp Data')
            return None

        self.trackpoints[0].speed = 0
        
        for i in range(1, self.trackpoints_count()):

            pt1 = self.trackpoints[i-1]
            pt2 = self.trackpoints[i]
            dist = pt2.distance2D_to(pt1)
            delta_time = pt2.deltatime_seconds(pt1)

            speed = dist / delta_time
            self.trackpoints[i].speed = speed


    # FIND CLOSEST TRACKPOINT TO CERTAIN POSITION
    def find_nearest(self, point:TrackPoint3D, max_distance:float = 10)->int:
        nearest_index = None
        min_dist = None

        if self.is_empty():
            return None
        
        for i in range(len(self.trackpoints)):
            trkpt = self.trackpoints[i]
            dist = trkpt.distance2D_to(point)

            if min_dist:
                if dist < min_dist:
                    min_dist = dist
                    nearest_index = i
            
            else:
                min_dist = dist
                nearest_index = i

        if min_dist < max_distance:            
            
            return nearest_index
        
        else:
            return None
        
    
    def at_index(self, index) -> TrackPoint3D:
        return self.trackpoints[index]


    def at_timestamp(self, at_time:datetime) -> TrackPoint3D:

        if self.is_empty():
            return None

        if not self.has_timestamp():
            return None
        
        nearest_index = 0
        min_deltatime = self.trackpoints[0].timestamp - at_time

        for i in range(self.trackpoints_count()):
            delta_time = self.trackpoints[i].timestamp - at_time

            if delta_time < min_deltatime:
                nearest_index = i
                min_deltatime = delta_time

        print(f'Found index: {nearest_index}')
        return nearest_index


    def density_at(self, at_index:int, search_radius:float, windowsize=100)->list:

        half_window = int(windowsize/2)

        for pt1 in self.trackpoints:

            n_points = 0

            for pt2 in self.trackpoints:
                dist = pt1.distance2D_to(pt2)
                if pt1.distance2D_to(pt2) < search_radius:
                    n_points += 1
            
            pt1.density = n_points
            print(n_points)


    def add_missing_timestamp(self, start_time:datetime, average_speed:float=.6, div:float = .1, end_index = None):
        
        if len(self.trackpoints) < 1:
            return None

        if not end_index:
            end_index = len(self.trackpoints) - 1

        self.trackpoints[0].timestamp = start_time

        random.seed(157)

        index=1

        while index <= end_index:
            dist = self.trackpoints[index].distance2D_to(self.trackpoints[index-1])
            speed = average_speed + div * (2 * random.random() - 1)
            deltatime_sec = dist / speed
            new_timestamp = self.trackpoints[index-1].timestamp + timedelta(seconds=deltatime_sec)
            self.trackpoints[index].set_timestamp(new_timestamp)
            
            index += 1


    # AVERAGE SPEED
    def average_speed(self):

        extents = self.extents()

        track_length = self.track_length()
        start_time:datetime = extents['start-time']
        end_time:datetime = extents['end-time']
        duration = (end_time - start_time).total_seconds

        return track_length / duration


    # N_TRACKPOINTS
    def trackpoints_count(self):
        return len(self.trackpoints)


    # TRACK TIME RANGE
    def time_range(self):
        if self.is_empty():
            return None
        
        if self.has_timestamp():
            return [self.trackpoints[0].timestamp, self.trackpoints[-1].timestamp]
        
        else:
            return None
    

    # TRACK EXTENTS
    def extents(self)->dict:

        lats = np.array([pt3D.lat for pt3D in self.trackpoints])
        longs = np.array([pt3D.long for pt3D in self.trackpoints])
        elevs = np.array([pt3D.elevation for pt3D in self.trackpoints])

        if len(lats) > 0 and len(longs) and len(elevs):
            lat_extents = (np.min(lats), np.max(lats))
            long_extents = (np.min(longs), np.max(longs))
            elev_extents = (np.min(elevs), np.max(elevs))

            return {
                'min-lat' : lat_extents[0],
                'max-lat' : lat_extents[1],
                'min-long' : long_extents[0],
                'max-long' : long_extents[1],
                'min-elevation' : elev_extents[0],
                'max-elevation' : elev_extents[1]
            }

        else:
            return None

    
    # RANDOMIZE POSITION
    def randomize_elev(self, div_z:float=4):
        random.seed(341)

        for pt in self.trackpoints:
            z_div = -div_z + 2 * div_z * random.random()
            pt.elevation += z_div


    # REGULATE TIME
    def regulate_points(self, min_deltatime_sec:float=2):

        new_point_list:list[TrackPoint3D] = []

        last_point = self.trackpoints[0]

        for index in range(1, len(self.trackpoints)):
            pt = self.trackpoints[index]

            delta_time = pt.timestamp - last_point.timestamp
            
            if delta_time.total_seconds() >= min_deltatime_sec:                
                new_point_list.append(pt)
                last_point = pt

        self.trackpoints = new_point_list


    # TRIM
    def trim(self, start_time:datetime, end_time:datetime):

        result_waypoints:list[TrackPoint3D] = []
        for pt3D in self.waypoints:
            if pt3D.timestamp > start_time and pt3D.timestamp < end_time:
                result_waypoints.append(pt3D)
            else:
                print(f'out of range: {pt3D.timestamp.strftime('%m/%d/%Y, %H:%M:%S')}')

        result_trackpoints:list[TrackPoint3D] = []
        for pt3D in self.trackpoints:
            if pt3D.timestamp > start_time and pt3D.timestamp < end_time:
                result_trackpoints.append(pt3D)
            else:
                print(f'out of range: {pt3D.timestamp.strftime('%m/%d/%Y, %H:%M:%S')}')

        self.waypoints = result_waypoints
        self.trackpoints = result_trackpoints


    # TIME SHIFT
    def time_shift(self, ref_timestamp:datetime, at_index:int=0):
        
        result_list:list[TrackPoint3D] = []

        orig_timestamp = self.trackpoints[at_index].timestamp
        delta = ref_timestamp - orig_timestamp

        result_list = []
        for pt3D in self.trackpoints:
            pt3D.timestamp += delta
            result_list.append(pt3D)

        self.trackpoints = result_list

        result_list = []
        for pt3D in self.waypoints:
            pt3D.timestamp += delta
            result_list.append(pt3D)

        self.waypoints = result_list


    # REVERSE TIME
    def time_reverse(self):
        
        self.update_speed()

        time_extents = self.time_range()
        start_time = time_extents[0]
        end_time = time_extents[1]
        
        delta = end_time - start_time
        center_time = start_time + delta / 2
        

        for pt in self.waypoints:

            if pt.timestamp < center_time:
                new_timestamp = center_time + (center_time - pt.timestamp)

            else:
                new_timestamp = center_time - (pt.timestamp - center_time)

            pt.timestamp = datetime(new_timestamp.year,
                                    new_timestamp.month,
                                    new_timestamp.day,
                                    new_timestamp.hour,
                                    new_timestamp.minute,
                                    new_timestamp.second,
                                    tzinfo= new_timestamp.tzinfo)

        self.trackpoints.reverse()

        self.trackpoints[0].timestamp = start_time
        for i in range(1, len(self.trackpoints)):

            pt1 = self.trackpoints[i - 1]
            pt2 = self.trackpoints[i]

            dist = pt2.distance2D_to(pt1)

            if pt1.speed != 0:
                deltatime_sec = dist / pt1.speed                
            else:
                deltatime_sec = 2

            new_timestamp = pt1.timestamp + timedelta(seconds=deltatime_sec)
            self.trackpoints[i].timestamp = datetime(new_timestamp.year,
                                     new_timestamp.month,
                                     new_timestamp.day,
                                     new_timestamp.hour,
                                     new_timestamp.minute,
                                     new_timestamp.second,
                                     tzinfo= new_timestamp.tzinfo
            )
     
    
    # SNAP TO / ATTRACT
    def attract_to(self, other, max_dist:float, attr_weight:float, preserve_height:bool = True, start_time:datetime=None, end_time:datetime=None):

        result_track_points:list[TrackPoint3D] = []

        time_extents = self.time_range()

        if not start_time:
            start_time = time_extents[0]

        if not end_time:
            end_time = time_extents[1]

        if start_time > end_time:
            temp_time = start_time
            start_time = end_time
            end_time = temp_time


        if isinstance(other, Tracklog):            
            
            for trkpt in self.trackpoints:                
                
                if trkpt.timestamp > start_time and trkpt.timestamp < end_time:

                    target_index = other.find_nearest(trkpt, max_dist)
                    
                    if target_index:
                        target = self.at_index(target_index)

                    if target_index:
                        mod_pt = trkpt.attract_to(target, attr_weight, preserve_height)
                    else:
                        mod_pt = trkpt
                
                else:
                    mod_pt = trkpt


                result_track_points.append(mod_pt)

            self.trackpoints = result_track_points
                

    # APPEND
    def append_track(self, other):
        
        if isinstance(other, Tracklog):
            for pt in other.trackpoints:
                self.trackpoints.append(pt)

            for pt in other.waypoints:
                self.waypoints.append(pt)

    
    def sort_waypoints(self):

        n_waypoints = len(self.waypoints)

        for i1 in range(0, n_waypoints-1):
            for i2 in range(i1+1, n_waypoints):

                pt1 = self.waypoints[i1]
                pt2 = self.waypoints[i2]

                if pt1.timestamp > pt2.timestamp:
                    self.waypoints[i1] = pt2
                    self.waypoints[i2] = pt1
        
        for i in range(0, n_waypoints):
            new_annotation = f'wpt{i}'
            self.waypoints[i].name = new_annotation
            self.waypoints[i].comment = new_annotation
            self.waypoints[i].description = new_annotation


    def sort_trackpoints(self):
        
        n_trackpoints = self.trackpoints_count()

        for i1 in range(0, n_trackpoints-1):
            for i2 in range(i1 + 1, n_trackpoints):

                pt1 = self.trackpoints[i1]
                pt2 = self.trackpoints[i2]

                if pt1.timestamp > pt2.timestamp:
                    self.trackpoints[i1] = pt2
                    self.trackpoints[i2] = pt1

    
    # WRITE GPX
    def export_gpx(self, output_path, template_log = None):

        self.regulate_points(2)
        self.randomize_elev(4)

        gpxdata = GPX.GPX()
        
        if isinstance(template_log, Tracklog) and template_log:
            gpxdata.creator = template_log.gpx_creator
            gpxdata.name = template_log.gpx_name
            gpxdata.link = template_log.gpx_link
            gpxdata.link_text = template_log.gpx_link_text
            gpxdata.nsmap=template_log.gpx_nsmap
            gpxdata.schema_locations=template_log.gpx_schema_locations
            gpxdata.version = template_log.gpx_version

        for pt3D in self.waypoints:            
            pt3D.regulate()
            gpxdata.waypoints.append(GPX.GPXWaypoint(pt3D.lat,
                                                     pt3D.long,
                                                     pt3D.elevation,
                                                     pt3D.timestamp,
                                                     pt3D.name,
                                                     pt3D.description))

        track = GPX.GPXTrack()

        if isinstance(template_log, Tracklog) and template_log:
            track.name = template_log.track_name
            track.comment = template_log.track_comment
            track.description = template_log.track_desc

        tracksegment = GPX.GPXTrackSegment()

        for pt3D in self.trackpoints:
            tracksegment.points.append(GPX.GPXTrackPoint(round(pt3D.lat, 6),
                                                         round(pt3D.long, 6),
                                                         round(pt3D.elevation, 3),
                                                         pt3D.timestamp))

        track.segments.append(tracksegment)
        gpxdata.tracks.append(track)


        with open(output_path, 'w', encoding='utf-8') as output_file:
            output_file.write(gpxdata.to_xml())



