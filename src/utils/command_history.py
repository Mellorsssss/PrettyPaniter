from utils.command import Command


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
