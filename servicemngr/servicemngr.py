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

# package imports #
from args import *
from logger import *

# system imports #
import sys
import json
import argparse

from subprocess import Popen, PIPE
from time import sleep

class Service:
    def __init__(self, name, delay, args, logger):
        """ Creates a new service """
        self.startException = False
        self.delay = delay
        self.name = name
        self.args = args
        self.logger = logger
        self.service = None

    def checkService(self):
        """ Checks if all services are running and restarts them if neccessary """
        if self.service is None:
            # service is not running
            self.startService()
        else:
            # service is currently running
            r = self.service.poll()
            if r is not None: # service exited with code r
                self.service = None
                self.logger.info('Service \'{}\' exited with code {}, trying to restart...'
                    .format(self.name, r))
                self.startService()
    
    def status(self):
        return self.service is not None

    def startService(self):
        """ Starts the given service using the given config. """
        # we only want to start services once if there
        # already was an error just by starting the subprocess
        if not self.startException:
            argsString = ' '.join(self.args)
            self.logger.info('Starting service \'{}\' with command \'{}\''
                .format(self.name, argsString))
            try:
                self.service = Popen(self.args)
            except Exception as e:
                self.logger.error('Could not start {} with command \'{}\': Error {}'
                    .format(self.name, argsString, e))
                self.service = None
                self.startException = True

class ServiceManager:
    """ A service manager class responsible for checking and managing a server process. """

    LOG_NAME = 'ServiceSystem'
    LOG_FILE = 'startup.log'

    @staticmethod
    def fromArgs():
        parser = argparse.ArgumentParser()
        parser.add_argument('--file', type=str, default='config.json', 
            help='Location of the config file to load (default: \'config.json\').')
        parser.add_argument('--source', type=str, default=None,
            help='Loads the config file as a string. This value cannot be used in combination'
            'with the config file argument.')
        parser.add_argument('--timing', type=int, default=5,
            help='Interval between service checks (default: 5 seconds).')

        addLoggerArguments(parser, ServiceManager.LOG_FILE, ServiceManager.LOG_NAME)
        args = parser.parse_args()
        logger = createLoggerFromArgs(args)

        if args.source is not None:
            return ServiceManager.fromText(args.source, logger)
        elif args.file is not None:
            return ServiceManager.fromPath(args.file, logger)
        else:
            raise Exception('Unknown source object')

    @staticmethod
    def fromPath(path:str, logger):
        servicemngr = ServiceManager(logger)
        servicemngr.loadConfigFromPath(path)
        return servicemngr

    @staticmethod
    def fromText(text:str, logger):
        servicemngr = ServiceManager(logger)
        servicemngr.loadConfigFromString(text)
        return servicemngr

    @staticmethod
    def fromDict(data:dict, logger):
        servicemngr = ServiceManager(logger)
        servicemngr.loadConfigFromDict(data)
        return servicemngr

    def __init__(self, logger):
        self.timing = 5
        self.logger = logger if logger is not None else createDefaultLogger(
            ServiceManager.LOG_FILE, ServiceManager.LOG_NAME)

    def loadConfigFromPath(self, path:str):
        """ Loads a config file from a path. """
        try:
            data = None
            with open(path, 'r') as cfg:
                data = cfg.read()
        except Exception as e:
            self.logger.error('Could not load config file {}'.format(e))
            raise
        self.loadConfigFromString(data)

    def loadConfigFromString(self, data:str):
        """ Loads a config file from a source string. """
        try:
            dictData = json.loads(data)
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

            validator = DictValidator(
                TypeValidator(str),
                ListValidator(
                    DictValidator(
                        keyValidator=TypeValidator(str),
                        valueValidator=PassValidator(),
                        tupleValidator=AnyValidator([
                            TupleValidator([
                                ValueValidator('name'),
                                TypeValidator(str)
                            ]),
                            TupleValidator([
                                ValueValidator('args'),
                                ListValidator(TypeValidator(str))
                            ]),
                            TupleValidator([
                                ValueValidator('exec'),
                                TypeValidator(str)
                            ]),
                            TupleValidator([
                                ValueValidator('dir'),
                                TypeValidator(str)
                            ]),
                        ])
                    )
                )
            )


            result = validator.validate(data)
            
            print(json.dumps(result, indent=4))
            
            '''
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
            '''
        except Exception as e:
            self.logger.error('Could not parse config file!\n{}'.format(e))
            raise

        # ==== All checks were done successfully ==== #

        self.services = []

    def checkService(self):
        """ Checks all services if they are up and running.

        Restarts any processes that are offline.

        Parameters
        ----------
        data : dict
            The config that is used to (re)start services.
        """
        for service in self.services:
            service.checkService()
    
    def info(self):
        """ Prints out status information to standard out. """
        for service in self.services:
            self.logger.info('Service {}:\t{}'.format(
                service.name, 'UP' if service.status() else 'DOWN'))

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
    servicemngr = ServiceManager.fromArgs()
    servicemngr.repeat(None)