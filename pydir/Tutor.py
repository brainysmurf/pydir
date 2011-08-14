"""
Strings to use with the tutorial
The third none item is reserved for callbacks
"""
import os

class TutorInfo():
    TutorInfo = {
        'basic': [
                (None, "Welcome to the tutor, yo!\n\nHere you will learn how to navigate your file system with a minimum of keystrokes. Files are green, folders are yellow, everything is columnized and fills up the entire screen (if there's enough files). Right now you're at your home directory. Type 'desktop' to navigate to your desktop folder. It doesn't matter where you are, it'll always take you to the ~/Desktop folder. Case doesn't matter.", None),
                ([os.path.expanduser('~/Desktop/')], "These are the files on your desktop that the size of the screen can display. Notice the first line shows you the path? All these files can be accessed by typing the number associated with it. You can also go up one directory just by typing '..'.\n\nDo that now.", None),
                ([os.path.expanduser('~/')], "Now navigate to the Documents folder. Select it by typing the number associated with it, then press return. Use a plus sign to find it on the next screen if it's not visible here.", None),
                ([os.path.expanduser('~/Documents/')], "Right, so that's how you get around. It's a lot like using the shell directly, except faster. Cool thing is, you can use any shell commands too. Try making a temp folder, call it 'AAAAH' and create it by typing 'mkdir AAAAH'.", None),
                (['mkdir'], "Good. You see it has created the new folder by going back to the shell briefly and executed your command. The new folder is light blue because that's the most recently modified item. Since it's the default, there's no number, but a return indicator, which means you can just type return to change directory to there. Just hit return now!", None),
                ([''],  # indicates user hit return
                 "Right, so here we are in your newly created folder, but there's nothing there, and so nothing is listed. Let's put a bunch of files there so we can practice navigating without worry. Type the command 'manyfiles'.", None),
                (['manyfiles'], "That command (we'll learn more about commands later) created a bunch of dummy files for us to use.\nNotice that there is a Documents.txt TEXT FILE there (the first one), which represents a name collision with a FOLDER that we aleady know and love: ~/Documents. What happens if we type 'documents', how does it know which one I want? Try it and find out.", None),
                (['documents'], "How clever. It presents me with a choice. Choose the current directory, which you can select just by typing 0.\nIt'll open the file for you, because it knows it's a file rather than a directory.", None),
                (None, "Text files are automatically opened by your default text editor. So let's continue the on-screen navigation controls by noting that there is a plus sign on the bottom-left of the screen. That means there are more files than screen space. Type '+' to get to the next screen.", None),
                (['+'], "A '-' gets you back.", None),
                (['-'], "You can also input multiple plus signs to jump ahead. Try inputting two or three of them.", None),
                ('+'*3, # indicates multiple entries
                 "And now navigate to the parent directory so we can delete this folder, just type '..', do that now.", None),
                ([os.path.expanduser('~/Documents/')], "Let's delete that folder, because we don't need it. We could do that by typing 'rm -r AAAAH', but that's a lot of typing. Plus, it's dangerous; it'd be better to put it in the trash. So use the command 'trash AAAAH'. Even better, trash followed by the number that directory is associated with. Try it.", None),
                (["trash"], "It's gone. Did you have your volume turned up? You got the trash sound because we're connected to the Finder via AppleScript. Trash is just one of these automatic commands, which you can find by using the built-in command 'commands'. Type that now.", None),
                (['commands'], "What you have here is a list of all available commands. Select 'new', and you'll be assisted be the ever-helpful documentation system, which will explain what each commands expects as arguments. Pick one.", None),
                ([os.path.expanduser('~/Documents/')], "The documentation (white text) that appears tells you what each command does, and how to use it. So instead of using the shell-specific mkdir, you can just use 'new folder'. There are lots of commands, but now go back to commands to learn how to tag files.", None),
                (['commands'], "Select tag by typing the number associated with 'tag' (Careful, not 'tags'!).", None),        
                ([os.path.expanduser('~/Documents/')], "Tag lets you tag your files, so that you can easily find them later. As you can see, the documentation says to type tag and then the file number. First, create a file using the 'new file' command, andthen tag it by typing 'tag' and the number associated with that file.", None),
                (['tag'], "Choose 'default'.", None),
                ([os.path.expanduser('~/Documents/')], "So it doesn't look like it did much, but now that file is accessible by going to the default menu, which you can get to by typing the tag it's associated with: 'default'.", None),
                (['default'], "This menu has all the files on your system tagged as 'default'. Collections of files and folders under the same tag is called a 'project'. Keeping with an emphasis of easy recollection, is that these files are now accessible from anywhere, by name minus extension, without having to go to this menu. So that means the Documents folder and Desktop can be accessed simply by typing their name. Cancel out of this selection by typing 'q' (or cntrl-C)", None),
                ([os.path.expanduser('~/Documents/')], "Now switch to the Desktop folder by typing 'desktop'. It is not case sensitive (in fact, if there is a name conflict you are presented with a choice).", None),
                ([os.path.expanduser('~/Desktop/')], "Right. So you are very easily able to switch between folders just by recalling its name. Now for some real magic. Search your documents folder for every file that has pdf in it, by typing 'search pdf'.", None),
                ('search pdf', "Every file with pdf in the name. Pick a file, and type its associated number.", None),
                (None,"That file opens, and your at the directory in which that file is contained. The tutor has now concluded.", None),
                (None,"Leave the tutor by typing 'tutorial off', or just 'q'", None),
                (None, "", None),
                ],
        'intermediate': [
                ([], "", None),
                                     ]}

    def __init__(self):
        self._info = self.TutorInfo.copy()
        self.where = 0
        self.change_mode('basic')

    def change_mode(self, mode):
        self._mode = mode

    def delete_x_times(self, x):
        old_where = self.where
        for time in range(x):
            self._info[self._mode].pop(0)
        self.where = old_where + x

    def update_tutor(self, check):
        _tutor = self._info[self._mode]
        result = None
        if _tutor:
            if check == []:
                result = _tutor[0][1]
                _tutor.pop(0)
            if not _tutor[0][0] or check in _tutor[0][0]:
                result = _tutor[0][1]
                _tutor.pop(0)
                self.where += 1
        return result
