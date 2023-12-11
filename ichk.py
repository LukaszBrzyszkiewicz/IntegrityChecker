#!/usr/bin/env python
# ==== BUILT-IN librariers of Python
import os, sys, stat

# ==== EXTERNAL librariers installed by PyPI
import trio
import xxhash

# ==== INTERNAL librariers
from intlib.args      import IChkArgumentParser
from intlib.traverser import IChkGlobTraverser
from intlib.hash      import IChkFileHash, IChkFileHashProgress

ICHK_VER = "0.1.0"

async def main():
    with IChkFileHashProgress(arguments.args.progress) as hashProgress:
        fileTraverse = IChkGlobTraverser(hashProgress)
        fileHasher   = IChkFileHash(arguments, hashProgress)

        async with trio.open_nursery() as nursery:
            nursery.start_soon(fileTraverse.traverse, arguments.args.inputFiles, arguments.args.recursive)
            nursery.start_soon(fileHasher.traverse, fileTraverse.queue)
            

if __name__ == '__main__':
    arguments = IChkArgumentParser(sys.argv[1:])
    if arguments.args.version:
        print(f"ICHK v{ICHK_VER}")
        print(f"XXHASH v{xxhash.XXHASH_VERSION}")
        exit(0)

    if arguments.args.lock_file and not os.geteuid() == 0:
        print("WARNING: to set also immutable bit for files you need to run this tool as a root user.")
    if arguments.args.immutable and not os.getuid() == 0:
        print("ERROR: to set also immutable bit for files you need to run this tool as a root user.")
        exit(128)
    arguments.args.lock_file = arguments.args.lock_file or arguments.args.immutable

    trio.run(main)