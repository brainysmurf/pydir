#! /usr/bin/env python3
"""
Filer

Turns a file into a record of information
Symlinks in particular are followed
"""

import os
from pydir.DirXattr import DirTagger

def build_from_scratch(_list):
    scratch = File_list("", [])
    scratch._list = _list
    scratch.initialize()
    return scratch

class DefaultList:
    """
    A list of strings: names of files that are defaults
    """
    def __init__(self, _list):
        self._list = _list
        self.where = None

    def __iter__(self):
        self.where = 0
        return self

    def __next__(self):
        if not self._list or self.where >= len(self._list):
            self.where = None
            raise StopIteration
        else:
            where = self.where
            self.where += 1
            return self._list[where]

    def __getitem__(self, i):
        return self._list[i]

    def __len__(self):
        return len(self._list)

    def __repr__(self):
        return "\n".join([str(item) for item in self])

    def add(self, what):
        if isinstance(what, list):
            self._list.extend(what)
            for w in what:
                w.default = True
        else:
            self._list.append(what)
            what.default = True

    def single_out(self, what):
        verbose = False
        verbose and print("single_out:")
        for i in self._list:
            verbose and print(i)
            i.default = False
        self.add(what)

    def remove(self, what):
        verbose = False
        if what in self._list:
            what.default = False
            verbose and print("{}.default = False".format(what))
            del self._list[self._list.index(what)]
            if self.where is not None:
                self.where -= 1
            verbose and print("del self._list[self._list.index({})]".format(what))
            verbose and print(self._list)
        
class File_list():
    """
    List of sortable file objects, tracks information
    """
    def __init__(self, path, _list, klass=None):
        if not klass:
            klass = File_object
        self._list = [klass(path, _list[i], i) for i in range(len(_list))]
        self._folder = Folder_object(path)
        self._path = path
        self.initialize()

    def initialize(self):
        """
        Set up state
        """
        #
        # Set up most recents
        #

        # exclude hidden and files that start with __ and end with __
        # TODO: Allow user to decide this
        mod_dates = [l.last_modified for l in self._list if not l.is_support_file]
        when = max(mod_dates) if mod_dates else 0
        recents = self.which_equals('last_modified', when)
        if recents:
            for target in recents:
                target.most_recent = True
        self.reset_most_recents()

        # post-process by setting up default
        self.default = self.derive_default()

    def __iter__(self):
        self.iter_index = 0
        return self._list

    def __next__(self):
        index = self.iter_index
        if len(self._list) >= index:
            raise StopIteration
        self.iter_index += 1
        self._list[index]

    def __repr__(self):
        return "\n".join([str(item) for item in self._list])

    def __len__(self):
        return len(self._list)

    def __getitem__(self, index):
        return self.index(index)

    def __del__(self):
        """
        Automatically sets the default information for the _folder object
        """
        verbose = False
        if self.default:
            verbose and print([d.full_path for d in self.default])
            self._folder.metadata and self._folder.metadata.set_object('defaults', [d.full_path for d in self.default])

    def index(self, index):
        return self._list[index]

    def do_indexing(self):
        for i in range(len(self._list)):
            self._list[i].index = i

    def from_scratch(self, _list):
        self._list = _list
        self.initialize()

    def sort_by(self, s):
        if s in ["date", "name", "ext", "kind", "size"]:
            getattr(self, 'sort_by_'+s)()

    def sort_by_kind(self):
        self._list.sort(key=lambda x: x.kind)

    def sort_by_size(self):
        self._list.sort(key=lambda x: x.size)
        self._list.reverse()

    def sort_by_ext(self):
        self._list.sort(key=lambda x: x.ext)

    def sort_by_date(self):
        self._list.sort(key=lambda x: x.last_modified)
        self._list.reverse()

    def sort_by_name(self):
        self._list.sort(key=lambda x: x.name)

    def sort_by_kind(self):
        self._list.sort(key=lambda x: x.kind)

    def reset_most_recents(self):
        verbose = False
        verbose and print("resetting most recents")
        self._most_recents = []

    def most_recents(self):
        verbose = False
        if self._most_recents:
            verbose and print("returning _most_recents")
            return self._most_recents

        if self._list:
            self._most_recents = DefaultList(self.which_equals('most_recent', True))
            verbose and print("_most_recents set to {0}".format(self._most_recents))
            return self._most_recents
        else:
            verbose and print("most_recents returning None")
            return None

    def which_equals(self, _property, equals_what,
                     first_only=False,                # returns first item in string 
                     case_insensitive=False           # false as not all attributes are strings
                     ):
        if case_insensitive:
            l = [item for item in self._list if getattr(item, _property).lower() == equals_what.lower()]
        else:
            l = [item for item in self._list if getattr(item, _property) == equals_what]
        if not l:
            return None
        if first_only:
            return l[0]
        else:
            return l        

    def map_each(self, callback, first_only=False):
        return [item for item in self._list if callback(item)]

    def add_or_remove(self, which):
        """
        Dynamically sets the variables
        """
        verbose = False
        if which in self.default:
            # turn off
            verbose and print("turn off {}".format(which))
            self.default.remove(which)
        else:
            verbose and print("turning on {}".format(which))
            self.default.add(which)

    def single_out(self, which):
        verbose = False
        verbose and print("single out's defaults:")
        verbose and print(self.default)
        for item in self.default:
            verbose and print("calling remove on {}".format(item))
            self.default.remove(item)
        self.default.add(which)

    def derive_default(self):
        """
        If there is default information in self._folder, return that
        Otherwise, use the most_recent items
        """
        verbose = False
        if self._folder.default_info:
            all_of_them = [self.which_equals('full_path', d, first_only=True) for d in self._folder.default_info]
            for a in all_of_them:
                if a:
                    a.default = True
            return DefaultList([a for a in all_of_them if a])   # rid of Nones
        else:
            latest = self.most_recents()
            verbose and print("most recents returned {}".format(l))
            if latest:
                for item in latest:
                    item.most_recent = True
                    item.default = True
                return latest
            else:
                return []

    def copy(self):
        return self._list[:]

class File_object():
    """
    File object suitable with commonly-used aspects deliminated by properties
    """
    def __init__(self, path, name, i):
        self.index = i
        self.path = path
        self.full_path = os.path.join(path, name)
        self.quoted_full_path = '"{}"'.format(self.full_path)
        self.real_path = os.path.realpath(self.full_path)
        self.parent_directory, junk = os.path.split(self.real_path)
        _, self.full_name = os.path.split(self.full_path)
        self.str_trick = 'full_name'
        self.name, self.ext = os.path.splitext(self.full_name)
        self.is_mounted = True
        self.is_hidden = self.name.startswith('.')
        self.is_support_file = self.is_hidden
        if not self.is_support_file:
            # support_file is defined as hidden files, and the __files__ that python makes
            # or #files# that some programs make
            # TODO: add support for user to be able to change these
            self.is_support_file = (self.name == "__pycache__") \
            or \
            (self.name.startswith('#') and name.endswith('#'))
        self.default = False
        self.force_default = False
        self.is_directory = os.path.isdir(self.real_path)
        self.is_link = os.path.islink(self.full_path)
        if self.is_link:
            self.real_is_directory = os.path.isdir(self.real_path)
        if self.full_path:
            if self.is_directory and not self.full_path[-1] == os.sep:
                self.full_path += os.sep
            self.metadata = DirTagger(self.full_path)
        else:
            self.metadata = None

        self.most_recent = False
        #TODO: Make these meaningful:
        if os.path.exists(self.real_path):
            st_mode, self.id, \
                 st_dev, st_nlink, \
                 st_uik, st_gid, \
                 self.size, st_atime, \
                 self.last_modified, self.created = os.stat(self.real_path)
        else:
            self.is_mounted = False
            st_mode, self.id, \
                 st_dev, st_nlink, \
                 st_uik, st_gid, \
                 self.size, st_atime, \
                 self.last_modified, self.created = (None, None, \
                                                 None, None, \
                                                 None, None, \
                                                 0, None, \
                                                 0, 0)

        # post-process: figure out its "kind"
        #TODO: Best done with metadata?
        if not self.is_mounted:
            self.kind = 'zzz'
        elif self.is_directory:
            self.kind = '_dir'
        elif self.is_link:
            junk, self.kind = os.path.splitext(self.real_path)
        elif self.ext:
            self.kind = self.ext
        else:
            self.kind = '_doc'
        #TODO: expand desc to links, aliases
        self.desc = "folder" if self.is_directory else "file"

    def __repr__(self):
        return self.full_path
    
    def __str__(self):
        return getattr(self, self.str_trick)

    def __eq__(self, comp):
        if not comp:
            return False
        else:
            return self.full_path == comp.full_path

    def tag(self, tag, value):
        pass
        #self.xattr[tag] = value

    def clear_tag(self, tag):
        pass
        #del self.xattr[tag]

class Folder_object(File_object):
    def __init__(self, path):
        File_object.__init__(self, path, '', None)
        self.default_info = self.setup_defaults()

    def setup_defaults(self):
        try:
            verbose = False
            if not self.full_path: return None
            if self.metadata.has('defaults'):
                defaults = self.metadata.get_object('defaults')
                verbose and print(defaults)
                verbose and input("Got defaults!")
                return defaults
            else:
                verbose and input("No defaults")
                return None
        except IOError:
            return None

if __name__ == '__main__':

    l = File_list('/Users/brainysmurf/Dropbox/RISS/Year 7/TermThree/', os.listdir('/Users/brainysmurf/Dropbox/RISS/Year 7/TermThree/'))
    print(l.default.path)
