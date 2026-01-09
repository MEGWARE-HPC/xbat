from flask import request
from bson.objectid import ObjectId
from shared import httpErrors
from shared.mongodb import MongoDB
from shared.date import get_current_datetime
from shared.helpers import sanitize_mongo
from backend.restapi.user_helper import get_user_from_token, get_user_projects

db = MongoDB()

COLLECTION_NAME = "configuration_folders"


def transform_shared(v):
    """
    Convert sharedProjects strings to ObjectId if they exist
    """
    if "sharedProjects" in v:
        v["sharedProjects"] = [ObjectId(p) for p in v["sharedProjects"]]
    return v


def get_user_folders(_id=None):
    """
    Retrieves folders based on user's permissions and project access.
    If _id is provided, returns a single folder.
    """
    filters = []

    user = get_user_from_token()
    if user is None:
        return None

    if user["user_type"] not in ["admin", "demo"]:
        filters.append({"owner": user["user_name"]})
        project_ids = [p["_id"] for p in get_user_projects(user)]
        if project_ids:
            filters.append({"sharedProjects": {"$in": project_ids}})

    filter_query = {"$or": filters} if filters else {}

    if _id is None:
        return sanitize_mongo(db.getMany(COLLECTION_NAME, filter_query))

    filter_query["_id"] = ObjectId(_id)

    folder = db.getOne(COLLECTION_NAME, filter_query)

    if folder is None:
        return None

    return sanitize_mongo(folder)


def get_all():
    """
    Return all configuration folders the user has access to
    """
    result = get_user_folders()
    return {"data": sorted(result, key=lambda x: x.get("folderName", ""))}, 200


def get(_id):
    """
    Return a single folder by _id
    """
    result = get_user_folders(_id)

    if result is None:
        raise httpErrors.NotFound()

    return result, 200


def post():
    """
    Create a new folder
    """
    user = get_user_from_token()
    if user is None:
        raise httpErrors.Unauthorized()

    folder = request.json
    if folder is None:
        raise httpErrors.BadRequest("No folder data provided")

    timestamp = get_current_datetime()
    folder["owner"] = user["user_name"]
    folder["created"] = timestamp
    folder["edited"] = timestamp

    folder = transform_shared(folder)

    result = db.insertOne(COLLECTION_NAME, folder)

    if not result.acknowledged:
        raise httpErrors.InternalServerError("Insertion of folder failed")

    return {"_id": str(result.inserted_id)}, 201


def put(_id):
    """
    Replace an entire folder document
    """
    folder = request.json

    if folder is None:
        raise httpErrors.BadRequest("No folder data provided")

    folder["edited"] = get_current_datetime()
    folder = transform_shared(folder)

    del folder["_id"]
    identifier = {"_id": ObjectId(_id)}

    result = db.replaceOne(COLLECTION_NAME, identifier, folder)

    if not result.acknowledged:
        raise httpErrors.InternalServerError("Update of folder failed")

    return sanitize_mongo(db.getOne(COLLECTION_NAME, identifier)), 200


def delete(_id):
    """
    Delete folder. Only owner, manager, or admin can delete.
    """
    user = get_user_from_token()

    if user is None:
        raise httpErrors.Unauthorized()

    folder = db.getOne(COLLECTION_NAME, {"_id": ObjectId(_id)})

    if folder is None:
        raise httpErrors.NotFound()

    if user["user_name"] != folder.get("owner") and user["user_type"] not in [
            "manager", "admin"
    ]:
        raise httpErrors.Forbidden()

    result = db.deleteOne(COLLECTION_NAME, {"_id": ObjectId(_id)})

    return {}, 204 if result.acknowledged else 400
