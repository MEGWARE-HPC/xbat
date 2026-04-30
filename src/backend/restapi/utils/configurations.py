from shared import httpErrors
from shared.mongodb import MongoDB
from shared.helpers import sanitize_mongo, convert_jobscript_to_v0160
from backend.restapi.utils.ids import ensure_objectId
from backend.restapi.utils.users import get_user_from_token, get_user_projects, has_full_read_access
from backend.restapi.utils.folders import owner_folder

db = MongoDB()

COLLECTION_NAME = "configurations"
CONFIGURATION_FOLDERS_COLLECTION = "configuration_folders"


def check_config_name(config):
    cfg = config.setdefault("configuration", {})
    name = str(cfg.get("configurationName") or "").strip()

    if not name:
        raise httpErrors.BadRequest("Configuration name is required")

    cfg["configurationName"] = name
    return name


def check_config_folder(config, owner):
    cfg = config.setdefault("configuration", {})
    fid = ensure_objectId(cfg.get("folderId"))

    if fid:
        folder = db.getOne(
            CONFIGURATION_FOLDERS_COLLECTION,
            {"_id": fid},
            {"misc.owner": 1},
        )
        folder_owner = (folder.get("misc")
                        or {}).get("owner") if folder else None

        if folder_owner != owner:
            fid = ensure_objectId(owner_folder(owner))
    else:
        fid = ensure_objectId(owner_folder(owner))

    cfg["folderId"] = fid
    return fid


def unique_config_name(folder_id, name, exclude_id=None):
    query = {
        "configuration.folderId": ensure_objectId(folder_id),
        "configuration.configurationName": name,
    }

    if exclude_id is not None:
        query["_id"] = {"$ne": ensure_objectId(exclude_id)}

    duplicate = db.getOne(COLLECTION_NAME, query, {"_id": 1})

    if duplicate is not None:
        raise httpErrors.BadRequest(
            "A configuration with this name already exists in the selected folder"
        )


def _transform_configurations(configurations):
    """
    # TODO remove when there a no configurations left with old format
    Handles legacy configuration documents and jobscript compatibility.
    """
    if not configurations:
        return configurations

    folder_ids = set()
    for c in configurations:
        cfg = c.get("configuration", {}) or {}
        oid = ensure_objectId(cfg.get("folderId"))
        if oid:
            folder_ids.add(oid)

    owner_folders = {}
    if folder_ids:
        cursor = db.getMany(
            CONFIGURATION_FOLDERS_COLLECTION,
            {"_id": {
                "$in": list(folder_ids)
            }},
            {
                "_id": 1,
                "misc.owner": 1,
            },
        )
        for f in cursor:
            owner_folders[f["_id"]] = (f.get("misc") or {}).get("owner")

    owner_home_cache = {}

    def get_owner_home(owner):
        if owner not in owner_home_cache:
            home_id = owner_folder(owner)
            owner_home_cache[owner] = home_id

            owner_folders[ensure_objectId(home_id) or home_id] = owner

        return owner_home_cache[owner]

    for c in configurations:
        cfg = c.get("configuration", {}) or {}
        owner = c["misc"]["owner"]

        # jobscript compatibility
        for jobscript in cfg.get("jobscript") or []:
            convert_jobscript_to_v0160(jobscript)

        cid = ensure_objectId(c.get("_id"))
        if not cid or not owner:
            continue

        raw_fid = cfg.get("folderId", None)

        if raw_fid is None or raw_fid == "":
            new_folder = get_owner_home(owner)
            cfg["folderId"] = new_folder

            db.updateOne(
                COLLECTION_NAME,
                {"_id": cid},
                {"$set": {
                    "configuration.folderId": new_folder
                }},
            )
            continue

        folder_oid = ensure_objectId(raw_fid)

        if folder_oid is None:
            new_folder = get_owner_home(owner)
            cfg["folderId"] = new_folder

            db.updateOne(
                COLLECTION_NAME,
                {"_id": cid},
                {"$set": {
                    "configuration.folderId": new_folder
                }},
            )
            continue

        folder_owner = owner_folders.get(folder_oid)
        if not folder_owner:
            new_folder = get_owner_home(owner)
            cfg["folderId"] = new_folder

            db.updateOne(
                COLLECTION_NAME,
                {"_id": cid},
                {"$set": {
                    "configuration.folderId": new_folder
                }},
            )
            continue

        if folder_owner != owner:
            new_folder = get_owner_home(owner)
            cfg["folderId"] = new_folder

            db.updateOne(
                COLLECTION_NAME,
                {"_id": cid},
                {"$set": {
                    "configuration.folderId": new_folder
                }},
            )
            continue

    return configurations


def get_user_configurations(_id=None):
    """
    Retrieves configurations based on user's permissions and project access
    with optional _id filter.

    :param _id: database id
    :return: Returns a list of configurations if `_id` is `None`,
    otherwise it returns a single configuration or an empty dictionary.
    """
    user = get_user_from_token()

    if user is None:
        return None

    filters = []

    if not has_full_read_access(user):
        filters.append({"misc.owner": user["user_name"]})

        project_ids = [p["_id"] for p in get_user_projects(user)]

        if len(project_ids):
            filters.append(
                {"configuration.sharedProjects": {
                    "$in": project_ids
                }})

    query = {}
    if len(filters):
        query["$or"] = filters

    if _id is None:
        return _transform_configurations(
            sanitize_mongo(db.getMany(COLLECTION_NAME, query)))

    _id = ensure_objectId(_id)

    query["$and"] = [{"_id": _id}]

    configurations = db.getOne(COLLECTION_NAME, query)

    if configurations is None:
        return None

    return _transform_configurations([sanitize_mongo(configurations)])[0]


def find_existing_config(owner, folder_id, configuration_name):
    query = {
        "misc.owner": owner,
        "configuration.folderId": ensure_objectId(folder_id),
        "configuration.configurationName": configuration_name,
    }

    return db.getOne(COLLECTION_NAME, query, {
        "_id": 1,
        "configuration.configurationName": 1,
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
