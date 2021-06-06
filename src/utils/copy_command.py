from utils.command import Command


class CopyCommand(Command):
    def __init__(self):
        super(CopyCommand, self).__init__()

    def __init__(self, _app, _canvas):
        super(CopyCommand, self).__init__(_app, _canvas)

    def execute(self) ->bool:
        if self.canvas.get_selection() is None:
            return False

        self.app.set_clipboard(self.canvas.get_selection().clone())
        return False
