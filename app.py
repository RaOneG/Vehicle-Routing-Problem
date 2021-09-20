from flask import Flask
from flask_restful import Resource, Api, reqparse
import vrp_io
import os
import ast


app = Flask(__name__)
api = Api(app)
#port = int(os.environ.get('PORT',  46433))

class Routing(Resource):
    def get(self):
        return vrp_io.get_deliverer_route([0, 1, 3, 9, 7, 5, 6, 8, 10, 4, 2], '53.425334%2C-6.231581')

api.add_resource(Routing, '/routing')

if __name__ == '__main__':
     app.run()  # run our Flask app

#@app.route('/routing_table', methods=['GET'])
# def get_route():
#     routes = vrp_pickup.get_routes()
#     route_table = vrp_io.get_deliverer_route(routes[0], '53.425334%2C-6.231581')
#     # store in a json filewith open('route_table.json', 'w') as file:
#     route_table = json.dumps(route_table, indent=4)
#     return route_table




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


