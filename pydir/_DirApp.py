from dir.Dir import Dir
from multiprocessing import Process, Queue

class DirThreads(Dir):
    
    def __init__(self):
        self.mdfind_threads = []
        self.mdfind_queue   = Queue()

    def mdfind(self, qu, search_str, *args, **kwargs):
        result = Dir.mdfind(self, search_str, lazy=False, save=False)
        qu.put({keyword: result))

    def mdfind_thread(self):        
        for project in self.list_current_projects():
            self.threads.append[
                Process(target=self.mdfind, args=(qu, project)}) ]
        for thread in self.threads:
            thread.start()

    def sync_mdfind_threads(self):
        for thread in self.threads:
            thread.join()

        while not qu.empty():
            d = qu.get()
            for k in d:
                self._project_saved_searches[k] = d[k]

    def parse_input(self, user_input):
        self.sync_mdfind_threads()
        return Dir.parse_input(self, user_input)
