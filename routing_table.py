import json
import vrp_io
import vrp_pickup

route = [0, 1, 3, 9, 7, 5, 6, 8, 10, 4, 2]
route_table = vrp_io.get_deliverer_route([0, 1, 3, 9, 7, 5, 6, 8, 10, 4, 2], '53.425334%2C-6.231581')
# store in a json filewith open('route_table.json', 'w') as file: