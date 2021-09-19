from flask import Flask
from flask_restful import Resource, Api, reqparse
import os
import json
import ast
import vrp_io
import vrp_pickup

app = Flask(__name__)
port = int(os.environ.get('PORT',  46433))


@app.route('/routing_table', methods=['GET'])
def get_route():
    routes = vrp_pickup.get_routes()
    route_table = vrp_io.get_deliverer_route(routes[0], '53.425334, 2C-6.231581')
    # store in a json filewith open('route_table.json', 'w') as file:
    route_table = json.dumps(route_table, indent=4)
    return route_table


if __name__ == '__main__':
     app.run(host='0.0.0.0', port=port, debug=True)  # run our Flask appS

# class RoutingTable(Resource):
#     def GET(self):
#         data = {"deliverer_location": "53.425334, 2C-6.231581",
#                 "921945_pickup": "53.34581, -6.25543",
#                 "18_pickup": "51.89851, -8.4756",
#                 "17_pickup": "51.89851, -8.4756",
#                 "921945_dropoff": "53.32604, -6.31861",
#                 "18_dropoff": "51.562092, -0.076668",
#                 "17_dropoff": "51.507351, -0.127758"
#                 }
#         return data, 200

# api.add_resource(RoutingTable, '/routing_table')


