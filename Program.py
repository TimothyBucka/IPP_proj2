# author: Timotej Bucka (xbucka00)

from Argument import Argument
from Error import Error
from Frame import Frame
from Instruction import Instruction
import sys
import xml.etree.ElementTree as ET

class Program:
    """
    Class representing the program represented by XML file.
    Contains all the instructions and data.
    """

    def __init__(self, instream) -> None:
        """
        Constructor for the Program class.
        @param instream: input stream (stdin/file)
        """

        self.instructions = []
        self.nof_instructions = 0
        self.labels = {}    # {label_name: index in self.instructions}
        self.call_stack = []
        self.data_stack = []   # [[value, type], ...]
        self.gf = Frame()   # always exists
        self.lfs = []   # at the beginning is empty
        self.tf = None  # at the beginning it does not exist

        sys.stdin = instream
    
    def parse_XML(self, source_file):
        """
        Parses the XML file by using ElementTree module.
        Sets self.instructions to the list of instructions.
        Parses the labels and sets self.labels to the dictionary of labels.
        Performs syntactic and semantic checks of the XML file.
        @param source_file: path to the XML file
        """

        try:
            tree = ET.parse(source_file)
        except ET.ParseError:
            Error.print_error(Error.XML_format, "XML parse error")
        root = tree.getroot()

        if root.tag != "program":
            Error.print_error(Error.XML_structure, "Missing program tag")
        if root.attrib.get("language") != "IPPcode23":
            Error.print_error(Error.XML_structure, "Wrong language")

        if len(root.attrib) == 2:
            if root.attrib.get("name") == None and root.attrib.get("description") == None:
                Error.print_error(Error.XML_structure, "Invalid program attributes")
        elif len(root.attrib) == 3:
            if root.attrib.get("name") == None or root.attrib.get("description") == None:
                Error.print_error(Error.XML_structure, "Invalid program attributes")
        elif len(root.attrib) > 3:
            Error.print_error(Error.XML_structure, "Invalid program attributes")

        for child in root:
            if child.tag != "instruction":
                Error.print_error(Error.XML_structure, "Wrong tag instead of instruction")
            if len(child.attrib) == 2:
                if child.attrib.get("order") == None or child.attrib.get("opcode") == None:
                    Error.print_error(Error.XML_structure, "Invalid instruction attributes")
            else:
                Error.print_error(Error.XML_structure, "Invalid number of instruction attributes")

            if (child.attrib.get("order").isnumeric() and int(child.attrib.get("order")) > 0) == False:
                Error.print_error(Error.XML_structure, "Invalid instruction order")

            args = []
            for arg in child:
                if arg.tag != "arg1" and arg.tag != "arg2" and arg.tag != "arg3":
                    Error.print_error(Error.XML_structure, "Wrong argument tag")
                if len(arg.attrib) != 1:
                    Error.print_error(Error.XML_structure, "Invalid argument attributes")
                if arg.attrib.get("type") == None:
                    Error.print_error(Error.XML_structure, "Invalid argument attributes")
                if arg.text == None:
                    arg.text = ""
                args.append(Argument(int(arg.tag[-1]), arg.attrib.get("type"), arg.text.strip()))

            # 1 arg needed and got arg2 or arg3 instead of arg1
            if sum([a.order for a in args]) != sum([i for i in range(1, len(args) + 1)]):
                Error.print_error(Error.XML_structure, "Invalid arguments")

            args.sort(key=lambda x: x.order)

            # check for duplicate order of arguments
            if len([a.order for a in args]) != len(set([a.order for a in args])):
                Error.print_error(Error.XML_structure, "Invalid argument order")

            instruction = Instruction(int(child.attrib.get("order")), str.upper(child.attrib.get("opcode")), args)
            if self.check_instruction_args(instruction):
                self.instructions.append(instruction)
        
        # check for duplicate order of instructions
        order_list = [i.order for i in self.instructions]
        if len(order_list) != len(set(order_list)):
            Error.print_error(Error.XML_structure, "Invalid instruction order")
        self.instructions.sort(key=lambda x: x.order)

        self.nof_instructions = len(self.instructions)

        # add correct order to instructions and create labels dictionary
        for i in range(self.nof_instructions):
            self.instructions[i].order = i
            if self.instructions[i].opcode == "LABEL":
                if self.labels.get(self.instructions[i].args[0].text) != None:
                    Error.print_error(Error.semantic, "Duplicate label")
                self.labels[self.instructions[i].args[0].text] = i

    def check_instruction_args(self, instruction):
        """
        Checks if the instruction has correct number of arguments and if the argument types are correct.
        @param instruction: instruction to be checked
        """

        rules = {
            "MOVE": ["var", "symb"],
            "CREATEFRAME": [],
            "PUSHFRAME": [],
            "POPFRAME": [],
            "DEFVAR": ["var"],
            "CALL": ["label"],
            "RETURN": [],
            "PUSHS": ["symb"],
            "POPS": ["var"],
            "ADD": ["var", "symb", "symb"],
            "SUB": ["var", "symb", "symb"],
            "MUL": ["var", "symb", "symb"],
            "IDIV": ["var", "symb", "symb"],
            "LT": ["var", "symb", "symb"],
            "GT": ["var", "symb", "symb"],
            "EQ": ["var", "symb", "symb"],
            "AND": ["var", "symb", "symb"],
            "OR": ["var", "symb", "symb"],
            "NOT": ["var", "symb"],
            "INT2CHAR": ["var", "symb"],
            "STRI2INT": ["var", "symb", "symb"],
            "READ": ["var", "type"],
            "WRITE": ["symb"],
            "CONCAT": ["var", "symb", "symb"],
            "STRLEN": ["var", "symb"],
            "GETCHAR": ["var", "symb", "symb"],
            "SETCHAR": ["var", "symb", "symb"],
            "TYPE": ["var", "symb"],
            "LABEL": ["label"],
            "JUMP": ["label"],
            "JUMPIFEQ": ["label", "symb", "symb"],
            "JUMPIFNEQ": ["label", "symb", "symb"],
            "EXIT": ["symb"],
            "DPRINT": ["symb"],
            "BREAK": []
        }

        if rules.get(instruction.opcode) == None:
            Error.print_error(Error.XML_structure, "Invalid instruction opcode")

        inst_args = [a.type for a in instruction.args]
        rule_args = rules.get(instruction.opcode)
        if len(inst_args) != len(rule_args):
            Error.print_error(Error.XML_structure, "Invalid number of instruction arguments")
        for i in range(len(inst_args)):
            if rule_args[i] == "symb":
                if inst_args[i] != "var" and inst_args[i] != "int" and \
                   inst_args[i] != "bool" and inst_args[i] != "string" and \
                   inst_args[i] != "nil" and inst_args[i] != "float":
                    Error.print_error(Error.XML_structure, "Invalid instruction argument type")
            elif rule_args[i] != inst_args[i]:
                Error.print_error(Error.XML_structure, "Invalid instruction argument type")

        return True
    
    def run(self):
        """
        Runs the program by executing instructions in order.
        """
        
        instr_num = 0
        while instr_num < self.nof_instructions:
            next_num = self.instructions[instr_num].run(self)   # runs instruction at index with Program instance as argument
            if next_num != None:  # change flow of execution (jump)
                instr_num = next_num
            instr_num += 1
