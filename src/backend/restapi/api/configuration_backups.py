from flask import request, Response
from bson.objectid import ObjectId
from copy import deepcopy
import json

from shared import httpErrors
from shared.mongodb import MongoDB
from shared.date import get_current_datetime
from shared.helpers import sanitize_mongo, convert_jobscript_to_v0160
from backend.restapi.user_helper import get_user_from_token

db = MongoDB()

CONFIG_COLLECTION = "configurations"
FOLDER_COLLECTION = "configuration_folders"

PRIVILEGED_TYPES = ("manager", "admin")


def ensure_objectId(v):
    if isinstance(v, ObjectId):
        return v
    if v is None or v == "":
        return None
    try:
        return ObjectId(v)
    except Exception:
        return None


def get_export_scope():
    """
    Export scope rules:
    - normal user: only self
    - manager/admin: self | owner | all
    """
    user = get_user_from_token()
    if user is None:
        raise httpErrors.Unauthorized()

    the_scope = (request.args.get("scope") or "self").strip().lower()
    the_owner = (request.args.get("owner") or "").strip()

    if the_scope not in ("self", "owner", "all"):
        raise httpErrors.BadRequest("Invalid scope")

    is_privileged = user["user_type"] in PRIVILEGED_TYPES

    if not is_privileged:
        if the_scope != "self":
            raise httpErrors.Forbidden()

        if the_owner and the_owner != user["user_name"]:
            raise httpErrors.Forbidden()

        return user, {
            "mode": "self",
            "owners": [user["user_name"]],
            "owner": user["user_name"],
        }

    # manager / admin
    if the_scope == "all":
        return user, {
            "mode": "all",
            "owners": None,  # None => all owners
            "owner": None,
        }

    if the_scope == "owner":
        if not the_owner:
            raise httpErrors.BadRequest("owner is required when scope=owner")
        return user, {
            "mode": "owner",
            "owners": [the_owner],
            "owner": the_owner,
        }

    return user, {
        "mode": "self",
        "owners": [user["user_name"]],
        "owner": user["user_name"],
    }


def get_owned_folders(owners=None):
    query = {}
    if owners is not None:
        query["misc.owner"] = {"$in": owners}

    return sanitize_mongo(db.getMany(FOLDER_COLLECTION, query))


def get_owned_configurations(owners=None):
    query = {}
    if owners is not None:
        query["misc.owner"] = {"$in": owners}

    return sanitize_mongo(db.getMany(CONFIG_COLLECTION, query))


def get_home_ids(owners=None):
    """
    Returns { owner: "<home_folder_id>" }
    Home folder is defined as:
    - folder.parentFolderId == None
    - folder.folderName == misc.owner
    """
    query = {"folder.parentFolderId": None}
    if owners is not None:
        query["misc.owner"] = {"$in": owners}

    raw = sanitize_mongo(
        db.getMany(
            FOLDER_COLLECTION,
            query,
            {
                "_id": 1,
                "folder.folderName": 1,
                "misc.owner": 1,
            },
        ))

    result = {}
    for doc in raw:
        owner = (doc.get("misc") or {}).get("owner")
        folder_name = (doc.get("folder") or {}).get("folderName")

        if owner and folder_name == owner and owner not in result:
            result[owner] = str(doc["_id"])

    return result


def build_folder_map(folders):
    """
    Returns:
    - folder_owner_map: { "<folder_id>": "<owner>" }
    - folder_ids: set("<folder_id>")
    """
    folder_owner_map = {}
    folder_ids = set()

    for doc in folders:
        folder_id = str(doc["_id"])
        owner = (doc.get("misc") or {}).get("owner")

        folder_ids.add(folder_id)
        folder_owner_map[folder_id] = owner

    return folder_owner_map, folder_ids


def normalize_export_id(folder_doc, home_ids, folder_owner_map, folder_ids):
    """
    Rules:
    - parent is home => None
    - missing / invalid / cross-owner parent => None
    - otherwise parent folder id string
    """
    owner = (folder_doc.get("misc") or {}).get("owner")
    folder = folder_doc.get("folder") or {}

    raw_parent = folder.get("parentFolderId")
    parent_oid = ensure_objectId(raw_parent)
    if not parent_oid:
        return None

    parent_id = str(parent_oid)
    owner_home_id = home_ids.get(owner)

    if owner_home_id and parent_id == owner_home_id:
        return None

    if parent_id not in folder_ids:
        return None

    parent_owner = folder_owner_map.get(parent_id)
    if parent_owner != owner:
        return None

    return parent_id


def normalize_config_folder_export_id(config_doc, home_ids, folder_owner_map):
    """
    Rules:
    - folder is home => None
    - missing / invalid / cross-owner folder => None
    - otherwise folder id string
    """
    owner = (config_doc.get("misc") or {}).get("owner")
    cfg = config_doc.get("configuration") or {}

    raw_folder_id = cfg.get("folderId")
    folder_oid = ensure_objectId(raw_folder_id)
    if not folder_oid:
        return None

    folder_id = str(folder_oid)
    owner_home_id = home_ids.get(owner)

    if owner_home_id and folder_id == owner_home_id:
        return None

    folder_owner = folder_owner_map.get(folder_id)
    if folder_owner != owner:
        return None

    return folder_id


def build_backup_payload(actor, scope_info, folders, configurations):
    """
    Backup schema:
    - does NOT export home folders as normal folders
    - top-level folders use parentExportId = None
    - configs directly under home use folderExportId = None
    """
    home_ids = get_home_ids(scope_info["owners"])
    folder_owner_map, folder_ids = build_folder_map(folders)

    exported_folders = []
    for doc in folders:
        owner = (doc.get("misc") or {}).get("owner")
        if not owner:
            continue

        folder = doc.get("folder") or {}
        folder_id = str(doc["_id"])
        owner_home_id = home_ids.get(owner)

        # do not export the home/root folder itself
        if owner_home_id and folder_id == owner_home_id:
            continue

        exported_folders.append({
            "exportId":
            folder_id,
            "owner":
            owner,
            "folderName":
            folder.get("folderName", "Unnamed Folder"),
            "parentExportId":
            normalize_export_id(doc, home_ids, folder_owner_map, folder_ids),
            "sharedProjects": [
                str(p) for p in (folder.get("sharedProjects") or [])
                if p is not None
            ],
            "created": (doc.get("misc") or {}).get("created"),
            "edited": (doc.get("misc") or {}).get("edited"),
        })

    exported_configurations = []
    for doc in configurations:
        owner = (doc.get("misc") or {}).get("owner")
        if not owner:
            continue

        cfg = deepcopy(doc.get("configuration") or {})

        for jobscript in (cfg.get("jobscript") or []):
            convert_jobscript_to_v0160(jobscript)

        folder_export_id = normalize_config_folder_export_id(
            doc, home_ids, folder_owner_map)

        if "folderId" in cfg:
            del cfg["folderId"]

        cfg["sharedProjects"] = [
            str(p) for p in (cfg.get("sharedProjects") or []) if p is not None
        ]

        exported_configurations.append({
            "exportId":
            str(doc["_id"]),
            "owner":
            owner,
            "folderExportId":
            folder_export_id,
            "created": (doc.get("misc") or {}).get("created"),
            "edited": (doc.get("misc") or {}).get("edited"),
            "configuration":
            cfg,
        })

    exported_folders.sort(key=lambda x: (x["owner"], x["parentExportId"] or "",
                                         x["folderName"].lower()))
    exported_configurations.sort(key=lambda x: (
        x["owner"],
        x["folderExportId"] or "",
        str((x.get("configuration") or {}).get("configurationName") or "").
        lower(),
    ))

    return {
        "schemaVersion": "configuration-backup-v1",
        "exportedAt": get_current_datetime(),
        "exportedBy": {
            "userName": actor["user_name"],
            "userType": actor["user_type"],
        },
        "scope": {
            "mode": scope_info["mode"],
            "owner": scope_info["owner"],
        },
        "homeFoldersIncluded": False,
        "counts": {
            "folders": len(exported_folders),
            "configurations": len(exported_configurations),
        },
        "folders": exported_folders,
        "configurations": exported_configurations,
    }


def export_backup():
    """
    Exports configurations + folders as a JSON backup file.

    Query params:
    - scope=self|owner|all
    - owner=<username>   (required if scope=owner)
    """
    actor, scope_info = get_export_scope()

    folders = get_owned_folders(scope_info["owners"])
    configurations = get_owned_configurations(scope_info["owners"])

    payload = build_backup_payload(
        actor=actor,
        scope_info=scope_info,
        folders=folders,
        configurations=configurations,
    )

    body = json.dumps(payload, ensure_ascii=False, indent=2, default=str)

    scope_name = scope_info["mode"]
    owner_name = scope_info["owner"] or "all"
    timestamp = str(get_current_datetime()).replace(":", "-").replace(" ", "_")

    filename = (
        f"configuration-backup-{scope_name}-{owner_name}-{timestamp}.json")

    return Response(
        body,
        mimetype="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
