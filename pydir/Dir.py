#! /usr/bin/env python3

"""
Dir
Keyboard-only navigation system that replaces the Finder and regular command line
Adam Morris
TODO: Fix it so that aliases behave like symlinks in the terminal
"""

from pydir.Command import Shell_Emulator as Shell
from pydir.Console import Output, Overflow
from pydir.Conversion_Dict import Conversion_Dict
from pydir.Menu import PydirMenu, Menu, BadArguments
from pydir.Filer import File_list, File_object
from pydir.Errors import Error_Handler
from pydir.Error_info import error_dict
from pydir.Parser import Parse_Input
from pydir.DirXattr import DirTagger
from AppleScriptWrapper.Basic import get_front_app

import os
import sys
import shlex
import re
from colorama import Fore, Back, Style
from colorama import init as colorama_init
from colors import white, green, \
     cyan, yellow

user_home_directory = os.path.expanduser('~')
path_to_trash       = os.path.expanduser('~/.Trash')

__path__, _ = os.path.split(__file__)


class PydirShell():
    """

    """

    def __init__(self, cntrl):
        self.cntrl = cntrl

    def _which_check(self, command):
        # route to known instance
        return self.cntrl.command._which_check(command)

    def _drop(self, command):
        """ drop to the shell and back again """
        get_front_app().keystroke("{};{};{}\n".format(
                "drop", command, "dir"))
        
    def run_command(self, command):
        """
        Uses _which_check to make sure it's a possible command, drops the program
        """
        verbose = False
        verbose and print("command is {}".format(command))
        if self._which_check(command):
            self.cntrl.stop()
            self._drop(command)
        else:
            self.cntrl.errors.handle_error('command not recognized', command)

class File_object_dir(File_object):
    pydir_ext     = '.▼'
    unknown_ext = '.?'

    def __init__(self, path, name, i):
        File_object.__init__(self, path, name, i)
        self.original_name = self.full_name
        if not self.is_mounted:
            # Extension becomes question mark if it isn't mounted
            self.full_name += self.unknown_ext
        if self.is_directory:
            # Directory gets a bit of eye candy in extension
            self.full_name += self.pydir_ext
        if self.is_link:
            # give links the behaviour of automatically take on ext
            # of target file, given the right conditions
            junk, ext = os.path.splitext(self.real_path)
            if self.ext and ext != self.ext:
                pass  # don't add its own extension
            else:
                self.full_name += ext        
        self.name, self.ext = os.path.splitext(self.full_name)


class Lister:
    def __init__(self, cntrl):
        verbose = False
        self.cntrl = cntrl
        self.reset()
        verbose and input("reset!")
        self._save = None

    def __call__(self):
        if not self._list:
            path = self.cntrl.current_directory
            self._list = File_list(
                path, [item for item in os.listdir(path) if self.cntrl.filter(item)],
                klass=File_object_dir)
        return self._list

    def force_reset(self):
        self._list = []

    def reset(self):
        """
        Resets it only if the conditions are right
        """
        verbose = False
        if not hasattr(self, '_list'):
            self.force_reset()
        elif self._list and not self._list._folder.full_path == self.cntrl.current_directory:
            verbose and print(self._list)
            verbose and print(self._list._folder.full_path)
            verbose and print(self.cntrl.current_directory)
            verbose and input()
            self.force_reset()    

    def save(self, what):
        self._save = what


class AbstractDir():
    quit_request = 'q'
    xattr_signature = "com_mistermorris_pydir"
    
    def __init__(self, menu_class=Menu):
        """
        Init app
        """
        self.ask_pound()
        self._user_saved = None
        self.errors = Error_Handler(error_dict)
        self.command = Shell(avoid_recursion="pydir", errors=self.errors)
        self.user_command = PydirShell(self)
        colorama_init()
        self.input_list = []
        self.reset_pages()
        self.user_filter = None
        self.user_sorter = 'name'
        self.menu = menu_class(self)
        self.last_mod_time = None
        self._project_saved_searches = {}
        self.output = Output()
        
    def set_current_directory(self, path):
        try:
            os.chdir(path)
        except OSError:
            self.errors.handle_error('permission denied', path)

    def __getattribute__(self, name):
        """ Sets up aliases """
        if name == "current_directory":
             return os.getcwd() + os.sep
        elif name == "parent_directory":
            return os.path.split(self.current_directory)[0]
        elif name == "join":
            return os.path.join
        elif name == "split":
            return shlex.split
        elif name == "split_extension":
            return os.path.splitext
        elif name == "last_modified":
            return os.path.getmtime
        else:
            return object.__getattribute__(self, name)

class ApplicationSupport(DirTagger):
    """
    Sets up the defaults for the program
    """
    application_support_path = "{}/Library/Application Support/pydir/user info".format(user_home_directory)

    def __init__(self, cntrl):
        verbose = True
        self.cntrl = cntrl
        path = self.application_support_path
        virgin = False
        p, f = os.path.split(path)
        if not os.path.exists(p):
            virgin = True
            os.mkdir(p)
        if not os.path.exists(path):
            virgin = True
            open(path, 'w') # touch
        DirTagger.__init__(self, path)
        if virgin:
            verbose and print("Adding new project 'default'")
            self.add_project('default')
            verbose and print("Did it work?: {}".format(self.get_projects()))
            defaults = [os.path.expanduser("~/Documents/"), os.path.expanduser("~/Desktop/"), os.path.expanduser("~/Downloads/")]
            for i in range(len(defaults)):
                DirTagger(defaults[i]).tag('default')

    def add_project(self, project_name):
        projects = self.get_projects()
        if isinstance(project_name, list):
            projects.extend(project_name)
        else:
            projects.append(project_name)
        self.set_object('projects', projects)

    def get_projects(self):
        return self.get_object('projects') if self.has('projects') else []

class Pydir(AbstractDir):
    user_home_directory = os.path.expanduser('~')

    def __init__(self, menu_class=PydirMenu):
        self.current_project = 'default'
        self.list_current_directory = Lister(self)
        self._history = []
        self.helper_message = ""
        self._clear_screen = None
        self._saved_default = None
        AbstractDir.__init__(self, menu_class=menu_class)
        self.user_info = ApplicationSupport(self)

    def initialize(self):
        """
        Reset everything to initial state
        Call when menu is wanted
        """
        verbose = False
        self.project_screen()

    def set_helper_message(self, m):
        self.output.set_bottom_message(m)

    def set_current_directory(self, path):
        AbstractDir.set_current_directory(self, path)

    def list_current_projects(self):
        return self.user_info.get_projects()

    def new_project(self, project_name):
        verbose = True
        verbose and print("tagging user_info with project_name")
        self.user_info.add_project(project_name)

    def remove_project(self, project_name):
        # search for items and remove xattr as well?
        self.user_info.remove_tag(project_name)

    def highlight(self, which):
        """
        Interacts with Filer to get the highlight right
        """
        self.list_current_directory().add_or_remove(which)

    def single_out(self, which):
        verbose = False
        verbose and print("single_out")
        self.list_current_directory().single_out(which)
    
    def clear_screen(self):
        if not self._clear_screen:
            self._clear_screen = self.command.run_command('clear')[0].decode()
        print(self._clear_screen, end="")

    def execute(self):
        """
        
        """
        verbose = False
        self.clear_screen()
        old_bottom_message = self.output.bottom_message

        # Send control to list current directory, or the currage page, if available
        if not self.pages:
            self.list_items()
        else:
            self.list_current_page()

        # Send control to manually get info from user, or pop through input_list in case of multiple inputs
        if not self.input_list:
            # TODO: Set up so that input is not called but callable object
            try:
                page = self.parse_input(input(self.ask))
            except KeyboardInterrupt:
                page = None
                if self._history:
                    os.chdir(self._history.pop())  # do it manually to avoid re-entering in history
                else:
                    self.errors.handle_error("keyboard-interrupt")
        else:
            # TODO: Need to implement input_list
            for _ in self.input_list:
                page = self.parse_input(self.input_list.pop(0))

        # Clean up pages state as appropriate
        # parse_input returns None or page number, indicating what to do about pages
        if page is None:  # 0 is a legit page number
            verbose and print('parse_input returned None')
            self.reset_pages()
        else:
            self.set_helper_message(old_bottom_message) # restore it
            self.turn_page(page)

    def start(self, path):
        """
        Endlessly take input, pass to parse_input until self.stop() is triggered
        """
        """
        Smart enough to see if there are pages to display, and throws control appropriately
        TODO: Abstract this away so that input is controlled by object instead
        """
        self.set_current_directory(path)
        self._determine_continue = True

        try:
            while self.determine_continue():

                self.execute()

        except KeyboardInterrupt:
            print()

        return self

    def ask_pound(self):
        self.ask = "$ "

    def ask_plus(self):
        self.ask = "+/- "

    def ask_question(self):
        self.ask = "? "

    def ask_copy(self):
        return self.ask[:]

    def stop(self):
        """ Stop the loop created by start """
        self._determine_continue = False
        with open('/tmp/tee_output.txt', 'w') as f:
            print(self.current_directory, file=f)

    def reset_pages(self):
        self.pages = None

    def turn_page(self, page):
        """

        """
        l = self.pages['list']
        if page < 0: 
            page = 0
        elif page > len(l)-1: 
            page = len(l)-1
        self.pages['page'] = page

    def force_reset(self):
        if hasattr(self.list_current_directory, 'force_reset'):
            self.list_current_directory.force_reset()

    def loop_iteration(self):
        """
        Call whenever a new loop should be indicated
        """
        verbose = False
        self.list_current_directory.reset()  # triggers call to current directory in next line
        verbose and input("reset!")
        self.output.set_list(self.list_current_directory())

    def swap_and_save(self, swap):
        """
        Stores current info internally, ready for call to self.restore()
        """
        self._save = (self.list_current_directory()[:], self.output)
        self._list_current_directory = swap
        self.output = Output(self._list_current_directory)

    def restore(self):
        self._list_current_directory, self.output = self._save

    def determine_continue(self):
        """
        Continue our loop or not?
        """
        self.loop_iteration()
        return self._determine_continue
    
    def is_directory(self, file_name, path=None):
        """
        Returns whether it is a folder or not
        Known issue with getting Pages files to not look like directories, compensates
        DEPRECIATED, use Filer.is_directory() instead
        """
        ext = self.split_extension(file_name)[1]
        if ext and ext == '.pages' or ext == '.key':
            # FIXME: Applescript ! 
            return False
        else:
            if not path:
                path = self.current_directory
            return os.path.isdir(self.join(path, file_name))

    def is_link(self, file_name, path=None):
        if not path:
            path = self.current_directory
        return os.path.islink(self.join(path, file_name))

    def set_directory(self, folder):
        self.set_current_directory(folder.rstrip('/'))

    def get_file_name(self, dir):
        return os.path.split(dir)[1]

    def filter(self, name):
        """
        Allows for default filter as well as dynamic one
        """
        if name == '.default.dir': return False
        ffile, ext = self.split_extension(name)
        if ext in ['.pyc']:
            return False
        if ffile in ['.DS_Store']:
            return False
        if self.user_filter:
            return re.search(self.user_filter, name.lower())
        else:
            return True

    def print_header(self):
        """
        Prints header -- with style
        """
        header = " ".join(self.current_directory.split(os.sep)).strip(' ')
        
        print(Fore.BLACK + Back.WHITE + self.current_directory.rstrip('/').replace(
            user_home_directory, ' ~').replace(
                  r'/', ' ' + Style.RESET_ALL + ' > ' + Fore.BLACK + Back.WHITE + ' ') + ' ' + Style.RESET_ALL)        

    def list_items(self, header=None):
        """
        Asks screenful for output and prints out whatever is in the current directory
        """
        self.ask_pound()
        if not header:
            self.print_header()
        else:
            print(header)

        for line in self.output.screenful(truncate=self.truncate,
                              pre_process         =self.pre_process,
                              process             =self.process,
                              post_process        =self.post_process,
                              overflow_delegate   =self.setup_pages):
            print(line)

    def setup_pages(self, list_of_items, _max):
        """
        Sets state so that next time through the start() loop will know we have pages to comb through
        Is the overflow_delegate sent to screenful
        """
        
        def set_page(what, p):
            # can't do assignment in list comp
            what.page = p

        verbose = False
        verbose and print("setup_pages taking list of {} items and putting them in chunks with max={}".format(
            len(list_of_items), max))
        chunks = [list_of_items[i:i+_max] for i in range(0, len(list_of_items), _max)]
        defaults = []
        for p in range(len(chunks)):
            [set_page(c, p) for c in chunks[p]]
            defaults.extend([c for c in chunks[p] if c.default])
        self.ask_plus()
        self.pages = {'page':0, 'list':chunks}        
        if defaults:
            # return first number of index of first page, and that associated list
            # always go with first default found
            return chunks[defaults[0].page][0].index, chunks[defaults[0].page]
        else:
            # simple
            return chunks[0].index, chunks[0]

    def list_current_page(self, header=None):
        """
        Asks screenful for output and prints out whatever page we're currently on
        """
        verbose = False
        if not header:
            self.print_header()
        else:
            print(header)
        page = self.pages['page']
        start_at = 0
        for p in range(page):
            # calc start_at value by iterating through list
            start_at += len(self.pages['list'][p])
        verbose and print('start_at is now {0}'.format(start_at))
        for line in self.output.screenful(_list=self.pages['list'][page],
                              truncate=self.truncate,
                              pre_process=self.pre_process,
                              process    =self.process,
                              post_process=self.post_process,
                              start_at=start_at):
            print(line)

    def truncate(self, this, _max):
        """
        Adds a truncated property to this that should be used as the printout
        This should be an object
        #TODO: Make it so that if there are files with similar names that the unique part is returned
               (This would involve checking for uniques in self.list_current_directory() )

        """
        verbose = False
        verbose and print(str(this))
        ellipse = '..'
        if this.is_hidden:
            # hard cut
            verbose and print("dot file-----------")
            if len(str(this)) <= _max:
                this.truncated = str(this)
            else:
                this.truncated = str(this)[:_max - len(ellipse)] + ellipse
        else:
            if this.ext:
                if len(str(this)) <= _max:
                    verbose and print("ext file no truncate")
                    this.truncated = str(this)
                else:
                    t = _max - len(this.ext)
                    ffile = str(this)[:t]
                    ffile = ffile[:-len(ellipse)] + ellipse
                    verbose and print("ext file------------")
                    this.truncated = ffile + this.ext
            else:
                if len(str(this)) <= _max:
                    verbose and print("no max--------------")
                    this.truncated = str(this)
                else:
                    verbose and print("exceeds max---------")
                    this.truncated = str(this)[:_max-len(ellipse)] + ellipse
        this.str_trick = 'truncated'
        if verbose:
            if str(this) != this.truncated:
                print('\n\n{}\n> {}\n> {}'.format(this, str(this), this.truncated))

    def pre_process(self, this):
        """
        Sets up state so I know which item was last modified
        Returns ok if file is legit file
        """
        return this.is_mounted

    def process(self, this, max_length, columns=False):
        """
        Determine the file name based on the context of the printout
        Put is in printout property
        Most cases, just returns file_name, but will change the whitespace if the occassion arises
        """
        verbose = False
        s = str(this)
        if this.is_hidden:
            this.printout = s
        
        ffile, ext = os.path.splitext(s)
        if ext:            
            white_space = ' ' * (max_length - len(s))
            this.printout = ffile + white_space + ext
        else:
            verbose and print("Process returning default")
            this.printout = s
        this.str_trick = 'printout'
        verbose and print(': ' + s + '\n: ' + this.printout)

    def determine_command(self, this):
        """
        Examine file record and return appropriate command
        Default behaviour returns open
        """
        if not this: return ""
        if isinstance(this, str) and os.sep in this:            
            p, n = os.path.split(this)
            this = File_object(p, n, 0)
        if this.is_directory:
            leadoff = "cd"
        elif this.is_link:
            if this.real_is_directory:
                leadoff= 'cd'
            else:
                leadoff= 'open'
        elif this.kind == '.txt':
            leadoff = 'pico'
        elif this.kind == '.py':
            leadoff = 'aquamacs'
        else:
            leadoff = 'open'

        return "{} '{}'".format(leadoff, this.full_path)
       
    def post_process(self, this, num, max_length):
        """
        Colorizes items in print display
        (1) Makes most recently modified item cyan
        (2) Any directory yellow
        (3) Symlinks green
        (4) Files are left unchanged
        """
        verbose = False
        verbose and print("in post process: {}".format(this))
        item = str(this)
        if not this.is_mounted:
            strikeout = '☓' * len(str(num))
            return (strikeout, green(item))

        if this.default and this.force_default:
            return ( cyan(num), cyan(item) )

        if this.default:
            return ( cyan(num), cyan(item) )

        if this.is_directory:
            return ( num, yellow(item) )

        if this.is_link:
            return ( num, green(item) )
        else:
            # is file
            pass

        ffile, ext = os.path.splitext(item) 
        if ext:
            return ( num, green(ffile + ext) )
        else:
            return ( num, green(item) )

    def replace_digits_with_paths(self, user_input):
        """
        Takes input and replaces numbers on word boundaries with full paths
        """
        verbose = False
        verbose and print(user_input)
        _user_input = user_input[:]
        for before, num, after in re.findall(r'(\/|\b)([\d.]+)(\/|\b)', _user_input):
            verbose and print("before: {}, num: {}, after: {}".format(before, num, after))
            if not before and not after and num.isdigit():
                # If found a clean match replace with full path name of file
                try:
                    file_path = self.list_current_directory().index(int(num)).full_path
                    verbose and print(file_path)
                except IndexError:
                    verbose and print("Got index error, wonder why?")
                else:
                    verbose and print("what is it doing?")
                    _user_input = _user_input.replace(num, '"{0}"'.format(self.join(self.current_directory,
                                                                                    file_path)))
        return _user_input

    def get_default(self):
        return self.list_current_directory().default

    def get_item(self, i, first_only=True):
        if i.isdigit():
            return self.list_current_directory().index(int(i))
        else:
            if os.sep in i:
                return self.list_current_directory().which_equals('full_path', i, first_only=first_only)
            else:
                return self.list_current_directory().which_equals('name', i, first_only=first_only)

    def walk(self, user_input):
        """
        Looks to see what files are available, given:
        (1) the current directory
        (2) tagged files
        (3) user-defined projects
        returns a list of the full paths of each file, or [] if none match

        (4) any shell commands, by using which
        """
        verbose = False
        results = []
        which = self.list_current_directory().which_equals('name', user_input,
                                                           first_only=True, case_insensitive=True)
        if which:
            results.append([which.full_path, "Current directory: {}".format(which.name)])

        if user_input in self.list_current_projects():
            # short-circut
            self.menu.project(user_input)
            return None #indicates that I've handled the command

        else:
            for proj in self.list_current_projects():
                verbose and print('project {}'.format(proj))
                fullinfo, _ = self.mdfind(proj)
                filenames = [os.path.split(f)[1].lower() for f in fullinfo]
                if user_input.lower() in filenames:
                    item = fullinfo[filenames.index(user_input.lower())]
                    # eliminates duplicates by excluding current directory
                    p, _ = os.path.split(item)
                    p += '/' # needed
                    if not p == self.current_directory:
                        results.append([item, item])
                    else:
                        pass # skipped because has already appeared in list_current_directory

            if user_input.lower() in self.list_current_projects():
                results.append([user_input.lower(), "Project: {}".format(user_input.lower())])

            return results

    def walk_current_directory(self, user_input):
        """
        
        """
        which = self.list_current_directory().which_equals('name', user_input,
                                                           first_only=True, case_insensitive=True)
        if which:
            return str(which.index)
        else:
            return user_input

    def walk_main_menu(self, user_input):
        """
        Looks inside of each symlink at home_directory, and sees if there is a directory
        by the user_input's name, if so, then CDs into it
        """

        def get_three_levels_of_directories(path):
            time = 0
            names =[]
            paths = []
            for top in os.walk(path):
                time += 1
                dirpath, dirnames, filenames = top
                names.extend([d.lower() for d in dirnames])
                paths.extend([dirpath]*len(dirnames))
                if time == 4:
                    break
            return (paths, names)

        def get_main_menu():
            result = []
            for item in os.listdir(self.home_directory):
                if os.path.islink(item):
                    result.append(item)
            return result

        all_directories = []
        shortcuts = []
        paths = []
        for menu_item in get_main_menu():
            dirs, names = get_three_levels_of_directories(menu_item)
            all_directories.extend([name.lower() for name in names])
            # shortcuts.extend([n[:len(user_input)].lower() for n in names])
            # list comprehension allows short-cuts
            paths.extend(dirs)
        if user_input.lower() in all_directories:
            where = all_directories.index(user_input.lower())
            path = paths[where]
            self.command.run_command('cd "{}"'.format(os.path.join( path, all_directories[where])))
            return True
        else:
            return False

    def parse_input(self, user_input):
        """
        Passes user_input to a subprocess
        Converts integers to folder equivalents
        Detects a change in directory, and sets state accordingly
        Returns a page number if user enters 'n' or 'v', or other appropriate functions
        """
        return Parse_Input(self, user_input)

    def _override_and_fake(self, _list, header=None):
        """
        
        """
        raise NotImplemented("override_and_fake is depreciated")
        if isinstance(_list, File_list):
            self.swap_and_save(_list)
        else:
            self.swap_and_save(SelectList(_list))
        ask = self.ask_copy()
        self.ask_question()

        # manually call methods that immitate self.execute
        done = False
        selection = None
        while not done:
            self.clear_screen()
            if not self.pages:
                self.list_items(header=header)
            else:
                self.list_current_page(header=header)
                
            _input = input(self.ask)
            
            if not _input == self.quit_request:
                selection = _input[:]
                page = self.parse_input(_input)
                if page is None:
                    self.reset_pages()
                else:
                    self.turn_page(page)
                done = True
            else:
                done = True

        self.ask = ask
        item = self.get_item(selection)
        self.restore()
        return item

    def select_wrapper(self, _list, using, *args, header=None, paths=False, sync_properties=[], klass=None):
        verbose = False
        if not klass:
            klass = SelectPydir
        d = klass(_list, *args, header=header, paths=paths)
        verbose and print(_list)
        verbose and print(d)
        
        # pre
        for prop in sync_properties:
            setattr(d, prop, getattr(self, prop))
        
        selection = d.select(using)

        # post
        for prop in sync_properties:
            if not getattr(self, prop) == getattr(d, prop):
                setattr(self, prop, getattr(d, prop))

        return selection
    
    def project_screen(self):
        """
        Derive the list needed for the project screen
        """
        verbose = False
        verbose and print("Current project is {}".format(self.current_project))
        old_project = self.current_project
        _list, errors = self.mdfind(self.current_project, lazy=False)
        selection = self.select_wrapper(_list,
                           lambda x: x,
                           header="PROJECT: {}".format(self.current_project),
                           paths=True,
                           sync_properties=['current_project'])
        if not old_project == self.current_project:
            # recurse because project was changed within project screen
            self.project_screen()
        elif selection:
            self.command.run_command(self.determine_command(selection))

    def mdfind(self, search_str, lazy=True, save=True):
        verbose = False
        if lazy and search_str in self._project_saved_searches:
            verbose and print("lazy bastard: {}".format(search_str))
            return self._project_saved_searches[search_str]
        else:
            _list, errors = self.command.run_command('/usr/bin/mdfind "{}"'.format(self.encode_tag(search_str)))
            result = [ [l for l in _list.decode().split('\n') if l and not l.startswith(__path__)], errors ]
            if save:
                self._project_saved_searches[search_str] = result
            # TODO: figure out how to use it even with multiple dirs open
            return result

    def encode_tag(self, s, **keywords):
        return self.user_info.encode_tag(s, **keywords)

    def appropriate_page_or_none(self):
        d = self.list_current_directory().default
        if d and d[0] and hasattr(d[0], 'page'):
            return d[0].page
        else:
            return None

class SelectList(File_list):
    def __init__(self, _list, paths=False):
        verbose = False
        Klass = SelectObject if not paths else SelectObjectPydir
        verbose and print("SelectList using {} for klass.".format(Klass))
        File_list.__init__(self, "", [item for item in _list if item], klass=Klass)

class SelectObject(File_object):
    def __init__(self, path, name, i):
        """
        Detect whether name has a path built-in or not,
        if so it sets path accordingly
        """
        verbose = False
        _extra = None
        if isinstance(name, list):
            verbose and print("Using _extra")
            _extra = name[1]
            name = name[0]
        p, n = os.path.split(name)
        if p:
            File_object.__init__(self, p, n, i)
        else:
            File_object.__init__(self, path, name, i)
        self._extra = _extra
        if self._extra:
            self.str_trick = '_extra'
        verbose and print("Here is the SelectObject: {}".format(self))
    
class SelectObjectPydir(File_object_dir):
    def __init__(self, path, name, i):
        """
        Detect whether name has a path built-in or not,
        if so it sets path accordingly
        """
        p, n = os.path.split(name)
        if p:
            File_object_dir.__init__(self, p, n, i)
        else:
            File_object_dir.__init__(self, path, name, i)

class SelectMenu(Menu):
    def tutorial(self, *args):
        pass

    def name(self, *args):
        verbose = False
        if not args or not args[0]:
            raise BadArguments("name what?")
        else:
            self.cntrl.not_done()
            which = self.cntrl.get_item(args[0])
            print("Full path of {} {}:".format(which.desc, which.name))
            print(which.full_path)
            input(": ")
            if self.cntrl.pages:
                return self.cntrl.pages['page']
            else:
                return None

    def goto(self, *args):
        """
        Goes to the parent directory of target
        """
        if len(args) == 0:
            raise BadArguments("Which item?")
        which = self.cntrl.get_item(" ".join(args))
        self.cntrl.set_current_directory(which.parent_directory)

    def back(self, *args):
        self.cntrl.stop()

    def q(self, *args):
        self.cntrl.stop()


class SelectPydir(Pydir):

    def __init__(self, _list, header=None, paths=False):
        """
        Override completely is easier
        """
        verbose = False
        self.ask_pound()
        self.header=header
        self.reset_pages()
        self.user_sorter = 'name'
        self._clear_screen = None
        self.user_command = PydirShell(self)
        self.command = Shell(avoid_recursion="projects")
        self.menu = SelectMenu(self)
        self.last_mod_time = None
        self.output = Output()
        self.initialize()
        self.paths = paths
        self._list = SelectList(_list, paths=paths)
        verbose and print("SelectDir _list is {}".format(self._list))

    def loop_iteration(self):
        """
        Call whenever a new loop should be indicated
        """
        self.output.set_list(self.list_current_directory())

    def ask_pound(self):
        self.ask = '-> '

    def initialize(self):
        self._selection = None

    def list_current_directory(self):
        return self._list

    def pre_process(self, file_name):
        if self.paths:
            return Pydir.pre_process(self, file_name)
        else:
            return True

    def print_header(self):
        print(Fore.BLACK + Back.WHITE + " {} ".format(self.header) + Style.RESET_ALL)        

    def post_process(self, file_name, num, max_length):
        if self.paths:
            return Pydir.post_process(self, file_name, num, max_length)
        else:
            return (num, file_name)
        
    def parse_input(self, user_input):
        # specialized code given the fact we're working with an abstract list rather than
        # a list based on the directory

        # TODO: I shouldn't need to call this, find out what is throwing off the indexing
        self.list_current_directory().do_indexing()

        if not user_input.strip():
            user_input = str(self.list_current_directory().default.index)

        this = self.list_current_directory().which_equals('name', user_input, first_only=True)
            
        if user_input.isdigit() and not user_input.startswith('name '):
            # "make it so" feature: user types in number and we
            # figure out if it's a cd or an open statement
            which = int(user_input)
            if which < len(self.list_current_directory()):
                this = self.list_current_directory().index(which)
        try:
            handled = self.menu._parse(user_input)
        except BadArguments:
            handled = True

        if not handled:
            if user_input == self.quit_request:
                self.stop()
            elif user_input.startswith('+'):
                if self.pages:
                    self.not_done()
                    return self.pages['page'] + user_input.count('+')
                else:
                    input("No page to turn")
            elif user_input.startswith('-'):
                if self.pages:
                    self.not_done()
                    return self.pages['page'] - user_input.count('-')
                else:
                    input("No page to turn")

        if this:
                self.got_good_input(self.derive_selectable_from_this(this))

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

        try:
            page = self.parse_input(input(self.ask))
        except KeyboardInterrupt:
            print()
            page = None

        # Clean up pages state as appropriate
        if page is None: 
            # If parse_input returns None (page 0 is legitimate number)
            self.reset_pages()
        else:
            self.turn_page(page)

    def start(self):
        """ Instead of looping, just take input once """
        self.not_done()
        while not self._done:
            self.done()  # force someone else to say the opposite
            self.loop_iteration()
            self.execute()
        return self.stop()

    def done(self):
        self._done = True

    def not_done(self):
        self._done = False

    def stop(self):
        return self._selection

    def select(self, using):
        """
        Returns the item selected by the user
        """
        self.derive_selectable_from_this = using
        return self.start()

    def walk(self, _):
        """
        Overwrite to return nothing, as not used
        """
        return []

class ProjectMenu(SelectMenu):

    def nickname(self, *args):
        if not args:
            raise BadArguments("Which file?")
        which = self.cntrl.get_item(args[0])
        print("Enter nickname for {} {}:".format(which.desc, which.name))
        _nick = input(": ")
        which.metadata.set('nickname', _nick)

class ProjectPydir(SelectPydir):

    def __init__(self, *args, **kwargs):
        SelectPydir.__init__(self, *args, **kwargs)
        self.menu = ProjectMenu(self)

if __name__ == '__main__':
    pass
