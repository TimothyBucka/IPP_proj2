# author: Timotej Bucka (xbucka00)

from Error import Error

class Frame:
    """
    Class that represents a frame.
    """

    def __init__(self) -> None:
        """
        Constructor for the Frame class.
        """

        self.data = {}  # {name: [value, type]} - type: None if not initialized, nil if nil
    
    def add_variable(self, var):
        """
        Adds a variable to the data dictionary.
        If the variable already exists, prints an error.
        @param var: name of the variable
        """

        if self.data.get(var) != None:
            Error.print_error(Error.semantic, "Variable already exists")
        self.data[var] = [None, None]

    def get_variable(self, var):
        """
        Returns the value of the variable.
        If the variable does not exist, prints an error.
        @param var: name of the variable
        @return: array of value and type of the variable eg: data = {"a": [1, "int"]} -> [1, "int"]
        """

        if self.data.get(var) == None:
            Error.print_error(Error.variable, "Variable does not exist")
        return self.data[var]

    def set_variable(self, var, value, type):
        """
        Sets the value and type of the variable.
        If the variable does not exist, prints an error.
        @param var: name of the variable
        @param value: value of the variable
        @param type: type of the variable
        Eg: data = {"a": [1, "int"]} -> set_variable("a", 2, "int") -> data = {"a": [2, "int"]}
        """
        
        if self.data.get(var) == None:
            Error.print_error(Error.variable, "Variable does not exist")
        self.data[var] = [value, type]

    def __repr__(self) -> str:
        s = "{\n"
        for key, value in self.data.items():
            s += f"\t{key}: {str(value[0])} [{str(value[1])}]\n"
        s += "}"
        return s