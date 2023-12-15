import os.path

import pymongo as mongo
import yaml
import logging
from os import path

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
)

CONFIGURATION_FILE_NAME = "configuration.yaml"


def __reading_app_configuration() -> dict:
    with open(f"{path.dirname(__file__)}/{CONFIGURATION_FILE_NAME}", mode="r", encoding="utf-8") as f:
        yaml_data = yaml.load(f.read(), Loader=yaml.FullLoader)
    return yaml_data


__app_configuration = __reading_app_configuration()

# initial and link mongodb server
__mongo_client = mongo.MongoClient(
    f"mongodb://{__app_configuration['mongo']['username']}:{__app_configuration['mongo']['password']}@{__app_configuration['mongo']['hostname']}:{__app_configuration['mongo']['port']}")


def get_mongo_database():
    logging.info(f"get mongo database {__app_configuration['mongo']['database']}.")
    if __app_configuration['mongo']['database'] in __mongo_client.list_database_names():
        logging.debug(f"mongo database {__app_configuration['mongo']['database']} already exists.")
        return __mongo_client[__app_configuration['mongo']['database']]
    logging.debug(
        f"creating mongo database {__app_configuration['mongo']['database']} and create initial collection and inserting initial data to collection.")
    database = __mongo_client[__app_configuration['mongo']['database']]
    database['initial'].insert_one({'name': 'initial database.'})
    return database


def get_juliang_configuration() -> dict:
    return __app_configuration['proxy']['juliang']
