#!/usr/bin/env python

""" This class manages the different services and checks their status

This file contains functions to manage server processes.
It regulary checks the status of each process to see whether
they are still running. It automatically tries to restart them if they
are not running. The configuration is read from a config file.
"""

__author__ = "Konstantin Rolf"
__copyright__ = "Copyright 2020, ALLTHEWAYAPP LTD"
__credits__ = []

__license__ = """ MIT """

__version__ = "0.0.1"
__maintainer__ = "Konstantin Rolf"
__email__ = "konstantin.rolf@gmail.com"
__status__ = "Prototype"

import sys
import json
import logging
import argparse


from subprocess import Popen, PIPE
from time import sleep

from logutils.logger import addLogArgs, createLoggerFromArgs
from logutils.arg import argReplaceCheck
    
def hello():
    parent_parser = argparse.ArgumentParser(add_help=False)                                                                                                  
    parent_parser.add_argument('--user', '-u', default=getpass.getuser(), help='username')                                                                                                                     
    parent_parser.add_argument('--debug', default=False, required=False, action='store_true', dest="debug", help='debug flag')
    
    main_parser = argparse.ArgumentParser()                                                                                                                  
    service_subparsers = main_parser.add_subparsers(title="service", dest="service_command")                                                                                                              
    service_parser = service_subparsers.add_parser("first", help="first", parents=[parent_parser])                                                                                                             
    action_subparser = service_parser.add_subparsers(title="action", dest="action_command")                                                                                                               
    action_parser = action_subparser.add_parser("second", help="second", parents=[parent_parser])                                                                                                             

class Service:
    def __init__(self, args)
        self.startException = False
        self.args
    def startService(self):
        """ Starts the given service using the given config.

        Parameters
        ----------
        serviceInfo : dict
            The configuration used to start up the service. See the config.json
            for more information about the possible arguments.
        """
        # we only want to start services once if there
        # already was an error just by starting the subprocess
        if not self.startExceptions[idx]:
            argsString = ' '.join(self.args[idx])
            self.logger.info('Starting service {} with command \'{}\''
                .format(idx, argsString))
            try:
                self.services[idx] = Popen(self.args[idx])
            except Exception as e:
                self.logger.error('Could not start {} with command \'{}\': Error {}'
                    .format(serviceInfo['name'], argsString, e))
                self.startExceptions[idx] = True

class ServiceManager:
    """ A service manager class responsible for checking and managing a server process. """

    SOURCE_PATH = 0
    SOURCE_TEXT = 1
    SOURCE_DICT = 2

    @staticmethod
    def addArgParserArguments(parser: argparse.ArgumentParser, useLogger:bool=True):
        parser = argparse.ArgumentParser()
        parser.add_argument('--file', type=str, default='config.json', 
            help='Location of the config file to load (default: \'config.json\').')
        parser.add_argument('--string', type=str, default=None,
            help='Loads the config file as a string. This value cannot be used in combination'
            'with the config file argument.')
        parser.add_argument('--timing', type=int, default=5,
            help='Interval between service checks (default: 5 seconds).')

        if useLogger:
            addLogArgs(parser, 'startup.log', 'ServiceSystem')

    def __init__(self, source, tp:int, logger, timing:int=1):
        """ Creates a service manager using the given config dictionary.
        See the given config.json file for more information about the possible arguments.

        Parameters
        ----------
        source
            The source that is used to load the config which is then used to
            start up the services. The value may be a [path], [text] or [dict]
            depending on the value of the tp argument
        tp : int
            The type of the source. This value must be SOURCE_PATH, SOURCE_TEXT
            or SOURCE_DICT.
        logger :
            The logger used to log 
        """
        self.timing = timing
        self.logger = logger
        if tp == SOURCE_PATH:
            self.loadConfigFromPath(source)
        elif tp == SOURCE_TEXT:
            self.loadConfigFromString(source)

    def loadConfigFromPath(self, data:str):
        """ Loads a config file from a path. """
        try:
            data = None
            with open(args.config, 'r') as cfg:
                data = cfg.read()
        except Exception as e:
            self.logger.error('Could not load config file {}'.format(e))
            raise
        self.loadConfigFromString(data)

    def loadConfigFromString(self, data:str):
        """ Loads a config file from a source string. """
        try:
            dictData = json.load(data)
        except Exception as e:
            self.logger.error('Could not parse config string {}'.format(e))
            raise
        self.loadConfigFromDict(dictData)

    def loadConfigFromDict(self, data:dict):
        """ Loads a config file from a dictionary. """
        try: # JSON Syntax checking
            # (arg, type, required, <default>)
            checks = [
                ('clean_logs', bool, False, False),
                ('services', list, False, [])
            ]
            serviceChecks = [
                ('name', str, True), ('args', list, False, []),
                ('exec', str, True), ('dir', str, False, './')
            ]

            # checks if the base dictionary satisfy the conditions
            baseCheck = argReplaceCheck(data, checks)
            if baseCheck is not None: # a check failed
                raise AttributeError('Could not satisfy check: {}'.format(str(baseCheck)))

            # checks if all services satisfy the conditions
            for service in data['services']:
                serviceCheck = argReplaceCheck(service, serviceChecks)
                if serviceCheck is not None: # check failed
                    raise AttributeError('Could not satisfy check: {}'.format(str(serviceCheck)))
                # checks if the arg list satisfies the conditions
                for arg in service['args']:
                    if not isinstance(arg, str):
                        raise AttributeError('Could not satisfy check: Arg elements must be str')
        except Exception as e:
            self.logger.error('Could not parse config file!\n{}'.format(e))
            raise

        # ==== All checks were done successfully ==== #
        self.serviceCount = len(data['services'])
        self.services = [None] * self.serviceCount
        self.startExceptions = [False] * self.serviceCount
        self.args = [None] * self.serviceCount
        # creates the commands used to start the services
        for idx, service in enumerate(data['services']):
            self.args[idx] = service['exec'].split(' ')
            for arg in service['args']:
                self.args[idx].extend(arg.split(' '))
        



    def checkService(self):
        """ Checks all services if they are up and running.

        Restarts any processes that are offline.

        Parameters
        ----------
        data : dict
            The config that is used to (re)start services.
        """
        for idx, info in enumerate(data['services']):
            if self.services[idx] is not None:
                r = self.services[idx].poll()
                if r is not None:
                    self.logger.info('Service {} exited with code {}, trying to restart...'.format(idx, r))
                    self.startService(idx)
            else:
                self.startService(idx)
    
    def info(self):
        """ Prints out status information to standard out. """
        for index, info in enumerate(self.services): 
            isUp = self.services[index] is None
            self.logger.info('Service {}:\t{}'.format(
                index, 'UP' if isUp else 'DOWN'))

    def repeat(self, exitCondition):
        """ Runs the checkService function repeatedly with timing difference
        
        Parameters
        ----------
        timing : float
            The amount of seconds to wait between calls of checkService
        exitCondition : 
        """ 
        while True:
            self.checkService()
            sleep(float(self.timing))


if __name__ == "__main__":
    args = parser.parse_args()
    # creates a logger from the supplied arguments
    

    logger.info('Starting up ServerSystem...')
    

    mngr = ServiceManager(data, logger, timing=args.timing)
    mngr.repeat()
