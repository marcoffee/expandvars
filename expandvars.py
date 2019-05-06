# Author: Arijit basu (https://arijitbasu.in)
# Ref: https://www.gnu.org/software/bash/manual/html_node/Shell-Parameter-Expansion.html

from os import environ


def _valid_char(char):
    return char.isalnum() or char == "_"


def _isint(val):
    try:
        int(val)
        return True
    except ValueError:
        return False


class Expander(object):
    """A class that helps expanding variables.
    
    Params:
        vars_ (str): System variables to expand

    Example usage: ::
        
        val = Expander('${FOO:-default}:${BAR:2:10}').result
    """

    def __init__(self, vars_):
        self._result = []
        self._buffr = []
        if len(vars_) == 0:
            return
        variter = iter(vars_)
        c = next(variter)
        if c == "$":
            self.expand_var(variter)
            return
        self.expand_val(variter, c)

    def _next_or_done(self, variter):
        try:
            return next(variter)
        except StopIteration:
            self.process_buffr()
            return

    def process_buffr(self):
        if not self._buffr:
            return
        if ":" not in self._buffr:
            self._result.extend(environ.get("".join(self._buffr), ""))
            self._buffr.clear()
            return

        x, y = "".join(self._buffr).split(":", 1)
        x, y = x.strip(), y.strip()

        if y.startswith("+"):
            y = y[1:]
            if x in environ:
                self._result.extend(y)
            self._buffr.clear()
            return

        if y.startswith("-") or y.startswith("="):
            _y = y[0]
            y = y[1:]
            self._result.extend(environ.get(x, y))
            if _y == "=" and x not in environ:
                environ.update({x: y})
            self._buffr.clear()
            return

        if ":" not in y:
            if not y.isalnum():
                raise ValueError("bad substitution")
            if not _isint(y):
                self._result.extend(environ.get(x, ""))
                self._buffr.clear()
                return
            self._result.extend(environ.get(x, "")[int(y) :])
            self._buffr.clear()
            return

        y, z = y.split(":", 1)
        y, z = y.strip(), z.strip()

        if not z or z.isalpha():
            self._buffr.clear()
            return

        if not z.isalnum() and not _isint(z):
            raise ValueError(
                "FOO: {}: syntax error: operand expected (error token is {})".format(
                    z, repr(z)
                )
            )

        z = int(z)
        if z < 0:
            raise ValueError("{}: substring expression < 0".format(z))

        if not y or not y.isdigit():
            self._result.extend(environ.get(x, "")[:z])
            self._buffr.clear()
            return
        y = int(y)
        self._result.extend(environ.get(x, "")[y : y + z])
        self._buffr.clear()

    def expand_var(self, variter):
        if self._buffr:
            self.process_buffr()
        c = self._next_or_done(variter)
        if not c:
            self._result.append("$")
            return

        if c == "{":
            self.expand_modifier_var(variter)
            return

        while _valid_char(c):
            self._buffr.append(c)
            c = self._next_or_done(variter)
            if not c:
                return
        self.process_buffr()
        if c == "$":
            self.expand_var(variter)
        self.expand_val(variter, c)

    def expand_modifier_var(self, variter):
        if self._buffr:
            self.process_buffr()
        try:
            c = next(variter)
            while c != "}":
                self._buffr.append(c)
                c = next(variter)
        except StopIteration:
            raise ValueError('{}: "{" was never closed.'.format("".join(self._buffr)))

        c = self._next_or_done(variter)
        if not c:
            return
        if c == "$":
            self.expand_var(variter)
        self.expand_val(variter, c)

    def expand_val(self, variter, c):
        if self._buffr:
            self.process_buffr()
        while c and c != "$":
            self._result.append(c)
            c = self._next_or_done(variter)
        if c:
            self.expand_var(variter)

    @property
    def result(self):
        return "".join(self._result)


def expandvars(vars_):
    """Expand system variables Unix style.

    NOTE: Unlike `Expander` class, the argument to this
    function must start with "$".

    Params:
        vars_ (str): System variables to expand.
    
    Returns:
        str: Expanded values.
    
    Example usage: ::
        
        val = expandvars('${FOO:-default}:${BAR:2:10}')
    """
    if not vars_.startswith("$"):
        return vars_
    return Expander(vars_).result
