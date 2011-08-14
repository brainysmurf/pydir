"""
Snippet

An object that is a dictionary but can input and output to human readable form
Each key and value is strictly defined as strings with no spaces
Keys are output in alphabetical order, and the colons are lined up
to make it more readable

"""


class Snippet(dict):

    def __init__(self, *args):
        if args:
            self._pack(args[0])
        else:
            dict.__init__({})

    def _pack(self, _d):
        for key in _d:
            self[str(key.strip())] = str(_d[key.strip()])

    def human_readable_form(self):
        max_length = max([len(self[i]) for i in self])
        print(max_length)
        for key in sorted([k for k in self]):
            whitespace = " " * (max_length - len(self[key]))
            yield "{}{}:{}\n".format(key, whitespace, self[key])

if __name__ == '__main__':

    s = Snippet({'zup':'yo', 'mywifeis':'yuri', 'hi':'there'})
    print("".join(s.human_readable_form()), end="")
