import logging
from xbatctld.processing import process
import threading
import traceback
from shared.mongodb import MongoDB
from xbatctld.slurm import SlurmConnector
import time

db = MongoDB()
slurm = SlurmConnector()

logger = logging.getLogger("xbatctld")

QUEUE_TIMEOUT = 5


def registration_handler(cancelled):
    """
    Checks for new xbat-related jobs and forwards them for processing.
    
    :param slurm: Slurm connector
    """

    logger.debug("Registration-Thread initialised")
    # TODO Remove old benchmarks from list when no longer within slurms job list
    registered_benchmarks = []
    while not cancelled.is_set():
        try:
            slurm_jobs = slurm.get_jobs()
            for jobId in slurm_jobs.keys():
                benchmark = db.getOne("benchmarks",
                                      {"jobIds": {
                                          "$in": [jobId]
                                      }})
                if benchmark is None:
                    continue

                if benchmark["runNr"] in registered_benchmarks:
                    continue

                registered_benchmarks.append(benchmark["runNr"])
                threading.Thread(target=process,
                                 args=(benchmark["runNr"], ),
                                 daemon=True).start()

        except Exception as e:
            logger.error(
                "Error while registering benchmarks for processing: %s\n%s", e,
                traceback.format_exc())

        time.sleep(QUEUE_TIMEOUT)

    logger.debug("Registration-Thread shut down")
