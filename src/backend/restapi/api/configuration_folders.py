from flask import request
from bson.objectid import ObjectId
from shared import httpErrors
from shared.mongodb import MongoDB
from shared.date import get_current_datetime
from shared.helpers import sanitize_mongo
from backend.restapi.user_helper import get_user_from_token, get_user_projects

db = MongoDB()

COLLECTION_NAME = "configuration_folders"


def transform_objectId(v):
    """
    Convert sharedProjects strings to ObjectId if they exist
    """
    # transform parentFolderId
    if ("parentFolderId" in v and v["folder"]["parentFolderId"] is not None):
        v["folder"]["parentFolderId"] = ObjectId(v["folder"]["parentFolderId"])
    # transform projectId(s)
    if "sharedProjects" in v:
        v["folder"]["sharedProjects"] = [
            ObjectId(p) for p in v["folder"]["sharedProjects"]
        ]

    return v


def sanitize_folder_document(doc):
    """
    Ensures a folder document has all required fields with default values if missing.
    This is particularly useful for handling legacy documents.
    """
    if doc is None:
        return None

    # Ensure the top-level structure is correct based on your schema
    # Assuming structure: {"_id": ..., "folder": {...}, "misc": {...}}
    folder_part = doc.get("folder", {})
    misc_part = doc.get("misc", {})

    sanitized_folder = {
        "folderName": folder_part.get("folderName", "Unnamed Folder"),
        "parentFolderId": folder_part.get("parentFolderId"),
    }

    sanitized_misc = {
        "owner": misc_part.get("owner", ""),
        "created": misc_part.get("created"),
        "edited": misc_part.get("edited")
    }

    sanitized_doc = {
        "_id": doc.get("_id"),
        "folder": sanitized_folder,
        "misc": sanitized_misc
    }

    return sanitized_doc


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
        filters.append({"misc.owner": user["user_name"]})

        project_ids = [p["_id"] for p in get_user_projects(user)]

        if project_ids:
            filters.append({"folder.sharedProjects": {"$in": project_ids}})

    filterQuery = {}
    if (len(filters)): filterQuery["$or"] = filters

    if _id is None:
        raw_results = db.getMany(COLLECTION_NAME, filterQuery)
        return [
            sanitize_folder_document(r) for r in sanitize_mongo(raw_results)
            if r is not None
        ]

    filterQuery["_id"] = ObjectId(_id)

    folder = db.getOne(COLLECTION_NAME, filterQuery)

    if folder is None:
        return None

    return sanitize_folder_document(sanitize_mongo(folder))


def build_folder_tree(raw_folders):
    """
    Builds a hierarchical tree structure from a sanitized list of folder documents.
    """
    folder_map = {}
    root_items = []

    sanitized_folders = [
        sanitize_folder_document(f) for f in raw_folders if f is not None
    ]

    for raw_folder in sanitized_folders:
        if not raw_folder:
            continue

        folder_id = raw_folder["_id"]
        parent_id = raw_folder["folder"].get("parentFolderId")

        folder_node = {
            "id": str(folder_id),
            "name": raw_folder["folder"]["folderName"],
            "type": "folder",
            "children": []
        }

        folder_map[folder_id] = folder_node

        if parent_id is None:
            root_items.append(folder_node)

    for raw_folder in sanitized_folders:
        folder_id = raw_folder["_id"]
        parent_id = raw_folder["folder"].get("parentFolderId")

        if parent_id is not None and parent_id in folder_map:
            parent_node = folder_map[parent_id]
            parent_node["children"].append(folder_map[folder_id])

    def sort_children(node):
        node["children"].sort(key=lambda x: x["name"])
        for child in node["children"]:
            sort_children(child)

    for root in root_items:
        sort_children(root)

    root_items.sort(key=lambda x: x["name"])

    return root_items


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

    if "parentFolderId" not in folder["folder"]:
        folder["folder"]["parentFolderId"] = None

    timestamp = get_current_datetime()
    folder["misc"] = {
        "owner": user["user_name"],
        "created": timestamp,
        "edited": timestamp,
    }

    folder = transform_objectId(folder)

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

    folder["misc"]["edited"] = get_current_datetime()
    folder = transform_objectId(folder)

    if "_id" in folder:
        del folder["_id"]

    identifier = {"_id": ObjectId(_id)}

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

    if (user["user_name"] != folder["misc"]["owner"]
            and user["user_type"] not in ("manager", "admin")):
        raise httpErrors.Forbidden()

    def collect_folder_ids(folder_id):
        visited = set()
        folder_ids = [folder_id]
        queue = [folder_id]

        while queue:
            current_id = queue.pop(0)
            children = db.getMany(COLLECTION_NAME,
                                  {"folder.parentFolderId": current_id},
                                  projection={"_id": 1})
            for child in children:
                cid = child["_id"]
                if cid not in visited:
                    visited.add(cid)
                    folder_ids.append(cid)
                    queue.append(cid)

        return folder_ids

    folder_ids = collect_folder_ids(folder_id)

    # delete all configurations in there folders
    db.deleteMany("configurations",
                  {"configuration.folderId": {
                      "$in": folder_ids
                  }})
    # delete the folder and all subfolders
    db.deleteMany(COLLECTION_NAME, {"_id": {"$in": folder_ids}})

    return {}, 204


def home_folder(user):
    root = db.getOne(
        COLLECTION_NAME,
        {
            "folder.folderName": user["user_name"],
            "folder.parentFolderId": None,
            "misc.owner": user["user_name"],
        },
    )

    if root:
        return root["_id"]

    timestamp = get_current_datetime()

    result = db.insertOne(
        COLLECTION_NAME,
        {
            "folder": {
                "folderName": user["user_name"],
                "parentFolderId": None,
                "sharedProjects": [],
            },
            "misc": {
                "owner": user["user_name"],
                "created": timestamp,
                "edited": timestamp,
            },
        },
    )

    if not result.acknowledged:
        raise httpErrors.InternalServerError(
            "Failed to create user root folder")

    return result.inserted_id
