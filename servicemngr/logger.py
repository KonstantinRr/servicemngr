#!/usr/bin/env python

""" Logger utility functions """

__author__ = "Konstantin Rolf"
__copyright__ = "Copyright 2020, ALLTHEWAYAPP LTD"
__credits__ = []

__license__ = """ MIT """

__version__ = "0.0.1"
__maintainer__ = "Konstantin Rolf"
__email__ = "konstantin.rolf@gmail.com"
__status__ = "Prototype"

import sys, os
import logging
import multiprocessing
import traceback
import argparse

from datetime import datetime
from pathlib import Path

def create_logger(stdout:bool=True, logfile:str=None, name:str='LOG', logdir:str='logs', level:int=logging.DEBUG):
    """ Creates a logger that is able to log messages between subprocesses.
    
    Logs may be written simultaneously a log file in the log directory and stdout.

    Parameters
    ----------
    stdout : bool, optional
        Whether the logger should send messages to the standard output stream. The output stream is a
        shared resource. The logger used for this purpose is therefore the multiprocessing logger.
        The default value for this argument is True.
    name : str, optional
        The logger's name (default is LOG).
    logdir: str, optional
        The log directory under which all log files are stored. The default value is 'logs'.
    level: int, optional
        The log level used by this logger. The default value is logging.DEBUG.
    logfile : str, optional
        The path where the shared log is stored. This place is placed below logDir. The default value
        for this argument is 'shared.log'.
    Returns
    -------
        The created logger
    """
    # applies the different handlers
    formatter = logging.Formatter(
        '[%(asctime)s| {}| %(levelname)s| %(processName)s] %(message)s'.format(name))

    # Creates the log directory if it does not already exists
    if logfile is not None and logdir is not None:
        Path(logdir).mkdir(parents=True, exist_ok=True)
    # Logs are stored in the current log directory by default
    if logdir is None:
        logdir = './'

    logger = multiprocessing.get_logger()
    logger.setLevel(level)
    # this bit will make sure you won't have  duplicated messages in the output
    if not len(logger.handlers):
        # Registers the multiprocessing logger, this logger is only used for shared messages
        # between threads. The file will only be accessed by a single process and can therefore
        # be implemented by the default logging package.

        if stdout: # logs to the shared output stream
            handler_stdout = logging.StreamHandler(sys.stdout)
            handler_stdout.setFormatter(formatter)
            logger.addHandler(handler_stdout)

        if logfile is not None: # logs to the shared log document
            fullpath = os.path.join(logdir, logfile)
            Path(os.path.dirname(fullpath)).mkdir(parents=True, exist_ok=True)
            # Creates the file handler
            handlerFile = logging.FileHandler(fullpath)
            handlerFile.setFormatter(formatter)
            logger.addHandler(handlerFile)

    return logger

def addLoggerArguments(parser, logfile:str, logname:str):
    # General log options
    parser.add_argument('--logdir', type=str, default='logs',
        help='The directory where the logs will be created (default: logs)')
    parser.add_argument('--stdout', type=bool, default=True,
        help='Whether the server should log to stdout (default: True)')
    parser.add_argument('--logfile', type=str, default=logfile,
        help='Storage location for the server logfiles (default: {})'.format(logfile))
    parser.add_argument('--loglevel', type=str, default='DEBUG',
        help='Log level (default: DEBUG)', choices=['DEBUG', 'INFO', 'WARN'])
    parser.add_argument('--logname', type=str, default=logname,
        help='The loggers name that is logged with every message.')

def createDefaultLogger(logfile:str, logname:str):
    return create_logger(
        stdout=True,
        logdir='logs',
        logfile=logfile,
        level=logging.INFO,
        name=logname
    )

def createLoggerFromArgs(args):
    levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARN': logging.WARN
    }

    # Creates the logfile defined by the args
    return create_logger(
        stdout=args.stdout, # Uses stdout 
        logdir=args.logdir, # Argument directory
        logfile=args.logfile, # logfile
        level=levels[args.loglevel], # loglevel
        name=args.logname
    )

if __name__ == '__main__':
    print('FILE: util_logger.py')
    print('This file does not have any functionality on its own.')