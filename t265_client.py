#!/usr/bin/python

# First import the library
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import keyboard
import requests

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


matplotlib.interactive(True)
fig = plt.figure()
ax = plt.axes(projection='3d')
plt.xlabel('x')
plt.ylabel('y')
xlist = list()
ylist = list()
zlist = list()


while not keyboard.is_pressed('q'):
    # Wait for the next set of frames from the camera
    resp = requests.get('http://127.0.0.1:5000/log')
    if resp.status_code == 200:
        lines = str(resp.content)[2:-1].split('\\n')
        lines = lines[:-1]
        for i in range(len(lines)):
            line_elem = lines[i].split(',')
            xlist.append(float(line_elem[2]))
            zlist.append(float(line_elem[3]))
            ylist.append(float(line_elem[4]))
            print("Frame #{} (press q to quit)".format(line_elem[0]))
        ax.cla()
        ax.plot3D(xlist, ylist, zlist, linewidth=3, alpha=.3, color='blue')
        LAST_SIZE = 100
        if len(xlist) > LAST_SIZE:
            lastx = xlist[-LAST_SIZE:]
            lasty = ylist[-LAST_SIZE:]
            lastz = zlist[-LAST_SIZE:]
            ax.plot3D(lastx, lasty, lastz, linewidth=3, color='blue')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.draw()
        set_axes_equal(ax)
        plt.pause(.01)
    else:
        print('Status code: ' + str(resp.status_code))