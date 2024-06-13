from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

class AnimalShelter:
    def __init__(self, uri, db_name, collection_name):
        # Initialize the MongoDB client using the provided URI
        self.client = MongoClient(uri)

        # Test the connection
        try:
            self.client.admin.command('ping')
            print("Connected successfully to MongoDB Atlas!")
        except ConnectionFailure as e:
            print(f"Server not available: {e}")
            raise

        # Set the database and collection
        self.database = self.client[db_name]
        self.collection = self.database[collection_name]

    def read(self, query):
        try:
            documents = self.collection.find(query)
            return list(documents)
        except Exception as e:
            raise Exception(f"An error occurred while reading data: {e}")
