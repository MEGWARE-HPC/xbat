import logging
import os

from xbatctld.pipe import execute_on_host
from shared import configuration as app_configuration

logger = logging.getLogger("xbatctld")


def get_user_info(username):
    """
    Retrieves UID, GID and home directory for given user.
    
    :param username: name of user
    :return: dictionary with UID, GID and home directory.
    """

    if app_configuration.get_build() == "dev" or app_configuration.get_demo():
        return {
            "uidnumber": 1000,
            "gidnumber": 1000,
            "homedirectory": "/home/xbat"
        }

    [retUid, uid] = execute_on_host("id -u {}".format(username))
    [retGid, gid] = execute_on_host("id -g {}".format(username))
    [retHome,
     home] = execute_on_host("getent passwd {} | cut -d: -f6".format(username))

    if retUid != 0 or retGid != 0 or retHome != 0 or not uid.isnumeric(
    ) or not gid.isnumeric():
        logger.error(
            "Could not retrieve information for user '%s' from host (uid=%s, gid=%s, homedir=%s).",
            username, uid, gid, home)
        return None

    return {"uidnumber": uid, "gidnumber": gid, "homedirectory": home}


def get_user_name_by_uid(uid):
    """
    Retrieves user name for given UID.
    
    :param uid: UID of user
    :return: name of user
    """
    [ret,
     username] = execute_on_host("getent passwd {} | cut -d: -f1".format(uid))

    if ret != 0:
        logger.error(
            "Could not retrieve username for UID '%s' from host. - %s", uid,
            ret)
        return None

    return username


def dir_owned_by_user(path, username, uid, gid):
    stat = os.stat(path)
    # Get the username associated with the user ID
    owner_name = get_user_name_by_uid(stat.st_uid)
    return stat.st_uid == uid and stat.st_gid == gid and owner_name == username
