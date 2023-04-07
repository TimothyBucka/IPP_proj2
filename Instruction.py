from Argument import Argument
from Error import Error

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
        func(program)

    ################################# Frames and stack #################################
    def MOVE(self, program):
        pass
    
    def CREATEFRAME(self, program):
        pass

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