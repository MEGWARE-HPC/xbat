from flask import request
from bson.objectid import ObjectId
from shared import httpErrors
from shared.mongodb import MongoDB
from shared.date import get_current_datetime
from shared.helpers import sanitize_mongo, convert_jobscript_to_v0160
from backend.restapi.user_helper import get_user_from_token, get_user_projects
from backend.restapi.api.configuration_folders import home_folder

db = MongoDB()

COLLECTION_NAME = "configurations"
CONFIGURATION_FOLDERS_COLLECTION = "configuration_folders"


def transform_objectId(c):
    # transform folderId
    if ("folderId" in c["configuration"]
            and c["configuration"]["folderId"] is not None):
        c["configuration"]["folderId"] = ObjectId(
            c["configuration"]["folderId"])
    # transform projectId(s)
    if ("sharedProjects" in c["configuration"]):
        c["configuration"]["sharedProjects"] = [
            ObjectId(p) for p in c["configuration"]["sharedProjects"]
        ]

    return c


def get_user_configurations(_id=None):
    """
    Retrieves configurations based on user's permissions and project
    access with optional _id filter.
    
    :param _id: database id
    :return: Returns a list of configurations if `_id` is `None`,
    otherwise it returns a single configuration or an empty dictionary.
    """

    # TODO remove when there a no configurations left with old format
    def transform_configurations(configurations, user):
        home_folderId = home_folder(user)
        folder_ids = []

        for configuration in configurations:
            cfg = configuration["configuration"]
            for jobscript in cfg["jobscript"]:
                jobscript = convert_jobscript_to_v0160(jobscript)

            if "folderId" not in cfg or not cfg["folderId"]:
                cfg["folderId"] = home_folderId
                configuration["_id"] = ensure_objectId(configuration["_id"])
                folder_ids.append(configuration["_id"])

        if folder_ids:
            db.updateMany(
                COLLECTION_NAME,
                {"_id": {
                    "$in": folder_ids
                }},
                {"$set": {
                    "configuration.folderId": home_folderId
                }},
            )
        return configurations

    def ensure_objectId(v):
        if isinstance(v, ObjectId):
            return v
        if v is None:
            return None
        try:
            return ObjectId(v)
        except Exception:
            raise ValueError(f"Invalid ObjectId format: {v}")

    filters = []

    user = get_user_from_token()

    if user is None:
        return None

    if user["user_type"] not in ["admin", "manager", "demo"]:
        filters.append({"misc.owner": user["user_name"]})

        project_ids = [p["_id"] for p in get_user_projects(user)]

        if len(project_ids):
            filters.append(
                {"configuration.sharedProjects": {
                    "$in": project_ids
                }})

    filterQuery = {}
    if (len(filters)): filterQuery["$or"] = filters

    if _id is None:
        return transform_configurations(
            sanitize_mongo(db.getMany(COLLECTION_NAME, filterQuery)), user)

    _id = ensure_objectId(_id)

    filterQuery["$and"] = [{"_id": _id}]

    configurations = db.getOne(COLLECTION_NAME, filterQuery)

    if configurations is None:
        return None

    return transform_configurations([sanitize_mongo(configurations)], user)[0]


def get_all():
    """
    Returns all configurations of user including ones shared from project.

    :return: benchmarks
    """
    result = get_user_configurations()
    return {
        "data":
        sorted(result, key=lambda x: x["configuration"]["configurationName"])
    }, 200


def get(_id):
    """
    Returns configuration with specified _id.
    
    :param _id: database id of configuration
    :return: configuration
    """
    result = get_user_configurations(_id)

    if result is None:
        raise httpErrors.NotFound()

    return result, 200


def post():
    """
    Add new configuration to database.

    :return: database id of inserted document
    """
    user = get_user_from_token()
    if user is None:
        raise httpErrors.Unauthorized()

    config = request.json
    if config is None:
        raise httpErrors.BadRequest("No configuration provided")

    if "folderId" not in config["configuration"]:
        home_folderId = home_folder(user)
        config["configuration"]["folderId"] = home_folderId

    timestamp = get_current_datetime()
    config["misc"] = {
        "created": timestamp,
        "owner": user["user_name"],
        "edited": timestamp,
    }

    config = transform_objectId(config)

    result = db.insertOne(COLLECTION_NAME, config)

    if not result.acknowledged:
        raise httpErrors.InternalServerError(
            "Insertion of configuration failed")

    return {"_id": str(result.inserted_id)}, 201


def put(_id):
    """
    Update configuration by replacing entire document - request must contain entire configuration.
    
    :param _id: database id
    :return: updated configuration
    """
    user = get_user_from_token()
    if user is None:
        raise httpErrors.Unauthorized()

    config = request.json

    if config is None:
        raise httpErrors.BadRequest("No configuration provided")

    if "folderId" not in config["configuration"]:
        home_folderId = home_folder(user)
        config["configuration"]["folderId"] = home_folderId

    config["misc"]["edited"] = get_current_datetime()
    config = transform_objectId(config)

    del config["_id"]

    identifier = {"_id": ObjectId(_id)}

    result = db.replaceOne(COLLECTION_NAME, identifier, config)

    if not result.acknowledged:
        raise httpErrors.InternalServerError("Update of configuration failed")

    # return replaced document for consistent API similar to patch
    return sanitize_mongo(db.getOne(COLLECTION_NAME, identifier)), 200


def delete(_id):
    """
    Delete configuration with specified _id. Configurations may only be
    deleted by the owner or users of type 'manager' and 'admin'.
    
    :param _id: database id of configuration
    :return: empty response
    """

    user = get_user_from_token()

    if user is None:
        raise httpErrors.Unauthorized()

    configuration = db.getOne(COLLECTION_NAME, {"_id": ObjectId(_id)})

    if configuration is None:
        raise httpErrors.NotFound()

    if user["user_name"] != configuration["misc"]["owner"] and not (
            user["user_type"] == 'manager' or user["user_type"] == "admin"):
        raise httpErrors.Forbidden()

    result = db.deleteOne(COLLECTION_NAME, {"_id": ObjectId(_id)})

    return {}, 204 if result.acknowledged else 400
