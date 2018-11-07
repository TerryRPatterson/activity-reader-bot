#! /usr/bin/env python3

import zipfile
from glob import glob
from os import chdir, remove, EX_IOERR
from sys import exit
from utility import get_user_confirmation


OUTPUT_FILE = "ActivityReader.zip"


def create_new_archive():
    with zipfile.ZipFile(OUTPUT_FILE, mode="x") as builtArchive:
        chdir("dist")
        for file in glob("**", recursive=True):
            builtArchive.write(file, f"ActivityReader/{file}")


try:
    create_new_archive()
except FileExistsError:
    user_response = get_user_confirmation("The distribution zip archive "
                                          "already exists would you like to "
                                          "overwrite it?(Y/N)\n")
    if user_response is True:
        remove(OUTPUT_FILE)
        create_new_archive()
    else:
        print("File not removed")
        exit(EX_IOERR)
