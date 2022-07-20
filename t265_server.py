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

def set_axes_equal(ax):
    '''Make axes of 3D plot have equal scale so that spheres appear as spheres,
    cubes as cubes, etc..  This is one possible solution to Matplotlib's
    ax.set_aspect('equal') and ax.axis('equal') not working for 3D.

    Input
      ax: a matplotlib axis, e.g., as output from plt.gca().
    '''

    x_limits = ax.get_xlim3d()
    y_limits = ax.get_ylim3d()
    z_limits = ax.get_zlim3d()

    x_range = abs(x_limits[1] - x_limits[0])
    x_middle = np.mean(x_limits)
    y_range = abs(y_limits[1] - y_limits[0])
    y_middle = np.mean(y_limits)
    z_range = abs(z_limits[1] - z_limits[0])
    z_middle = np.mean(z_limits)

    # The plot bounding box is a sphere in the sense of the infinity
    # norm, hence I call half the max range the plot radius.
    plot_radius = 0.5*max([x_range, y_range, z_range])

    ax.set_xlim3d([x_middle - plot_radius, x_middle + plot_radius])
    ax.set_ylim3d([y_middle - plot_radius, y_middle + plot_radius])
    ax.set_zlim3d([z_middle - plot_radius, z_middle + plot_radius])

# Create pose queue
qpose_log = queue.Queue()
qpose_plt = queue.Queue()
evt_quit = threading.Event()

# Declare RealSense pipeline, encapsulating the actual device and sensors
pipe = rs.pipeline()

# Build config object and request pose data
cfg = rs.config()
cfg.enable_stream(rs.stream.pose)

# Flask app
ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask('nameless')

# Start streaming with requested config
pipe.start(cfg)

now = datetime.now()
dt_string = now.strftime("log-%Y-%m-%d-%H-%M-%S")

if SHOW_PLOT_REALTIME is True:
    matplotlib.interactive(True)
    fig = plt.figure()
    ax = plt.axes(projection='3d')
    plt.xlabel('x')
    plt.ylabel('y')
    xlist = list()
    ylist = list()
    zlist = list()

if SAVE_LOG is True:
    logfile = open(dt_string + '.txt', 'wt')

def producer(pipe, qpose_plt, qpose_log, evt_quit:threading.Event):
    while not evt_quit.is_set():
        # Wait for the next set of frames from the camera
        frames = pipe.wait_for_frames()
        # Fetch pose frame
        pose = frames.get_pose_frame()
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
            #qpose_plt.get()
            qpose_log.put(newline)

@app.route('/log',methods=["GET","POST"])
def sendlog():
    html_str = ''
    while not qpose_plt.empty():
        html_str += qpose_plt.get()
    return html_str


def consumer_log(evt_quit:threading.Event, qpose_log:queue.Queue, SAVE_LOG:bool, logfile:_io.TextIOWrapper):
    while not evt_quit.is_set():
        while not qpose_log.empty():
            newline = qpose_log.get()
            if SAVE_LOG is True:
                logfile.write(newline)
        time.sleep(.05)

try:
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        executor.submit(producer, pipe, qpose_plt, qpose_log, evt_quit)
        executor.submit(consumer_log, evt_quit, qpose_log, SAVE_LOG, logfile)
        print('T265 info is being logged. Press \'q\' to quit.')
        app.run(host="0.0.0.0", threaded=True)
        print('Flask ended.')
        while not keyboard.is_pressed('q'):
            time.sleep(.05)
        evt_quit.set()
        print('Finished recording.')

finally:
    pipe.stop()

if SAVE_LOG is True:
    logfile.close()