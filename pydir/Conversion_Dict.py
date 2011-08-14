class Conversion_Dict(dict):
    """
    Dictionary that returns index itself if not in dictionary
    Create it with init call, allows the syntax:
    new = Convertion_Dict(
        hi='not'
        )[original]
    """
    def __init__(self, *d, **kwargs):
        if d:
            for key in d[0]:
                self[key] = d[0][key]
        for key in kwargs:
            self[key] = kwargs[key]

    def __getitem__(self, index):
        if index in self:
            return dict.__getitem__(self, index)
        else:
            return index

if __name__ == "__main__":

    pass
