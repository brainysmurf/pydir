"""
Main parser routines
See Dir.py Dir object parse_input for docstring
"""
from pydir.Menu import BadArguments, DefaultItems
import os
from colors import red
import re

user_home_directory = os.path.expanduser('~')
path_to_trash       = os.path.expanduser('~/.Trash')
path_to_dir_folder  = os.path.expanduser('~/.dir')


def Parse_Input(self, user_input):
    verbose = False
    verbose and print("parse_input with: {}".format(user_input))
    handled = False
    converted_digits_already = False

    # TODO: Confirmed I don't need this call
    #self.list_current_directory().do_indexing()

    if not user_input.strip():
        # special case where user wants 'default' selection
        defaults = self.list_current_directory().default
        folders = [f for f in defaults if f.is_directory]
        if folders and len(folders) == 1:
            self.set_directory(folders[0].full_path)
        elif folders and len(folders) > 1:
            selection = self.select_wrapper([[f.name, f.full_path] for f in folders], lambda x:x.full_path, header="More than one directory found in selection:")
            if selection:
                self.set_directory(selection)
        if folders:
            defaults = [f for f in defaults if not f.is_directory]
        if defaults:
            self.menu.open(defaults, None)
        return

    if not all(map(lambda x: x == '-', user_input)) \
           and not re.sub(r"[, \d-]", "", user_input): # exclude '-' strings
        converted_digits_already = True
        if user_input[0] == ',':
            add_kind = True
            user_input = user_input.lstrip(',')
        else:
            add_kind = False
        _list = []
        length = len(self.list_current_directory())

        def match_callback(obj):
            nonlocal _list
            nonlocal length
            obj_str = obj.group(1)
            inner = re.match(r"(\d{0,})-(\d{0,})", obj_str)
            if inner:
                first = inner.group(1)
                last  = inner.group(2)
                if not first:
                    first = 0
                else:
                    first = int(first)
                if not last:
                    last = (length - 1)
                else:
                    last = int(last)
                step = -1 if not last > first else 1
                for i in range(first, last+1, step):
                    if i < length:
                        _list.append(str(i))
            else:
                if int(obj.group(0)) < length:
                    _list.append(obj_str)
            return ""

        p1 = r"[, ]?(\d{0,}-\d{0,})"
        p2 = r"[, ]?(\d+)"
        for pattern in (p1, p2):
            user_input = re.sub(pattern, match_callback, user_input)

        if not _list:
            self.errors.handle_error('out of range', user_input)
            return
        
        if add_kind:
            self.highlight(self.list_current_directory().index(int(_list[0])))
        else:
            self.single_out(self.list_current_directory().index(int(_list[0])))
        for item in _list[1:]:
            this = self.list_current_directory().index(int(item))
            self.highlight(this)
        return self.appropriate_page_or_none()
        
    if '...' in user_input and self.user_saved:
        user_input = user_input.replace('...', self.user_saved)

    if '~' in user_input:
        user_input = user_input.replace('~', user_home_directory)

    if user_input == '..':
        self.set_current_directory(self.list_current_directory()._folder.parent_directory)
        handled = True

    if user_input.startswith('cd '):
        try:
            path = user_input[3:].strip("'").strip('"')
            self.set_current_directory(path)
            handled = True
        except OSError:
            self.errors.handle_error('path does not exist', path)
            return

    if user_input == self.quit_request:
        self.stop()
        return None

    elif user_input.startswith('+'):
        verbose and print("Detected + and we're on page {}".format(self.pages['page']))
        if self.pages:
            verbose and print("Upping pages")
            return self.pages['page'] + user_input.count('+')
        else:
            input("No page to turn")
            return
    elif user_input.startswith('-'):
        if self.pages:
            return self.pages['page'] - user_input.count('-')
        else:
            input("No page to turn")
            return

    if not handled:

        try:
            handled = self.menu._parse(user_input)
            verbose and print("handled by menu._parse")
        except BadArguments as bad:
            handled = True

    verbose and handled and print("handled already before first if handle statement")
    verbose and not handled and print("NOT handled already before first if handle statement")

    if not handled:
        which = None
        potential_list = self.walk(user_input)
        if potential_list is None:
            handled = True
            potential_list = []  # poor man's goto
        # since walk returns a list of lists
        # treat it a bit differently than other select_wrapper calls
        if len(potential_list) == 1:
            which = potential_list[0][0].lower()
        elif len(potential_list) > 1:
            verbose and print(potential_list)
            which = self.select_wrapper(potential_list, lambda x:x.full_path, 
                                        header='Found more than one "{}"'.format(
                                            user_input.lower()))

        if which:
            # checks to see if it's a project being asked for...
            if which in self.list_current_projects():
                try:
                    verbose and print("seeing if menu.project knows what to do with it")
                    handled = True
                    self.menu.project(which)
                except BadArguments:
                    handled = True
            # otherwise it's just a regular command
            else:
                user_input = self.determine_command(which)
                if user_input.startswith('cd '):
                    try:
                        self.set_current_directory(which)
                        handled = True
                    except OSError:
                        self.errors.handle_error('path does not exist', red(which.full_path))

        if not handled:
            # Work towards sending it to the shell
            if not converted_digits_already:
                user_input = self.replace_digits_with_paths(user_input)

            if user_input.startswith('rm '):
                print('*******')
                print(user_input)
                print('*******')
                yesno = input('Really?')
                if yesno.lower().startswith('n'):
                    return

            if './' in user_input:   # requiring use of slash prevents extensions from being messed up
                where = user_input.find('./')
                user_input = user_input[:where] + self.current_directory + user_input[where+1:]

            self.user_filter = None
            try:
                result = self.user_command.run_command(user_input)
            except ValueError:
                self.errors.handle_error('unbalanced-quotation', red(user_input))
                result = None

            if result and result[0]:
                if isinstance(result[0], type(b'')):
                    input(result[0].decode())
                else:
                    if len(result[0].split('\n')) > 1:
                        input(result[0])
                    else:
                        print(result[0])
            if result and result[1]:
                input("Error: {0}".format(result[1]))





