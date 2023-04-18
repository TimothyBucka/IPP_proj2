# author: Timotej Bucka (xbucka00)

from Error import Error
from Program import Program
import argparse
import sys
import os

class Interpreter:
    """
    Singleton class that parses arguments and runs the program.
    """

    def __new__(cls):
        """
        Creates singleton instance
        """

        if not hasattr(cls, 'instance'):
            cls.instance = super(Interpreter, cls).__new__(cls)
        return cls.instance 
    
    def __init__(self):
        """
        Constructor for the Interpreter class.
        """

        self.args = None
        self.source_file = None
        self.input_file = None
        self.program = None
        self.parse_arguments()

    def parse_arguments(self):
        """
        Parses command-line arguments by using argparse module.
        Sets self.args to the parsed arguments.
        Sets self.source_file to the correct source (file or stdi.n).
        Sets self.input_file to the correct input (file or stdin)
        """

        parser = argparse.ArgumentParser()
        parser.add_argument("--source", help="source file", nargs = 1)
        parser.add_argument("--input", help="input file", nargs = 1)
        parser.add_argument("--stats", help="stats file", nargs = 1)
        parser.add_argument("--insts", help="number of executed instructions", nargs = '?')
        parser.add_argument("--hot", help="order number of instruction smth smth", nargs = '?')
        parser.add_argument("--vars", help="maximum number of variables defined at one moment", nargs = '?')
        parser.add_argument("--frequent", help="most frequent instructions", nargs = '?')
        parser.add_argument("--string", help="write string string to stats file", nargs = 1)
        parser.add_argument("--eol", help="write end of line to stats file", nargs = '?')

        try:
            self.args = parser.parse_args()
        except SystemExit as exc:
            if exc.code:
                Error.print_error(Error.param, "Wrong arguments")
            else:   # is help
                if len(sys.argv)-1 > 1:
                    Error.print_error(Error.param, "Arguments with --help")
                exit(Error.success)

        if self.args.source == None and self.args.input == None:
            Error.print_error(Error.param, "No source and no input file")
        
        if self.args.source != None:
            if not os.access(self.args.source[0], os.R_OK):
                Error.print_error(Error.in_files, "Source file is not readable")
            self.source_file = self.args.source[0]
        else:
            self.source_file = sys.stdin
        
        if self.args.input != None:
            try:
                self.input_file = open(self.args.input[0], "r")
            except IOError:
                Error.print_error(Error.in_files, "Input file is not readable")
        else:
            self.input_file = sys.stdin

    def run(self):
        """
        Creates Program instance.
        Parses XML file.
        Runs the program.
        """

        self.program = Program(self.input_file)
        self.program.parse_XML(self.source_file)
        self.program.run()
