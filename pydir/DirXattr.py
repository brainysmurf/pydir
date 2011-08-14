from pydir.XattrWrapper import XattrWrapper
import re
from AppleScriptWrapper.Basic import get_app

class DirTagger(XattrWrapper):
    """
    Used by dir's Filer to label files
    """
    signature = "com_mistermorris_dir"

    def __init__(self, path):
        XattrWrapper.__init__(self, path, self.signature)

    def finder_comment(self, comment):
        get_app("Finder").spotlight_add_comment(self._path, comment)

    def tag(self, tag):
        """
        alias for set_tag
        """
        self.finder_comment(self.encode_tag(tag))

    def remove_tag(self, tag):
        raise NotImplemented

    #def set_tag(self, tag, value):
    #    self.set(self.encode_tag(tag), value)

    #def get_tag(self, tag):
    #    return self.get(self.encode_tag(tag))

    def encode_tag(self, tag, escapes=True, escape_orig_parens=False, for_pass_to_re_module=False):
        """
        returns 'com_mistermorris_pydir_tag(tag)'
        """
        verbose = False
        s  = self._encode("tag")
        verbose and print("ENCODING: {}".format(s))
        if for_pass_to_re_module:
            escape_orig_parens = True
            escapes = False
        if escape_orig_parens:
            s += "\({}\)"
        else:
            s += "({})"
        if escapes:
            return s.format(tag.replace(')', ']').replace('(', '['))
        else:
            return s.format(tag)        

    def decipher_tags(self):
        """
        Return list of everything inside parentheses from xattr list
        """
        verbose = False
        potential_tags = ", ".join(self.list())
        verbose and print(potential_tags)
        result = re.findall(self.encode_tag('(.*?)', for_pass_to_re_module=True), potential_tags)
        verbose and print(result)
        if not result:
            return []
        else:
            return result
