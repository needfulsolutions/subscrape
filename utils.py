import re
from os.path import exists, isdir, join
from os import getcwd, makedirs

illegal_pattern = r"[^a-zA-Z0-9_]+"


def contains_illegal_characters(s):
    results = re.search(illegal_pattern, s)
    return not (results is None)


def file_exists(path):
    return exists(path)


def directory_exists(path):
    return isdir(path)


def make_directory(path):
    current_directory = getcwd()
    directory = join(current_directory, path)
    if not directory_exists(directory):
        makedirs(directory)
