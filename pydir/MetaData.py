"""

Provides a workaround for giving file objects
dynamic values ... metadata

"""

import shelve
import os

class SimpleStore():
    def __init__(self, path_to_file):
        self._shelve = shelve.open(path_to_file, writeback=True)

    def __del__(self):
        if shelf.shelve:
            self._shelve.close()

    def _convert(self, what):
        return "{}{}".format('com_brainysmurf_dir_', str(what).replace(' ', '_').replace('.', '_'))

    def write(self, _which, _key, _value):
        _key = self._convert(_key)
        _which = self._convert(_which)
        if _which not in self._shelve:
            self._shelve[_which] = {}
        self._shelve[_which][_key] = _value

    def has(self, _key):
        _key = self._convert(_key)
        return _key in self._shelve

    def combine(self, _which, _dict):
        """
        Copies keys in _which over to _dict
        Also copies 'path' key into into metadata store
        """
        _which = self._convert(_which)
        if not _which in self._shelve:
            return
        for key in self._shelve[_which]:
            if not key in self._shelve:
                _dict[key] = self._shelve[_which][key]
        if 'full_path' in _dict:
            self.write(_which, 'full_path', _dict['full_path'])

    def clear(self, *args):
        if len(args) == 1:
            del self._shelve[str(args[0])]
        elif len(args) == 2:
            if str(args[0]) in self._shelve and str(args[1]) in self._shelve[str(args[0])]:
                del self._shelve[str(args[0])][str(args[1])]

    def metadata(self, _id):
        _id = self._convert(_id)
        if _id in self._shelve:
            return self._shelve[_id]
        else:
            return None

class AbstractStore(SimpleStore):
    """
    shelfable object that 
    """
    def __init__(self, path_to_file, top_nodes=[]):
        SimpleStore.__init__(self, path_to_file)
        self._node = None
        self._top_nodes = top_nodes
        for node in self._top_nodes:
            self._shelve[node] = {}

    def __del__(self):
        if self._shelve:
            self._shelve.close()

    def __getattr__(self, name):
        if name.startswith('write_to_'):
            _node = name[9:]
            if not _node in self._shelve:
                raise AttributeError("AbstractStore object call to {}; does not have node {}".format(name, _node))
            else:
                self._node = _node
                return self._write_to
        elif name.startswith('has_'):
            _has_what = name[4:]
            self._has_what = _has_what
            return self._has
        elif name.startswith('combine_'):
            _with_what = name[8:]
            print(_with_what)
            self._combine_what = _with_what
            return self._combine
        elif name.startswith('clear_'):
            _clear_what = name[6:]
            print(_clear_what)
            self._clear_what = _clear_what
            return self._clear
        else:
            return object.__getattr__(self, name)
    
    def _write_to(self, _key, _value):
        if not self._node:
            raise NotImplemented("Don't call _write_to directly")
        self._shelve[self._node][_key] = _value
        self._shelve.sync()
        self._node = None

    def _clear(self, _key):
        if not self._clear_what:
            raise NotImplemented("Don't call _clear directly")
        _clear_what = self._clear_what
        self._clear_what = None
        del self._shelve[_clear_what][_key]

    def _has(self, name):
        if not self._has_what:
            raise NotImplemented("Don't call _has directly")
        _node = self._has_what
        self._has_what = None
        return name in self._shelve[_node]

    def _combine(self, _which, _dict):
        for key in self._shelve[self._combine_what][_which]:
            _dict[key] = self._shelve[self._combine_what][_which][key]

class TreeStore(AbstractStore):
    """

    """
    def __init__(self, path):
        AbstractStore.__init__(self, path, top_nodes=['id'])

class some_object():
    def __str__(self):
        for key in self.__dict__:
            return "{}:{}".format(key, self.__dict__[key])

if __name__ == '__main__':
    from Filer import File_list
    
    os.chdir('/Users/brainysmurf/Desktop')
    os.listdir('/Users/brainysmurf/Desktop')
    store = TreeStore('/tmp/storefront')
    store.write_to_id(38384, {'default':23894})
    if store.has_id(38384):
        print("SUCCESS")
    print(store._shelve)

    d = some_object()
    store.combine_id(38384, d.__dict__)
    print(d)
