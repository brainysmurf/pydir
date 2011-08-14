class lister:
    def __init__(self):
        self.reset()
        self._save = None

    def reset(self):
        self._list = []

    def save(self, what):
        self._save = what
    
    def __call__(self, *args):
        if not self._list:
            self._list = ['zowie', 'howdie']
            if self._save:
                self._list.append(self._save)
        return self._list



l = lister()
print(l())
print(l())
l.save(l()[0])
l.reset()
print(l())
