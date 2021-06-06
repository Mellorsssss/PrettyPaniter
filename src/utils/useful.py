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

    def execute(self) -> bool:
        self.backup = self.canvas.get_context()
        self.canvas.add_item(self.canvas.get_selection(), self.id)
        return True


class CommandHistory(object):
    '''
    Command History stores the command_list
    '''
    def __init__(self):
        self.command_list: list[Command] = []

    def push_command(self, commnd: Command):
        self.command_list.append(commnd)

    def pop_command(self):
        if len(self.command_list) == 0:
            return None
        return self.command_list.pop()

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


class RemoveCommand(Command):
    def __init__(self):
        super(RemoveCommand, self).__init__()

    def __init__(self, _app, _canvas):
        super(RemoveCommand, self).__init__(_app, _canvas)

    def execute(self) ->bool:
        self.backup = self.canvas.get_context()
        self.canvas.remove_selection()
        return True # no item added, status unchanged


class UndoCommand(Command):
    def __init__(self):
        super(UndoCommand, self).__init__()

    def __init__(self, _app, _canvas):
        super(UndoCommand, self).__init__(_app, _canvas)

    def execute(self) ->bool:
        self.app.undo_command()
        return False