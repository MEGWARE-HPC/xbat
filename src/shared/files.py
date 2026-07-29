import os
import logging
import json
import csv
import shutil
import tarfile
import time
from pathlib import Path
from ast import literal_eval
from shared.configuration import get_logger

logger = logging.getLogger(get_logger())


def read_file_to_str(path):
    """
    Reads specified file and returns its contents as string.


    Args:
        path: Path of file to be read.

    Raises:
        OSError
    """
    if path is None:
        logger.error("Invalid file path '%s'", path)
        return ""
    try:
        with open(path, 'r') as f:
            # logger.debug("Reading file '%s'", path)
            data = f.read()
            f.close()
            return data
    except OSError as e:
        logger.error("Error reading file '%s' - %s", path, e)
        return ""


def read_file_to_dict(path):
    """
    Reads specified file and returns its contents as a dictionary.


    Args:
        path: Path of file to be read.
    """
    file = read_file_to_str(path)
    if not file or not len(file):
        file = "{}"
    try:
        return json.loads(file)
    except json.decoder.JSONDecodeError as e:
        logger.error("Error reading file '%s' to json - %s", path, e)
        return {}


def remove_file(path):
    """
    Delete file from file system

    Args:
        path: Path(s) of file to be deleted
    """
    if not isinstance(path, list):
        path = [path]

    for p in path:
        p = Path(p)

        # file already deleted
        if not p.is_file() or p.is_dir():
            continue

        try:
            Path(p).unlink()

        except FileNotFoundError:
            logger.error("Error deleting file '%s' - file not found", str(p))


def copy_file(source, destination):
    """
    Copy file

    Args:
        source: Source of file
        destination: Destination of file
    """
    source = Path(source)
    destination = Path(destination)

    if not source.is_file():
        logger.error("Source '%s' is not a file", str(source))
        return False

    shutil.copy2(source, destination)
    logger.debug("Copied '%s' to '%s'", str(source), str(destination))
    return True


def read_csv(path, delimiter=","):
    """
    Reads specified file and returns its contents as string.


    Args:
        path: Path of file to be read.

    Raises:
        OSError
    """
    try:
        with open(path) as csvfile:
            dialect = csv.Sniffer().sniff(csvfile.read(1024))
            csvfile.seek(0)
            reader = csv.reader(csvfile, dialect)
            return list(reader)
    except OSError as e:
        logger.error("Error reading csv file '%s' - %s", path, e)
        return []


def write_to_file(path, data, append=False):
    """
    Writes string data to file.


    Args:
        path: Path for writing data to file.
        data: Data to be written to <path>.
    """
    try:
        if not isinstance(path, Path):
            path = str(path)
        f = open(path, "a" if append else "w")
        f.write(data)
        f.close()
        return True
    except OSError as e:
        logger.error("Error writing to '%s' - %s", path, e)
        return False


def parse_to_json(path):

    if not isinstance(path, Path):
        path = str(path)

    if not os.path.isfile(path):
        logger.error("File %s not found", path)
        return {}

    with open(path) as file:
        lines = [line.strip() for line in file]
    parsed = {}
    for line in lines:
        if not len(line) or line.startswith("#"):
            continue
        split = line.split("=")
        key = split[0].strip()
        value = split[1].strip() if len(split) == 2 else ""
        if value.lower() == "true":
            value = True
        elif value.lower() == "false":
            value = False
        else:
            try:
                # dont use literal_eval for booleans as "true" will remain a string, only "True" is actually converted...
                value = literal_eval(value)
            except:
                pass

        parsed[key] = value

    return parsed


def dir_permissions_match(path, permissions):
    mode = os.stat(path).st_mode
    # Isolate the permission bits and compare to permissions
    return (mode & 0o777) == permissions


def recreate_folder(folder_path, parents=False):
    """
    Create the folder, if it exists, delete it and recreate it.
    :param folder_path: Path to the folder to be recreated
    :param parents: Whether to create parent directories if they do not exist
    """
    if folder_path.exists():
        shutil.rmtree(folder_path)

    folder_path.mkdir(parents=parents, exist_ok=True)


def contains_files(folder):
    """
    Checks whether a folder (and its subfolder) contains files
    :param folder: Path to the folder
    """
    for item in folder.rglob("*"):
        if item.is_file():
            return True
    return False


def compress_folder(folder_path, uuid):
    """
    Compress all files in the specified folder to tar format and delete the original files and folders.
    :return: compressed file path, or error message
    """
    start_time = time.time()
    source_folder = folder_path / Path(str(uuid))
    if not source_folder.is_dir():
        raise FileNotFoundError("The specified folder does not exist")
    if not contains_files(source_folder):
        logger.error(
            f"The folder '{source_folder}' does not contain any files.")
        compress_status = False
    else:
        tar_path = folder_path / Path(str(uuid) + '.tar.gz')
        try:
            with tarfile.open(tar_path, "w:gz") as tar:
                tar.add(source_folder, arcname=source_folder.name)
        except Exception as e:
            raise RuntimeError("Error during compression: " + str(e))
        compress_status = True

    try:
        shutil.rmtree(source_folder)
    except Exception as e:
        raise RuntimeError("Error during deletion of original folder: " +
                           str(e))
    end_time = time.time()
    logger.debug(
        f"Total compression and cleanup duration: {end_time - start_time:.2f} seconds"
    )
    return compress_status


def decompress_folder(tar_path, extract_folder):
    """
    Decompress the tar file to the specified folder, and delete the tar file.
    """
    if not tar_path.is_file():
        raise FileNotFoundError("The specified file does not exist")
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=extract_folder)
    tar_path.unlink()


def check_extension(file_name, extension):
    """
    Check if file extension is valid.
    :param file_name: name of the file
    :param extension: file extension
    :return: True if file extension is valid, otherwise False
    """
    return file_name.endswith(extension)
