# author: Timotej Bucka (xbucka00)

class Argument:
    """
    Class that represents an argument of an instruction.
    """

    def __init__(self, order, type, text):
        """
        Constructor for the Argument class.
        @param order: order of the argument
        @param type: type of the argument
        @param text: text of the argument
        Eg: <arg2 type="var">LF@val</arg2> -> Argument(2, "var", "LF@val")
        """
        
        self.order = order
        self.type = type
        self.text = text