import json
import vrp_io
import vrp_pickup

routes = vrp_pickup.get_routes()
route_table = vrp_io.get_deliverer_route(routes[0], '53.425334%2C-6.231581')
# store in a json filewith open('route_table.json', 'w') as file:
route_table = json.dumps(route_table, indent=4)
