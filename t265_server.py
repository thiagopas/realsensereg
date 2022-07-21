#!/usr/bin/python
# -*- coding: utf-8 -*-
## License: Apache 2.0. See LICENSE file in root directory.
## Copyright(c) 2019 Intel Corporation. All Rights Reserved.

#####################################################
##           librealsense T265 example             ##
#####################################################

# First import the library
import _io
import pyrealsense2 as rs
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import keyboard
import queue
import concurrent.futures
import threading
import time
from flask import Flask, request, jsonify
import os
from datetime import datetime

SAVE_LOG = True
SHOW_PLOT_REALTIME = False

# Create pose queue
qpose_log = queue.Queue()
qpose_plt = queue.Queue()
evt_quit = threading.Event()

# Declare RealSense pipeline, encapsulating the actual device and sensors
pipe = rs.pipeline()

# Build config object and request pose data
cfg = rs.config()
cfg.enable_stream(rs.stream.pose)
# Start streaming with requested config
pipe.start(cfg)

class GlobalData():
    def __init__(self):
        self.running = False
        self.logfile = None

globaldata = GlobalData()

# Flask app
ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask('nameless')

@app.route('/start_t265',methods=["GET","POST"])
def start_t265():
    now = datetime.now()
    dt_string = now.strftime("log-%Y-%m-%d-%H-%M-%S")
    if SAVE_LOG is True:
        globaldata.logfile = open('./static/' + dt_string + '.txt', 'wt')
    globaldata.running = True
    return "Started.<br><a href='./stop_t265'>Stop</a>"

#start_t265()

@app.route('/stop_t265',methods=["GET","POST"])
def stop_t265():
    globaldata.logfile.close()
    globaldata.running = False
    return "Stopped.<br><a href='"+globaldata.logfile.name+"' target=_new>"+globaldata.logfile.name+"</a><br><a href='./start_t265'>Start</a>"

def producer(pipe, qpose_plt, qpose_log, evt_quit:threading.Event):
    while not evt_quit.is_set():
        try:
            # Wait for the next set of frames from the camera
            frames = pipe.wait_for_frames()
            # Fetch pose frame
            pose = frames.get_pose_frame()
            if globaldata.running is True:
                if pose:
                    # Print some of the pose data to the terminal
                    data = pose.get_pose_data()
                    newline = str(frames[0].frame_number) + ',' + \
                              str(frames.get_pose_frame().timestamp) + ',' + \
                              str(data.translation.x) + ',' + \
                              str(data.translation.y) + ',' + \
                              str(data.translation.z) + ',' + \
                              str(data.tracker_confidence) + \
                              str(data.rotation.x) + ',' + \
                              str(data.rotation.y) + ',' + \
                              str(data.rotation.z) + ',' + \
                              str(data.rotation.w) + ',' + \
                              str(data.velocity.x) + ',' + \
                              str(data.velocity.y) + ',' + \
                              str(data.velocity.z) + ',' + \
                              str(data.acceleration.x) + ',' + \
                              str(data.acceleration.y) + ',' + \
                              str(data.acceleration.z) + ',' + \
                              str(data.angular_acceleration.x) + ',' + \
                              str(data.angular_acceleration.y) + ',' + \
                              str(data.angular_acceleration.z) + ',' + \
                              str(data.angular_velocity.x) + ',' + \
                              str(data.angular_velocity.y) + ',' + \
                              str(data.angular_velocity.z) + ',' + \
                              str(data.mapper_confidence) + '\n'
                    qpose_plt.put(newline)
                    qpose_log.put(newline)
                else:
                    print('pose false')
        except Exception as e:
            print('producer: ' + str(e))

@app.route('/log',methods=["GET","POST"])
def sendlog():
    html_str = ''
    while not qpose_plt.empty():
        html_str += qpose_plt.get()
    return html_str




def consumer_log(evt_quit:threading.Event, qpose_log:queue.Queue, SAVE_LOG:bool, logfile:_io.TextIOWrapper):
    while not evt_quit.is_set():
        try:
            #print('checking qpose_log')
            while not qpose_log.empty():
                newline = qpose_log.get()
                if SAVE_LOG is True and globaldata.running is True:
                    globaldata.logfile.write(newline)
            time.sleep(0.05)
        except Exception as e:
            print(e)


with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    executor.submit(producer, pipe, qpose_plt, qpose_log, evt_quit)
    executor.submit(consumer_log, evt_quit, qpose_log, SAVE_LOG, globaldata.logfile)
    print('T265 info is being logged. Press \'q\' to quit.')
    app.run(host="0.0.0.0", threaded=True)
    print('Flask ended.')
    evt_quit.set()
    print('Finished recording.')

pipe.stop()
