from utils.command import Command


class PasteCommand(Command):
    def __init__(self):
        super(PasteCommand, self).__init__()

    def __init__(self, _app, _canvas):
        super(PasteCommand, self).__init__(_app, _canvas)

    def execute(self) ->bool:
        self.backup = self.canvas.get_context()
        if self.app.get_clipboard() is not None:
            self.canvas.add_item(self.app.get_clipboard().clone())
            return True
        return False # no item added, status unchanged
