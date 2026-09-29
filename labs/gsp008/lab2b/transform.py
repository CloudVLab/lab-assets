#!/usr/bin/env python3

# Copyright 2016 Google Inc.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

# See https://github.com/GoogleCloudPlatform/datalab-samples/blob/master/basemap/earthquakes.ipynb for a notebook that illustrates this code

import csv
import requests
import io
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt

# Cartopy imports
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# Classes to hold the data
class EarthQuake:
  def __init__(self, row):
    # Parse earthquake data from USGS
    self.timestamp = row[0]
    self.lat = float(row[1])
    self.lon = float(row[2])
    try:
      self.magnitude = float(row[4])
    except ValueError:
      self.magnitude = 0
    
def get_earthquake_data(url):
  # Read CSV earthquake data from USGS
  response = requests.get(url)
  csvio = io.StringIO(response.text)
  reader = csv.reader(csvio)
  header = next(reader)
  quakes = [EarthQuake(row) for row in reader]
  quakes = [q for q in quakes if q.magnitude > 0]
  return quakes


# control marker color and size based on magnitude
def get_marker(magnitude):
    markersize = magnitude * 2.5;
    if magnitude < 1.0:
        return ('bo'), markersize
    if magnitude < 3.0:
        return ('go'), markersize
    elif magnitude < 5.0:
        return ('yo'), markersize
    else:
        return ('ro'), markersize


def create_png(url, outfile):

    quakes = get_earthquake_data(url)

    print(quakes[0].__dict__)

    # Set up Cartopy
    mpl.rcParams['figure.figsize'] = (16, 12)

    fig = plt.figure()

    ax = plt.axes(
        projection=ccrs.Robinson(central_longitude=-90)
    )

    ax.set_global()

    # background color
    ax.set_facecolor('0.3')

    # map features
    ax.coastlines()

    ax.add_feature(
        cfeature.BORDERS,
        linewidth=0.5
    )

    # gridlines
    gl = ax.gridlines(
        draw_labels=False,
        linewidth=0.5,
        color='gray',
        alpha=0.5,
        linestyle='--'
    )

    gl.xlocator = plt.FixedLocator(
        np.arange(-180., 180., 60.)
    )

    gl.ylocator = plt.FixedLocator(
        np.arange(-90., 90., 30.)
    )

    # sort earthquakes by magnitude
    # stronger quakes plotted first
    start_day = quakes[-1].timestamp[:10]
    end_day = quakes[0].timestamp[:10]

    quakes.sort(
        key=lambda q: q.magnitude,
        reverse=True
    )

    # add earthquake info to the plot
    for q in quakes:

        mcolor, msize = get_marker(q.magnitude)

        ax.plot(
            q.lon,
            q.lat,
            mcolor,
            markersize=msize,
            transform=ccrs.PlateCarree()
        )

    # add title
    plt.title(
        "Earthquakes {0} to {1}".format(
            start_day,
            end_day
        )
    )

    plt.savefig(
        outfile,
        bbox_inches='tight'
    )

if __name__ == '__main__':
  url = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.csv'
  outfile = 'earthquakes.png'
  create_png(url, outfile)