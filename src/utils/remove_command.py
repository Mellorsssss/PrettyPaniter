from utils.command import Command


class RemoveCommand(Command):
    def __init__(self):
        super(RemoveCommand, self).__init__()

    def __init__(self, _app, _canvas):
        super(RemoveCommand, self).__init__(_app, _canvas)

    def execute(self) ->bool:
        self.backup = self.canvas.get_context()
        self.canvas.remove_selection()
        return True # no item added, status unchanged
