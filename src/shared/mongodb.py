import os
import sys
import logging
import pymongo
import threading
from bson.objectid import ObjectId
from filelock import FileLock
from pymongo.errors import ConnectionFailure
from shared.date import get_current_datetime
from shared.configuration import get_logger, get_config

logger = logging.getLogger(get_logger())

run_lock = FileLock("/tmp/mongodb.lock" if os.getenv('BUILD', "dev") ==
                    "dev" else "/run/xbat/mongodb.lock")

job_id_lock = FileLock("/tmp/mongodb_jobid.lock" if os.getenv('BUILD', "dev")
                       == "dev" else "/run/xbat/mongodb_jobid.lock")


# singleton pattern based upon https://stackoverflow.com/a/40542664/8212473
class MongoConnector(object):

    def __init__(self, address="", database="", user="", password=""):
        self.connection = None
        self.address = address
        self.database = database
        self.user = user
        self.password = password

    def create_connection(self):
        if not self.address:
            settings = get_config()["mongodb"]
            self.address = settings["address"]
            self.database = settings["database"]
            self.user = settings["user"]
            self.password = settings["password"]

        logger.info("Creating connection to %s with database '%s'",
                    self.address, self.database)
        if not len(self.address) or not len(self.database):
            raise ConnectionAbortedError("No address or database specified")

        return pymongo.MongoClient(self.address,
                                   username=self.user,
                                   password=self.password,
                                   authSource="admin")[self.database]

    def disconnect(self):
        if self.connection:
            self.connection.close()


class MongoDB(object):
    connection = None
    _lock = threading.Lock()
    address = ""
    database = ""
    user = ""
    password = ""

    @classmethod
    def set(cls, address, database, user, password):
        if cls.address == "":
            cls.address = address
            cls.database = database
            cls.user = user
            cls.password = password

    @classmethod
    def get_connection(cls, new=False):
        # double check connection for None reduces number expensive lock operations
        if new or cls.connection is None:
            with cls._lock:
                if new or cls.connection is None:
                    cls.connection = MongoConnector(
                        cls.address, cls.database, cls.user,
                        cls.password).create_connection()
        return cls.connection

    @classmethod
    def _get_cursor(cls):
        connection = cls.get_connection()
        try:
            # check if connection is valid as recommended by mongodb since MongoClient does not throw an exception
            # https://github.com/mongodb/mongo-python-driver/blob/c8d920a46bfb7b054326b3e983943bfc794cb676/pymongo/mongo_client.py#L157-L173
            connection.command("ismaster")
        except ConnectionFailure:
            logger.error(
                "Error - invalid connection to database - attempting reconnect"
            )
            connection = cls.get_connection(new=True)
        except pymongo.errors.OperationFailure as e:
            logger.error(
                "Error - could not authenticate against database - %s", e)
            sys.exit(1)
        return connection

    @classmethod
    def get_db_info(cls):
        return cls._get_cursor().name

    @classmethod
    def insertOne(cls, collection, data):
        return cls._get_cursor()[collection].insert_one(data)

    @classmethod
    def insertMany(cls, collection, data):
        return cls._get_cursor()[collection].insert_many(data)

    @classmethod
    def deleteOne(cls, collection, identifierObj):
        return cls._get_cursor()[collection].delete_one(identifierObj)

    @classmethod
    def deleteMany(cls, collection, identifierObj):
        return cls._get_cursor()[collection].delete_many(identifierObj)

    @classmethod
    def replaceOne(cls, collection, identifierObj, data, upsert=False):
        return cls._get_cursor()[collection].replace_one(identifierObj,
                                                         data,
                                                         upsert=upsert)

    @classmethod
    def getNextRunNr(cls):
        with run_lock:
            # TODO any idea for a better mechanism?
            if "misc" not in cls._get_cursor().list_collection_names():
                cls.insertOne("misc", {"last_run": 0})

            misc = cls._get_cursor()["misc"].find_one()
            run = int(misc["last_run"]) + 1
            cls._get_cursor()["misc"].find_one_and_update(
                {"_id": misc["_id"]}, {"$inc": {
                    "last_run": 1
                }})
            return run

    @classmethod
    def getNextAvailableJobId(cls):
        """
        Get the next available jobId by finding gaps in existing jobIds.
        Thread-safe across multiple API instances using MongoDB for reservation tracking.
        
        :return: Next available jobId
        """
        with job_id_lock:
            from datetime import datetime, timedelta

            # Clean up old reservations (older than 1 hour, in case of crashes)
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            cls.deleteMany("reserved_jobIds",
                           {"reservedAt": {
                               "$lt": one_hour_ago
                           }})

            # Get all existing jobIds from MongoDB
            all_jobs = list(
                cls.getMany("jobs", {}, {
                    "jobId": True,
                    "_id": False
                }))
            existing_jobIds = set([job["jobId"] for job in all_jobs
                                   ]) if all_jobs else set()

            # Get all reserved jobIds
            reserved_jobs = list(
                cls.getMany("reserved_jobIds", {}, {
                    "jobId": True,
                    "_id": False
                }))
            reserved_jobIds = set([job["jobId"] for job in reserved_jobs
                                   ]) if reserved_jobs else set()

            # Combine existing and reserved
            all_used_jobIds = existing_jobIds.union(reserved_jobIds)

            if all_used_jobIds:
                sorted_jobIds = sorted(all_used_jobIds)

                # Find first gap in the sequence starting from 1
                for i in range(1, sorted_jobIds[-1] + 2):
                    if i not in all_used_jobIds:
                        # Reserve this jobId in MongoDB
                        cls.insertOne("reserved_jobIds", {
                            "jobId": i,
                            "reservedAt": datetime.utcnow()
                        })
                        return i
            else:
                # No jobs exist, start from 1
                cls.insertOne("reserved_jobIds", {
                    "jobId": 1,
                    "reservedAt": datetime.utcnow()
                })
                return 1

    @classmethod
    def releaseReservedJobIds(cls, jobIds):
        """
        Release jobIds from the reserved collection after they've been persisted.
        
        :param jobIds: List or set of jobIds to release
        """
        if jobIds:
            cls.deleteMany("reserved_jobIds", {"jobId": {"$in": list(jobIds)}})

    @classmethod
    def getOne(cls, collection, identifierObj, excludeObj={}):
        # pymongo differs from mongodbs find implementation
        # an empty dict for exclusion of fields has no effect in mongodb
        # but pymongo only retrieves the _id if the excludeObj is empty
        if (bool(excludeObj)):
            return cls._get_cursor()[collection].find_one(
                identifierObj, excludeObj)
        else:
            return cls._get_cursor()[collection].find_one(identifierObj)

    @classmethod
    def getMany(cls, collection, identifierObj={}, excludeObj={}):
        if (bool(excludeObj)):
            return cls._get_cursor()[collection].find(identifierObj,
                                                      excludeObj)
        else:
            return cls._get_cursor()[collection].find(identifierObj)

    @classmethod
    def aggregate(cls, collection, pipeline):
        return cls._get_cursor()[collection].aggregate(pipeline)

    @classmethod
    def getObjectId(cls, collection, field, value):
        return cls._get_cursor()[collection].find({field: value}, {'_id': 1})

    @classmethod
    def list_collection_names(cls):
        return cls._get_cursor().list_collection_names()

    @classmethod
    def createBenchmark(cls,
                        name,
                        configId,
                        issuer,
                        state="pending",
                        cli=False,
                        variables=[],
                        sharedProjects=[],
                        jobIds=[]):
        data = {
            "name":
            name,
            "issuer":
            issuer,
            "startTime":
            get_current_datetime(),
            "state":
            state,
            "sharedProjects":
            [ObjectId(p) if isinstance(p, str) else p for p in sharedProjects],
            "variables":
            variables,
            "cli":
            cli,
            "configuration":
            None,
            "failureReason":
            None,
            "jobIds":
            jobIds,
        }

        if configId is not None:
            referencedConfig = cls.getOne("configurations",
                                          {"_id": ObjectId(configId)})
            if referencedConfig is None:
                logger.error(
                    "No entry for config '{}' in database".format(configId))
                return ""
            data["configuration"] = referencedConfig

        data["runNr"] = int(cls.getNextRunNr())
        result = cls.insertOne("benchmarks", data)
        if result.acknowledged:
            logger.debug(
                "Created benchmark with id: {}".format(result.inserted_id), )
            return result.inserted_id
        logger.error("Benchmark could not be inserted into database")
        return None

    @classmethod
    def updateOne(cls, collection, identifierObj, changesObj, upsert=False):
        # returns modified document
        return cls._get_cursor()[collection].find_one_and_update(
            identifierObj,
            changesObj,
            return_document=pymongo.ReturnDocument.AFTER,
            upsert=upsert)

    @classmethod
    def updateMany(cls, collection, identifierObj, changesObj, upsert=False):
        return cls._get_cursor()[collection].update_many(identifierObj,
                                                         changesObj,
                                                         upsert=upsert)
