from flask import current_app as app
from shared import httpErrors
from shared.auth import get_request_token
from shared.mongodb import MongoDB

db = MongoDB()


def get_user_from_token(exclude={}):
    """
    Retrieves user information based on a request token.
    :return: user object or None
    """
    token = get_request_token()
    if token is None or not "user_id" in token:
        app.logger.error("Could not retrieve user information for token")
        raise httpErrors.OAuthTokenNotFound()

    return db.getOne("users", {"_id": token["user_id"]}, exclude)


def get_user_projects(user):
    """
    Returns all projects where `user` is a member of
    
    :param user: user entry
    :return: list of projects
    """
    project_filter = {}
    if user["user_type"] != "admin" and user["user_type"] != "demo":
        project_filter = {"members": user["user_name"]}
    projects = db.getMany("projects", project_filter)

    return list(projects)


def create_user_benchmark_filter(user):
    filters = []
    if user["user_type"] != "admin" and user["user_type"] != "demo":
        filters.append({"issuer": user["user_name"]})

        project_ids = [p["_id"] for p in get_user_projects(user)]

        if len(project_ids):
            filters.append({"sharedProjects": {"$in": project_ids}})

    filterQuery = {}
    if (len(filters)): filterQuery["$or"] = filters

    return filterQuery
