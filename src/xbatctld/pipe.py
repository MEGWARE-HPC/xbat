"""
Implements a pool of pipes to communicate with the host system
"""

import logging
import uuid
import subprocess
import time
import re
import os
import subprocess
from pathlib import Path
import threading
from shared.helpers import Singleton
from shared.files import read_file_to_str, remove_file

PIPE_DIRECTORY = Path("/run/xbat/")
PIPE_INITIAL_SLEEP = 0.25
PIPE_READ_SLEEP = 0.5
PIPE_READ_RETRIES = 30
PIPE_AQUIRE_TIMEOUT = 15
PIPE_TIMEOUT = 15
logger = logging.getLogger("xbatctld")


class PipePool(object, metaclass=Singleton):
    """
    Manages a pool of pipes to communicate with the host system
    """

    semaphore = None
    resource_lock = None
    available_pipes = []
    pool_size = 0

    def __init__(self):
        logger.debug("Initializing PipePool as pid %d", os.getpid())
        if not PIPE_DIRECTORY.is_dir():
            logger.error("Directory %s not present", PIPE_DIRECTORY)
            return

        valid_pipe = re.compile(rf"^host-pipe-xbatctld-\d+$")

        # Identify all available pipes
        self.available_pipes = [
            f for f in PIPE_DIRECTORY.iterdir()
            if f.is_fifo() and valid_pipe.match(str(f.stem))
        ]

        logger.debug("Found %d valid pipes", len(self.available_pipes))

        self.pool_size = len(self.available_pipes)
        if not self.pool_size:
            logger.error("No valid pipes found")
            return

        # Create a semaphore to limit access to the number of available resources
        self.semaphore = threading.BoundedSemaphore(self.pool_size)

        # Lock to synchronize access to the available pipes list
        self.resource_lock = threading.Lock()
        logger.debug("PipePool initialized with %d pipes", self.pool_size)

    def alloc_pipe(self):
        # logger.debug("Worker %d attempting to acquire a pipe", os.getpid())

        if not self.semaphore or not self.resource_lock:
            logger.error("PipePool not initialized")
            return None

        # Acquire the semaphore, blocking until a pipe is available
        if not self.semaphore.acquire(timeout=PIPE_AQUIRE_TIMEOUT):
            logger.error("Worker %d unable to acquire a pipe after retries",
                         os.getpid())
            return None

        # Lock the resource list to safely acquire a specific pipe
        with self.resource_lock:
            if not self.available_pipes:
                logger.error(
                    "No pipes available despite semaphore indicating availability"
                )
                return None
            # Pop a pipe from the list
            pipe = self.available_pipes.pop()
            # logger.debug("Worker %d acquired pipe %s", os.getpid(), pipe)
            return pipe

    def free_pipe(self, pipe):
        # logger.debug("Worker %d attempting to release pipe %s", os.getpid(),
        #  pipe)

        if not self.semaphore or not self.resource_lock:
            logger.error("PipePool not initialized")
            return None

        # Lock the resource list to safely release the pipe back into the pool
        with self.resource_lock:
            self.available_pipes.append(pipe)
            # logger.debug("Worker %d released pipe %s", os.getpid(), pipe)

        # Release the semaphore to indicate that a resource is available
        self.semaphore.release()


pool = PipePool()


def execute_on_host(command):
    """
    Sends a command to host via a named pipe, executes it, and returns the
    output or error information along with the return code.
    
    :param command: command to be executed
    :return: tuple with return code and output or error information (depending on return code)
    """
    pipe = pool.alloc_pipe()

    if pipe is None:
        logger.error("Unable to aquire pipe")
        return (-1, "")

    ident = str(uuid.uuid4())
    out_stdout = PIPE_DIRECTORY / (ident + "_stdout")
    out_stderr = PIPE_DIRECTORY / (ident + "_stderr")
    out_ret = PIPE_DIRECTORY / (ident + "_ret")
    fileList = [out_stdout, out_stderr, out_ret]

    if not Path(pipe).is_fifo():
        logger.error("Pipe not found at '%s'", pipe)
        pool.free_pipe(pipe)
        return (-1, "")

    fullCommand = "echo '{};{}' > {}".format(ident, command, pipe)
    try:
        subprocess.call(fullCommand, shell=True, timeout=PIPE_TIMEOUT)
        logger.debug("Sending command to host: %s ", fullCommand)
    except subprocess.TimeoutExpired:
        logger.error("Pipe timeout for command '%s'", command)
        remove_file(fileList)
        return (-1, "")
    finally:
        pool.free_pipe(pipe)

    time.sleep(PIPE_INITIAL_SLEEP)

    retries = 0
    while not out_ret.is_file() and retries < PIPE_READ_RETRIES:
        retries += 1
        time.sleep(PIPE_READ_SLEEP)

    if not out_ret.is_file():
        logger.error("Could not read back results from '%s' for command '%s'",
                     ident, command)
        remove_file(fileList)
        return (-1, "")

    retCode = int(read_file_to_str(str(out_ret)))
    if retCode == 0:
        stdout = (read_file_to_str(str(out_stdout))).rstrip()
        remove_file(fileList)
        return (0, stdout)

    stderr = (read_file_to_str(str(out_stderr))).rstrip()
    logger.error("Command '%s' returned error code %s - %s", command, retCode,
                 stderr)

    remove_file(fileList)
    return (retCode, stderr)


def clear_run_files():

    if not PIPE_DIRECTORY.is_dir():
        return

    pattern = re.compile(
        r"^[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}_[a-z]+$"
    )

    for entry in PIPE_DIRECTORY.iterdir():
        if entry.is_file() and pattern.match(str(entry.stem)):
            remove_file(entry)
