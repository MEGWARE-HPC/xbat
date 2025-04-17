import sys
import logging
import datetime
import copy
from configparser import ConfigParser
from pymongo import cursor
from bson.objectid import ObjectId
from shared.configuration import get_logger

CONFIG_PATH = "/etc/xbat/xbat.conf"

logger = logging.getLogger(get_logger())


class Singleton(type):

    def __init__(cls, name, bases, dict):
        super().__init__(name, bases, dict)
        cls.instance = None

    def __call__(cls, *args, **kw):
        if cls.instance is None:
            cls.instance = super().__call__(*args, **kw)
        return cls.instance


def get_service_configuration():
    try:
        cp = ConfigParser()
        cp.read(CONFIG_PATH)
        return cp
    except Exception as e:
        logger.error("Missing or invalid configuration at %s - %s",
                     CONFIG_PATH, e)
        sys.exit(1)


def format_error(e):
    return f"{type(e).__module__}:{type(e).__name__}: {str(e).rstrip()}"


def overwrite_log_level(logger, level):
    log_levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR
    }
    logging.getLogger(logger).setLevel(log_levels[level.lower()])


def dict_get_key(dictionary, value):
    return list(dictionary.keys())[list(dictionary.values()).index(value)]


def sanitize_mongo(d):
    """
    Recursively sanitizes MongoDBs `ObjectId`s 
    
    :param d: data to be sanitized
    :return: sanitized data
    """
    if d is None:
        return None
    if isinstance(d, cursor.Cursor): d = list(d)
    stack = d
    is_dict = isinstance(d, dict)
    if is_dict: stack = [d]
    for entry in stack:
        for k, v in entry.items():
            if isinstance(v, dict):
                sanitize_mongo(v)
            elif isinstance(v, list):
                entry[k] = [
                    str(x) if isinstance(x, ObjectId) else x for x in v
                ]
            elif isinstance(v, datetime.datetime):
                entry[k] = v.isoformat()
            else:
                if (isinstance(v, ObjectId)):
                    entry[k] = str(v)
    return stack[0] if is_dict else stack


def desanitize_mongo(d):
    """
    Recursively converts sanitized MongoDB `ObjectId`s and `datetime` strings back to their original types.

    :param d: data to be desanitized
    :return: desanitized data
    """
    if d is None:
        return None
    if isinstance(d, list):
        return [desanitize_mongo(item) for item in d]
    elif isinstance(d, dict):
        for k, v in d.items():
            if k in ("issuer", "uidnumber", "gidnumber", "state", "status",
                     "jobId", "jobIds", "runNr", "user_name", "user_type",
                     "password", "homedirectory"):
                continue

            if k == "sharedProjects" and isinstance(v, list):
                # Convert each element in sharedProjects to ObjectId
                d[k] = [
                    ObjectId(item) for item in v
                    if len(item) == 24 and all(c in "0123456789abcdefABCDEF"
                                               for c in item)
                ]
            elif k == "_id" and isinstance(v, str):
                if len(v) == 24 and all(c in "0123456789abcdefABCDEF"
                                        for c in v):
                    try:
                        d[k] = ObjectId(v)
                    except Exception:
                        pass
            elif isinstance(v, dict) or isinstance(v, list):
                d[k] = desanitize_mongo(v)
            elif isinstance(v, str):
                # Convert to ObjectId if valid
                if len(v) == 24 and all(c in "0123456789abcdefABCDEF"
                                        for c in v):
                    try:
                        d[k] = ObjectId(v)
                    except Exception:
                        pass
                # Convert to datetime if valid
                if "-" in v and ":" in v:
                    try:
                        d[k] = datetime.datetime.fromisoformat(v)
                    except ValueError:
                        pass
    return d


def replace_runNr(data, new_runNr):
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "runNr":
                data[key] = new_runNr
            else:
                replace_runNr(value, new_runNr)
    elif isinstance(data, list):
        for item in data:
            replace_runNr(item, new_runNr)


def keys_exist(d, *keys):
    _d = d
    for key in keys:
        try:
            _d = _d[key]
        except KeyError:
            return False
    return True


def get_entry_string(v):
    if isinstance(v, list) and len(v):
        v = v[0]
    return str(v)


def filter_dict(d, remove):
    """
    Returns copy of dictionary without the specified keys (shallow only).
    
    :param d: dictionary
    :param remove: keys to be filtered out
    :return: filtered dict (copy)
    """
    d = copy.deepcopy(d)
    for r in remove:
        if r in d:
            del d[r]
    return d


def to_camel_case(text):
    return ''.join(word.capitalize() if i else word
                   for i, word in enumerate(text.split('_')))


def dict_to_camcel_case(dict):
    return {to_camel_case(key): value for key, value in (dict).items()}


def convert_jobscript_to_v0160(jobscript):
    """
    Converts jobscript to format used from v0.16.0 onwards

    Before v0.16.0 jobscripts were separated into preparation, execution and postprocessing phase.
    This transformation ensures backwards compatibility by transforming the jobscripts to the new format.
    Additionally, #XBAT-START# and #XBAT-STOP# instructions are placed to provided consistent behaviour.
    A few keys are also renamed to match Slurm.
    """
    if ("preparation" in jobscript and "execution" in jobscript
            and "postprocessing" in jobscript):
        jobscript[
            "script"] = f"\n{jobscript['preparation']}\n\n#XBAT-START#\n\n{jobscript['execution']}\n\n#XBAT-STOP#\n\n{jobscript['postprocessing']}"
        for key in ["preparation", "execution", "postprocessing"]:
            del jobscript[key]

    for [old, new] in [["nodeCount", "nodes"], ["walltime", "time"],
                       ["jobName", "job-name"]]:
        if old in jobscript:
            jobscript[new] = jobscript.pop(old)

    if not ("nodelist") in jobscript:
        jobscript["nodelist"] = ""

    for v in ["output", "error"]:
        # TODO remove when adding customisation of output and error location
        # if not (v in jobscript):
        jobscript[v] = ".xbat/outputs/%j.out"

    if "partition" in jobscript and isinstance(jobscript["partition"], list):
        jobscript["partition"] = ",".join(jobscript["partition"])

    return jobscript


def strip_first_slash(s):
    if s.startswith('/'):
        return s[1:]
    return s


def str_to_bool(s):
    """
    Convert a string to boolean
    """
    return s.strip().lower() in ("yes", "true", "t", "1", "y")
