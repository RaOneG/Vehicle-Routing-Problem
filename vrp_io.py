import json
from collections import OrderedDict

def get_orders_list(orders):
  orders_addresses = []
  for order in orders:
    # create a dict of orders pickup with id
    order_id_pickup = str(order['order_id']) + '_pickup'
    pickup_loc = order['pickup'].replace(',', '%2C')
    orders_pickup = {order_id_pickup: pickup_loc}
    orders_addresses += [orders_pickup]
    # create a dict of orders dropoff with id
    order_id_dropoff = str(order['order_id']) + '_dropoff'
    dropoff_loc = order['dropoff'].replace(',', '%2C')
    orders_dropoff = {order_id_dropoff: dropoff_loc}
    orders_addresses += [orders_dropoff]
  return orders_addresses


"Input Lat-Lon Location"
def get_addresses(deliverer_location, data, orders):
  orders_addresses = get_orders_list(orders)
  data['addresses'] = [deliverer_location.replace(',', '%2C')]
  for order in orders_addresses:
    for loc in order.values():
      data['addresses'].append(loc)
  return data


"Pickup-Dropoff mapping"
def get_pickup_dropoff(data, orders):
  orders_addresses = get_orders_list(orders)
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
def get_deliverer_route(routes, deliverer_location, orders):
  orders_addresses = get_orders_list(orders)
  routes.pop(0) # remove the deliverer_location
  route_table = []
  route_table += [{'deliverer_location': deliverer_location.replace('%2C', ',')}]
  for loc_idx in routes:
    loc_idx = loc_idx - 1   # because the deliverer_location = 0 which is not in the orders_adresses so orders_adresses[0] is equivalent to routes[1]
    order = orders_addresses[loc_idx]
    for key, value in order.items():
      order[key] = value.replace('%2C', ',')
      route_table += [orders_addresses[loc_idx]]
  route_table = json.dumps(route_table)
  return route_table