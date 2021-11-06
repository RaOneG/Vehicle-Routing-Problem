from __future__ import division
from __future__ import print_function
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from flask import Flask, jsonify
import os
from boto.s3.connection import S3Connection
from flask_restful import Resource, Api, reqparse, request
#from dotenv import load_dotenv
#from starlette.config import Config
import urllib.request
import json

app = Flask(__name__)
api = Api(app)

def get_orders_list(deliverers_location, orders):
  addresses = []
  for deliverer in deliverers_location:
    deliverer_id = 'deliverer_' + str(deliverer["deliverer_id"])
    deliverer_loc = deliverer["deliverer_coordinates"].replace(',', '%2C')
    single_deliverer = {deliverer_id: deliverer_loc}
    addresses += [single_deliverer]
  for order in orders:
    # create a dict of orders pickup with id
    order_id_pickup = str(order['order_id']) + '_pickup'
    pickup_loc = order['pickup'].replace(',', '%2C')
    orders_pickup = {order_id_pickup: pickup_loc}
    addresses += [orders_pickup]
    # create a dict of orders dropoff with id
    order_id_dropoff = str(order['order_id']) + '_dropoff'
    dropoff_loc = order['dropoff'].replace(',', '%2C')
    orders_dropoff = {order_id_dropoff: dropoff_loc}
    addresses += [orders_dropoff]
  return addresses


"Input Lat-Lon Location"
def get_addresses(data, deliverers_location, orders):
  addresses = get_orders_list(deliverers_location, orders)
  data['addresses'] = []
  for address in addresses:
    for loc in address.values():
      data['addresses'].append(loc)
  return data["addresses"]


def create_data(deliverers_location, orders):
  """Creates the data."""
  #config = Config(".env")
  #load_dotenv()
  data = {}
  data['API_key'] = S3Connection(os.environ.get('API_KEY'))
  data['addresses'] = get_addresses(data, deliverers_location, orders)
  return data


def create_distance_matrix(deliverers_location, orders):
  data = create_data(deliverers_location, orders)
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
  end_node = []
  for i in range(len(addresses)+1):
    end_node.append(0)
  distance_matrix.append(end_node)
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
  dist_matrix = []
  for row in distance_matrix:
    if len(row) == len(addresses)+1:
      dist_matrix.append(row)
    elif len(row) == len(addresses):
      row.insert(0,0)
      dist_matrix.append(row)
  distance_matrix = dist_matrix
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


"Pickup-Dropoff, no of vehicles, start-end loc Mapping"
def get_data(data, deliverers_location, orders):
  addresses = get_orders_list(deliverers_location, orders)
  data['pickups_deliveries'] = []
  start = len(deliverers_location)
  end = len(addresses)
  # check it has equal pickups and dropoffs
  if (end - start) % 2 == 0:
    for n in range(start, end, 2):
      data['pickups_deliveries'].append([n+1, n+2])
  else:
    print("Warning there's a missing pickup or drop off location!")
  data['num_vehicles'] = start
  data['starts'] = []
  data['ends'] = []
  for n in range(start):
    data['starts'] += [n+1]
    data['ends'].append(0) #data['starts'][::-1]
  return data


def create_data_model(deliverers_location, orders):
  """Stores the data for the problem."""
  data = {}
  data['distance_matrix'] = create_distance_matrix(deliverers_location, orders)
  data = get_data(data, deliverers_location, orders)
  return data


def get_routes(deliverers_location, orders):
  solution, routing, manager = main_solution(deliverers_location, orders)
  """Get vehicle routes from a solution and store them in an array."""
  # Get vehicle routes and store them in a two dimensional array whose
  # i,j entry is the jth location visited by vehicle i along its route.
  routes = []
  for route_nbr in range(routing.vehicles()):
    index = routing.Start(route_nbr)
    route = [manager.IndexToNode(index)]
    while not routing.IsEnd(index):
      index = solution.Value(routing.NextVar(index))
      route.append(manager.IndexToNode(index))
    del route[-1]
    routes.append(route)
  return routes


# def print_solution(data, manager, routing, solution):
#     """Prints solution on console."""
#     print(f'Objective: {solution.ObjectiveValue()}')
#     total_distance = 0
#     for vehicle_id in range(data['num_vehicles']):
#         index = routing.Start(vehicle_id)
#         plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
#         route_distance = 0
#         while not routing.IsEnd(index):
#             plan_output += ' {} -> '.format(manager.IndexToNode(index))
#             previous_index = index
#             index = solution.Value(routing.NextVar(index))
#             route_distance += routing.GetArcCostForVehicle(
#                 previous_index, index, vehicle_id)
#         plan_output += '{}\n'.format(manager.IndexToNode(index))
#         plan_output += 'Distance of the route: {}m\n'.format(route_distance)
#         print(plan_output)
#         total_distance += route_distance
#     print('Total Distance of all routes: {}m'.format(total_distance))



def main_solution(deliverers_location, orders):
  """Entry point of the program."""
  # Instantiate the data problem.
  data = create_data_model(deliverers_location, orders)

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
    300000,  # vehicle maximum travel distance
    True,  # start cumul to zero
    dimension_name)
  distance_dimension = routing.GetDimensionOrDie(dimension_name)
  distance_dimension.SetGlobalSpanCostCoefficient(100)

  # Define Transportation Requests.
  # [START pickup_delivery_constraint]
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
  # routing.SetPickupAndDeliveryPolicyOfAllVehicles(
  #       pywrapcp.RoutingModel.PICKUP_AND_DELIVERY_FIFO)
  # [END pickup_delivery_constraint]

  # Setting first solution heuristic.
  # [START parameters]
  search_parameters = pywrapcp.DefaultRoutingSearchParameters()
  search_parameters.first_solution_strategy = (
    routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION)
  # search_parameters.local_search_metaheuristic = (
  #       routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
  # search_parameters.time_limit.FromSeconds(15)
  # search_parameters.log_search = True # to monitor objective value in real time...
  # [END parameters]

  # Solve the problem.
  # [START solve]
  solution = routing.SolveWithParameters(search_parameters)
  # [END solve]

  # if solution:
  #   print_solution(data, manager, routing, solution)
  
  return solution, routing, manager


"Final Output"
# mapping back to order_id and pickup and delivery location
def get_deliverer_route(routes, deliverers_location, orders):
  total_routes = []
  route = []
  for r in routes:
    for j in r:
      route.append(j-1)
    total_routes.append(route)
    route = []
  addresses = get_orders_list(deliverers_location, orders)
  route_table = []
  deliverer_request = []
  for idx in range(len(total_routes)):
    # create delivere location id
    address = addresses[idx]
    for key, value in address.items():
      single_loc = {}
      k = key.split('_')
      single_loc['deliverer_id'] = k[1]
      single_loc['coordinates'] = value.replace('%2C', ',')
      deliverer_request = [single_loc]
      route_table.append(deliverer_request)
    # create orders addresses
    route = total_routes[idx]
    route.pop(0)
    for n in route:
      order_address = addresses[n]
      for key, value in order_address.items():
        single_loc = {}
        k = key.split("_")
        single_loc["order_id"] = k[0]
        single_loc["coordinates"] = value.replace('%2C', ',')
        single_loc["type"] = k[1]
        route_table[idx].append(single_loc)
  return route_table


@app.route('/routing_table', methods=['POST'])
def post():
    if request.method == 'POST':
        parser = reqparse.RequestParser()  # initialize
        parser.add_argument('deliverers_coordinates', required=True)  # add arguments
        parser.add_argument('orders_address', required=True)
        req = parser.parse_args()  # parse arguments to dictionary
        orders = json.loads(req['orders_address'])
        deliverers_location = json.loads(req['deliverers_coordinates'])
        return jsonify(get_deliverer_route(get_routes(deliverers_location, orders), deliverers_location, orders))

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