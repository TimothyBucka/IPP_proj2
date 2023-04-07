from Argument import Argument
from Error import Error
from Frame import Frame
from Instruction import Instruction
import xml.etree.ElementTree as ET

class Program:
    def __init__(self, instream) -> None:
        self.instram = instream
        self.instructions = []
        self.nof_instructions = 0
        self.labels = {} # {label_name: index in self.instructions}
        self.gf = Frame()
        self.lfs = []
        self.tfs = []
    
    def parse_XML(self, source_file):
        try:
            tree = ET.parse(source_file)
        except ET.ParseError:
            Error.print_error(Error.XML_format, "XML parse error")
        root = tree.getroot()

        if root.tag != "program":
            Error.print_error(Error.XML_structure, "Missing program tag")
        if root.attrib.get("language") != "IPPcode23":
            Error.print_error(Error.XML_format, "Wrong language")

        if len(root.attrib) == 2:
            if root.attrib.get("name") == None and root.attrib.get("description") == None:
                Error.print_error(Error.XML_format, "Invalid program attributes")
        elif len(root.attrib) == 3:
            if root.attrib.get("name") == None or root.attrib.get("description") == None:
                Error.print_error(Error.XML_format, "Invalid program attributes")
        elif len(root.attrib) > 3:
            Error.print_error(Error.XML_format, "Invalid program attributes")

        for child in root:
            if child.tag != "instruction":
                Error.print_error(Error.XML_structure, "Wrong tag instead of instruction")
            if len(child.attrib) == 2:
                if child.attrib.get("order") == None or child.attrib.get("opcode") == None:
                    Error.print_error(Error.XML_format, "Invalid instruction attributes")
            else:
                Error.print_error(Error.XML_format, "Invalid number of instruction attributes")

            if (child.attrib.get("order").isnumeric() and int(child.attrib.get("order")) > 0) == False:
                Error.print_error(Error.XML_structure, "Invalid instruction order")

            args = []
            for arg in child:
                if arg.tag != "arg1" and arg.tag != "arg2" and arg.tag != "arg3":
                    Error.print_error(Error.XML_structure, "Wrong argument tag")
                if len(arg.attrib) != 1:
                    Error.print_error(Error.XML_format, "Invalid argument attributes")
                if arg.attrib.get("type") == None:
                    Error.print_error(Error.XML_format, "Invalid argument attributes")
                args.append(Argument(int(arg.tag[-1]), arg.attrib.get("type"), arg.text))
            args.sort(key=lambda x: x.order)

            # check for duplicate order of arguments
            if len([a.order for a in args]) != len(set([a.order for a in args])):
                Error.print_error(Error.XML_structure, "Invalid argument order")

            instruction = Instruction(int(child.attrib.get("order")), child.attrib.get("opcode"), args)
            if self.check_instruction_args(instruction):
                self.instructions.append(instruction)
        
        # check for duplicate order of instructions
        if len([i.order for i in self.instructions]) != len(set([i.order for i in self.instructions])):
            Error.print_error(Error.XML_structure, "Invalid instruction order")
        self.instructions.sort(key=lambda x: x.order)

        self.nof_instructions = len(self.instructions)

        # add correct order to instructions and create labels dictionary
        for i in range(self.nof_instructions):
            self.instructions[i].order = i+1
            if self.instructions[i].opcode == "LABEL":
                if self.labels.get(self.instructions[i].args[0].text) != None:
                    Error.print_error(Error.XML_structure, "Duplicate label")
                self.labels[self.instructions[i].args[0].text] = i+1

    def check_instruction_args(self, instruction):
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
        instr_num = 0
        while instr_num < self.nof_instructions:
            next_num = self.instructions[instr_num].run(self)
            if next_num == -1:
                instr_num += 1
            else:   # jump to label
                instr_num = next_num
