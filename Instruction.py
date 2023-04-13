from Argument import Argument
from Error import Error
from Frame import Frame
import sys

class Instruction:
    # static variables
    called_instructions = 0

    def __init__(self, order, opcode, args) -> None:
        self.order = order
        self.opcode = opcode
        self.args = args
        self.nof_args = len(args)
    
    def run(self, program): # will return index of next instruction
        type(self).called_instructions += 1

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
                try:
                    return [int(symb.text), "int"]
                except ValueError:
                    Error.print_error(Error.XML_structure, "line " + str(self.order) + ": Invalid int value")
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
                    for key, value in {"&lt;": "<", "&gt;": ">", "&amp;": "&"}.items():
                        new_string = new_string.replace(key, value)
                return [new_string, "string"]
            elif symb.type == "nil":
                return [None, "nil"]
            elif symb.type == "float":
                try:
                    return [float(symb.text), "float"]
                except ValueError:
                    try:
                        return [float.fromhex(symb.text), "float"]
                    except ValueError:
                        Error.print_error(Error.XML_structure, "line " + str(self.order) + ": Invalid float value")
                    
        # if variable
        else:
            frame, name = self.split_frame_name(symb.text)
            if frame == "GF":
                return gf.get_variable(name)
            elif frame == "LF":
                if (len(lfs) == 0):
                    Error.print_error(Error.frame, "line " + str(self.order) + ": LF stack is empty")
                return lfs[-1].get_variable(name)
            elif frame == "TF":
                if tf == None:
                    Error.print_error(Error.frame, "line " + str(self.order) + ": TF is uninitialized")
                return tf.get_variable(name)
        
    def store_value_to_variable(self, variable, value, type, gf, lfs, tf):
        frame, name = self.split_frame_name(variable.text)
        if frame == "GF":
            gf.set_variable(name, value, type)
        elif frame == "LF":
            if (len(lfs) == 0):
                Error.print_error(Error.frame, "line " + str(self.order) + ": LF stack is empty")
            lfs[-1].set_variable(name, value, type)
        elif frame == "TF":
            if tf == None:
                Error.print_error(Error.frame, "line " + str(self.order) + ": TF is uninitialized")
            tf.set_variable(name, value, type)

    ################################# Frames and stack #################################
    def MOVE(self, program):
        value, type = self.get_value_from_symb(self.args[1], program.gf, program.lfs, program.tf)
        if type == None:
            Error.print_error(Error.missing_value, "Variable not initialized")
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
            program.gf.add_variable(name)
        elif frame == "LF":
            if (len(program.lfs) == 0):
                Error.print_error(Error.frame, "LF stack is empty")
            program.lfs[-1].add_variable(name)
        elif frame == "TF":
            if program.tf == None:
                Error.print_error(Error.frame, "line " + str(self.order) + " DEFVAR: TF is uninitialized")
            program.tf.add_variable(name)

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
        if type == None:
            Error.print_error(Error.missing_value, "Variable not initialized")
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
            Error.print_error(Error.string, "line " + str(self.order) + " INT2CHAR: Cant convert int to char. Int out of range")

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
        
        try:
            in_val = input()
        except EOFError:
            self.store_value_to_variable(self.args[0], None, "nil", program.gf, program.lfs, program.tf)
            return
        
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
        val = self.get_value_from_symb(self.args[0], program.gf, program.lfs, program.tf)
        s = val[0]

        if val[1] == None:
            Error.print_error(Error.missing_value, "line " + str(self.order) + " WRITE: Wrong type of arguments")
            
        if val[1] == "float":
            s = float.hex(s)
        if val[1] == "bool":
            if s:
                s = "true"
            else:
                s = "false"
        elif val[1] == "nil":
            s = ""
        
        print(s, end="")


    ################################ String operations ################################
    def CONCAT(self, program):
        val1 = self.get_value_from_symb(self.args[1], program.gf, program.lfs, program.tf)
        val2 = self.get_value_from_symb(self.args[2], program.gf, program.lfs, program.tf)
        if val1[1] != "string" or val2[1] != "string":
            Error.print_error(Error.operands, "line " + str(self.order) + " CONCAT: Wrong type of arguments")
        self.store_value_to_variable(self.args[0], val1[0] + val2[0], "string", program.gf, program.lfs, program.tf)

    def STRLEN(self, program):
        val = self.get_value_from_symb(self.args[1], program.gf, program.lfs, program.tf)
        if val[1] != "string":
            Error.print_error(Error.operands, "line " + str(self.order) + " STRLEN: Wrong type of arguments")
        self.store_value_to_variable(self.args[0], len(val[0]), "int", program.gf, program.lfs, program.tf)

    def GETCHAR(self, program):
        val1 = self.get_value_from_symb(self.args[1], program.gf, program.lfs, program.tf)
        val2 = self.get_value_from_symb(self.args[2], program.gf, program.lfs, program.tf)
        if val1[1] != "string" or val2[1] != "int":
            Error.print_error(Error.operands, "line " + str(self.order) + " GETCHAR: Wrong type of arguments")
        try:
            self.store_value_to_variable(self.args[0], val1[0][val2[0]], "string", program.gf, program.lfs, program.tf)
        except IndexError:
            Error.print_error(Error.string, "line " + str(self.order) + " GETCHAR: Index out of range")

    def SETCHAR(self, program):
        var_string = self.get_value_from_symb(self.args[0], program.gf, program.lfs, program.tf)
        var_index = self.get_value_from_symb(self.args[1], program.gf, program.lfs, program.tf)
        var_char = self.get_value_from_symb(self.args[2], program.gf, program.lfs, program.tf)

        if var_string[1] != "string" or var_index[1] != "int" or var_char[1] != "string":
            Error.print_error(Error.operands, "line " + str(self.order) + " SETCHAR: Wrong type of arguments")
        if len(var_char[0]) == 0:
            Error.print_error(Error.string, "line " + str(self.order) + " SETCHAR: Empty string")
        if len(var_char[0]) > 1:
            var_char[0] = var_char[0][0]
        try:
            var_string[0] = var_string[0][:var_index[0]] + var_char[0] + var_string[0][var_index[0]+1:]
        except IndexError:
            Error.print_error(Error.string, "line " + str(self.order) + " SETCHAR: Index out of range")
        self.store_value_to_variable(self.args[0], var_string[0], "string", program.gf, program.lfs, program.tf)

    ##################################### Type  #####################################
    def TYPE(self, program):
        val = self.get_value_from_symb(self.args[1], program.gf, program.lfs, program.tf)
        if val[1] == None: # variable not initialized
            self.store_value_to_variable(self.args[0], "", "string", program.gf, program.lfs, program.tf)
        else:
            self.store_value_to_variable(self.args[0], val[1], "string", program.gf, program.lfs, program.tf)

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
        val = self.get_value_from_symb(self.args[0], program.gf, program.lfs, program.tf)
        s = val[0]
        if val[1] == "bool":
            if s:
                s = "true"
            else:
                s = "false"
        elif val[1] == "nil":
            s = "nil"
        elif val[1] == None:
            s = "%UNINITIALIZED%"

        print("--- DPRINT: ", end="", file=sys.stderr)
        if self.args[0].type == "var":
            print(self.args[0].text + ": ", end="", file=sys.stderr)
        print(s, end="", file=sys.stderr)
        print(" ---", file=sys.stderr)
    
    def BREAK(self, program):
        print("\n--- BREAK ---", file=sys.stderr)
        print(f"Instruction order: {self.order}", file=sys.stderr)
        print(f"Number of run instructions: {type(self).called_instructions}", file=sys.stderr)
        print("GF:", file=sys.stderr)
        print(program.gf, file=sys.stderr)
        print("LFs:", file=sys.stderr)
        print("[", file=sys.stderr)
        for i in range(len(program.lfs)-1, -1, -1):
            print(f"LF{i}: ", end="", file=sys.stderr)
            print(program.lfs[i], end="", file=sys.stderr)
            if i != 0:
                print(",", end="", file=sys.stderr)
            print(file=sys.stderr)
            i += 1
        print("]", file=sys.stderr)
        print("TF:", file=sys.stderr)
        print(program.tf, file=sys.stderr)
        print("--- ----- ---\n", file=sys.stderr)


    def __repr__(self) -> str:
        s = f"{self.order} -- {self.opcode}"
        for arg in self.args:
            s += f"\n\t{arg.order} {arg.type} {arg.text}"
        return s+"\n"