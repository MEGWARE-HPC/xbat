from flask import request
from shared.mongodb import MongoDB

db = MongoDB()

COLLECTION_NAME = "settings"
EXCLUDE = {"_id": False}


def get():
    settings = db.getOne(COLLECTION_NAME, {}, EXCLUDE)
    return settings or {}, 200


def patch():
    data = request.get_json()
    res = db.getOne(COLLECTION_NAME, {})

    # remove all tokens of users which are not on whitelist if enabled
    if "whitelist" in data and data["whitelist"]["enabled"]:
        whitelistedUsers = data["whitelist"]["users"]
        users = db.getMany("users", {})
        for user in users:
            if user["user_type"] == "admin": continue
            if user["user_name"] not in whitelistedUsers:
                db.deleteMany("tokens",
                              {"client_id": "wf_{}".format(user["user_name"])})

    if res is None:
        db.insertOne(COLLECTION_NAME, data)
    else:
        db.updateOne(COLLECTION_NAME, {"_id": res["_id"]}, {"$set": data})
    return db.getOne(COLLECTION_NAME, {}, EXCLUDE), 200
