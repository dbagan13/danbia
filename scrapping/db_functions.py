# import pymongo
from pymongo import MongoClient
import pandas as pd

SAVE_DIR = "data/"

HOST = 'localhost'
PORT = 27017
DATABASE = 'danbia'


def save_to_csv(df, file_name, path=SAVE_DIR):
    df.to_csv(f"{path}{file_name}")
    print(f"{file_name} saved!")
    return True


# DOCUMENTATION
# https://pymongo.readthedocs.io/en/stable/tutorial.html

def save_to_mongo(collection, df):
    client = get_client()
    insert_documents(client, collection, df)

def get_client():
    client = MongoClient(HOST, PORT)
    return client

def insert_documents(client, collection, df):
    # get database
    db = client[DATABASE]
    #get collection
    collection = db[collection]
    documents = df.to_dict("records")
    collection.insert_many(documents)
    return True
