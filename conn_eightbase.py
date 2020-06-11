from graphqlclient import GraphQLClient
import request
import json
import schema8base

class EightbaseConnection(object):
    def __init__(self):
        self._graphQLEndpoint = ''
        self._client = GraphQLClient(self._graphQLEndpoint)
        self._client.inject_token('')
        
        # function to get all necessary data from taxonomy
    def getAllOccupations(self):
        result = self._client.execute(schema8base.getAllOccupationsQuery)
        return result
        # function to upload created SOWs to 8base
    def uploadSOW(self, title, description, skills, requirements, feedback, rating):
        variables = { 'title' : title, 'description' : description, 
                     'skills' : skills, 'requirements' : requirements, 
                     'feedback' : feedback, 'rating' : rating }
        result = self._client.execute(schema8base.createSowMutation, variables)