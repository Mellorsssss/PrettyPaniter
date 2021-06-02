from utils.command import Command


class UndoCommand(Command):
    def __init__(self):
        super(UndoCommand, self).__init__()

    def __init__(self, _app, _canvas):
        super(UndoCommand, self).__init__(_app, _canvas)

    def undo(self):
        pass
