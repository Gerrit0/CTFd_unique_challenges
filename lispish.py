"""
LispIsh - a simple lisp-like language.

>>> compiler = LispIsh()
>>> expression = compiler.parse('(xor 5 6)')
>>> expression.evaluate({ 'XOR': lambda v: v[0] ^ v[1] })
3

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

LispIshTypes = Union[str, int, bool]
LispIshMethods = Dict[str, Callable[[List[LispIshTypes]], LispIshTypes]]

def _get_indent(size: int) -> str:
    """ Helper to get indented code
    >>> _get_indent(1)
    '\\t'
    >>> _get_indent(2)
    '\\t\\t'
    """
    return '\t' * size

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
            self._die(f"Expected <{text}> but found <{self.text[self.index]}>")
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

    def _parse_name(self) -> str:
        """ Parses a LispIsh name, allows ASCII letters or a hyphen, but hyphens
        may not be the first character in a name.

        >>> LispIsh().parse('(-bad)')
        Traceback (most recent call last):
            ...
        LispIshParseError: Expected a name but found <-> at 1:1
        """
        self._consume_ws()
        name = []
        while self._peek() in string.ascii_letters or self._peek() == '-' and name:
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
                self._die("Expected a string, number, or function call but got <{self._peek()>")
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
