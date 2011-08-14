import sys

class StandardOut():
    def clear_screen(self):
        print("\x1b[H\x1b[2J")

    def write(self, what):
        print(what)

class Error_Handler():
    def __init__(self, error_dict, output=None):
        if not output:
            self.output = StandardOut()
        else:
            self.output = output
        self._error_dict = error_dict

    def handle_error(self, key, *args):
        if hasattr(self.output, 'clear_screen'):
            self.output.clear_screen()
        print(file=self.output)
        if key not in self._error_dict:
            raise AttributeError("Error {} not recognized".format(key))
        error_message = self._error_dict[key]
        if not error_message.count('{}') == len(args):  #TODO better algorythm
            print("Arguments don't match the error message, (or else I need to update the algorythm",
                  file=self.output)
        print(error_message.format(*args), file=self.output)
        print('[return to continue, cntrl-c to exit]', file=self.output)
        input()

    def define_errors(self, error_dict):
        self._error_dict = error_dict

if __name__ == '__main__':

    yikes = {'iloveyou':'{}'}
    error = Error_Handler(yikes)
    error.handle_error('iloveyou', 'bunny')
