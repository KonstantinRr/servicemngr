#!/usr/bin/env python

""" Argument Utility functions

This file combines some utility functions to check arguments.
"""

__author__ = "Konstantin Rolf"
__copyright__ = "Copyright 2020, ALLTHEWAYAPP LTD"
__credits__ = []

__license__ = """ MIT """

__version__ = "0.0.1"
__maintainer__ = "Konstantin Rolf"
__email__ = "konstantin.rolf@gmail.com"
__status__ = "Prototype"

from abc import ABC, abstractmethod
from collections.abc import Sequence, Iterable

class AbstractValidator(ABC): 
    """ The general interface of any validator. Each subclass must
    implement the call method with a single parameter. It should
    return the validated block iff the validator test passed, None otherwise. """

    def __init__(self):
        self.info = True

    @abstractmethod
    def _validate(self, value, level:int):
        pass

    def validate(self, value, level:int=0):
        result = self._validate(value, level + 1)
        if self.info:
            print('{}{} {} {}'.format(self.indent(level), result, value, self.name()))
        return result

    def setInfo(self, value:bool):
        self.info = value

    def indent(self, level):
        return '  ' * level

class PassValidator(AbstractValidator):
    def __init__(self):
        super().__init__()

    def _validate(self, value, level:int):
        """ Passes any value """
        return value

    def __str__(self):
        return 'PassValidator[]'

    def name(self):
        return 'PassValidator'

class ReplaceValidator(AbstractValidator):
    """ Validates the given input and replaces the input with a replacement
    value if the validator does not parse the value successful. """

    def __init__(self, validator, replacement):
        """ Creates a new ReplaceValidator.
        
        Parameters
        ----------
        validator : AbstractValidator
            The validator used to validate any input.
        replacement :
            The value that is returned if the validation fails.
        """
        super().__init__()
        self.validator = validator
        self.replacement = replacement

    def _validate(self, value, level:int):
        result = self.validator.validate(value, level)
        return result if result is not None else self.replacement

    def __str__(self) -> str:
        return 'ReplaceValidator[validator={} replacement={}]'.format(
            self.validator, self.replacement)
    
    def __repr__(self) -> str:
        return str(self)

    def name(self):
        return 'ReplaceValidator'
            
# logical validator operators #

class AllValidator(AbstractValidator):
    """ Combines multiple validators in one class and returns the
    validated block iff all validators are successful, None otherwise. """

    def __init__(self, validators=[], shortCircuit:bool=False, allowEmpty:bool=False):
        """ Creates a new all validator with a list of subchecks
        
        Parameters
        ----------
        validators :
            The list of subvalidators that need to be validated
        shortCircuit : bool
            Whether the list of validators can be short-evaluated. All validators are
            skipped if a previous validator returned True (default is False).
        allowEmpty : bool
            Whether a value should be accepeted iff there is no validator specified.
            (default is False) 
        """
        super().__init__()
        self.validators = validators
        self.shortCircuit = shortCircuit
        self.allowEmpty = allowEmpty

    def _validate(self, value, level:int):
        if not self.validators:
            return value if self.allowEmpty else None

        checkResult = True
        for validator in self.validators:
            checkResult = checkResult and (validator.validate(value, level) is not None)
            if self.shortCircuit and not checkResult:
                break
        return value if checkResult else None

    def __str__(self):
        return 'All[validators={}, circuit={}, allowEmpty={}]'.format(
            self.validators, self.shortCircuit, self.allowEmpty)
    
    def __repr__(self) -> str:
        return str(self)

    def name(self):
        return 'AllValidator'

class AnyValidator(AbstractValidator):
    """ Combines multiple validators in one class and returns the
    validated block iff any validator was successful, None otherwise. """

    def __init__(self, validators=[], shortCircuit:bool=False, allowEmtpy:bool=False):
        """ Creates a new all validator with a list of subchecks
        
        Parameters
        ----------
        validators : Sequence[AbstractValidator]
            The list of subvalidators that need to be validated
        shortCircuit : bool
            Whether the list of validators can be short-evaluated.
            All validators are skipped iff a previous validator returned True.
        allowEmpty : bool
            Whether a value should be accepeted iff there is no validator specified.
            (default is False) 
        """
        super().__init__()
        self.validators = validators
        self.shortCircuit = shortCircuit
        self.allowEmpty = allowEmtpy

    def _validate(self, value, level:int):
        if not self.validators:
            return value if self.allowEmpty else None

        result = None
        for validator in self.validators:
            newResult = validator.validate(value, level)
            if newResult is not None:
                if result is not None:
                    raise Exception('Multiple validators matched!')
                result = newResult
            if self.shortCircuit and not (result is not None):
                break
        return value if checkResult else None

    def __str__(self):
        return 'Any[validators={}, circuit={}, allowEmpty={}]'.format(
            self.validators, self.shortCircuit, self.allowEmpty)
    
    def __repr__(self) -> str:
        return str(self)

    def name(self):
        return 'AnyValidator'


class TypeValidator(AbstractValidator):
    """ Validator that checks if a variable is of given type """

    def __init__(self, tp):
        """ Creates a new type validator from a given type
        
        Parameters
        ----------
        tp :
            The type which the value is validated against
        """
        super().__init__()
        self.tp = tp

    def _validate(self, value, level:int):
        """ Returns True iff value is of a given type, False otherwise """ 
        return value if isinstance(value, self.tp) else None

    def __str__(self):
        return 'Type[type={}]'.format(self.tp)
    
    def __repr__(self) -> str:
        return str(self)

    def name(self):
        return 'TypeValidator'


class ListValidator(AbstractValidator):
    """ Creates a checker that checks if a variable is a of a given type
    and if all children (when iterated) satisfy a a another checker. """

    def __init__(self, validator, removeIfNone:bool=True):
        """ Creates a new list validator

        Parameters
        ----------
        validator : AbstractValidator
            The validator used to validate all objects in the list
        removeIfNone : bool
            Whether to remove all values that are None from the list.
            The default value is True.
        """
        super().__init__()
        self.validator = validator
        self.removeIfNone = removeIfNone

    def _validate(self, value, level:int):
        if not isinstance(value, Iterable):
            return None
        newValues = (self.validator.validate(val, level) for val in value)
        return ([val for val in newValues if val is not None]
            if self.removeIfNone else [newValues])

    def __str__(self):
        return 'List[validator={}, removeIfNone={}]'.format(
            self.validator, self.removeIfNone)
    
    def __repr__(self) -> str:
        return str(self)

    def name(self):
        return 'ListValidator'

class TupleValidator(AbstractValidator):
    def __init__(self, validators, allowEmpty:bool=True, shortCircuit:bool=True, matchLength:bool=True):
        super().__init__()
        self.matchLength = matchLength
        self.allowEmpty = allowEmpty
        self.shortCircuit = shortCircuit
        self.validators = validators

    def _validate(self, value, level:int):
        # must be of instance tuple
        if not isinstance(value, tuple):
            return None
        # the case in which no validators specified
        if not self.validators:
            return value if self.allowEmpty else None
        if self.matchLength and len(value) != len(self.validators):
            return None
        
        result = tuple(validator.validate(v, level) for validator, v in
            zip(self.validators, value))
        return result

    def __str__(self):
        return 'Tuple[validators={}, circuit={}, allowEmpty={}, matchLength={}]'.format(
            self.validators, self.shortCircuit, self.allowEmpty, self.matchLength)
    
    def __repr__(self) -> str:
        return str(self)

    def name(self):
        return 'TupleValidator'


class ValueValidator(AbstractValidator):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def _validate(self, value, level:int):
        return value if value == self.value else None

    def __str__(self):
        return 'Value[value={}]'.format(self.value)
    
    def __repr__(self) -> str:
        return str(self)

    def name(self):
        return 'ValueValidator'


class DictValidator(AbstractValidator):
    def __init__(self, keyValidator=None, valueValidator=None, tupleValidator=None, removeIfNone:bool=True):
        super().__init__()
        self.keyValidator = keyValidator if keyValidator is not None else PassValidator()
        self.valueValidator = valueValidator if valueValidator is not None else PassValidator()
        self.tupleValidator = tupleValidator if tupleValidator is not None else PassValidator()
        self.removeIfNone = removeIfNone

    def _validate(self, value, level:int):
        if not isinstance(value, dict):
            return None
        tupleGenerator = (self.tupleValidator.validate(
            (self.keyValidator.validate(k, level), self.valueValidator.validate(v, level)), level
        ) for k, v in value.items())
        if self.removeIfNone:
            tupleGenerator = (t for t in tupleGenerator if t is not None)
        return {k: v for k, v in tupleGenerator}

    def __str__(self):
        return 'Dict[keyValidator={}, valueValidator{}, tupleValidator={}, removeIfNone={}]'.format(
            self.keyValidator, self.valueValidator, self.tupleValidator, self.removeIfNone)
    
    def __repr__(self) -> str:
        return str(self)

    def name(self):
        return 'DictValidator'

if __name__ == '__main__':
    print('FILE: args.py')
    print('This file does not have any functionality on its own.')

    def unitTest(inp, validator):
        print('Input:', inp)
        print('Validator:', validator)
        result = validator(inp)
        print('Result:', result)

    unitTest(
        [1, 'str', 3],
        ListValidator(ReplaceValidator(TypeValidator(int), 3))
    )
