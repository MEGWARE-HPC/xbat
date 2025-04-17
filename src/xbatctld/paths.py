from pathlib import Path

HOME_MOUNT_PREFIX = Path("/external")
HOME_BASE_PATH = Path(".xbat")
HOME_JOBSCRIPT_PATH = "jobscripts"
HOME_LOG_PATH = "logs"
HOME_OUTPUT_PATH = "outputs"


def get_xbat_directories(homedir):
    """
    Generates the internal and external paths for the xbat directories.

    External paths are regular paths on the host system, internal paths are (mounted) paths within the container.
    """

    external_base = homedir / HOME_BASE_PATH

    external_jobscripts = external_base / HOME_JOBSCRIPT_PATH
    external_logs = external_base / HOME_LOG_PATH
    external_output = external_base / HOME_OUTPUT_PATH

    internal_base = HOME_MOUNT_PREFIX / str(external_base).lstrip("/")

    internal_jobscripts = internal_base / HOME_JOBSCRIPT_PATH
    internal_logs = internal_base / HOME_LOG_PATH
    internal_output = internal_base / HOME_OUTPUT_PATH

    return {
        "external": {
            "base": external_base,
            "jobscripts": external_jobscripts,
            "logs": external_logs,
            "outputs": external_output
        },
        # warning: submission.py:submit iterates over this list and changes owner and permissions
        "internal": {
            "base": internal_base,
            "jobscripts": internal_jobscripts,
            "logs": internal_logs,
            "outputs": internal_output,
        }
    }
