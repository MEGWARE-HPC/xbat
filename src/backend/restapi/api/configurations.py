from flask import request
from bson.objectid import ObjectId
from shared import httpErrors
from shared.mongodb import MongoDB
from shared.date import get_current_datetime
from shared.helpers import sanitize_mongo, convert_jobscript_to_v0160
from backend.restapi.user_helper import get_user_from_token, get_user_projects
from backend.restapi.api.configuration_folders import owner_folder

db = MongoDB()

COLLECTION_NAME = "configurations"
CONFIGURATION_FOLDERS_COLLECTION = "configuration_folders"


def ensure_objectId(v):
    if isinstance(v, ObjectId):
        return v
    if v is None:
        return None
    try:
        return ObjectId(v)
    except Exception:
        return None


def transform_objectId(c):
    cfg = c.get("configuration", {})
    # transform folderId
    if cfg.get("folderId"):
        cfg["folderId"] = ensure_objectId(cfg["folderId"])
    # transform projectId(s)
    if "sharedProjects" in cfg:
        cfg["sharedProjects"] = [
            ensure_objectId(p) for p in cfg["sharedProjects"]
        ]

    c["configuration"] = cfg
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
    def transform_configurations(configurations):
        if not configurations:
            return configurations

        folder_ids = set()
        for c in configurations:
            fid = c.get("configuration", {}).get("folderId")
            oid = ensure_objectId(fid)
            if oid:
                folder_ids.add(oid)

        existing_folders = set()
        if folder_ids:
            cursor = db.getMany(
                CONFIGURATION_FOLDERS_COLLECTION,
                {"_id": {
                    "$in": list(folder_ids)
                }},
                projection={"_id": 1},
            )
            existing_folders = {f["_id"] for f in cursor}

        owner_home_cache = {}

        def get_owner_home(owner):
            if owner not in owner_home_cache:
                owner_home_cache[owner] = owner_folder(owner)
            return owner_home_cache[owner]

        update_ids = []

        for c in configurations:
            cfg = c["configuration"]
            owner = c["misc"]["owner"]

            # jobscript compatibility
            for jobscript in cfg.get("jobscript", []):
                convert_jobscript_to_v0160(jobscript)

            folder_id = ensure_objectId(cfg.get("folderId"))
            valid = folder_id in existing_folders if folder_id else False

            if not valid:
                cfg["folderId"] = get_owner_home(owner)
                update_ids.append(ensure_objectId(c["_id"]))

        if update_ids:
            db.updateMany(
                COLLECTION_NAME,
                {"_id": {
                    "$in": update_ids
                }},
                {"$set": {
                    "configuration.folderId": cfg["folderId"]
                }},
            )

        return configurations

    user = get_user_from_token()

    if user is None:
        return None

    filters = []

    if user["user_type"] not in ["admin", "manager", "demo"]:
        filters.append({"misc.owner": user["user_name"]})

        project_ids = [p["_id"] for p in get_user_projects(user)]

        if len(project_ids):
            filters.append(
                {"configuration.sharedProjects": {
                    "$in": project_ids
                }})

    query = {}
    if (len(filters)):
        query["$or"] = filters

    if _id is None:
        return transform_configurations(
            sanitize_mongo(db.getMany(COLLECTION_NAME, query)))

    _id = ensure_objectId(_id)

    query["$and"] = [{"_id": _id}]

    configurations = db.getOne(COLLECTION_NAME, query)

    if configurations is None:
        return None

    return transform_configurations([sanitize_mongo(configurations)])[0]


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
    if not config:
        raise httpErrors.BadRequest("No configuration provided")

    owner = user["user_name"]

    if not config["configuration"].get("folderId"):
        config["configuration"]["folderId"] = owner_folder(owner)

    timestamp = get_current_datetime()
    config["misc"] = {
        "created": timestamp,
        "owner": owner,
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

    if not config:
        raise httpErrors.BadRequest("No configuration provided")

    owner = config["misc"]["owner"]

    if not config["configuration"].get("folderId"):
        config["configuration"]["folderId"] = owner_folder(owner)

    config["misc"]["edited"] = get_current_datetime()
    config = transform_objectId(config)

    del config["_id"]

    identifier = {"_id": ensure_objectId(_id)}

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

    cfg = db.getOne(COLLECTION_NAME, {"_id": ensure_objectId(_id)})

    if cfg is None:
        raise httpErrors.NotFound()

    if (user["user_name"] != cfg["misc"]["owner"]
            and user["user_type"] not in ("manager", "admin")):
        raise httpErrors.Forbidden()

    result = db.deleteOne(COLLECTION_NAME, {"_id": ensure_objectId(_id)})

    return {}, 204 if result.acknowledged else 400
