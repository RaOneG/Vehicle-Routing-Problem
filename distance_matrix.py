"""
filename  Distance Matrix
---------------------------
This file converts a list of pick up/drop off locations
to the distance between each location to be ready for 
Vehicle Routing Optimization
"""
from __future__ import division
from __future__ import print_function
import os
from dotenv import load_dotenv
import requests
import json
import urllib.request
import vrp_io


def create_data():
  """Creates the data."""
  load_dotenv()
  data = {}
  data['API_key'] = os.getenv('MAPS_API_KEY')
  data['addresses'] = vrp_io.get_addresses('53.425334%2C-6.231581', data)
  return data


def create_distance_matrix():
  data = create_data()
  addresses = data["addresses"]
  API_key = data["API_key"]
  # Distance Matrix API only accepts 100 elements per request, so get rows in multiple requests.
  max_elements = 100
  num_addresses = len(addresses)
  # Maximum number of rows that can be computed per request.
  max_rows = max_elements // num_addresses
  # num_addresses = q * max_rows + r (q = 2 and r = 4 in this example).
  q, r = divmod(num_addresses, max_rows)
  dest_addresses = addresses
  distance_matrix = []
  # Send q requests, returning max_rows rows per request.
  for i in range(q):
    origin_addresses = addresses[i * max_rows: (i + 1) * max_rows]
    response = send_request(origin_addresses, dest_addresses, API_key)
    distance_matrix += build_distance_matrix(response)

  # Get the remaining remaining r rows, if necessary.
  if r > 0:
    origin_addresses = addresses[q * max_rows: q * max_rows + r]
    response = send_request(origin_addresses, dest_addresses, API_key)
    distance_matrix += build_distance_matrix(response)
  return distance_matrix


def send_request(origin_addresses, dest_addresses, API_key):
  """ Build and send request for the given origin and destination addresses."""
  def build_address_str(addresses):
    # Build a pipe-separated string of addresses
    address_str = ''
    for i in range(len(addresses) - 1):
      address_str += addresses[i] + '|'
    address_str += addresses[-1]
    return address_str

  request = 'https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial'
  origin_address_str = build_address_str(origin_addresses)
  dest_address_str = build_address_str(dest_addresses)
  request = str(request) + '&origins=' + str(origin_address_str) + '&destinations=' + str(dest_address_str) + '&key=' + str(API_key)
  jsonResult = urllib.request.urlopen(request).read()
  response = json.loads(jsonResult)
  return response


def build_distance_matrix(response):
  distance_matrix = []
  for row in response['rows']:
    row_list = [row['elements'][j]['distance']['value'] for j in range(len(row['elements']))]
    distance_matrix.append(row_list)
  return distance_matrix