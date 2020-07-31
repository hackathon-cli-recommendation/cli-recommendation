from cosmos_client import MyCosmosClient
import utils.config as config


def write_back():
    client = MyCosmosClient()
    database_id = config.settings['database_id']
    database = client.get_database(database_id)
    container = database.get_container_client(config.settings['container_id'])
    results = container.read_all_items()
    ret = container.query_items("select * from c where c.command = 'az storage account create'")

    for item in results:
        print(item['command'])

    for item in ret:
        print(item['command'])
    return results


if __name__ == "__main__":
    write_back()
