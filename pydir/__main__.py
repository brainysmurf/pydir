#!/usr/bin/env python3 

from pydir.DirThreads import DirThreads
from pydir.Menu import PydirMenu
from pydir.Tutorial import TutorialDir
import sys

class DirApp(DirThreads):

    # defining tutorial here avoids recurive import
    def tutorial(self, on):
        if on:
            self._tutor = TutorialDir()
            self._tutor.start(self.current_directory)

        else:
            raise BadArguments("Not on!")


def main(argv):
    path = argv[0]  # must be from dir file, a horrible coupling indeed
    argv.pop(0)
    if len(argv) > 1:
        if argv[0] == '-tutorial':
            d = TutorialDir()
            if len(argv) == 2 and argv[1].isdigit:
                d.tutor_info.delete_x_times(int(argv[1]))
            else:
                d.set_current_directory(os.user.expanduser('~'))
            d.start(path)
            
    elif len(argv) == 1:
        if argv[0] == '-tutorial':
            d = TutorialDir()
            d.start(path)
        else:
            d = DirApp()
            d.start(path)
    else:
        DirApp().start(path)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
