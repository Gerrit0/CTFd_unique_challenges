import sys
from io import TextIOWrapper, BytesIO

class CaptureExec:
    """ Helper class to wrap user scripts that print to stdout.
    """

    def __init__(self, script):
        self._script = script

    def run(self, extra_script="", local_vars={}):
        # Setup, capture stdout
        old, sys.stdout = sys.stdout, TextIOWrapper(
            BytesIO(), sys.stdout.encoding)
        # Run user script, note that builtins are enabled. Untrusted input
        # should not be passed to this function.
        exec("{}\n{}".format(self._script, extra_script), {}, local_vars)
        # Get the output
        sys.stdout.seek(0)
        out = sys.stdout.read()
        sys.stdout.close()
        sys.stdout = old
        return out
