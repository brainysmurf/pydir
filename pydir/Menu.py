import os
from pydir.Filer import File_list, File_object, build_from_scratch
from colorama import Fore, Back, Style
from colors import white, green, \
     red, cyan, yellow, magenta
from pydir.Command import copy_to_clipboard
import fileinput
import re
import fnmatch

__path__, _j = os.path.split(__file__)

from AppleScriptWrapper.Basic import get_app, User_Canceled, get_front_app, choose_from_list, \
     get_list_of_every_open_application, get_name_of_front_application, \
     tell_app_to_do, reveal_in_finder

class BadArguments(Exception): pass

DefaultItems = "pydir_mistermorris_default_item"
NoArguments = "pydir_mistermorris_no_arguments"
OptionalArgument = "pydir_mistermorris_optional_argument"
RequiredArgument = "pydir_mistermorris_required_argument"

class Menu(object):
    """
    Abstract class that represents a menu, where the commands are defined in each method
    Implemented through self._parse method
    """
    """
    doc method prints out selfs' methods docs, main calls controller.initialize,
    and command prints out all method names
    """
    def __init__(self, cntrl):
        self.cntrl = cntrl
        self.command_line = self.cntrl.user_command.run_command
        self.invisible_command_line = self.cntrl.command.run_command

    def _all_commands(self):
        return [f for f in dir(self) if not f.startswith('_') and callable(getattr(self, f))]

    def _parse(self, user_input):        
        verbose = False
        split_input = user_input.split(' ')
        first_word = split_input[0].lower() if ' ' in user_input else user_input.lower()
        verbose and print("first word is {}".format(first_word))
        split_input.pop(0)
        rest = " ".join(split_input).strip()
        verbose and print("the rest is {}".format(rest))
        if rest:
            # Not a number or name available to
            verbose and print("splitting")
            arguments = [rest]
        else:
            verbose and print("no arguments detected")
            arguments = []
            
        verbose and print("Arguments are {}".format(arguments))
        handled = False
        dont_force_reset = False
        
        if hasattr(self, first_word):
            try:
                g = getattr(self, first_word)
                handled = True
            except TypeError:
                raise BadArguments

            a = g.__annotations__
            if not a:
                # no annotations, just send what you got
                verbose and print("No annotations for {}".format(g))
                g(*split_input)
            else:
                # If function is expecting default item, set that up now
                if DefaultItems in list(a.values()):
                    which = self.cntrl.list_current_directory().default
                    verbose and print("inserting default")
                    arguments.insert(0, which)

                if RequiredArgument in list(a.values()) and not arguments:
                    self.cntrl.errors.handle_error('required argument missing', first_word, self._derive_doc(g))
                    return handled
            
                if OptionalArgument in list(a.values()):
                    while len(arguments) < len(list(a.keys())):
                        arguments.append(None)

                verbose and print("About to send command {} arguments {}".format(g, arguments))
                try:
                    dont_force_reset = g(*arguments)
                except TypeError:
                    self.cntrl.errors.handle_error('bad arguments', first_word, self._derive_doc(g))

        if not dont_force_reset:
            # Forces it to update the list
            self.cntrl.force_reset()
        return handled

    def open(self, which: DefaultItems, what: OptionalArgument):
        """
        Examine file record and return appropriate command
        Default behaviour returns open
        """
        if what == '.':
            which = self.cntrl.current_directory()
        all_leadoffs = {}
        for this in which:
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

            if leadoff not in all_leadoffs:
                all_leadoffs[leadoff] = []
            all_leadoffs[leadoff].append(this.full_path)

        visible_sequence = []
        invisible_sequence = []
        for l in all_leadoffs:
            if l in ['pico']:
                visible_sequence.append("{} '{}'".format(l, "' '".join(all_leadoffs[l])))
            else:
                invisible_sequence.append("{} '{}'".format(l, "' '".join(all_leadoffs[l])))

        if invisible_sequence:
            self.invisible_command_line(";".join(invisible_sequence))
        if visible_sequence:
            self.command_line(";".join(visible_sequence))

    def quit(self: NoArguments):
        """
        Stops running
        """
        self.cntrl.stop()

    def q(self: NoArguments):
        """
        Same as quit
        """
        self.quit()

    def help(self: NoArguments):
        """
        Prints suggestions on how to use documentation system
        """
        self.doc('doc')

    def tutorial(self, *args):
        """
        tutorial on|off
        Turn the tutorial on or off
        Equivalent to dir -tutorial at the command line
        """
        if not args:
            raise BadArguments("Expecting 'on' or 'off'")
        if args[0].lower() == 'on':
            self.cntrl.tutorial(True)
        elif args[0].lower() == 'off':
            self.cntrl.tutorial(False)

    def main(self: NoArguments):
        """
        Goes to the project page ('main menu') for the current project
        """
        self.cntrl.initialize()

    def projects(self: NoArguments):
        """
        Gives a list of user-created projects, and can select from it to make that
        the current project
        """
        _list = self.cntrl.list_current_projects()
        result = self.cntrl.select_wrapper(_list, lambda x: x.name, header="List of Projects")
        if result:
            self.project(result)

    def project(self, *args):
        """
        Changes current project to project_name
        If project_name is not valid, does not raise error
        """
        verbose = False
        if len(args) == 0:
            self.projects()
        else:
            proj = " ".join(args)
            verbose and print("Setting project to {}".format(proj))
            if proj in self.cntrl.list_current_projects():
                self.cntrl.current_project = proj
                verbose and print("Set!")
                self.cntrl.initialize()
            else:
                pass

    def _derive_doc(self, func):
        funca = func.__annotations__
        doc = func.__doc__
        # parse the arguments for header
        funcargs = list(funca.keys())
        default = "-Operates on the currently selected item(s)-" if funcargs and funcargs[0] == 'which' else ""
        if default:
            funcargs.pop(0)
        if funcargs and funcargs[0] == 'self':
            funcargs.pop(0)
        result = "\n\t{} {}{}\n\t{}\n".format(func.__name__,
                              "" if not funcargs else "<{}>".format("> <".join(funcargs)),
                              "\n\t{}\n".format(default) if default else "",
                              doc.strip() if doc else "")
        return result
        

    def commands(self, name: OptionalArgument):
        """
        Lists and allows user to select from menu of currently available commands
        """
        if not name:
            name = self.cntrl.select_wrapper(self._all_commands(),
                                             lambda x: x.name, header="List of commands available:")
        if name:
            if hasattr(self, name):
                self.cntrl.set_helper_message(self._derive_doc(getattr(self, name)))

        

class PydirMenu(Menu):
    """
    Includes doc 
    """
    def __init__(self, cntrl):
        Menu.__init__(self, cntrl)
        self.finderapp = get_app("Finder")

    def _quotify_args(self, args):
        """ wraps up list into quotes """
        return '"{}"'.format(" ".join(args))

    def filecopy(self, *args):
        """
        Example filecopy ...

        Copies file to current directory
        doc copy for more info on how to get the ... to be saved
        """
        if not args:
            raise BadArguments("Expecting file")
        item = self._quotify_args(args)
        # don't get item with get_item... because file probably isn't in current directory anyway (duh)
        self.command_line('cp {} {}'.format(item, '"{}"'.format(self.cntrl.current_directory)))

    def trash(self, which: DefaultItems):
        """
        Moves file to trash
        """
        verbose = False
        verbose and print(which)
        verbose and print(which.full_path)
        try:
            self.cntrl.errors.handle_error('trash confirm', red("\n".join([w.full_path for w in which])))
        except KeyboardInterrupt:
            return
        self.finderapp.move([w.full_path for w in which], to_idiom="trash")
        
    def save(self, *args):
        """
        Provide name of application and will tell it to save.
        Gives you a chance to name it before doing so.
        """
        """
        FIXME: Applescript's save command makes keynote and pages files a directory instead of a file (for some reason)
        I know what the problem is now... have to test to ensure
        """
        wanted_app = args[0] if args else None
        wanted_where = args[1] if len(args) > 1 else None
        if wanted_app:
            all_open_apps = get_list_of_every_open_application()
            list_of_possibles = [appli for appli in all_open_apps if appli.lower().startswith(wanted_app.lower())]
            if len(list_of_possibles) > 1:
                try:
                    wanted_app = choose_from_list("Which app?", list_of_possibles)
                except User_Canceled:
                    return
            elif len(list_of_possibles) == 0:
                return ["", "Error, no app by that name"]
            else:
                wanted_app = list_of_possibles[0]
            if not wanted_where:
                try:
                    wanted_where = get_app(wanted_app).name_of_current_document()
                except:
                    wanted_where = input("Couldn't figure out name to use, enter now: ")

        else:
            try:
                all_open_apps = get_list_of_every_open_application()
                try:
                    wanted_app = choose_from_list("Which app?", get_list_of_every_open_application())
                except User_Canceled:
                    return
            except User_Canceled:
                return
            try:
                wanted_where = get_app(wanted_app).name_of_current_document()
            except:
                wanted_where = input("Couldn't figure out name to use, enter now: ")

        try:
            wanted_where = get_app(wanted_app).display_dialog_convenience("Modify?", default_answer=wanted_where)
        except User_Canceled:
            return

        if wanted_app and wanted_where:
            a = get_app(wanted_app)
            path = os.path.join(self.cntrl.current_directory, wanted_where)
            a.save_as(path)
            ext = a.extension_of_current_document()
            a.close()
            a.open(path + ext)

    def remember(self, which: DefaultItems):
        """
        "Remembers" the currently selected items for use in other commands
        """
        self.cntrl._user_saved = which[:]

    def path(self, which: DefaultItems):
        """
        Copies the path of currently selected item to the clipboard.
        Useful for use in open and save dialog boxes
        """
        if len(which) == 1:
            copy_to_clipboard(which[0].full_path)
        else:
            input("One item required to be selected")

    def move_to(self: NoArguments):
        """
        Copies remembered (see command 'remember') items to the current directory
        """
        if not self.cntrl._user_saved:
            self.cntrl.errors('no saved')
        self.finderapp.move([i.full_path for i in self.cntrl._user_saved], self.cntrl.current_directory)

    def name(self, which: DefaultItems, chosen: OptionalArgument):
        """
        Diplay the full path for any item
        """
        if chosen:
            input(chosen.full_path)
        elif which:
            input(which.full_path)        

    def finder(self: NoArguments):
        script = ['tell application "Finder"', 
                      "try", 'return POSIX path of (folder of front window as text)', 
                      "on error", 'return ""', "end try", 
                      "end tell"]
        unpacked_script = [" -e '{0}'".format(s) for s in script]
        final = "/usr/bin/osascript"
        for s in unpacked_script:
            final += s
        target_dir = self.command_line(final, silence=True)[0].strip().decode()
        if target_dir:
            self.cntrl.set_directory(target_dir)
        else:
            input("Finder has no open windows")

    def goto(self, which: DefaultItems):
        self.cntrl.set_current_directory(which.parent_directory)

    def by(self, *args):
        """
        by name | ext | kind

        'Sorts'
        """
        if not args or not args[0]:
            # default, assumes reset
            self.cntrl.user_sorter = None
        else:
            self.cntrl.user_sorter = args[0]

    def exec(self, which: DefaultItems):
        """
        Looks at extension and then decides which environment to invoke
        """
        control_list = {'.py': 'python3', '.sh': 'bash'}
        self.command_line('{} "{}"'.format(control_list.get(which.ext, ""), which.full_path))
                
    def reveal(self, which: DefaultItems):
        reveal_in_finder(which.full_path)

    def finderall(self: NoArguments):
        script = ['tell application "Finder"', 
#                      "try",
                      "set boot_volume to boot volume of (get system info)", "set p to get POSIX path of (folder of every window as text)", "set AppleScript's text item delimiters to boot_volume", "set l to text items of p", "set AppleScript's text item delimiters to \"\"", "return l", 
#                      "on error", 'return ""', "end try", 
                      "end tell"]

    def files(self, *args):
        """
        TODO: Look at what this does more closely
        How is it different from files? Are they dissimilar enough?
        Are the names right?
        """
        verbose = False
        if not args:
            search_string = input("Enter name to look for: ")
        else:
            search_string = " ".join(args)
        print("Searching...")
        stdout, stderr = self.invisible_command_line(
            """mdfind -onlyin {} '((kMDItemDisplayName == \"{}\"wc) && (kMDItemContentType != public.folder))'""".format(
                self.cntrl.user_home_directory, search_string)
            )
        results = stdout.decode().split("\n")
        verbose and print(stdout)
        print("complete")
        if not results:
            BadArguments("Nothing found")
        which = self.cntrl.select_wrapper(results, lambda x: x.path, header="Search results for:")
        if which:
            self.cntrl.set_current_directory(which)

    def search(self, *args):
        """
        TODO: see files above
        search <searchstring>

        'Searches only in local directories'
        'Uses mdfind'
        """
        """
        Save output's list, set it to mdfind results (which I have to make myself), and reset
        """
        verbose = False
        if not args:
            raise BadArguments()
        print("Searching...")
        stdout, stderr = self.invisible_command_line("mdfind -name -onlyin '{}' '{}'".format(
            self.cntrl.user_home_directory, " ".join(args)))
        if stderr:
            raise BadArguments("Search resulted in error: {}".format(stderr))
        results = stdout.decode().split('\n')
        verbose and print(stdout)
        print("complete.")
        if not results:
            raise BadArguments("Nothing found")

        which = self.cntrl.select_wrapper(results, lambda x: x, header="Search results for:", paths=True)
        if which:
            self.cntrl.set_current_directory(which.path)
            self.command_line('open "{}"'.format(which.full_name))
        
    def rename(self, which: DefaultItems, name: OptionalArgument):
        """
        Rename file, keeping extension, if any, the same.
        """
        for w in which:
            name = input("Enter new name for {} (sans extension): ".format(w.full_name))
            self.finderapp.rename(w.full_path, "{}{}".format(name, w.ext))

    def append(self, which: DefaultItems, what: OptionalArgument):
        """
        TODO: Look at this in more detail
        """
        pass
#        with open(item.full_path, 'a') as f:
#            f.write(append_what + '\n')

    def touchout(self, *args):
        """
        TODO: Useful but is this the right interface?
        touchout <file>

        'Reads file and makes a new file for each line encountered.'
        'File names are contents of each line with .txt extension.'
        """
        if not args:
            raise BadArguments("Needs file... full path")
        ffile = " ".join(args)
        with open(ffile) as f:
            lines = f.readlines()
        input(lines)
        for line in lines:
            self.command_line('touch "{}.txt"'.format(line.strip('\n')))

    def copycontents(self, *args):
        """
        Copy contents to the clipboard ... only works with text files (duh)
        The lines are combined with spaces instead of return characters

        Workflow is this: Add information to files with append and copy them
        with copycontents to paste into Word or other documents
        """
        if not args:
            item = self.cntrl.get_default()
        else:
            item = self.cntrl.get_item(args[0])
        with open(item.full_path) as f:
            lines = f.readlines()
        copy_to_clipboard(" ".join([l.strip('\n') for l in lines]))

    def inplace(self, *args):
        """
        TODO: Test
        inplace <files>

        'Search and replace'
        'Will ask for search and replace string'
        """
        if args:
            list_of_files = [self.cntrl.get_item(a).full_path for a in args]
        else:
            raise BadArguments('needs files')
        if list_of_files:
            print("(Backups stored in /tmp)")
            s  = input("Replace: ")
            r = input ("   With: ")
            for ffile in list_of_files:
                self.command_line("cp '{0}' '/tmp/{1}.bak'".format(ffile, ffile.replace(os.path.dirname(ffile)+'/', "", 1)))
                for line in fileinput.input(ffile.strip('"'), inplace=True):
                    print(line.replace(s, r), end="")  # goes back to the file

    def savepdf(self, *args):
        self.save(*args)
        self.pdf(*args)

    def pdf(self, *args):
        """
        Communicates with app and tries to make current file a pdf file
        at the same location with the same name, but with .pdf extension.
        """
        wanted_app = None
        if len(args) == 1:
            if args[0].isdigit():
                the_file = self.cntrl.get_item(args[0])
                self.command_line("open {0}".format(the_file.quoted_full_path))
                wanted_app = get_name_of_front_application()
            else:
                entered = args[0]
                all_open_apps = get_list_of_every_open_application()
                list_of_possibles = [appli for appli in all_open_apps if appli.lower().startswith(entered.lower())]
                if len(list_of_possibles) > 1:
                    try:
                        wanted_app = choose_from_list("Which app?", list_of_possibles)
                    except User_Canceled:
                        return
                elif len(list_of_possibles) == 0:
                    return ["", "Error, no app by that name"]
                else:
                    wanted_app = list_of_possibles[0]
        else:
            try:
                all_open_apps = get_list_of_every_open_application()
                wanted_app = choose_from_list("Which app?", get_list_of_every_open_application())
            except User_Canceled:
                return

        if wanted_app:
            a = get_app(wanted_app)
            a.save_as_pdf()

    def g(self, *args):
        """
        g <no arguments>

        'Enter commit message for git.'
        """
        result = self.command_line('git commit -a -m "{0}"'.format(input("Enter commit message: ")))
        if result[0]:
            input(result[0])

    def setup(self, *args):
        """

        """
        pass

    def setup3(self, *args):
        """
        Looks for a setup.py file and if found launches idiom
        """
        result = self.command_line('python3 setup.py install')
        if result[0]:
            input(result[0])
        if result[1]:
            input(result[1])

    def drop(self, *args):
        """
        Exits and puts the resulting shell in the same as the current directory
        """
        get_front_app().keystroke('drop\n')
        self.cntrl.stop()

    def no(self, *args):
        """
        no filter
        'Takes off any filtering'

        no tag <file> <tag*>
        'Removes tag from file. You can select tag from list.'
        """
        which = None
        if not args:
            # default is to assume it's "filter" that's wanted
            self.no("filter")
            return
        elif args[0].lower() == 'filter':
            self.cntrl.user_filter = None
        elif args[0].lower() == 'tag':
            if len(args) <= 1:
                raise BadArguments("No file indicated")
            elif len(args) == 2:
                which = self.cntrl.get_item(args[1])
                comment = self.finderapp.spotlight_get_comment(which.full_path)
                s = self.cntrl.encode_tag('(.*?)', for_pass_to_re_module=True)
                tags = re.findall(s, comment)
                tag = self.cntrl.select_wrapper(tags, lambda x: x.name,
                                          header="Remove which tags for {} {}?".format(
                                                    which.desc, which.name))
            else:
                which = self.cntrl.get_item(args[1])
                tag = " ".join(args[2:])
        if which:
            self.finderapp.spotlight_remove_comment(which.full_path, self.cntrl.encode_tag(tag))

    def h(self, pattern: RequiredArgument):
        """
        Shortcut to highlight
        """
        return self.highlight(pattern)

    def only(self: NoArguments):
        selection = self.cntrl.select_wrapper([i.full_path for i in self.cntrl.list_current_directory().default], lambda x: x, paths=True,
                                              header="Currently selected items:")
        selection.default = True
            
    def highlight(self, pattern: RequiredArgument):
        """
        Use asterix as a wildcard to match file names.
        If asterix is not used in pattern then matches anywhere in file name.
        Case insensitive.

        EX)
        highlight f*
        Highlights all files that begin with f or F

        highlight *.pdf
        Highlights all pdf files

        highlight blah
        Highlights all files that have blah or BLAH or bLaH, etc somewhere in their name
        """
        verbose = True
        verbose and print(pattern)
        if '*' not in pattern:
            pattern = '*' + pattern + '*'
        _list = self.cntrl.list_current_directory()

        # known bug in glob means I have to filter out files with certain names:
        # TODO: How to fix?
        # Result is that files with [ or ] in their name won't ever get highlighted, confusing the user

        subset = [_list[i] for i in range(len(_list)) \
                  if '[' not in _list[i].original_name and ']' not in _list[i].original_name and \
                  fnmatch.fnmatch(_list[i].original_name.lower(), pattern.lower())]
        verbose and print(subset)
        if subset:
            verbose and print("highlighting {}".format(subset[0]))
            self.cntrl.single_out(subset[0])
            subset.pop(0)
            if subset:
                for item in subset:
                    verbose and print("highlighting {}".format(item))
                    self.cntrl.highlight(item)

        return True # do NOT force reset

    def xattr(self, which: DefaultItems):
        """
        Set the extensible attribute of a file
        """
        parameter = input("key:")
        value = input('value:')
        for w in which:
            w.metadata.set(parameter, value)

    def tag(self, which: DefaultItems, tag: OptionalArgument):
        """
        Tag file with <tag>. Tag is optional, leaving it out will present a choice
        which you can use to choose already user-defined used tags used on other files.
        """
        verbose = True
        for item in which:
            if not tag:
                projects = self.cntrl.list_current_projects()
                
                verbose and print("Path: {}".format(item.full_path))
                tag = self.cntrl.select_wrapper(projects, lambda x:x.name,
                                                header="Tag for {} {}".format(
                                                    item.desc, item.name))
                if tag not in projects:
                    verbose and print("adding new project")
                    self.cntrl.new_project(tag)

            if not which or not tag:
                verbose and print("no which and no tag!")
                raise BadArguments("User escaped!")
            
            self.finderapp.spotlight_add_comment(item.full_path, self.cntrl.encode_tag(tag))


    def tags(self, *args):
        """
        tags <file>

        'Simply displays the tags that are associated with the file'
        """
        if not args:
            raise BadArguments("Which file?")
        which = self.cntrl.get_item(" ".join(args))
        comment = self.finderapp.spotlight_get_comment(which.full_path)        
        s = self.cntrl.encode_tag('(.*?)', for_pass_to_re_module=True)
        tags = re.findall(s, comment)
        print("Tags for {} {}:".format(which.desc, which.name))
        if not tags:
            print("<none>")
        else:
            print(", ".join(tags))
        input(": ")

    def info(self, *args):
        if not args:
            raise BadArguments("Info on which item?")
        which = self.cntrl.get_item(" ".join(args))
        input(repr(which))

    def new(self, *args):
        """
        new folder | file <*name>

        'Create a folder or file with a certain name'
        'name is optional, will be prompte if left out'
        """
        if not args or not args[0] or not hasattr(args[0], 'lower') or not args[0].lower() in ['file', 'folder', 'project']:
            filefolder = self.cntrl.select_wrapper(['folder', 'file', 'project'], lambda x:x.name,
                                               header="New file or folder?:")
        else:
            filefolder = args[0]
        name = ""
        if len(args) > 1:
            name = " ".join(args[1:])
        elif filefolder == 'file':
            if not name:
                name = input("Enter file name: ")
            self.command_line("touch '{}'".format(os.path.join(self.cntrl.current_directory, name)))
        elif filefolder == 'folder':
            if not name:
                name = input("Enter folder name: ")
            self.command_line("mkdir '{}'".format(os.path.join(self.cntrl.current_directory, name)))

        elif filefolder == 'project':
            if not name:
                name = input("Enter project name: ")
            self.cntrl.new_project(name)
