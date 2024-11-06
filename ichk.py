#!/usr/bin/env python
# ==== BUILT-IN librariers of Python
import os, sys, signal

# ==== EXTERNAL librariers installed by PyPI
import trio
import xxhash

# ==== INTERNAL librariers
from intlib.common    import SIGINT_handler
from intlib.args      import IChkArgumentParser
from intlib.traverser import IChkGlobTraverser
from intlib.hash      import IChkFileHash, IChkFileHashProgress

ICHK_VER = "0.3.0"

async def main():
    with IChkFileHashProgress(arguments.args.progress, arguments.args.cronicle) as hashProgress:
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

    if arguments.args.rate_limit:
        print(f"WARNING: rate limiter enabled to {arguments.args.rate_limit}MB/s\n")

    handler  = SIGINT_handler()
    signal.signal(signal.SIGINT, handler.signal_handler)

    trio.run(main)

    if handler.SIGINT: exit(130)