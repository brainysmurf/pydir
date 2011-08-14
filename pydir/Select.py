"""
Select Module
Subclasses main Dir class so that it presents user a list of choices,
selection.
"""
from dir.Dir import Dir
from dir.Filer import File_list, File_object
from dir.Menu import Menu, BadArguments
from dir.Console import Output
from dir.Command import Shell_Emulator as Shell
from colorama import Fore, Back, Style
import os

class SelectList(File_list):
    def __init__(self, _list):
        File_list.__init__(self, "", [item for item in _list if item], klass=SelectObject)

class SelectObject(File_object):
    def __init__(self, path, name, i):
        """
        Detect whether name has a path built-in or not,
        if so it sets path accordingly
        """
        _extra = None
        if isinstance(name, list):
            _extra = name[1:]
            name = name[0]
        p, n = os.path.split(name)
        if p:
            File_object.__init__(self, p, n, i)
        else:
            File_object.__init__(self, path, name, i)
        self._extra = _extra
    
class SelectMenu(Menu):
    def tutorial(self, *args):
        pass

    def name(self, *args):
        if not args or not args[0]:
            raise BadArguments("name what?")
        else:
            input(self.cntrl.get_item(args[0]).full_path)
            if self.cntrl.pages:
                return self.cntrl.pages['page']
            else:
                return None
        

class SelectDir(Dir):

    def __init__(self, _list, header=None):
        """
        Override completely is easier
        """
        self.ask_pound()
        self.header=header
        self.reset_pages()
        self.user_sorter = 'name'
        self.menu = SelectMenu(self)
        self.command = Shell(avoid_recursion="projects")
        self.last_mod_time = None
        self.output = Output()
        self.initialize()
        self._list = SelectList(_list)

    def ask_pound(self):
        self.ask = '-> '

    def initialize(self):
        self._selection = None

    def list_current_directory(self):
        return self._list

    def pre_process(self, file_name):
        return True

    def print_header(self):
        print(Fore.BLACK + Back.WHITE + " {} ".format(self.header) + Style.RESET_ALL)        

    def post_process(self, file_name, num, max_length):
        return (num, file_name)
        
    def parse_input(self, user_input):
        # TODO: I shouldn't need to call this, find out what is throwing off the indexing
        self.list_current_directory().do_indexing()
        
        this = None
        if user_input.isdigit() and not user_input.startswith('name '):
            # "make it so" feature: user types in number and we figure out if it's a cd or an open statement
            which = int(user_input)
            if which < len(self.list_current_directory()):
                this = self.list_current_directory().index(which)
                    
        try:
            handled = self.menu._parse(user_input)
        except BadArguments:
            handled = False
            input("Bad arguments")

        if not handled:
            if user_input == self.quit_request:
                self.stop()
            elif user_input.startswith('+'):
                if self.pages:
                    return self.pages['page'] + user_input.count('+')
                else:
                    input("No page to turn")
            elif user_input.startswith('-'):
                if self.pages:
                    return self.pages['page'] - user_input.count('-')
                else:
                    input("No page to turn")

        if this:
            self.got_good_input(self.derive_selectable_from_this(this))
            self.stop()

    def derive_selectable_from_this(self, _this):
        """
        You can override me
        """
        raise NotImplemented

    def got_good_input(self, _input):
        """
        Sets _selection
        """
        self._selection = _input

    def execute(self):
        """
        
        """
        self.clear_screen()

        # Send control to list current directory, or the currage page, if available
        if not self.pages:
            self.list_items()
        else:
            self.list_current_page()

        page = self.parse_input(input(self.ask))

        # Clean up pages state as appropriate
        if page is None: 
            # If parse_input returns None (page 0 is legitimate number)
            self.reset_pages()
        else:
            self.turn_page(page)

    def stop(self):
        Dir.stop(self)
        return self._selection

    def select(self, using):
        self.derive_selectable_from_this = using
        return self.start().stop()

        

