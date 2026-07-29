from flask import request

from shared import httpErrors
from shared.mongodb import MongoDB
from shared.date import get_current_datetime
from shared.helpers import sanitize_mongo
from backend.restapi.utils.ids import ensure_objectId, transform_objectId
from backend.restapi.utils.users import get_user_from_token, can_modify_owned_doc
from backend.restapi.utils.configurations import (
    check_config_name,
    check_config_folder,
    unique_config_name,
    get_user_configurations,
)

db = MongoDB()

COLLECTION_NAME = "configurations"
CONFIGURATION_FOLDERS_COLLECTION = "configuration_folders"


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

    timestamp = get_current_datetime()
    config["misc"] = {
        "created": timestamp,
        "owner": user["user_name"],
        "edited": timestamp,
    }

    config = transform_objectId(config, "configuration")

    owner = user["user_name"]
    folder_id = check_config_folder(config, owner)
    name = check_config_name(config)

    unique_config_name(folder_id, name)

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

    cid = ensure_objectId(_id)
    if not cid:
        raise httpErrors.BadRequest("Invalid configuration id")

    existing = db.getOne(COLLECTION_NAME, {"_id": cid})
    if existing is None:
        raise httpErrors.NotFound()

    existing_owner = (existing.get("misc") or {}).get("owner")

    if not can_modify_owned_doc(user, existing_owner):
        raise httpErrors.Forbidden()

    config["misc"] = config.get("misc") or {}
    config["misc"]["owner"] = existing_owner
    config["misc"]["created"] = (existing.get("misc") or {}).get("created")
    config["misc"]["edited"] = get_current_datetime()

    config = transform_objectId(config, "configuration")

    folder_id = check_config_folder(config, existing_owner)
    name = check_config_name(config)

    unique_config_name(folder_id, name, exclude_id=cid)

    if "_id" in config:
        del config["_id"]

    result = db.replaceOne(COLLECTION_NAME, {"_id": cid}, config)

    if not result.acknowledged:
        raise httpErrors.InternalServerError("Update of configuration failed")

    # return replaced document for consistent API similar to patch
    return sanitize_mongo(db.getOne(COLLECTION_NAME, {"_id": cid})), 200


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

    if not can_modify_owned_doc(user, cfg["misc"]["owner"]):
        raise httpErrors.Forbidden()

    result = db.deleteOne(COLLECTION_NAME, {"_id": ensure_objectId(_id)})

    return {}, 204 if result.acknowledged else 400
