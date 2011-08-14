import xattr
import re
import json

class XattrWrapper():
    """
    Give it the app's signature and the parameters and the class handles all the rest
    """

    def __init__(self, path, sig):
        self._path = path
        self.signature = sig

    def list(self):
        return xattr.listxattr(self._path)

    def has(self, what):
        verbose = False
        verbose and print("Is {} in {}?".format(self._encode(what), self.list()))
        return self._encode(what) in self.list()

    def set(self, parameters, value):
        xattr.setxattr(self._path, self._encode(parameters), value)

    def get(self, parameters):
        return xattr.getxattr(self._path, self._encode(parameters))

    def set_object(self, key, value):
        verbose = False
        verbose and print('in set_object, key is {} value is {}'.format(key, value))
        verbose and input(json.dumps(value))
        self.set(key, json.dumps(value))

    def get_object(self, key):
        return json.loads(self.get(key))

    def _encode(self, parameters):
        """
        Turns a tag into the correct format
        parameter is a list of dir.<what>.<what>
        escapes true  -> don't let input of parentheses
        escapes false -> do so (useful for re module)
        escape_orig_parns true -> useful for re module
        """
        if not isinstance(parameters, list):
            parameters = [parameters]
        param = "_".join(parameters)
        return "{}_{}".format(self.signature, param)

    def decipher_parameters(self):
        """
        Returns a list of which parameters are present
        """
        sep = ", "
        potentials = sep.join(self.list())
        result = re.findall('{}_(.*?){}'.format(self.signature, sep), potentials)
        if not result:
            return None
        else:
            return result[0]
