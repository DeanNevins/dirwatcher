#!/usr/bin/env python3
"""
Dirwatcher - A long-running program
"""

__author__ = """
Dean Nevins +
Demo: A Comprehensive Look at Logging +
Demo: Long-Running Program with OS Signal and Exception Handling +
https://code.visualstudio.com/docs/python/debugging +
https://stackoverflow.com/questions/775049/
how-do-i-convert-seconds-to-hours-minutes-and-seconds +
https://www.programiz.com/python-programming/user-defined-exception
"""

import sys
import os
import argparse
import logging
import time
from time import strftime
from time import gmtime
import signal

logging.basicConfig(
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# A dictionary storing the filenames in the directory along with the line
# number of the last line that was read.
curr_dir_dict = {}
prev_dir_dict = {}
exit_program = False


def search_for_magic(filename, start_line, magic_string):
    """Searches for the magic text in a given file."""
    global curr_dir_dict
    with open(filename, 'r') as f:
        contents = [""] + f.readlines()

    for index in range(start_line, len(contents)):
        curr_dir_dict[filename] = index
        if magic_string in contents[index]:
            logger.info(f"""
            The magic text '{magic_string}' was found in {filename}
            on line {index}
            """)
            return


def detect_removed_files(prev_dict, files):
    """Checks if a file was removed from the watch directory."""
    global curr_dir_dict
    for file in prev_dict.keys():
        if file not in files:
            del curr_dir_dict[file]
            logger.info(f"""
            {file} has been removed from the watch directory.
            """)


def detect_added_files(prev_dict, files):
    """Checks if a file was added to the watch directory."""
    global curr_dir_dict
    for file in curr_dir_dict.keys():
        if file not in prev_dict.keys():
            logger.info(f"""
            {file} has been added to the watch directory.
            """)


def filter_extension(magic_string, extension, watch_files):
    """
    Filter files in the watch directory. If an extension is provided
    by the user, only search the files with the proper extension.
    """
    for file in watch_files:
        if extension is None or os.path.splitext(file)[1] == extension:
            start_line = curr_dir_dict.get(file, 0) + 1
            search_for_magic(file, start_line, magic_string)


class MagicStringError(Exception):
    """
    Raised when user provides no magic string in the command line arguments.
    """
    pass


class ExtensionError(Exception):
    """
    Raised when user provides an extension in the command line arguments that
    doesn't begin with '.'.
    """
    pass


class NoDirectoryError(Exception):
    """
    Raised when user doesn't provide a directory in the command line arguments.
    """
    pass


def alert_user(path, magic_string, extension):
    """
    Alert user about problematic command line arguments that they have entered.
    """
    if not magic_string:
        raise MagicStringError
    if extension is not None and extension[0] != '.':
        raise ExtensionError
    if not path:
        raise NoDirectoryError


def watch_directory(path, magic_string, extension, interval=1):
    """Searches for the magic text within a given directory."""
    global curr_dir_dict
    global prev_dir_dict
    global exit_program

    while not exit_program:
        try:
            alert_user(path, magic_string, extension)
            watch_files = [os.path.join(path, file) for file
                           in os.listdir(path)
                           if os.path.isfile(os.path.join(path, file))]

            filter_extension(magic_string, extension, watch_files)
            detect_removed_files(prev_dir_dict, watch_files)
            detect_added_files(prev_dir_dict, curr_dir_dict)

            logger.debug(f"""
                Current dictionary for the files in the watch directory:
                {curr_dir_dict}
                """)
            prev_dir_dict = curr_dir_dict.copy()
            time.sleep(interval)
        except KeyboardInterrupt:
            logger.debug("""
                This program has been interrupted.
                """)
        except FileNotFoundError:
            logger.error(f"""
            The directory you provided, <{path}>, can't be found
            in the current directory.
            """)
            time.sleep(5)
        except MagicStringError:
            logger.error("""
            No magic text provided. Please provide some magic text.
            """)
            break
        except ExtensionError:
            logger.error(f"""
            The extension you provided, '{extension}',
            must begin with a '.'.
            """)
            break
        except NoDirectoryError:
            logger.error("""
            NO DIRECTORY PROVIDED.Please provide a valid directory name.
            """)
            break
        except Exception as e:
            logger.error(f"""
            Something went wrong. :(
            {e}
            """)
            break


def create_parser():
    """Creates an argument parser."""
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dir', help='directory to watch')
    parser.add_argument('-e', '--ext', help='file extension to filter on')
    parser.add_argument('-i', '--int', help='polling interval',
                        type=int, default=1)
    parser.add_argument('-m', '--magic', help='magic text')
    return parser


def signal_handler(sig_num, frame):
    """Creates a signal handler used to initiate a program shutdown."""
    global exit_program
    print("Signal Received!", signal.Signals(sig_num).name)
    exit_program = True


def main(args):
    """
    Creates argument parser and watches the watch directory. When it receives
    the proper signal, it logs a closing message and then shuts down.
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    start = time.time()
    logger.info("""
                Welcome to Dirwatcher!
                """)
    try:
        watch_directory(parsed_args.dir, parsed_args.magic, parsed_args.ext,
                        parsed_args.int)
    except Exception as e:
        logger.error(f"""
        Something went wrong. :(
        {e}
        """)

    end = time.time()
    duration = strftime("%H:%M:%S", gmtime(end - start))
    logger.info(f"""
                Thank you for using Dirwatcher. We are shutting down now.
                You have been running this Dirwatcher session for {duration}
                """)
    return


if __name__ == '__main__':
    main(sys.argv[1:])
