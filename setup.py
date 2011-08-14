from setuptools import setup, Extension
from setuptools.command.install import install as _install
import sys
import shutil
import os

dir_version = '0.7'

class install(_install):
    def run(self):
        _install.run(self)
        version = "{}.{}".format(sys.version_info.major, sys.version_info.minor)
        the_path = "/Library/Frameworks/Python.framework/Versions/{}/bin".format(version)
        #shutil.copy('scripts/dir', the_path) scripts no longer used

        first_line = '# dir (version {0}) application modifying your bash profile starting here:\n#DO NOT MODIFY'.format(dir_version)
        user_bash_profile = os.path.expanduser('~/.bash_profile')
        if not os.path.exists(user_bash_profile):
            open(user_bash_profile, 'w') # touch
        with open(user_bash_profile) as f:
            user_profile = f.readlines()

        if not first_line in user_profile:
            with open(os.path.expanduser('~/.bash_profile'), 'a') as f:
                f.write('\n')
                f.write(first_line)
                f.write('\ntouch /tmp/tee_output.txt\n')
                f.write("""alias drop='cd "`cat /tmp/tee_output.txt| tail -2 | perl -ne "chomp and print"`"'""")
                f.write("\n#end dir modification\n")            
        print("Success")
        print()
        print("You may now launch dir program anytime by typing 'dir' at the console prompt")
        yesno = input("Would you like to launch it now with the tutorial? (y/n): ")
        if yesno.lower() == 'y':
            from AppleScriptWrapper.Basic import get_front_app
            get_front_app().keystroke('dir -tutorial\n')

if sys.version_info >= (3,0):
	root_dir = 'pydir'
else:
	raise Exception("Enter: 'python3 setup.py install' on command line to install\nRequires python3\n")

setup (name = 'dir_app',
       cmdclass = {'install': install},
       packages = [root_dir],
       version = dir_version,
       license = 'Public Domain',
       description = 'Navigate your directory structure, use easy-to-remember commands, fast',
       author = "Adam Ryan Morris",
       author_email = "amorris@mistermorris.com",
       url = "",
       )
