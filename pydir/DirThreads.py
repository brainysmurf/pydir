from pydir.Dir import Pydir
from multiprocessing import Process, Queue

class DirThreads(Pydir):

    launched = False
    
    def __init__(self):
        self.mdfind_threads = []
        self.mdfind_queue   = Queue()
        Pydir.__init__(self)
        self.start_mdfind_threads()

    def mdfind_thread(self, qu, search_str, *args, **kwargs):
        result = Pydir.mdfind(self, search_str, lazy=False, save=False)
        qu.put({search_str: result})

    def start_mdfind_threads(self):        
        for project in self.list_current_projects():
            self.mdfind_threads.append(
                Process(target=self.mdfind_thread, args=(self.mdfind_queue, project)))
        for thread in self.mdfind_threads:
            thread.start()

    def sync_mdfind_threads(self):
        if self.launched:
            self.mdfind_thread = []  # release memory
            return
        for thread in self.mdfind_threads:
            thread.join()

        while not self.mdfind_queue.empty():
            d = self.mdfind_queue.get()
            for k in d:
                self._project_saved_searches[k] = d[k]

    def parse_input(self, user_input):
        self.sync_mdfind_threads()
        self.launched = True
        return Pydir.parse_input(self, user_input)
