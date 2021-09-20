"""
Simple Vehicles Routing Problem (VRP).
Distances are in meters.
"""

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import distance_matrix as dis_mx
import vrp_io
import json

def create_data_model():
    """Stores the data for the problem."""
    data = {}
    data['distance_matrix'] = [[0, 14662, 55513, 14662, 16875, 14662, 9802, 14662, 9802, 14662, 9802], [13329, 0, 49853, 0, 2943, 0, 714, 0, 715, 0, 714], [56225, 50716, 0, 50716, 44373, 50716, 49898, 50716, 49898, 50716, 49898], [13329, 0, 49853, 0, 2943, 0, 714, 0, 715, 0, 714], [16446, 3847, 43935, 3847, 0, 3847, 3831, 3847, 3831, 3847, 3831], [13329, 0, 49853, 0, 2943, 0, 714, 0, 715, 0, 714], [10444, 1332, 50455, 1332, 3545, 1332, 0, 1332, 0, 1332, 0], [13329, 0, 49853, 0, 
2943, 0, 714, 0, 715, 0, 714], [10444, 1332, 50455, 1332, 3546, 1332, 0, 1332, 0, 1332, 0], [13329, 0, 49853, 0, 2943, 0, 714, 0, 715, 0, 714], [10444, 1332, 50455, 1332, 3545, 1332, 0, 1332, 0, 1332, 0]]
    data['num_vehicles'] = 1
    data['starts'] = [0]
    data['ends'] = [0]
    data['pickups_deliveries'] = vrp_io.get_pickup_dropoff(data)
    return data


def get_routes():
    solution, routing, manager = main_solution()
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
        routes.append(route)
    del routes[0][-1]
    return routes


def main_solution():
    """Entry point of the program."""
    # Instantiate the data problem.
    data = create_data_model()

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