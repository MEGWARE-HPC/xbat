from bson.objectid import ObjectId


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


def transform_objectId(doc, doc_type):
    """
    Transform ObjectId fields for supported REST API document types:
    - "configuration"
    - "folder"
    """
    if doc_type == "configuration":
        doc_dict = doc.get("configuration", {})
        # transform folderId
        if doc_dict.get("folderId"):
            doc_dict["folderId"] = ensure_objectId(doc_dict["folderId"])
        # transform projectId(s)
        if "sharedProjects" in doc_dict:
            doc_dict["sharedProjects"] = coerce_objectid_list(
                doc_dict.get("sharedProjects") or [])

        doc["configuration"] = doc_dict
        return doc

    if doc_type == "folder":
        doc_dict = doc.get("folder", {})

        doc_dict["parentFolderId"] = ensure_objectId(
            doc_dict.get("parentFolderId"))

        doc_dict["sharedProjects"] = coerce_objectid_list(
            doc_dict.get("sharedProjects") or [])

        doc["folder"] = doc_dict
        return doc

    return doc
