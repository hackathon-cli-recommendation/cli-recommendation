import azure.cosmos.cosmos_client as cosmos_client

import utils.config as config

HOST = config.settings['host']
MASTER_KEY = config.settings['master_key']
DATABASE_ID = config.settings['database_id']


class MyCosmosClient:
    def __init__(self):
        client = cosmos_client.CosmosClient(HOST, {"masterKey": MASTER_KEY})
        self._client = client

    def client(self):
        return self._client

    def get_database(self, database_id):
        db = self._client.get_database_client(database_id)
        return db

    def query(self, query_str):
        pass
