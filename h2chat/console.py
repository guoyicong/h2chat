import cmd
import readline

import client


# command line interface for the client
class Console(cmd.Cmd):

    def __init__(self):
       
        cmd.Cmd.__init__(self) 
        self.prompt = '(chat)'
        self.intro = 'Welcome to the chat'
        self.client = None


    # command definitions
    def do_login(self, arg):
        
        self.client = client.Client(*parse(arg))

    def do_send(self, arg):

        self.client.send_message(*parse(arg))

    def do_end(self, arg):

        self.client.end_chat()
     

# parse the arguments    
def parse(arg):
    return tuple(map(str, arg.split(maxsplit = 1)))


if __name__ == '__main__':
    console = Console()
    console.cmdloop()
