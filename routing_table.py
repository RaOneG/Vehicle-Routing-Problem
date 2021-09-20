import json
import vrp_io
import vrp_pickup

route = vrp_pickup.route
route_table = vrp_io.get_deliverer_route(route, '53.425334%2C-6.231581')
# store in a json filewith open('route_table.json', 'w') as file: