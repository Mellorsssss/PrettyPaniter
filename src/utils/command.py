class Command(object):
    """
    Base class for Command of copy/paste/undo

    Attributes:
        app: the main application
        canvas: receiver
        backup: previous state
    """
    def __init__(self):
        self.app= None
        self.canvas = None
        self.backup = None

    def __init__(self, _app, _canvas):
        self.app = _app
        self.canvas = _canvas
        self.backup = None

    def set_app(self, _app):
        self.app = _app
        return self

    def set_canvas(self, _canvas):
        self.canvas = _canvas
        return self

    def execute(self) ->bool:
        '''
        execute concrete command
        :return: true if this command needed to be added to history
        '''
        return False

    def undo(self):
        if self.backup is not None:
            self.canvas.set_context(self.backup)


