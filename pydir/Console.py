import os

class Overflow(Exception): pass

def getTerminalSize():
    s = os.popen('stty size', 'r').read().split()
    return ( int(s[1]), int(s[0]) )

class Output:
    """
    Class that outputs to screen based available dimensions
    """

    def __init__(self, _list=[]):
        self._list = _list
        self.width_padding  = 1  # room for \n
        self.height_padding = 2  # room for one-line header and input
        self.reset_bottom_message()

    def set_list(self, _list):
        verbose = False
#        if not _list:
#            raise Exception("Cannot set null list?")
        self._list = _list
        verbose and print("Set the list!")

    def copy(self):
        return self._list[:]

    def swap(self, _list):
        result = self.copy()
        self.set_list(_list)
        return result
    
    def no_columns_required(self):
        """
        Returns true if we want columns or not
        """
        return len(self._list) <= self.columns

    def reset_bottom_message(self):
        self.bottom_message = []

    def set_bottom_message(self, m):
        if not m:
            self.reset_bottom_message()
        elif isinstance(m, list):
            self.bottom_message = m
        else:
            self.bottom_message = m.split('\n')

    def calc_size(self):
        """
        return (width, height)
        """
        s = getTerminalSize()
        # last line has else 0 because split('\n') on an empty string returns 1... wrong
        return (s[0] - self.width_padding,   # [0]
                s[1] - self.height_padding \
                - (len(self.bottom_message) if self.bottom_message else 0)) # [1]

    def calc_padding(self, start_at):
        verbose = False
        verbose and print("start_at is {}".format(start_at))
        return len(str(len(self._list) + start_at)) + 1

    def calc_max_file_text(self):
        return 30 - self.padding

    def calc_columns(self):
        initial = int(self.width / (self.max_file_text + self.padding))
        if (self.max_file_text + self.padding) * initial > self.width:
            initial -= 1
        return initial

    def calc_max(self):
        return self.height * self.columns

    def calc_max_each_one(self):
        return self.height * self.columns

    def calc_dimensions(self, start_at):
        """
        Set state
        Called repeatedly because it assumes dynamic base
        """
        verbose = False
        if not self._list:
            verbose and input("Called calc_dimensions without any list")
        self.width, self.height = self.calc_size()
        verbose and input("width is {}".format(self.width))
        self.padding = self.calc_padding(start_at)
        verbose and input("padding is {}".format(self.padding))
        self.max_file_text = self.calc_max_file_text()
        verbose and input("max_file_text is {}".format(self.max_file_text))
        self.columns = self.calc_columns()
        verbose and input("columns is {}".format(self.columns))
        self.max = self.calc_max()
        verbose and input("max is {}".format(self.max))
        self.max_each_one = self.calc_max_each_one()
        verbose and input("max_each_one is {}".format(self.max_each_one))

    def columnize(self, _list=[],
                  pre_process=None, process=None, post_process=None, truncate=None,
                  start_at=0):
        """
        Puts the list into columns for proper output
        """
        if not _list:
            _list = self._list
        verbose = False
        self.calc_dimensions(start_at)
        while (self.max_file_text + 1) * self.columns < self.width - 1:
            # minor adjustment
            self.max_file_text += 1
        verbose and print('max_file_text: {}'.format(self.max_file_text))
        if len(_list) > self.max_each_one:
            pass
#           raise Overflow()

        if self.no_columns_required():
            for num in range(len(_list)):
                item = _list[num]
                if item:
                    ok = True
                    if pre_process:
                        ok = pre_process(item)
                    if truncate:
                        truncate(item, self.width-1)
                    else:
                        item = item[:self.max_file_text]
                    if post_process:
                        number, printable = post_process(item, num, self.width-1)
                    if ok:
                        if str(number).isdigit():
                            number = int(number) + start_at
                        else:
                            if len(str(num)) > len(number):
                                number = '{}{}'.format(' ' * (len(num) - len(number)), number)
                        yield "{0} {1}".format(number, printable)
                    else:
                        if str(number).isdigit():
                            number = int(number) + start_at
                        else:
                            if len(str(num)) > len(number):
                                number = '{}{}'.format(' ' * (len(num) - len(number)), number)
                        yield "{0} {1}".format(number, printable)
        else: 
            # requires columns; need to calculate it all out
            # front load the arithmetic to get it right        
            length = len(_list)
            num_in_column = int(length / self.columns)
            verbose and print("length: {}, num: {}".format(length, num_in_column))
            if length % self.columns > 0:
                # left-heavy
                num_in_column += 1
            verbose and print('num_in_column: {}'.format(num_in_column))
            offset = 0
            for i in range(num_in_column):
                row = []
                for k in range(0 + i, length, num_in_column):
                    n, item = str(k + start_at), _list[k]
                    if item:
                        local_max = self.max_file_text - (len(n)+1)  # max taking into account printing of numbers
                        if pre_process:
                            ok = pre_process(item)
                        else:
                            ok = True
                        if truncate:
                            truncate(item, local_max)
                        if process:
                            process(item, local_max, columns=True)

                        # calc whitespace here because post_process might return color characters
                        white_space = ""
                        if len(str(item)) < local_max:
                            white_space = " " * (local_max - len(str(item)))
                        if post_process:
                            number, item = post_process(item, k + start_at, local_max)
                        else:
                            number, item = str(k + start_at), str(item)
                        if ok:
                            if str(number).isdigit():
                                pass
                            else:
                                if len(n) > len(number):
                                    number = '{}{}'.format(' ' * (len(n) - len(number)), number)
                            row.append("{0} {1}{2}".format(number, item, white_space))
                        else: # print 
                            if str(number).isdigit():
                                pass
                            else:
                                if len(n) > len(number):
                                    number = '{}{}'.format(' ' * (len(n) - len(number)), number)
                            row.append("{0} {1}{2}".format(number, item, white_space))

                yield " ".join(row)

    def screenful(self, _list=[],
                  pre_process=None, process=None, post_process=None, truncate=None, overflow_delegate=None,
                  start_at=0):
        """
        Returns list of items processed for screen output
        If resulting list would result in overflow of the screen, control goes to overflow_delegate,
        which should pair down the list appropriately.
        Columnize is called to derive the columns.
        If resulting list is still an overflow, columnize will fail
        Expecting list to come back as well
        """
        verbose = False
        if not _list:
            _list = self._list
        self.calc_dimensions(start_at)
        verbose and print("Max calculated as {0} x {1} = {2}".format(self.height, self.columns, self.max))
        overflow_list = _list
        if len(_list) > self.max:
            if overflow_delegate:
                # the delegate should pair down the list (after processing) and return immediate one now
                overflow_start, overflow_list = overflow_delegate(_list, self.max)
                if overflow_start:
                    start_at = overflow_start
            else:
                raise Overflow()
        for row in self.columnize(_list=overflow_list,
                                   pre_process=pre_process,
                                   process=process,
                                   post_process=post_process,
                                   truncate=truncate,
                                   start_at=start_at):
            yield row

        if self.bottom_message:
            for line in self.bottom_message:
                yield line
            self.reset_bottom_message()

def test_screenful():
    import random
    alpha = [ chr(c) for c in range(ord('a'), ord('z')+1) ]
    result = []
    for times in range(100):
        l = random.randint(1, 24)
        result.append("".join(random.sample(alpha, l)))
    o = Output(result)
    for item in o.screenful():
        print(item)

if __name__ == '__main__':
    test_screenful()
