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
                return int(symb.text), "int"
            elif symb.type == "bool":
                if symb.text == "true":
                    return True, "bool"
                elif symb.text == "false":
                    return False, "bool"
            elif symb.type == "string":
                new_string = ""
                for s in symb.text.split("\\"):
                    if len(s) >= 3 and s[0:3].isnumeric():
                        n = chr(int(s[0:3]))
                        s = n+s[3:]
                    new_string += s
                return new_string, "string"
            elif symb.type == "nil":
                return None, "nil"
            elif symb.type == "float":
                return float.fromhex(symb.text), "float"
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
        pass

    def SUB(self, program):
        pass

    def MUL(self, program):
        pass

    def IDIV(self, program):
        pass

    def LT(self, program):
        pass
    
    def GT(self, program):
        pass

    def EQ(self, program):
        pass

    def AND(self, program):
        pass

    def OR(self, program):
        pass

    def NOT(self, program):
        pass

    def INT2CHAR(self, program):
        pass

    def STRI2INT(self, program):
        pass

    ########################### Input and output operations ###########################
    def READ(self, program):
        pass

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