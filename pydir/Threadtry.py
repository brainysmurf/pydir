from multiprocessing import Process, Queue
from dir.Command import Shell_Emulator as Shell

def mdfind(q, keyword, *args, **keywords):
    shell = Shell()
    result, _ = shell.run_command("mdfind {}".format(keyword))
    q.put({keyword:result.decode()})

    print("Starting...")
items = ("com_mistermorris_dir_tags", "com_mistermorris_dir",)
threads = []
qu = Queue()
for item in items:
    threads.append(Process(target=mdfind, args=(qu, item)))
    print("set up thread {}".format(item))

for item in threads:
    item.start()

print("...done")

print("Joining...")
for item in threads:
    item.join()
    print("thread {} joined".format(item.name))
print("...done.")

print(qu.get())
print(qu.get())
input("DONE!")
