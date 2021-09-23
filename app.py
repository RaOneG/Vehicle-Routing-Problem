from flask import Flask
from flask_restful import Resource, Api, reqparse, request
import pandas as pd
import json
import vrp_io
import vrp_pickup


app = Flask(__name__)
api = Api(app)


# @app.route('/routing_table', methods=['GET', 'POST'])
# def get():
#     if request.method == 'GET':
#         return vrp_io.get_deliverer_route(vrp_pickup.get_routes(), '53.425334%2C-6.231581')

# def post():
#     if request.method == 'POST':
#         parser = reqparse.RequestParser()  # initialize
#         parser.add_argument('userId', required=True)  # add arguments
#         parser.add_argument('name', required=True)
#         parser.add_argument('city', required=True)
#         args = parser.parse_args()  # parse arguments to dictionary
            
#         # create new dataframe containing new values
#         new_data = pd.DataFrame({
#             'userId': args['userId'],
#             'name': args['name'],
#             'city': args['city'],
#             'locations': [[]]
#             })
        
#         # convert to json
#         print(new_data)
#     return 200  # return data with 200 OK


class RoutingTable(Resource):
    #def get(self):
    #    return vrp_io.get_deliverer_route(vrp_pickup.get_routes(), '53.425334%2C-6.231581')
    
    def post(self):
        parser = reqparse.RequestParser()  # initialize
        parser.add_argument('deliverer_coordinates', required=True)  # add arguments
        parser.add_argument('orders_address', required=True)
        args = parser.parse_args()  # parse arguments to dictionary
            
        # create new dataframe containing new values
        # new_data = pd.DataFrame({
        #     'deliverer_coordinates': args['deliverer_coordinates'],
        #     'order': args['order']
        #     })
        
        # convert to json
        print(args)
        return vrp_io.get_deliverer_route(vrp_pickup.get_routes(), '53.425334%2C-6.231581')  # return data with 200 OK

api.add_resource(RoutingTable, '/routing_table')

if __name__ == '__main__':
     app.run()  # run our Flask app






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


