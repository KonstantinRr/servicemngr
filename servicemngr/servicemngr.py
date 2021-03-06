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

from util_logger import addLogArgs, createLoggerFromArgs
from util_arg import argReplaceCheck
from util_cleanlog import cleanLogs
    
class ServiceManager:
    """ The manager class responsible for checking and managing a server process. """

    def __init__(self, data: dict, logger, timing:int=1):
        """ Creates a service manager using the given config dictionary.

        Parameters
        ----------
        data : dict
            The config that is used to start up the services. See the given
            config.json file for more information about the possible arguments.
        logger :
            The logger used to log 
        """
        self.data = data
        self.timing = timing
        self.logger = logger
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
            baseCheck = argReplaceCheck(self.data, checks)
            if baseCheck is not None: # a check failed
                raise AttributeError('Could not satisfy check: {}'.format(str(baseCheck)))

            # checks if all services satisfy the conditions
            for service in self.data['services']:
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

        try:
            # Cleans the logs if the config option is set
            if self.data['clean_logs']:
                self.logger.info('Cleaning log files')
                cleanLogs()
        except Exception as e:
            self.logger.error('Could not clean logs!\n{}'.format(e))
            raise
        
        self.serviceCount = len(self.data['services'])
        self.services = [None] * self.serviceCount
        self.startExceptions = [False] * self.serviceCount
        self.args = [None] * self.serviceCount
        # creates the commands used to start the services
        for idx, service in enumerate(self.data['services']):
            self.args[idx] = service['exec'].split(' ')
            for arg in service['args']:
                self.args[idx].extend(arg.split(' '))
        

    def startService(self, idx:int):
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

    def repeat(self):
        """ Runs the checkService function repeatedly with timing difference
        
        Parameters
        ----------
        timing : float
            The amount of seconds to wait between calls of checkService
        """ 
        while True:
            self.checkService()
            sleep(float(self.timing))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Server Startup System (SSS)')
    parser.add_argument('--config', type=str, default='config.json', 
        help='Location of the config file to load (default: \'config.json\').')
    parser.add_argument('--timing', type=int, default=5,
        help='Interval between checks (default: 5 seconds).')
    addLogArgs(parser, 'startup.log', 'ServerSystem')

    args = parser.parse_args()
    # creates a logger from the supplied arguments
    logger = createLoggerFromArgs(args)

    logger.info('Starting up ServerSystem...')

    try:
        data = None
        with open(args.config, 'r') as cfg:
            data = json.load(cfg)
    except Exception as e:
        logger.error('Could not load config file {}'.format(e))
        sys.exit(-1)
    

    mngr = ServiceManager(data, logger, timing=args.timing)
    mngr.repeat()
