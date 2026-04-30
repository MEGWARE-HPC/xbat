from bson.objectid import ObjectId

from shared import httpErrors
from shared.mongodb import MongoDB
from shared.date import get_current_datetime
from shared.helpers import sanitize_mongo
from backend.restapi.utils.ids import ensure_objectId
from backend.restapi.utils.users import get_user_from_token, get_user_projects, has_full_read_access

db = MongoDB()

COLLECTION_NAME = "configuration_folders"


def check_folder_name(doc):
    folder = doc.setdefault("folder", {})
    name = str(folder.get("folderName") or "").strip()

    if not name:
        raise httpErrors.BadRequest("Folder name is required")

    folder["folderName"] = name
    return name


def unique_folder_name(parent_folder_id, name, exclude_id=None):
    query = {
        "folder.parentFolderId": ensure_objectId(parent_folder_id),
        "folder.folderName": name,
    }

    if exclude_id is not None:
        query["_id"] = {"$ne": ensure_objectId(exclude_id)}

    duplicate = db.getOne(COLLECTION_NAME, query, {"_id": 1})

    if duplicate is not None:
        raise httpErrors.BadRequest(
            "A folder with this name already exists in the selected directory")


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

    if not has_full_read_access(user):
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
            "misc": raw_folder.get("misc", {}),
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


def collect_folder_ids(folder_id):
    visited = set()
    folder_ids = [folder_id]
    queue = [folder_id]

    while queue:
        current_id = queue.pop(0)
        children = db.getMany(
            COLLECTION_NAME,
            {"folder.parentFolderId": current_id},
            {"_id": 1},
        )

        for child in children:
            cid = child["_id"]
            if cid not in visited:
                visited.add(cid)
                folder_ids.append(cid)
                queue.append(cid)

    return folder_ids


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


def owner_folder(owner):
    timestamp = get_current_datetime()

    doc = db.updateOne(COLLECTION_NAME, {
        "folder.folderName": owner,
        "folder.parentFolderId": None,
        "misc.owner": owner,
    }, {
        "$setOnInsert": {
            "folder": {
                "folderName": owner,
                "parentFolderId": None,
                "sharedProjects": [],
            },
            "misc": {
                "owner": owner,
                "created": timestamp,
                "edited": timestamp,
            }
        }
    },
                       upsert=True)

    if not doc:
        raise httpErrors.InternalServerError(
            "Failed to get/create home folder")

    return doc["_id"]


def find_existing_folder(owner, parent_folder_id, folder_name):
    query = {
        "misc.owner": owner,
        "folder.folderName": folder_name,
        "folder.parentFolderId": ensure_objectId(parent_folder_id),
    }

    return db.getOne(COLLECTION_NAME, query, {
        "_id": 1,
        "folder.folderName": 1
    })


def next_unique_folder_name(owner, parent_folder_id, base_name):
    candidate = base_name

    if find_existing_folder(owner, parent_folder_id, candidate) is None:
        return candidate

    idx = 2
    while True:
        candidate = f"{base_name} ({idx})"

        if find_existing_folder(owner, parent_folder_id, candidate) is None:
            return candidate

        idx += 1
