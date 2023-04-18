# author: Timotej Bucka (xbucka00)

import sys

class Error:
    """
    Class that contains all the error codes and a function for printing errors.
    """

    success = 0
    param = 10            # wrong or missing parameter
    in_files = 11         # problem with input file
    out_files = 12        # problem with output file
    XML_format = 31       # invalid XML format
    XML_structure = 32    # invalid XML structure (wrong order etc)
    semantic = 52         # udefined label, redefined variable, etc
    operands = 53         # invalid operands types
    variable = 54         # non-existing variable
    frame = 55            # non-existing frame
    missing_value = 56    # missing value in variable or on stack
    type = 57             # divison by zero, invalid exit code, etc
    string = 58           # invalid string operation
    internal = 99

    @staticmethod
    def print_error(err_code, message):
        """
        Prints an error message to stderr and exits the program with the given error code.
        @param err_code: error code
        @param message: error message
        """

        print("Error: " + message, file=sys.stderr)
        exit(err_code)
