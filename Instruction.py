from Argument import Argument
from Error import Error
from Frame import Frame
import sys

class Instruction:
    def __init__(self, order, opcode, args) -> None:
        self.order = order
        self.opcode = opcode
        self.args = args
        self.nof_args = len(args)
    
    def run(self, program): # will return index of next instruction
        try:
            func = getattr(self, self.opcode)
        except AttributeError:
            Error.print_error(Error.semantic, "line " + str(self.order) + ": Unknown opcode")
        next_step = func(program)
        
        return next_step


    def split_frame_name(self, variable):
        frame = variable.split("@")[0]
        name = variable.split("@")[1]
        if frame != "GF" and frame != "LF" and frame != "TF":
            Error.print_error(Error.semantic, "line " + str(self.order) + ": Invalid frame")
        return frame, name

    def get_value_from_symb(self, symb, gf, lfs, tf):
        # if constant
        if symb.type != "var":
            if symb.type == "int":
                return [int(symb.text), "int"]
            elif symb.type == "bool":
                if symb.text == "true":
                    return [True, "bool"]
                elif symb.text == "false":
                    return [False, "bool"]
            elif symb.type == "string":
                new_string = ""
                for s in symb.text.split("\\"):
                    if len(s) >= 3 and s[0:3].isnumeric():
                        n = chr(int(s[0:3]))
                        s = n+s[3:]
                    new_string += s
                return [new_string, "string"]
            elif symb.type == "nil":
                return [None, "nil"]
            elif symb.type == "float":
                return [float.fromhex(symb.text), "float"]
        # if variable
        else:
            frame, name = self.split_frame_name(symb.text)
            if frame == "GF":
                if gf.data.get(name) == None:
                    Error.print_error(Error.variable, "line " + str(self.order) + ": Variable does not exist")
                return gf.data[name]
            elif frame == "LF":
                if (len(lfs) == 0):
                    Error.print_error(Error.frame, "line " + str(self.order) + ": LF stack is empty")
                elif lfs[-1].data.get(name) == None:
                    Error.print_error(Error.variable, "line " + str(self.order) + ": Variable does not exist")
                return lfs[-1].data[name]
            elif frame == "TF":
                if tf == None:
                    Error.print_error(Error.frame, "line " + str(self.order) + ": TF is uninitialized")
                elif tf.data.get(name) == None:
                    Error.print_error(Error.variable, "line " + str(self.order) + ": Variable does not exist")
                return tf.data[name]
        
    def store_value_to_variable(self, variable, value, type, gf, lfs, tf):
        frame, name = self.split_frame_name(variable.text)
        if frame == "GF":
            if gf.data.get(name) == None:
                Error.print_error(Error.variable, "line " + str(self.order) + ": Variable does not exist")
            gf.data[name] = [value, type]
        elif frame == "LF":
            if (len(lfs) == 0):
                Error.print_error(Error.frame, "line " + str(self.order) + ": LF stack is empty")
            lfs[-1].data[name] = [value, type]
        elif frame == "TF":
            if tf == None:
                Error.print_error(Error.frame, "line " + str(self.order) + ": TF is uninitialized")
            tf.data[name] = [value, type]

    ################################# Frames and stack #################################
    def MOVE(self, program):
        value, type = self.get_value_from_symb(self.args[1], program.gf, program.lfs, program.tf)
        self.store_value_to_variable(self.args[0], value, type, program.gf, program.lfs, program.tf)
    
    def CREATEFRAME(self, program):
        program.tf = Frame()

    def PUSHFRAME(self, program):
        if program.tf == None:
            Error.print_error(Error.frame, "line " + str(self.order) + " PUSHFRAME: TF is uninitialized")
        program.lfs.append(program.tf)
        program.tf = None

    def POPFRAME(self, program):
        if len(program.lfs) == 0:
            Error.print_error(Error.frame, "line " + str(self.order) + " POPFRAME: LF stack is empty")
        program.tf = program.lfs.pop()

    def DEFVAR(self, program):
        frame, name = self.split_frame_name(self.args[0].text)
        if frame == "GF":
            if program.gf.data.get(name) != None:
                Error.print_error(Error.semantic, "line " + str(self.order) + " DEFVAR: Variable already exists")
            program.gf.data[name] = [None, None]
        elif frame == "LF":
            if (len(program.lfs) == 0):
                Error.print_error(Error.frame, "LF stack is empty")
            if program.lfs[-1].data.get(name) != None:
                Error.print_error(Error.semantic, "line " + str(self.order) + " DEFVAR: Variable already exists")
            program.lfs[-1].data[name] = [None, None]
        elif frame == "TF":
            if program.tf == None:
                Error.print_error(Error.frame, "line " + str(self.order) + " DEFVAR: TF is uninitialized")
            if program.tf.data.get(name) != None:
                Error.print_error(Error.semantic, "line " + str(self.order) + " DEFVAR: Variable already exists")
            program.tf.data[name] = [None, None]

    def CALL(self, program):
        if program.labels.get(self.args[0].text) == None:
            Error.print_error(Error.semantic, "line " + str(self.order) + " CALL: Label does not exist")
        program.call_stack.append(self.order)
        return program.labels[self.args[0].text]

    def RETURN(self, program):
        if len(program.call_stack) == 0:
            Error.print_error(Error.missing_value, "line " + str(self.order) + " RETURN: Call stack is empty")
        return program.call_stack.pop()
    
    #################################### Data stack ####################################
    def PUSHS(self, program):
        value, type = self.get_value_from_symb(self.args[0], program.gf, program.lfs, program.tf)
        program.data_stack.append([value, type])

    def POPS(self, program):
        if len(program.data_stack) == 0:
            Error.print_error(Error.missing_value, "line " + str(self.order) + " POPS: Data stack is empty")
        value, type = program.data_stack.pop()
        self.store_value_to_variable(self.args[0], value, type, program.gf, program.lfs, program.tf)

    ################## Arithmetic, boolean and convertion operations ##################
    def ADD(self, program):
        val1 = self.get_value_from_symb(self.args[1], program.gf, program.lfs, program.tf)
        val2 = self.get_value_from_symb(self.args[2], program.gf, program.lfs, program.tf)
        if val1[1] != "int" or val2[1] != "int":
            Error.print_error(Error.operands, "line " + str(self.order) + " ADD: Wrong type of arguments")
        self.store_value_to_variable(self.args[0], val1[0] + val2[0], "int", program.gf, program.lfs, program.tf)

    def SUB(self, program):
        val1 = self.get_value_from_symb(self.args[1], program.gf, program.lfs, program.tf)
        val2 = self.get_value_from_symb(self.args[2], program.gf, program.lfs, program.tf)
        if val1[1] != "int" or val2[1] != "int":
            Error.print_error(Error.operands, "line " + str(self.order) + " SUB: Wrong type of arguments")
        self.store_value_to_variable(self.args[0], val1[0] - val2[0], "int", program.gf, program.lfs, program.tf)

    def MUL(self, program):
        val1 = self.get_value_from_symb(self.args[1], program.gf, program.lfs, program.tf)
        val2 = self.get_value_from_symb(self.args[2], program.gf, program.lfs, program.tf)
        if val1[1] != "int" or val2[1] != "int":
            Error.print_error(Error.operands, "line " + str(self.order) + " MUL: Wrong type of arguments")
        self.store_value_to_variable(self.args[0], val1[0] * val2[0], "int", program.gf, program.lfs, program.tf)

    def IDIV(self, program):
        val1 = self.get_value_from_symb(self.args[1], program.gf, program.lfs, program.tf)
        val2 = self.get_value_from_symb(self.args[2], program.gf, program.lfs, program.tf)
        if val1[1] != "int" or val2[1] != "int":
            Error.print_error(Error.operands, "line " + str(self.order) + " IDIV: Wrong type of arguments")
        if val2[0] == 0:
            Error.print_error(Error.type, "line " + str(self.order) + " IDIV: Division by zero")
        self.store_value_to_variable(self.args[0], int(val1[0] / val2[0]), "int", program.gf, program.lfs, program.tf)

    def LT(self, program):
        val1 = self.get_value_from_symb(self.args[1], program.gf, program.lfs, program.tf)
        val2 = self.get_value_from_symb(self.args[2], program.gf, program.lfs, program.tf)
        if (val1[1] not in ["int", "bool", "string"] or val2[1] not in ["int", "bool", "string"]) or (val1[1] != val2[1]):
            Error.print_error(Error.operands, "line " + str(self.order) + " LT: Wrong type of arguments")
        self.store_value_to_variable(self.args[0], val1[0] < val2[0], "bool", program.gf, program.lfs, program.tf)
    
    def GT(self, program):
        val1 = self.get_value_from_symb(self.args[1], program.gf, program.lfs, program.tf)
        val2 = self.get_value_from_symb(self.args[2], program.gf, program.lfs, program.tf)
        if (val1[1] not in ["int", "bool", "string"] or val2[1] not in ["int", "bool", "string"]) or (val1[1] != val2[1]):
            Error.print_error(Error.operands, "line " + str(self.order) + " GT: Wrong type of arguments")
        self.store_value_to_variable(self.args[0], val1[0] > val2[0], "bool", program.gf, program.lfs, program.tf)

    def EQ(self, program):
        val1 = self.get_value_from_symb(self.args[1], program.gf, program.lfs, program.tf)
        val2 = self.get_value_from_symb(self.args[2], program.gf, program.lfs, program.tf)
        if (val1[1] not in ["int", "bool", "string"] or val2[1] not in ["int", "bool", "string"]) or (val1[1] != val2[1]):
            Error.print_error(Error.operands, "line " + str(self.order) + " EQ: Wrong type of arguments")
        self.store_value_to_variable(self.args[0], val1[0] == val2[0], "bool", program.gf, program.lfs, program.tf)

    def AND(self, program):
        val1 = self.get_value_from_symb(self.args[1], program.gf, program.lfs, program.tf)
        val2 = self.get_value_from_symb(self.args[2], program.gf, program.lfs, program.tf)
        if val1[1] != "bool" or val2[1] != "bool":
            Error.print_error(Error.operands, "line " + str(self.order) + " AND: Wrong type of arguments")
        self.store_value_to_variable(self.args[0], val1[0] and val2[0], "bool", program.gf, program.lfs, program.tf)

    def OR(self, program):
        val1 = self.get_value_from_symb(self.args[1], program.gf, program.lfs, program.tf)
        val2 = self.get_value_from_symb(self.args[2], program.gf, program.lfs, program.tf)
        if val1[1] != "bool" or val2[1] != "bool":
            Error.print_error(Error.operands, "line " + str(self.order) + " OR: Wrong type of arguments")
        self.store_value_to_variable(self.args[0], val1[0] or val2[0], "bool", program.gf, program.lfs, program.tf)

    def NOT(self, program):
        val1 = self.get_value_from_symb(self.args[1], program.gf, program.lfs, program.tf)
        if val1[1] != "bool":
            Error.print_error(Error.operands, "line " + str(self.order) + " NOT: Wrong type of arguments")
        self.store_value_to_variable(self.args[0], not val1[0], "bool", program.gf, program.lfs, program.tf)

    def INT2CHAR(self, program):
        val1 = self.get_value_from_symb(self.args[1], program.gf, program.lfs, program.tf)
        if val1[1] != "int":
            Error.print_error(Error.operands, "line " + str(self.order) + " INT2CHAR: Wrong type of arguments")
        try:
            self.store_value_to_variable(self.args[0], chr(val1[0]), "string", program.gf, program.lfs, program.tf)
        except ValueError:
            Error.print_error(Error.operands, "line " + str(self.order) + " INT2CHAR: Cant convert int to char. Int out of range")

    def STRI2INT(self, program):
        val1 = self.get_value_from_symb(self.args[1], program.gf, program.lfs, program.tf)
        val2 = self.get_value_from_symb(self.args[2], program.gf, program.lfs, program.tf)
        if val1[1] != "string" or val2[1] != "int":
            Error.print_error(Error.operands, "line " + str(self.order) + " STRI2INT: Wrong type of arguments")
        try:
            char = val1[0][val2[0]]
        except IndexError:
            Error.print_error(Error.string, "line " + str(self.order) + " STRI2INT: Index out of range")
        self.store_value_to_variable(self.args[0], ord(char), "int", program.gf, program.lfs, program.tf) 

    ########################### Input and output operations ###########################
    def READ(self, program):
        # check if variable is defined by trying to store value to it
        self.store_value_to_variable(self.args[0], None, None, program.gf, program.lfs, program.tf)

        in_type = self.args[1].text
        # check type before input
        if in_type not in ["int", "bool", "string", "float"]:
            Error.print_error(Error.type, "line " + str(self.order) + " READ: Invalid type argument")
        
        in_val = input()
        if in_type == "int":
            try:
                in_val = int(in_val)
            except ValueError:
                self.store_value_to_variable(self.args[0], None, "nil", program.gf, program.lfs, program.tf)
                return
        elif in_type == "bool":
            if in_val.lower() == "true":
                in_val = True
            else:
                in_val = False
        elif in_type == "string":
            pass
        elif in_type == "float":
            try:
                in_val = float(in_val)
            except ValueError:
                try:
                    in_val = float.fromhex(in_val)
                except ValueError:
                    self.store_value_to_variable(self.args[0], None, "nil", program.gf, program.lfs, program.tf)
                    return

        self.store_value_to_variable(self.args[0], in_val, in_type, program.gf, program.lfs, program.tf)

    def WRITE(self, program):
        pass

    ################################ String operations ################################
    def CONCAT(self, program):
        pass

    def STRLEN(self, program):
        pass

    def GETCHAR(self, program):
        pass

    def SETCHAR(self, program):
        pass

    ##################################### Type  #####################################
    def TYPE(self, program):
        pass

    ################################## Flow control ##################################
    def LABEL(self, program):
        pass # label already checked in Program

    def JUMP(self, program):
        if program.labels.get(self.args[0].text) == None:
            Error.print_error(Error.semantic, "line " + str(self.order) + " JUMP: Label does not exist")
        return program.labels[self.args[0].text]

    def JUMPIFEQ(self, program):
        if program.labels.get(self.args[0].text) == None:
            Error.print_error(Error.semantic, "line " + str(self.order) + " JUMPIFEQ: Label does not exist")
        
        val1 = self.get_value_from_symb(self.args[1], program.gf, program.lfs, program.tf)
        val2 = self.get_value_from_symb(self.args[2], program.gf, program.lfs, program.tf)

        if (val1[1] != val2[1]) and (val1[1] != "nil" and val2[1] != "nil"):
            Error.print_error(Error.operands, "line " + str(self.order) + " JUMPIFEQ: Invalid operands")
        if val1 == val2:
            return program.labels[self.args[0].text]

    def JUMPIFNEQ(self, program):
        if program.labels.get(self.args[0].text) == None:
            Error.print_error(Error.semantic, "line " + str(self.order) + " JUMPIFNEQ: Label does not exist")
        
        val1 = self.get_value_from_symb(self.args[1], program.gf, program.lfs, program.tf)
        val2 = self.get_value_from_symb(self.args[2], program.gf, program.lfs, program.tf)
        if (val1[1] != val2[1]) and (val1[1] != "nil" and val2[1] != "nil"):
            Error.print_error(Error.operands, "line " + str(self.order) + " JUMPIFNEQ: Invalid operands")
        if val1 != val2:
            return program.labels[self.args[0].text]

    def EXIT(self, program):
        val, type = self.get_value_from_symb(self.args[0], program.gf, program.lfs, program.tf)
        if type != "int":
            Error.print_error(Error.operands, "line " + str(self.order) + " EXIT: Invalid operands")
        if val < 0 or val > 49:
            Error.print_error(Error.type, "line " + str(self.order) + " EXIT: Invalidvalue (0-49)")
        sys.exit(val)

    #################################### Debugging ####################################
    def DPRINT(self, program):
        pass
    
    def BREAK(self, program):
        pass

    def __repr__(self) -> str:
        str = f"{self.order} -- {self.opcode}"
        for arg in self.args:
            str += f"\n\t{arg.order} {arg.type} {arg.text}"
        return str+"\n"