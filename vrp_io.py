"""VRP_io.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1CfVUYOejv0ZyjzIQH5VfjQqPekVX9D2P

# Main Code
"""

import pandas as pd
from collections import OrderedDict

"read the dataset"
dataset_path = 'orders.csv'
orders_dataset_original = pd.read_csv(dataset_path)

"""
Observation:
1. Query 'id', 'order_id', 'pickup_address',	
  'pickup_lat',	'pickup_lon', 'customer_address',	
  'customer_address_lat', and	'customer_address_lon'
2. Set id column as index.
3. Choose the last 5 rows to try them out from row 600 to 705.
"""
def get_cleaned_orders(orders_dataset_original):
  orders_dataset = orders_dataset_original[['id', 'order_id', 
                                            'pickup_address', 
                                            'pickup_lat', 'pickup_lon', 
                                            'customer_address', 'customer_address_lat', 
                                            'customer_address_lon']]
  
  orders_dataset.set_index('id', inplace=True)
  orders_dataset = orders_dataset.iloc[-5:]
  orders_dataset.reset_index(inplace=True)
  orders_dataset.drop('id', axis=1, inplace=True)
  
  orders_dataset['order_id'] = orders_dataset['order_id'].str.replace('Order #','')
  
  orders_dataset['pickup_address'] = orders_dataset['pickup_address'].str.replace(', ','+')
  orders_dataset['pickup_address'] = orders_dataset['pickup_address'].str.replace(' ','+')
  orders_dataset['customer_address'] = orders_dataset['customer_address'].str.replace(', ','+')
  orders_dataset['customer_address'] = orders_dataset['customer_address'].str.replace(' ','+')
  
  orders_dataset['pickup_lat_lon'] = ['%2C'.join(str(round(x, 6)) for x in y) for y in map(tuple, orders_dataset[['pickup_lat', 'pickup_lon']].values)]
  orders_dataset['dropoff_lat_long'] = ['%2C'.join(str(round(x, 6)) for x in y) for y in map(tuple, orders_dataset[['customer_address_lat',	'customer_address_lon']].values)]
  
  cleaned_orders = orders_dataset[['order_id',
                                 'pickup_lat_lon', 
                                 'dropoff_lat_long']]
  return cleaned_orders

def get_orders_list(orders_dataset_original):
  cleaned_orders = get_cleaned_orders(orders_dataset_original)
  orders_addresses = []
  for order in cleaned_orders.to_numpy():
    # create a list of orders pickup with id
    order_id_pickup = str(order[0]) + '_pickup'
    pickup = order[1]
    orders_pickup = [order_id_pickup, pickup]
    orders_addresses += [orders_pickup]
    # create a list of orders destination with id
    order_id_destination = str(order[0]) + '_dropoff'
    destination = order[2]
    orders_destination = [order_id_destination, destination]
    orders_addresses += [orders_destination]
  return orders_addresses


"Input Lat-Lon Location"
def get_addresses(deliverer_location, data):
  orders_addresses = get_orders_list(orders_dataset_original)
  data['addresses'] = [deliverer_location]
  for order in orders_addresses:
    address = order[1]
    data['addresses'].append(address)
  return data['addresses']


"Pickup-Dropoff mapping"
def get_pickup_dropoff(data):
  orders_addresses = get_orders_list(orders_dataset_original)
  data['pickups_deliveries'] = []
  no_location = len(orders_addresses)
  # check it has equal pickups and dropoffs
  if no_location % 2 == 0:
    for n in range(1, no_location, 2):
      data['pickups_deliveries'].append([n, n+1])
  else:
    print("Warning there's a missing pickup or drop off location!")
  return data['pickups_deliveries']


"Final Output"
# mapping back to order_id and pickup and delivery location
routes = [[0, 5, 3, 1, 6, 4, 2]] #THIS IS NOT AN ACTUAL LIST
def get_deliverer_route(routes, deliverer_location):
  orders_addresses = get_orders_list(orders_dataset_original)
  routes.pop(0) # remove the deliverer_location
  route_table = OrderedDict()
  route_table['deliverer_location'] = deliverer_location.replace('%2C', ', ')
  for location in routes:
    location = location - 1   # because the deliverer_location = 0 which is not in the orders_adresses so orders_adresses[0] is equivalent to routes[1]
    route_table[orders_addresses[location][0]] = orders_addresses[location][1].replace('%2C', ', ')
  return route_table