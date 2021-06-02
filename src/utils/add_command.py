from utils.command import Command


class AddCommand(Command):
    def __init__(self):
        super(AddCommand, self).__init__()
        self.id = None

    def __init__(self, _app, _canvas):
        super(AddCommand, self).__init__(_app, _canvas)
        self.id = None

    def set_id(self, _id):
        self.id = _id
        return self

    def execute(self) ->bool:
        self.backup = self.canvas.get_context()
        self.canvas.add_item(self.canvas.get_selection(), self.id)
        return True
