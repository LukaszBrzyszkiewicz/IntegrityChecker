# ==== BUILT-IN librariers of Python
import sys, os, glob
from queue import Queue

# ==== EXTERNAL librariers installed by PyPI
import trio

# ==== INTERNAL librariers
from intlib.common    import SIGINT_handler

#############################################################################################################
###### Internal class for providing access to files/directory traversing
#############################################################################################################
class IChkGlobTraverser():

    def __init__(self, progress=None) -> None:
        self.dirsList   = set([])
        self.filesList  = set([])
        self.queue      = Queue()
        self.p          = progress

    # .................................................................

    def __traverse(self, inputList, recursive):
        self.retraverseList = []
        
        for inputPattern in inputList:            
            inputPattern = inputPattern.strip()
            if not os.path.isfile(inputPattern) and not os.path.isdir(inputPattern):
                iglob = glob.iglob(inputPattern, recursive=recursive)
            else:
                iglob = [inputPattern]

            for iglobFile in iglob:
                if SIGINT_handler().SIGINT: 
                    return

                if os.path.isfile(iglobFile):
                    if iglobFile not in self.filesList:
                        self.filesList.add(iglobFile)
                        self.queue.put(iglobFile)

                        if self.p: self.p.advanceTotalSize(os.path.getsize(iglobFile))

                elif os.path.isdir(iglobFile) and recursive:
                    if iglobFile not in self.dirsList:
                        self.dirsList.add(iglobFile)
                        self.retraverseList += [os.path.join(iglobFile, '**')]

    # .................................................................

    async def traverse(self, inputList, recursive):
        if inputList is sys.stdin:
            if not sys.stdin.isatty():
                inputList = sys.stdin.readlines()
            else:
                self.queue.put("**END**")
                return

        if not SIGINT_handler().SIGINT: 
            await trio.to_thread.run_sync(self.__traverse, inputList, recursive)

        if not SIGINT_handler().SIGINT: 
            await trio.to_thread.run_sync(self.__traverse, self.retraverseList, recursive)

        self.queue.put("**END**")
        self.retraverseList = None

    # .................................................................




