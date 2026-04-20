from flask import request, Response
from bson.objectid import ObjectId
from copy import deepcopy
import json

from shared import httpErrors
from shared.mongodb import MongoDB
from shared.date import get_current_datetime, get_current_filename_datetime_str
from shared.helpers import sanitize_mongo, convert_jobscript_to_v0160
from backend.restapi.user_helper import get_user_from_token
from backend.restapi.api.configuration_folders import owner_folder

db = MongoDB()

CONFIG_COLLECTION = "configurations"
FOLDER_COLLECTION = "configuration_folders"

PRIVILEGED_TYPES = ("manager", "admin")
BACKUP_SCHEMA_VERSION = "configuration-backup-v1"


def ensure_objectId(v):
    if isinstance(v, ObjectId):
        return v
    if v is None or v == "":
        return None
    try:
        return ObjectId(v)
    except Exception:
        return None


def coerce_objectid_list(values):
    result = []
    for v in values or []:
        oid = ensure_objectId(v)
        if oid:
            result.append(oid)
    return result


def normalize_string(v):
    return str(v or "").strip()


# Export


def get_export_scope():
    """
    Export scope rules:
    - normal user: only self
    - manager/admin: self | owner | all
    """
    user = get_user_from_token()
    if user is None:
        raise httpErrors.Unauthorized()

    the_scope = normalize_string(request.args.get("scope") or "self").lower()
    the_owner = normalize_string(request.args.get("owner"))

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
            "owners": None,
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


def get_owned_configs(owners=None):
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

    exported_configs = []
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

        exported_configs.append({
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
    exported_configs.sort(key=lambda x: (
        x["owner"],
        x["folderExportId"] or "",
        str((x.get("configuration") or {}).get("configurationName") or "").
        lower(),
    ))

    return {
        "schemaVersion": BACKUP_SCHEMA_VERSION,
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
            "configurations": len(exported_configs),
        },
        "folders": exported_folders,
        "configurations": exported_configs,
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
    configurations = get_owned_configs(scope_info["owners"])

    payload = build_backup_payload(
        actor=actor,
        scope_info=scope_info,
        folders=folders,
        configurations=configurations,
    )

    body = json.dumps(payload, ensure_ascii=False, indent=2, default=str)

    scope_name = scope_info["mode"]
    owner_name = scope_info["owner"] or "all"
    timestamp = get_current_filename_datetime_str()

    filename = (
        f"configuration-backup-{scope_name}-{owner_name}-{timestamp}.json")

    return Response(
        body,
        mimetype="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


# Restore


def get_restore_scope():
    """
    Restore rules:
    - normal user: only self
    - manager/admin:
        - self  => restore everything into self
        - owner => restore everything into specified owner
        - all   => preserve original owner from backup
    conflictStrategy:
        - rename (default)
        - skip
    """
    user = get_user_from_token()
    if user is None:
        raise httpErrors.Unauthorized()

    the_scope = normalize_string(
        request.values.get("scope") or request.args.get("scope")
        or "self").lower()
    the_owner = normalize_string(
        request.values.get("owner") or request.args.get("owner"))
    conflict_strategy = normalize_string(
        request.values.get("conflictStrategy")
        or request.args.get("conflictStrategy") or "rename").lower()

    if the_scope not in ("self", "owner", "all"):
        raise httpErrors.BadRequest("Invalid scope")

    if conflict_strategy not in ("overwrite", "rename", "skip"):
        raise httpErrors.BadRequest("Invalid conflictStrategy")

    is_privileged = user["user_type"] in PRIVILEGED_TYPES

    if not is_privileged:
        if the_scope != "self":
            raise httpErrors.Forbidden()
        return user, {
            "mode": "self",
            "target_owner": user["user_name"],
            "preserve_original_owner": False,
            "keep_shared_projects": False,
            "conflict_strategy": conflict_strategy,
        }

    if the_scope == "all":
        return user, {
            "mode": "all",
            "target_owner": None,
            "preserve_original_owner": True,
            "keep_shared_projects": True,
            "conflict_strategy": conflict_strategy,
        }

    if the_scope == "owner":
        if not the_owner:
            raise httpErrors.BadRequest("owner is required when scope=owner")
        return user, {
            "mode": "owner",
            "target_owner": the_owner,
            "preserve_original_owner": False,
            "keep_shared_projects": False,
            "conflict_strategy": conflict_strategy,
        }

    return user, {
        "mode": "self",
        "target_owner": user["user_name"],
        "preserve_original_owner": False,
        "keep_shared_projects": False,
        "conflict_strategy": conflict_strategy,
    }


def read_backup_payload():
    """
    Supports:
    - multipart/form-data with file=<json file>
    - raw application/json request body
    """
    if "file" in request.files:
        upload = request.files["file"]
        if upload is None or not upload.filename:
            raise httpErrors.BadRequest("No backup file provided")

        raw = upload.read()
        if not raw:
            raise httpErrors.BadRequest("Backup file is empty")

        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception:
            raise httpErrors.BadRequest("Backup file is not valid JSON")

    else:
        payload = request.json
        if payload is None:
            raise httpErrors.BadRequest("No backup payload provided")

    if not isinstance(payload, dict):
        raise httpErrors.BadRequest("Backup payload must be a JSON object")

    if payload.get("schemaVersion") != BACKUP_SCHEMA_VERSION:
        raise httpErrors.BadRequest("Unsupported backup schemaVersion")

    folders = payload.get("folders")
    configurations = payload.get("configurations")

    if not isinstance(folders, list):
        raise httpErrors.BadRequest("Backup payload has invalid folders list")

    if not isinstance(configurations, list):
        raise httpErrors.BadRequest(
            "Backup payload has invalid configurations list")

    return payload


def validate_unique_export_ids(payload):
    folder_seen = set()
    for item in payload.get("folders") or []:
        export_id = normalize_string(item.get("exportId"))
        if not export_id:
            raise httpErrors.BadRequest(
                "Every folder in backup must have exportId")
        if export_id in folder_seen:
            raise httpErrors.BadRequest("Duplicate folder exportId in backup")
        folder_seen.add(export_id)


def normalize_backup_folder_item(item):
    if not isinstance(item, dict):
        raise httpErrors.BadRequest("Invalid folder item in backup")

    export_id = normalize_string(item.get("exportId"))
    owner = normalize_string(item.get("owner"))
    folder_name = normalize_string(item.get("folderName"))

    if not export_id:
        raise httpErrors.BadRequest("Folder exportId is required")
    if not folder_name:
        raise httpErrors.BadRequest("Folder folderName is required")

    parent_export_id = item.get("parentExportId")
    parent_export_id = normalize_string(parent_export_id) or None

    return {
        "exportId": export_id,
        "owner": owner,
        "folderName": folder_name,
        "parentExportId": parent_export_id,
        "sharedProjects":
        coerce_objectid_list(item.get("sharedProjects") or []),
        "created": item.get("created"),
        "edited": item.get("edited"),
    }


def normalize_backup_config_item(item):
    if not isinstance(item, dict):
        raise httpErrors.BadRequest("Invalid configuration item in backup")

    export_id = normalize_string(item.get("exportId"))
    owner = normalize_string(item.get("owner"))

    cfg = deepcopy(item.get("configuration") or {})
    if not isinstance(cfg, dict):
        raise httpErrors.BadRequest("Configuration payload is invalid")

    configuration_name = normalize_string(cfg.get("configurationName"))
    if not configuration_name:
        raise httpErrors.BadRequest(
            "Configuration configurationName is required")

    folder_export_id = item.get("folderExportId")
    folder_export_id = normalize_string(folder_export_id) or None

    cfg["configurationName"] = configuration_name
    cfg["sharedProjects"] = coerce_objectid_list(
        cfg.get("sharedProjects") or [])

    for jobscript in (cfg.get("jobscript") or []):
        convert_jobscript_to_v0160(jobscript)

    return {
        "exportId": export_id,
        "owner": owner,
        "folderExportId": folder_export_id,
        "created": item.get("created"),
        "edited": item.get("edited"),
        "configuration": cfg,
    }


def get_target_owner(item_owner, restore_info):
    if restore_info["preserve_original_owner"]:
        owner = normalize_string(item_owner)
        if not owner:
            raise httpErrors.BadRequest(
                "Backup item is missing owner, cannot restore with scope=all")
        return owner

    return restore_info["target_owner"]


def find_existing_folder(owner, parent_folder_id, folder_name):
    query = {
        "misc.owner": owner,
        "folder.folderName": folder_name,
        "folder.parentFolderId": ensure_objectId(parent_folder_id),
    }
    return db.getOne(FOLDER_COLLECTION, query, {
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


def find_existing_config(owner, folder_id, configuration_name):
    query = {
        "misc.owner": owner,
        "configuration.folderId": ensure_objectId(folder_id),
        "configuration.configurationName": configuration_name,
    }
    return db.getOne(CONFIG_COLLECTION, query, {
        "_id": 1,
        "configuration.configurationName": 1
    })


def next_unique_config_name(owner, folder_id, base_name):
    candidate = base_name
    if find_existing_config(owner, folder_id, candidate) is None:
        return candidate

    idx = 2
    while True:
        candidate = f"{base_name} ({idx})"
        if find_existing_config(owner, folder_id, candidate) is None:
            return candidate
        idx += 1


def restore_folders(payload, restore_info, summary):
    normalized_folders = [
        normalize_backup_folder_item(item)
        for item in (payload.get("folders") or [])
    ]

    folder_export_ids = {item["exportId"] for item in normalized_folders}
    folder_mapping = {}

    pending = normalized_folders[:]
    current_timestamp = get_current_datetime()

    while pending:
        progressed = False
        remaining = []

        for item in pending:
            target_owner = get_target_owner(item["owner"], restore_info)
            home_id = owner_folder(target_owner)

            parent_export_id = item["parentExportId"]

            # wait if parent exists in backup but is not created/mapped yet
            if (parent_export_id and parent_export_id in folder_export_ids
                    and parent_export_id not in folder_mapping):
                remaining.append(item)
                continue

            if parent_export_id and parent_export_id in folder_mapping:
                parent_live_id = folder_mapping[parent_export_id]
            else:
                parent_live_id = home_id

            existing = find_existing_folder(target_owner, parent_live_id,
                                            item["folderName"])

            if existing is not None and restore_info[
                    "conflict_strategy"] == "skip":
                folder_mapping[item["exportId"]] = str(existing["_id"])
                summary["foldersMerged"] += 1
                progressed = True
                continue

            if existing is not None and restore_info[
                    "conflict_strategy"] == "overwrite":
                updated_folder = db.updateOne(
                    FOLDER_COLLECTION,
                    {"_id": existing["_id"]},
                    {
                        "$set": {
                            "folder.sharedProjects":
                            (item["sharedProjects"]
                             if restore_info["keep_shared_projects"] else []),
                            "misc.owner":
                            target_owner,
                            "misc.created":
                            item["created"] or current_timestamp,
                            "misc.edited":
                            item["edited"] or current_timestamp,
                        }
                    },
                )

                if updated_folder is None:
                    raise httpErrors.InternalServerError(
                        "Failed to overwrite folder")

                folder_mapping[item["exportId"]] = str(existing["_id"])
                summary["foldersOverwritten"] += 1
                progressed = True
                continue

            final_name = item["folderName"]
            if existing is not None and restore_info[
                    "conflict_strategy"] == "rename":
                final_name = next_unique_folder_name(target_owner,
                                                     parent_live_id,
                                                     item["folderName"])
                if final_name != item["folderName"]:
                    summary["foldersRenamed"] += 1

            doc = {
                "folder": {
                    "folderName":
                    final_name,
                    "parentFolderId":
                    ensure_objectId(parent_live_id),
                    "sharedProjects":
                    (item["sharedProjects"]
                     if restore_info["keep_shared_projects"] else []),
                },
                "misc": {
                    "owner": target_owner,
                    "created": item["created"] or current_timestamp,
                    "edited": item["edited"] or current_timestamp,
                },
            }

            result = db.insertOne(FOLDER_COLLECTION, doc)
            if not result.acknowledged:
                raise httpErrors.InternalServerError(
                    "Failed to restore folder")

            folder_mapping[item["exportId"]] = str(result.inserted_id)
            summary["foldersCreated"] += 1
            progressed = True

        if progressed:
            pending = remaining
            continue

        # fallback: if we are stuck (e.g. cycle / broken parent link), place remaining folders under home
        forced_remaining = []
        for item in remaining:
            forced_item = dict(item)
            forced_item["parentExportId"] = None
            forced_remaining.append(forced_item)
        pending = forced_remaining

    return folder_mapping


def restore_configs(payload, restore_info, folder_mapping, summary):
    normalized_configs = [
        normalize_backup_config_item(item)
        for item in (payload.get("configurations") or [])
    ]

    current_timestamp = get_current_datetime()

    for item in normalized_configs:
        target_owner = get_target_owner(item["owner"], restore_info)
        home_id = owner_folder(target_owner)

        folder_export_id = item["folderExportId"]
        if folder_export_id and folder_export_id in folder_mapping:
            target_folder_id = folder_mapping[folder_export_id]
        else:
            target_folder_id = home_id

        cfg = deepcopy(item["configuration"])
        cfg["folderId"] = ensure_objectId(target_folder_id)

        if not restore_info["keep_shared_projects"]:
            cfg["sharedProjects"] = []

        existing = find_existing_config(target_owner, target_folder_id,
                                        cfg["configurationName"])

        if existing is not None and restore_info["conflict_strategy"] == "skip":
            summary["configurationsSkipped"] += 1
            continue

        if existing is not None and restore_info[
                "conflict_strategy"] == "overwrite":
            update_result = db.replaceOne(
                CONFIG_COLLECTION,
                {"_id": existing["_id"]},
                {
                    "configuration": cfg,
                    "misc": {
                        "owner": target_owner,
                        "created": item["created"] or current_timestamp,
                        "edited": item["edited"] or current_timestamp,
                    },
                },
            )

            if not update_result or not update_result.acknowledged:
                raise httpErrors.InternalServerError(
                    "Failed to overwrite configuration")

            summary["configurationsOverwritten"] += 1
            continue

        if existing is not None and restore_info[
                "conflict_strategy"] == "rename":
            final_name = next_unique_config_name(target_owner,
                                                 target_folder_id,
                                                 cfg["configurationName"])
            if final_name != cfg["configurationName"]:
                summary["configurationsRenamed"] += 1
            cfg["configurationName"] = final_name

        doc = {
            "configuration": cfg,
            "misc": {
                "owner": target_owner,
                "created": item["created"] or current_timestamp,
                "edited": item["edited"] or current_timestamp,
            },
        }

        result = db.insertOne(CONFIG_COLLECTION, doc)
        if not result.acknowledged:
            raise httpErrors.InternalServerError(
                "Failed to restore configuration")

        summary["configurationsCreated"] += 1


def restore_backup():
    """
    Restore a JSON backup.

    multipart/form-data:
      - file: uploaded backup json
      - scope: self|owner|all
      - owner: required for scope=owner
      - conflictStrategy: rename|skip
    """
    actor, restore_info = get_restore_scope()
    payload = read_backup_payload()
    validate_unique_export_ids(payload)

    summary = {
        "schemaVersion": payload.get("schemaVersion"),
        "restoredBy": {
            "userName": actor["user_name"],
            "userType": actor["user_type"],
        },
        "restoreMode": restore_info["mode"],
        "targetOwner": restore_info["target_owner"],
        "preserveOriginalOwner": restore_info["preserve_original_owner"],
        "conflictStrategy": restore_info["conflict_strategy"],
        "foldersCreated": 0,
        "foldersMerged": 0,
        "foldersRenamed": 0,
        "foldersOverwritten": 0,
        "configurationsCreated": 0,
        "configurationsSkipped": 0,
        "configurationsRenamed": 0,
        "configurationsOverwritten": 0,
    }

    folder_mapping = restore_folders(payload, restore_info, summary)
    restore_configs(payload, restore_info, folder_mapping, summary)

    return {"data": summary}, 200
