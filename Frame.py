from Error import Error

class Frame:
    def __init__(self) -> None:
        self.data = {}  # {name: [value, type]} - type: None if not initialized, nil if nil
    
    # TODO refactor code to use these functions
    def add_variable(self, var):
        if self.data.get(var) != None:
            Error.print_error(Error.semantic, "Variable already exists")
        self.data[var] = None

    def get_variable(self, var):
        pass

    def set_variable(self, var, value):
        pass

    def __repr__(self) -> str:
        s = "{\n"
        for key, value in self.data.items():
            s += f"\t{key}: {str(value[0])} [{str(value[1])}]\n"
        s += "}"
        return s