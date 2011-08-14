#! /usr/bin/env python3

"""

SHELL EMULATOR: python 3000
You pass it a string command line, it's smart enough to know what to do:
1) If command can be interpreted by the os module, it is
2) Everything else is passed to Popen
3) Mixed handling: glob (processed then passed to Popen)
TODO: Support multiple statements

"""

import subprocess
import shlex
import os
import re
from glob import glob

def extract_from_target_until_space(s, target, space):
    """
    String manip routine that does what it says
    Regular expressions sometimes are too complicated to bother with
    """
    if not '*' in s:
        return None
    s = " {0} ".format(s)  # simplifies logic if we know it's padded by spaces

    where_aster = s.find(target)
    for where in range(where_aster - 1, 0, -1):
        if s[where] == space:
            left = where + 1
            break
    for where in range(where_aster + 1, len(s)):
        if s[where] == space:
            right = where
            break

    return s[left:right]

def copy_to_clipboard(t):
    p1 = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
    p1.stdin.write(bytes(t, 'utf-8'))

class Shell_Emulator(object):
    def __init__(self, avoid_recursion=(), errors=None):
        self.send_to_shell = subprocess.Popen
        self.parse_command = shlex.split
        self.CommandNotRecognized = OSError
        self.errors = errors
        if not isinstance(avoid_recursion, list):
            # make it a list, [None] even
            avoid_recusion = [avoid_recursion]
        self.avoid_recursion = avoid_recursion

    def __getattribute__(self, name):
        if name == "current_directory":
            return os.getcwd()
        elif name == "parent_directory":
            return os.path.split(self.current_directory)[0]
        else:
            return object.__getattribute__(self, name)

    def handle_error(self, key, *args):
        if self.errors and hasattr(self.errors, 'handle_error'):
            self.errors.handle_error(key, *args)

    def simple(self, command_string):
        keywords = {'stdout': subprocess.PIPE,
                        'stderr': subprocess.PIPE}
        return self.send_to_shell(self.parse_command(command_string), **keywords).communicate()

    def _which_check(self, command):
        """
        Use which to find the path of the command assumed to be one word long
        returns None if not found
        """
        if isinstance(command, list):
            command = command[0]
        else:
            command = command.split(' ')[0]
        verbose = False
        verbose and print("which_check: {}".format(command))
        result = self.run_command('/usr/bin/which {0}'.format(command))[0].decode().strip()
        if result:
            verbose and print("which_check returning {}".format(result))
            return result
        else:
            verbose and print("which_check returning None")
            return None # raise error        

    def run_command(self, command_string, silence=True, will_send_to_shell=None, did_send_to_shell=None):
        """
        Sends command to the shell:
        raises CommandNotRecognized if a result from which leading returns none
        """
        verbose = False
        if command_string in self.avoid_recursion:
            return [None, "Avoiding recursion"]
        verbose and print("Entered run_command with command_string {}".format(command_string))
        if not command_string:
            return ["", "Failed: No command to run"]
        if silence:
            keywords = {'stdout': subprocess.PIPE,
                        'stderr': subprocess.PIPE}
        else:
            keywords = {}

        # glob-alize
        if '*' in command_string:
            # replace asterix in string with list of globbed items
            # only supports a single aster in this string
            match = extract_from_target_until_space(command_string, '*', ' ')
            where = command_string.find('*')
            file_list = glob(match)
            command_string = "{0}{1}{2}".format(command_string[:where], " ".join(file_list),
                                                command_string[where+len(match):])

        # change commands
        command_string = command_string.strip()
        where_space = command_string.find(' ')
        verbose and print("where_space: {} for string {}".format(where_space, command_string))

        try:

            if command_string.startswith('/usr/bin/which'):
                pass   # short circut the key which calls

            elif len(command_string.split(' ')) == 1:
                # short circut single word commands, which are far simpler
                result = self._which_check(command_string)
                if result:
                    command_string = result
                else:
                    raise self.CommandNotRecognized

            elif where_space > 0 and not command_string.startswith('/'):  # not startswith avoid endless recurssion
                leading, rest = command_string[:where_space], command_string[where_space+1:]
                verbose and print("leading is {}, and rest is {}".format(leading, rest))
                if leading in self.avoid_recursion:
                    verbose and print("Avoiding recursion")
                    return [None, "Avoiding recursion"]
                if leading == 'cd':
                    if not rest == ('..'):
                        os.chdir(rest.strip("'").strip('"'))   # ' are used to handle spaces often, so
                    else:
                        os.chdir(self.parent_directory)
                    return [self.current_directory, None]

                # recurse
                result = self._which_check([leading])  # avoid more processing by sending it as list
                if result:
                    command_string = '{0} {1}'.format(result, rest)
                else:
                    raise self.CommandNotRecognized

            else:
                verbose and print("HUH: {}".format(command_string))

            if will_send_to_shell:
                command_string = will_send_to_shell(command_string)

            verbose and print("Sending this command to the shell: {0}".format(self.parse_command(command_string)))
            result = self.send_to_shell(self.parse_command(command_string), **keywords).communicate()
            verbose and print(result)


        except self.CommandNotRecognized:
            self.handle_error('command not recognized', command_string)
            verbose and print("Command '{0}' not recognized".format(command_string))            
            return None

        
        if did_send_to_shell:
            result = did_send_command(result)
        return result

if __name__ == '__main__':

    shell = Shell_Emulator()
    print("HERE WE GO")
    print(shell.simple('which open'))
