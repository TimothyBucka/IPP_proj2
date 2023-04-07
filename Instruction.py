from Argument import Argument
from Error import Error
from Frame import Frame

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
            Error.print_error(Error.semantic, "Unknown opcode")
        next_step = func(program)
        
        return -1 if next_step == None else next_step


    def splt_frame_name(self, variable):
        frame = variable.split("@")[0]
        name = variable.split("@")[1]
        if frame != "GF" and frame != "LF" and frame != "TF":
            Error.print_error(Error.semantic, "Invalid frame")
        return frame, name

    def get_value_from_symb(self, symb, gf, lfs, tf):
        # if constant
        if symb.type != "var":
            if symb.type == "int":
                return int(symb.text)
            elif symb.type == "bool":
                if symb.text == "true":
                    return True
                elif symb.text == "false":
                    return False
            elif symb.type == "string":
                new_string = ""
                for s in symb.text.split("\\"):
                    if len(s) >= 3 and s[0:3].isnumeric():
                        n = chr(int(s[0:3]))
                        s = n+s[3:]
                    new_string += s
                return new_string
            elif symb.type == "nil":
                return None
            elif symb.type == "float":
                return float.fromhex(symb.text)
        # if variable
        else:
            frame, name = self.splt_frame_name(symb)
            if frame == "GF":
                if gf.data.get(name) == None:
                    Error.print_error(Error.symb, "Variable does not exist")
                return gf.data.get(name)
            elif frame == "LF":
                if (len(lfs) == 0):
                    Error.print_error(Error.frame, "LF stack is empty")
                return lfs[-1].data.get(name)
            elif frame == "TF":
                if tf == None:
                    Error.print_error(Error.frame, "TF stack is empty")
                return tf.data.get(name)
        
    def store_value_to_variable(self, variable, value, gf, lfs, tf):
        frame, name = self.splt_frame_name(variable)
        if frame == "GF":
            if gf.data.get(name) == None:
                Error.print_error(Error.variable, "Variable does not exist")
            gf.data[name] = value
        elif frame == "LF":
            if (len(lfs) == 0):
                Error.print_error(Error.frame, "LF stack is empty")
            lfs[-1].data[name] = value
        elif frame == "TF":
            if tf == None:
                Error.print_error(Error.frame, "TF stack is empty")
            tf.data[name] = value

    ################################# Frames and stack #################################
    def MOVE(self, program):
        value = self.get_value_from_symb(self.args[1], program.gf, program.lfs, program.tf)
        self.store_value_to_variable(self.args[0], value, program.gf, program.lfs, program.tf)
    
    def CREATEFRAME(self, program):
        program.tf = Frame()

    def PUSHFRAME(self, program):
        pass

    def POPFRAME(self, program):
        pass

    def DEFVAR(self, program):
        pass

    def CALL(self, program):
        pass

    def RETURN(self, program):
        pass
    
    #################################### Data stack ####################################
    def PUSHS(self, program):
        pass

    def POPS(self, program):
        pass

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
        pass

    def JUMP(self, program):
        pass

    def JUMPIFEQ(self, program):
        pass

    def JUMPIFNEQ(self, program):
        pass

    def EXIT(self, program):
        pass

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