from __future__ import division
from __future__ import print_function
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from flask import Flask
from flask_restful import Resource, Api, reqparse, request
from dotenv import load_dotenv
from starlette.config import Config
import urllib.request
import pandas as pd
import json
from collections import OrderedDict

app = Flask(__name__)
api = Api(app)

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
    return data["addresses"]


def create_data(deliverer_location, orders):
  """Creates the data."""
  #config = Config(".env")
  #load_dotenv()
  data = {}
  data['API_key'] = 'AIzaSyDg8oDMkIGwPg-JHc86lxvX4SNce6TzjWs'
  data['addresses'] = get_addresses(deliverer_location, data, orders)
  return data


def create_distance_matrix(deliverer_location, orders):
  data = create_data(deliverer_location, orders)
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
  request = str(request) + '&origins=' + str(origin_address_str) + '&destinations=' + str(dest_address_str) + '&key=' + API_key
  jsonResult = urllib.request.urlopen(request).read()
  response = json.loads(jsonResult)
  return response


def build_distance_matrix(response):
    distance_matrix = []
    for row in response['rows']:
        row_list = [row['elements'][j]['distance']['value'] for j in range(len(row['elements']))]
        distance_matrix.append(row_list)
    return distance_matrix


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


def create_data_model(deliverer_location, orders):
    """Stores the data for the problem."""
    data = {}
    data['distance_matrix'] = create_distance_matrix(deliverer_location, orders)
    data['num_vehicles'] = 1
    data['starts'] = [0]
    data['ends'] = [0]
    data['pickups_deliveries'] = get_pickup_dropoff(data, orders)
    return data


def get_routes(deliverer_location, orders):
    solution, routing, manager = main_solution(deliverer_location, orders)
    """Get vehicle routes from a solution and store them in an array."""
    # Get vehicle routes and store them in a two dimensional array whose
    # i,j entry is the jth location visited by vehicle i along its route.
    #routes = []     # use i,j location in case u have more than one vehicle
    for route_nbr in range(routing.vehicles()):
        index = routing.Start(route_nbr)
        route = [manager.IndexToNode(index)]
        while not routing.IsEnd(index):
            index = solution.Value(routing.NextVar(index))
            route.append(manager.IndexToNode(index))
        #routes.append(route)
    del route[-1]
    return route


def main_solution(deliverer_location, orders):
    """Entry point of the program."""
    # Instantiate the data problem.
    data = create_data_model(deliverer_location, orders)

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                           data['num_vehicles'], data['starts'],
                                           data['ends'])

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # Define cost of each arc.
    def distance_callback(from_index, to_index):
        """Returns the manhattan distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Distance constraint.
    dimension_name = 'Distance'
    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        3000000,  # vehicle maximum travel distance
        True,  # start cumul to zero
        dimension_name)
    distance_dimension = routing.GetDimensionOrDie(dimension_name)
    distance_dimension.SetGlobalSpanCostCoefficient(100)

    # Define Transportation Requests.
    for request in data['pickups_deliveries']:
        pickup_index = manager.NodeToIndex(request[0])
        delivery_index = manager.NodeToIndex(request[1])
        routing.AddPickupAndDelivery(pickup_index, delivery_index)
        routing.solver().Add(
            routing.VehicleVar(pickup_index) == routing.VehicleVar(
                delivery_index))
        routing.solver().Add(
            distance_dimension.CumulVar(pickup_index) <=
            distance_dimension.CumulVar(delivery_index))

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION)

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    return solution, routing, manager


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
  return route_table


@app.route('/routing_table', methods=['POST'])
def post():
    if request.method == 'POST':
        parser = reqparse.RequestParser()  # initialize
        parser.add_argument('deliverer_coordinates', required=True)  # add arguments
        parser.add_argument('orders_address', required=True)
        req = parser.parse_args()  # parse arguments to dictionary
        orders = json.loads(req['orders_address'])
        deliverer_location = req['deliverer_coordinates']
        return str(get_deliverer_route(get_routes(deliverer_location, orders), deliverer_location, orders))

# class RoutingTable(Resource):
#     def post(self):
#         if request.method == "POST":
#             parser = reqparse.RequestParser()  # initialize
#             parser.add_argument('deliverer_coordinates', required=True)  # add arguments
#             parser.add_argument('orders_address', required=True)
#             req = parser.parse_args()  # parse arguments to dictionary
#             orders = json.loads(req['orders_address'])
#             deliverer_location = req['deliverer_coordinates']
#             return get_deliverer_route(get_routes(deliverer_location, orders), deliverer_location, orders)
            
# api.add_resource(RoutingTable, '/routing_table')

if __name__ == '__main__':
     app.run()  # run our Flask app

