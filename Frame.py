from Error import Error

class Frame:
    def __init__(self) -> None:
        self.data = {}  # {name: [value, type]} - type: None if not initialized, nil if nil
    
    def add_variable(self, var):
        if self.data.get(var) != None:
            Error.print_error(Error.semantic, "Variable already exists")
        self.data[var] = None