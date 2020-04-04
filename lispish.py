"""
LispIsh - a simple lisp-like language.

>>> compiler = LispIsh()
>>> expression = compiler.parse('(xor 5 6)')
>>> expression.evaluate({ 'XOR': lambda v: v[0] ^ v[1] })
3

Some functions are built in. See the _defaults dict below for which ones.

>>> expression = compiler.parse('(= 5 6)')
>>> expression.evaluate({})
False
>>> expression = compiler.parse('(<= 5 6 7)')
>>> expression.evaluate({})
True
>>> expression = compiler.parse('(- 5 (- 1))')
>>> expression.evaluate({})
6

Errors may be raised when parsing or when evaluating. If the parse string is
not valid, an instance of LispIshParseError will be raised. When evaluating,
if a function does not exist, an instance of LispIshRuntimeError will be raised.

>>> compiler = LispIsh()
>>> compiler.parse('(non-matching-paren 1 2')
Traceback (most recent call last):
    ...
LispIshParseError: Ran off end of input at 1:23

The keys of the dict provided to evaluate should be upper cased for normalization.
Parse names are case-insensitive. (xor 1 2) === (XOR 1 2)
When emitting parsed code, indentation may not be preserved, but method name case
will be preserved.

This is used to store the internal representation of challenge requirements.
"""

from typing import List, Dict, Callable, Union, NoReturn
import json
import string
from functools import wraps

LispIshTypes = Union[str, int, bool]
LispIshMethods = Dict[str, Callable[[List[LispIshTypes]], LispIshTypes]]

def _get_indent(size: int) -> str:
    """ Helper to get indented code
    >>> _get_indent(1)
    '    '
    >>> _get_indent(2)
    '        '
    """
    return '    ' * size

class LispIshError(Exception):
    """ Base class for errors raised by this module """
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
    def __str__(self):
        return f"{self.message}"

class LispIshParseError(LispIshError):
    """ Error raised when a parse fails """
    def __init__(self, message: str, line: int, col: int):
        super().__init__(message)
        self.line = line
        self.col = col

    def __str__(self):
        return f"{self.message} at {self.line}:{self.col}"

class LispIshRuntimeError(LispIshError):
    """ Error raised when a problem is encountered when evaluating an expression """

class LispIshValue:
    """ Describes some kind of value that can be evaluated """
    def emit(self, indent: int = 0) -> str:
        """ Emit this value as code that could be re-parsed into the same value """
        raise NotImplementedError()

    def evaluate(self, function_map: LispIshMethods) -> LispIshTypes:
        """ Evaluate this value, resulting in some python type """
        raise NotImplementedError()

class LispIshNumber(LispIshValue):
    """ Type safe container for an int represented in the source """
    def __init__(self, value: int):
        super().__init__()
        self.value = value

    def evaluate(self, function_map: LispIshMethods) -> LispIshTypes:
        return self.value

    def emit(self, indent: int = 0) -> str:
        return _get_indent(indent) + f"{self.value}"

class LispIshString(LispIshValue):
    """ Type safe container for a string represented in the source """
    def __init__(self, value: str):
        super().__init__()
        self.value = value

    def evaluate(self, function_map: LispIshMethods) -> LispIshTypes:
        return self.value

    def emit(self, indent: int = 0) -> str:
        """ Emit a string, try to avoid escaping quotes.
        >>> LispIshString("hi there").emit()
        "'hi there'"
        >>> LispIshString("he's got it").emit()
        '"he\\'s got it"'
        """
        # Be a bit smarter about strings, try to avoid escaping quotes
        if "'" in self.value:
            return _get_indent(indent) + json.dumps(self.value)
        return _get_indent(indent) + repr(self.value)

class LispIshMethod(LispIshValue):
    """ Container for a method call in the source """
    def __init__(self, name: str, args: List[LispIshValue]):
        super().__init__()
        self.name = name
        self.canonical_name = name.upper()
        self.args = args

    def evaluate(self, function_map: LispIshMethods) -> LispIshTypes:
        if self.canonical_name in function_map:
            return function_map[self.canonical_name]([
                arg.evaluate(function_map) for arg in self.args
            ])
        if self.canonical_name in _defaults:
            return _defaults[self.canonical_name]([
                arg.evaluate(function_map) for arg in self.args
            ])
        raise LispIshRuntimeError(f"The method <{self.name}> is not defined.")

    def emit(self, indent: int = 0) -> str:
        r""" Smart emit that doesn't cause unnecessary indentation but is readable.
        >>> lisp = LispIsh()
        >>> code = lisp.parse("(and (or 0 1 2))")
        >>> print(code.emit().replace('\t', '    '))
        (and (or
            0
            1
            2))
        """
        if len(self.args) == 0:
            return _get_indent(indent) + f"({self.name})"
        if len(self.args) == 1:
            return _get_indent(indent) + f"({self.name} {self.args[0].emit(indent).lstrip()})"
        return '\n'.join([
            _get_indent(indent) + f"({self.name}",
            *[arg.emit(indent + 1) for arg in self.args[:-1]],
            f"{self.args[-1].emit(indent + 1)})"
        ])

def _assertArgs(arg, num: int, name: str):
    if len(arg) < num:
        raise LispIshRuntimeError(f"({name}) was passed {len(arg)} arguments, expected at least {num}.")

def _notFn(arg) -> bool:
    if len(arg) != 1:
        raise LispIshRuntimeError(f"(not) function was passed {len(arg)} arguments, expected 1.")
    return not arg[0]

# Note: Not limited to numbers.
def _eqFn(arg) -> bool:
    _assertArgs(arg, 2, '=')
    return len(set(arg)) == 1

def _neqFn(arg) -> bool:
    """ Checks if every arg is distinct from every other arg.
    >>> _neqFn([1, 2, 3])
    True
    >>> _neqFn([1, 2, 1])
    False
    """
    _assertArgs(arg, 2, '/=')
    return len(set(arg)) == len(arg)

def _gtFn(arg) -> bool:
    """ Checks if each arg is smaller than the previous.
    >>> _gtFn([3, 2, 1])
    True
    >>> _gtFn([3, 1, 2])
    False
    """
    _assertArgs(arg, 2, '>')
    for i in range(1, len(arg)):
        if arg[i - 1] <= arg[i]:
            return False
    return True

def _ltFn(arg) -> bool:
    """ Checks if each arg is greater than the previous.
    >>> _ltFn([1, 2, 3])
    True
    >>> _ltFn([1, 3, 2])
    False
    """
    _assertArgs(arg, 2, '<')
    for i in range(1, len(arg)):
        if arg[i - 1] >= arg[i]:
            return False
    return True

def _geqFn(arg) -> bool:
    """ Checks if each arg is less than or equal to the previous arg.
    >>> _geqFn([2, 2, 1])
    True
    >>> _geqFn([3, 2, 1])
    True
    >>> _geqFn([1, 2])
    False
    """
    _assertArgs(arg, 2, '>=')
    for i in range(1, len(arg)):
        if arg[i - 1] < arg[i]:
            return False
    return True

def _leqFn(arg) -> bool:
    """ Checks if each arg is greater than or equal to the previous arg.
    >>> _leqFn([1, 1, 2])
    True
    >>> _leqFn([1, 2, 1])
    False
    """
    _assertArgs(arg, 2, '<=')
    for i in range(1, len(arg)):
        if arg[i - 1] > arg[i]:
            return False
    return True

def _diffFn(arg) -> bool:
    """ Takes the difference of each argument.
    >>> _diffFn([1, 2, 3])
    -4
    >>> _diffFn([5, 1, -1])
    5
    >>> _diffFn([1])
    -1
    """
    _assertArgs(arg, 1, '-')
    if len(arg) == 1:
        return -arg[0]
    result = arg[0]
    for item in arg[1:]:
        result -= item
    return result

def _maxFn(arg) -> bool:
    _assertArgs(arg, 1, 'max')
    return max(arg)

def _minFn(arg) -> bool:
    _assertArgs(arg, 1, 'min')
    return min(arg)

_defaults = {
    'NOT': _notFn,
    'AND': all,
    'OR': any,
    '=': _eqFn,
    '/=': _neqFn,
    '>': _gtFn,
    '<': _ltFn,
    '>=': _geqFn,
    '<=': _leqFn,
    '+': sum,
    '-': _diffFn,
    'MAX': _maxFn,
    'MIN': _minFn,
}

class LispIsh:
    """ Parser for the LispIsh language, which is like lisp, but simpler.
    Double a number:
    >>> lisp = LispIsh()
    >>> method = lisp.parse("(double 7)")
    >>> method.evaluate({ "DOUBLE": lambda x: x[0] * 2 })
    14
    """

    def __init__(self):
        self.text, self.index, self.line, self.col = "", 0, 1, 0

    def parse(self, text: str):
        """ Parse the given text as a method. """
        self.text = text
        self.index = self.col = 0
        self.line = 1
        method = self._parse_method()
        self._consume_ws()
        self._expect_eof()
        return method

    def _die(self, message: str) -> NoReturn:
        raise LispIshParseError(message, self.line, self.col)

    def _peek(self) -> str:
        if self.index == len(self.text):
            self._die("Ran off end of input")
        return self.text[self.index]

    def _eof(self) -> bool:
        return self.index == len(self.text)

    def _consume(self) -> str:
        if self._peek() == '\n':
            self.line += 1
            self.col = 0
        else:
            self.col += 1
        self.index += 1
        return self.text[self.index - 1]

    def _expect(self, text: str) -> str:
        if self._peek() != text:
            self._die(f"Expected <{text}> but found <{self._peek()}>")
        return self._consume()

    def _expect_eof(self):
        if not self._eof():
            self._die(f"Expected <EOF> but found <{self._peek()}>")

    def _consume_ws(self):
        while not self._eof() and self._peek() in ' \t\r\n':
            self._consume()

    def _parse_method(self) -> LispIshMethod:
        self._consume_ws()
        self._expect('(')
        name = self._parse_name()
        args = self._parse_args()
        self._consume_ws()
        self._expect(')')
        return LispIshMethod(name, args)

    _NAME_CHARS = set(string.ascii_letters + '<=>/+-')

    def _parse_name(self) -> str:
        """ Parses a LispIsh name, allows ASCII letters, or one of <=>/+-
        """
        self._consume_ws()
        name = []
        while self._peek() in LispIsh._NAME_CHARS:
            name.append(self._consume())
        if not name:
            self._die(f"Expected a name but found <{self._peek()}>")
        return ''.join(name)

    def _parse_args(self) -> List[LispIshValue]:
        args = []
        self._consume_ws()
        while self._peek() != ')':
            if self._peek() == '(':
                args.append(self._parse_method())
            elif self._peek() in string.digits:
                args.append(self._parse_int())
            elif self._peek() in '"\'':
                args.append(self._parse_str())
            else:
                self._die(f"Expected a string, number, or function call but got <{self._peek()}>")
            self._consume_ws()
        return args

    def _parse_int(self) -> LispIshNumber:
        self._consume_ws()
        data = []
        while self._peek() in string.digits:
            data.append(self._consume())
        if not data:
            self._die(f"Expected a number but got <{self._peek()}>")
        return LispIshNumber(int(''.join(data)))

    def _parse_str(self) -> LispIshString:
        self._consume_ws()
        data = []
        escaped = False
        if self._peek() in '"\'':
            end = self._consume()
        else:
            self._die(f"Expected the start of a string but got <{self._peek()}>")

        while escaped or self._eof() or self._peek() != end:
            if self._eof():
                self._die("Unclosed string ran off end of input")
            if self._peek() == '\\':
                self._consume()
                if escaped:
                    data.append('\\')
                    escaped = False
                else:
                    escaped = True
                continue
            data.append(self._consume())
            escaped = False
        self._consume()
        return LispIshString(''.join(data))

if __name__ == '__main__':
    import doctest
    doctest.testmod()
