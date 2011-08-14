from pydir.Console import Output
from pydir.Menu import PydirMenu
from pydir.Dir import Pydir
from pydir.Dir import PydirShell
from pydir.Tutor import TutorInfo
from pydir.Dir import SelectPydir
import os
from colors import red
import textwrap
from AppleScriptWrapper.Basic import get_front_app

class TutorialSelect(SelectPydir):
    def __init__(self, _list, tutor_info, output, header=None, paths=False):
        SelectDir.__init__(self, _list, header=header, paths=paths)
        self.output = output
        self.tutor_info = tutor_info
        
    def list_items(self, header=None):
        SelectDir.list_items(self, header=header)
        for line in self.output.tutor_wrapped_message:
            print(red(line))

class TutorialOutput(Output):
    def __init__(self, _list):
        self.tutor_message = ""
        self.tutor_wrapped_message = []
        Output.__init__(self, _list)

    def set_message(self, m):
        self.tutor_message = m
    
    def calc_size(self):
        w, h = Output.calc_size(self)
        if self.tutor_message:
            self.tutor_wrapped_message = textwrap.wrap(self.tutor_message, width=w)
            h   -= (len(self.tutor_wrapped_message))
        return w, h
    
class TutorialMenu(PydirMenu):
    def basic(self, *args):
        """
        Change to 'basic' tutorial.

        You'll learn the basics of navigation and tagging.
        """
        self.cntrl.tutor_info.change_mode("basic")

    def intermediate(self, *args):
        """
        Change to 'intermediate' tutorial.

        You'll learn how to manage files with projects.
        """
        self.cntrl.tutor_info.change_mode("intermediate")

    def main(self, *args):
        """
        Goes to the current project's main menu.
        """
        old_proj = self.cntrl.current_project
        self.cntrl.update_tutor(old_proj)
        DirMenu.main(self, *args)

    def manyfiles(self, *args):
        """
        tutorizemenu <no arguments>

        'Creates a series of randomly-named files in the current directory.'
        """

        def random_file_names(how_many):
            import random

            for h in range(how_many):
                l = random.randint(6, 50)
                chr_list = [chr( (ord('a')-1) + random.randint(1, 26)) for t in range(l)]
                if len(chr_list) > 10:
                    where_spaces = [random.randint(6, l-4 if l > 6+4 else 7) for t in range(random.randint(1, 3))]
                    last = 0
                    for w in where_spaces:
                        if not w - 1 == last and not w == l:
                            chr_list[w] = ' '
                        last = w
                ext = "".join([chr( (ord('a')-1) + random.randint(1, 26)) for t in range(3)])
                yield "{}.{}".format("".join(chr_list), ext)
            yield "Documents.txt"

        how_many = int(self.cntrl.output.height * self.cntrl.output.columns * 2.5)
        for name in random_file_names(how_many):
            f = open(name, 'w')        
        

class TutorialShell(PydirShell):
    
    def _drop(self, command):
        """ drop to the shell and back again """
        get_front_app().keystroke("drop;{};dir -tutorial {}\n".format(command, self.cntrl.tutor_info.where))

class TutorialDir(Pydir):

    def __init__(self):
        Pydir.__init__(self, menu_class=TutorialMenu)
        self.set_current_directory(os.path.expanduser('~'))
        self.tutor_info = TutorInfo()
        self.user_command = TutorialShell(self)
        self.menu.basic()
        self.output = TutorialOutput(self.list_current_directory())
        self.list_current_directory().do_indexing()

    def start(self, path):
        """
        Same as dir but without set_current_directory because I want to always start at same place every time
        ->path is therefore ignored.
        """
        self.update_tutor([]) # tells it to take the first thing available
        return Dir.start(self, path)

    def set_message(self, m):
        self.message = m
        self.output.set_message(m)

    def update_tutor(self, check):
        result = self.tutor_info.update_tutor(check)
        if result:
            self.set_message(result)
        
    def list_items(self, header=None):
        Dir.list_items(self, header=header)
        for line in self.output.tutor_wrapped_message:
            print(red(line))

    def list_current_page(self, header=None):
        Dir.list_current_page(self, header=header)
        for line in self.output.tutor_wrapped_message:
            print(red(line))

    def parse_input(self, user_input):
        self.update_tutor(user_input.split(' ')[0])
        result = Dir.parse_input(self, user_input)
        self.update_tutor(self.current_directory)
        return result

    def select_wrapper(self, _list, using, *args, header=None, **kwargs):
        return Dir.select_wrapper(self, _list, using, self.tutor_info, self.output,
                                  *args, header=header, klass=TutorialSelect, **kwargs)

    def tutorial(self, on):
        if on:
            raise BadArguments("Already on!")
        else:
            self.stop()

    def _done_default(self):
        self.message = "Any file that has the return symbol instead of number\ncan be opened just by hitting return.\nIf it's a file, it'll open, if it's a directory, it'll navigate there.\n\nGet to the parent directory back by typing '..'"

    def stop(self):
        #TODO: remove tutor dir, go back to default
        Dir.stop(self)

