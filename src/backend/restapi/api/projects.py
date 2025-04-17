from flask import request
from bson.objectid import ObjectId
from werkzeug import exceptions
from shared import httpErrors
from shared.mongodb import MongoDB
from shared.date import get_current_datetime
from shared.helpers import sanitize_mongo

db = MongoDB()

COLLECTION_NAME = "projects"


def get_all():
    """
    Returns all projects.

    :return: all projects
    """
    return {"data": sanitize_mongo(db.getMany(COLLECTION_NAME))}, 200


def get(project):
    """
    Returns specified project.

    :return: project
    """
    return sanitize_mongo(
        db.getOne(COLLECTION_NAME, {"_id": ObjectId(project)})), 200


def patch(project):
    """
    Patch project information.
    
    :param project: project database _id
    :return: patched project
    """
    data = request.get_json()

    changes = {}

    if "name" in data:
        name = data["name"]
        if not name or not len(name):
            return {"error": "Name must not be empty"}, 400

        # names must be unique
        projectsWithSameName = db.getMany(COLLECTION_NAME, {"name": name})

        if len(list(projectsWithSameName)):
            for p in projectsWithSameName:
                if p["_id"] == ObjectId(project):
                    # raise more appropriate error
                    raise httpErrors.BadRequest()
        changes["name"] = name

    if "members" in data: changes["members"] = data["members"]

    if not bool(changes):
        raise httpErrors.BadRequest()

    result = db.updateOne(COLLECTION_NAME, {"_id": ObjectId(project)},
                          {"$set": changes})

    return sanitize_mongo(result), 200


def post():
    """
    Create new project.

    :return: dict with inserted _id
    """
    data = request.get_json()
    result = db.insertOne(
        COLLECTION_NAME, {
            "name": data["name"],
            "created": get_current_datetime(),
            "members": data["members"]
        })

    if not result.acknowledged: raise exceptions.InternalServerError

    return {"_id": str(result.inserted_id)}, 200


def delete(project):
    """
    Delete specified project and all references of shared benchmarks and configurations.
    
    :param project: project database _id
    :return: empty response
    """

    db.updateMany("benchmarks",
                  {"sharedProjects": {
                      "$in": [ObjectId(project)]
                  }}, {"$pull": {
                      "sharedProjects": ObjectId(project)
                  }})

    db.updateMany(
        "configurations",
        {"configuration.sharedProjects": {
            "$in": [ObjectId(project)]
        }}, {"$pull": {
            "configuration.sharedProjects": ObjectId(project)
        }})

    result = db.deleteOne(COLLECTION_NAME, {"_id": ObjectId(project)})

    return {}, 204 if result.acknowledged else 400
