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
import queue
import concurrent.futures
import threading
import time
from flask import Flask
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
        globaldata.logfile = open('./static/' + dt_string + '.csv', 'wt')
    globaldata.running = True
    ret = '''<html>
        <head><title>RUNNING</title>
        <script src='/static/plotly-2.12.1.min.js'></script>
        <script src='/static/d3.min.js'></script>
        <script src='/static/parsing.js'></script>
        </head>
        <body>
        Started.<br><a href='./stop_t265'>Stop</a><br>
        <input type="checkbox" id="liveplot" name="liveplot">
        <label for="liveplot"> Live plot</label><br>
        <div id=myDiv></div>
        <script language=JavaScript> 
        myDiv = document.getElementById("myDiv")
        liveplot = document.getElementById("liveplot")
        lasttext = " "
        arrX = Array(1)
        arrY = Array(1)
        arrZ = Array(1)
        function fetchdata(){
			if (liveplot.checked){
				//create XMLHttpRequest object 
				const xhr = new XMLHttpRequest() 
				//open a get request with the remote server URL 
				xhr.open("GET", "/log") 
				//send the Http request 
				xhr.send() 
	
				//EVENT HANDLERS
	
				//triggered when the response is completed
				xhr.onload = function() {
					if (xhr.status === 200) {
						//console.log("HERE")
						//console.log(xhr.responseText)
						lasttext = xhr.responseText
						lasttext = lasttext.substring(0, lasttext.length-1)
						array = CSVToArray(lasttext)
						aT = transpose(array)
						arrX = arrX.concat(aT[2])
						arrY = arrY.concat(aT[3])
						arrZ = arrZ.concat(aT[4])
						trace1 = {
							x: arrX,
							y: arrY,
							z: arrZ,
							mode: 'lines',
							marker: {
								color: '#1f77b4',
								size: 12,
								symbol: 'circle',
								line: {
									color: 'rgb(0,0,0)',
									width: 0
								}
							},
							line: {
								color: '#1f77b4',
								width: 3
							},
							type: 'scatter3d'
						};
						data = [trace1];
						layout = {
							title: 'T265 registered path',
							autosize: false,
							width: 500,
							height: 500,
							margin: {
								l: 0,
								r: 0,
								b: 0,	
								t: 65
							}
						};
						Plotly.react('myDiv', data, layout);
					} else{
						alert("Status " + xhr.status)
					}
				}
			}
        }
        
        setInterval(fetchdata, 200)
        </script>
        </body>
        </html>'''
    return ret

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
    app.run(host="0.0.0.0", threaded=True)
    print('Flask ended.')
    evt_quit.set()
    print('Finished communication to T265.')

pipe.stop()
