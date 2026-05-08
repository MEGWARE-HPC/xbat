from flask import request
from bson.objectid import ObjectId

from shared import httpErrors
from shared.mongodb import MongoDB
from shared.date import get_current_datetime
from shared.helpers import sanitize_mongo
from backend.restapi.utils.ids import ensure_objectId, transform_objectId
from backend.restapi.utils.users import get_user_from_token, can_modify_owned_doc
from backend.restapi.utils.folders import (
    check_folder_name,
    unique_folder_name,
    get_user_folders,
    build_folder_tree,
    collect_folder_ids,
    home_folder,
    owner_folder,
)

db = MongoDB()

COLLECTION_NAME = "configuration_folders"


def get_all(structure='tree'):
    """
    Return all configuration folders visible to the user.
    """
    raw_folders = get_user_folders()

    if raw_folders is None:
        pass

    if structure == 'flat':
        return {
            "data": sorted(raw_folders,
                           key=lambda x: x["folder"]["folderName"])
        }, 200

    else:
        tree_structure = build_folder_tree(raw_folders)
        return {"data": tree_structure}, 200


def get(_id):
    """
    Return a single configuration folder by ID.
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

    folder["folder"] = folder.get("folder") or {}

    if "parentFolderId" not in folder["folder"]:
        folder["folder"]["parentFolderId"] = None

    timestamp = get_current_datetime()
    folder["misc"] = {
        "owner": user["user_name"],
        "created": timestamp,
        "edited": timestamp,
    }

    folder = transform_objectId(folder, "folder")

    parent_id = folder["folder"].get("parentFolderId")
    name = check_folder_name(folder)

    unique_folder_name(parent_id, name)

    result = db.insertOne(COLLECTION_NAME, folder)

    if not result.acknowledged:
        raise httpErrors.InternalServerError("Insertion of folder failed")

    return {"_id": str(result.inserted_id)}, 201


def put(_id):
    """
    Replace an entire folder document
    """
    user = get_user_from_token()
    if user is None:
        raise httpErrors.Unauthorized()

    folder = request.json

    if folder is None:
        raise httpErrors.BadRequest("No folder data provided")

    fid = ensure_objectId(_id)
    if not fid:
        raise httpErrors.BadRequest("Invalid folder id")

    existing = db.getOne(COLLECTION_NAME, {"_id": fid})
    if existing is None:
        raise httpErrors.NotFound()

    existing_owner = (existing.get("misc") or {}).get("owner")
    if not can_modify_owned_doc(user, existing_owner):
        raise httpErrors.Forbidden()

    folder["folder"] = folder.get("folder") or {}
    folder["misc"] = folder.get("misc") or {}
    folder["misc"]["owner"] = existing_owner
    folder["misc"]["created"] = (existing.get("misc") or {}).get("created")
    folder["misc"]["edited"] = get_current_datetime()

    folder = transform_objectId(folder, "folder")

    parent_id = folder["folder"].get("parentFolderId")
    name = check_folder_name(folder)

    unique_folder_name(parent_id, name, exclude_id=fid)

    if "_id" in folder:
        del folder["_id"]

    identifier = {"_id": fid}

    result = db.replaceOne(COLLECTION_NAME, identifier, folder)

    if not result.acknowledged:
        raise httpErrors.InternalServerError("Update of folder failed")

    return sanitize_mongo(db.getOne(COLLECTION_NAME, identifier)), 200


def delete(_id):
    """
    Delete folder with specified _id recursively (rm -rf style).

    This deletes:
    - the folder itself
    - all subfolders recursively
    - all configurations contained in these folders

    Only the owner or users of type 'manager' and 'admin' are allowed.
    """
    user = get_user_from_token()

    if user is None:
        raise httpErrors.Unauthorized()

    folder_id = ObjectId(_id)
    folder = db.getOne(COLLECTION_NAME, {"_id": folder_id})

    if folder is None:
        raise httpErrors.NotFound()

    if not can_modify_owned_doc(user, folder["misc"]["owner"]):
        raise httpErrors.Forbidden()

    folder_ids = collect_folder_ids(folder_id)

    # delete all configurations in there folders
    db.deleteMany("configurations",
                  {"configuration.folderId": {
                      "$in": folder_ids
                  }})
    # delete the folder and all subfolders
    db.deleteMany(COLLECTION_NAME, {"_id": {"$in": folder_ids}})

    return {}, 204
