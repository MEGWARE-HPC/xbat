import re
from flask import request, current_app as app
from shared import httpErrors
from shared.auth import encrypt_pw
from shared.mongodb import MongoDB
from backend.restapi.user_helper import get_user_from_token, get_user_projects

db = MongoDB()

PATCHABLE_FIELDS = ['user_type', 'blocked']

USER_EXCLUDE = {"password": False, "_id": False}


def current_user():
    """
    Returns the current user's information including project membership
    :return: user
    """

    user = get_user_from_token(USER_EXCLUDE)

    if user is None:
        raise httpErrors.OAuthTokenNotFound()

    projects = get_user_projects(user)

    user["projects"] = sorted([{
        "name": p["name"],
        "_id": str(p["_id"])
    } for p in projects or []],
                              key=lambda x: x["name"])
    return user, 200


def get_all():
    """
    Returns all users from database.
    :return: list of users
    """
    return list(db.getMany("users", {}, USER_EXCLUDE) or []), 200


def patch(user_name):
    """
    Update user information
    
    :param user_name: name of user
    :return: updated user
    """
    data = request.get_json()
    patchData = {}

    user = db.getOne("users", {"user_name": user_name})

    if user is None:
        raise httpErrors.NotFound("User not found")

    if user["user_type"] == "admin" or user["user_type"] == "demo":
        if "password" in data:
            patchData["password"] = encrypt_pw(data["password"])
    else:
        for field in PATCHABLE_FIELDS:
            if field in data:
                if isinstance(data[field], bool) or len(data[field]):
                    patchData[field] = data[field]

    if not bool(patchData):
        raise httpErrors.BadRequest("No valid fields to update")

    db.updateOne("users", {"user_name": user_name}, {"$set": patchData})
    if "user_type" in patchData:
        db.updateOne("clients", {"client_id": "wf_" + user_name}, {
            "$set": {
                "default_scopes":
                app.config["security_roles"][patchData["user_type"]]
            }
        })

    # remove all associated tokens when blocking user
    if "blocked" in patchData and patchData["blocked"]:
        db.deleteMany(
            "tokens",
            {"client_id": {
                "$in": ["wf_{}".format(user_name), user_name]
            }})

    return db.getOne("users", {"user_name": user_name}, USER_EXCLUDE), 200


def get_swagger_redirect():
    """
    Returns configured swagger redirect uris

    :return: list of uris
    """

    user = get_user_from_token(USER_EXCLUDE)

    if user is None:
        raise httpErrors.OAuthTokenNotFound()

    result = db.getOne("clients", {"client_id": "admin"},
                       {"redirect_uris": True})

    if result is None:
        raise httpErrors.InternalServerError()

    return {"redirect_uris": result["redirect_uris"]}, 200


def patch_swagger_redirect():
    """
    Update swagger redirect uris
    
    :return: updated uris
    """
    user = get_user_from_token(USER_EXCLUDE)

    if user is None:
        raise httpErrors.OAuthTokenNotFound()

    if user["user_type"] != "admin":
        raise httpErrors.Forbidden()

    def validate_redirect_uris(uris):
        pattern = re.compile(
            r'^(https?)://([a-zA-Z0-9-.]+):(\d+)/api/v1/ui/oauth2-redirect\.html$'
        )

        uris = re.split(r'[ \t\n]+', uris.strip())

        for uri in uris:
            if not pattern.match(uri):
                return False
        return True

    data = request.get_json()

    if "redirect_uris" not in data or not validate_redirect_uris(
            data["redirect_uris"]):
        raise httpErrors.BadRequest("Missing or invalid redirect_uris")

    #remove tabs/newlines and duplicate spaces
    redirect_uris = " ".join(data["redirect_uris"].split())

    db.updateMany("clients", {}, {"$set": {"redirect_uris": redirect_uris}})

    return {}, 204
