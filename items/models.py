# items/models.py
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["lostfound_db"]

lost_col = db["lost_items"]
found_col = db["found_items"]

def get_next_sequence(collection_name):
    """Auto-increment ID generator"""
    counter = db["counters"].find_one_and_update(
        {"_id": collection_name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    return counter["seq"]

def insert_lost_item(data):
    data["lost_id"] = get_next_sequence("lost_items")
    data["status"] = "pending"
    lost_col.insert_one(data)
    return data["lost_id"]

def insert_found_item(data):
    data["found_id"] = get_next_sequence("found_items")
    data["status"] = "pending"
    found_col.insert_one(data)
    return data["found_id"]
