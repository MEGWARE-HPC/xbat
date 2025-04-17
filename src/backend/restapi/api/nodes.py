from flask import request
from shared.mongodb import MongoDB
from shared.date import get_current_timestamp, unix_ts_to_datetime_str

db = MongoDB()


def get_all(node_hashes=[]):
    """
    Retrieves node information based on the provided hashes.
    
    :param hashes: List of hashes to filter the nodes by.
    :return: hashes with their corresponding node information
    """
    query_filter = {}

    if len(node_hashes):
        query_filter = {"hash": {"$in": node_hashes}}

    result = db.getMany("nodes", query_filter, {"_id": False})
    if result is None:
        return {}, 200

    return {x["hash"]: x for x in result}, 200


def register(node_hash: str):
    """
    Registers a hash with the corresponding node information.
    
    :param node_hash: hash of node information.
    :return: hashes with their corresponding node information
    """
    data = request.get_json()

    data["hash"] = node_hash
    data["lastUpdate"] = get_current_timestamp()

    node = db.getOne("nodes", {"hash": node_hash})

    # check if node already exists even though it should already be in the database due to the jobs register call beforehand
    if node is None:
        db.insertOne("nodes", data)
    # update node information with new system information and benchmarks
    else:
        db.updateOne("nodes", {"hash": node_hash}, {"$set": data})

    return ({
        "hash": data["hash"],
        "lastUpdate": unix_ts_to_datetime_str(data["lastUpdate"])
    }), 200
