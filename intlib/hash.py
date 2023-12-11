# ==== BUILT-IN librariers of Python
import os, sys, time, re
from queue import Empty

# ==== EXTERNAL librariers installed by PyPI
import xxhash
import trio
from rich import print as rprint
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
    SpinnerColumn
)
from rich.table import Column
from rich.live import Live
from rich.padding import Padding

# ==== INTERNAL librariers
from .fattr import IChkFileAttributes
from .common import HumanBytes, SIGINT_handler

#############################################################################################################
###### Internal class for providing file hashing progress bar
#############################################################################################################
class IChkFileHashProgress():

    def __init__(self, enabled) -> None:
        self.enabled    = enabled
        self.history    = []
        self.maxHistory = 3
        self.layout     = None

        self.progress   = None
        self.taskTotal  = None
        self.taskNow    = None

    def __enter__(self):
        if self.enabled:
            self.layout = self.generateLayout()
            self.layout.start()

        return self
    
    def __exit__(self, exception_type, exception_value, exception_traceback):
        if self.layout:
            self.layout.stop()
            self.layout = None

    # .................................................................

    def generateLayout(self):
        self.txtcols = os.get_terminal_size().columns // 3
        self.progress = Progress(
            SpinnerColumn(),
            "{task.description}",
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.1f}%", "•",
            DownloadColumn(), "•",
            TransferSpeedColumn(), "•",
            TimeRemainingColumn(),
            TextColumn(
                "[bright_black]{task.fields[filename]}",
                justify="right", 
                table_column=Column(
                    no_wrap=True,
                    width=self.txtcols
                ))
        )

        layout = Live(Padding(self.progress, (1, 0)), transient=False, refresh_per_second=30)
        self.taskTotal = self.progress.add_task(
                            f"[bright_yellow]TOTAL", filename="",
                            total=None, start=True, visible=True
                        )

        return layout
    
    def fileNameEllipsis(self, fileName):
        minPathLen = 8
        txtCols    = max(self.txtcols, 12)
        fileLen  = len(fileName)
        fileBase = os.path.basename(fileName)
        filePath = os.path.dirname(fileName) + os.sep

        if fileLen <= txtCols:
            return fileName
        
        if len(filePath) > minPathLen:
            pathLen = txtCols - len(fileBase) - 2
            pathLen = max(minPathLen, pathLen)
            filePath = filePath[:pathLen] + "…" + os.sep

        if len(filePath) + len(fileBase) > txtCols:
            fileLen  = txtCols - len(filePath) - 1
            fileBase = "…" + fileBase[-fileLen:]

        return filePath + fileBase

    # .................................................................
    
    def updateTotalInfo(self, newTotal):
        if self.progress:
            self.progress.update(self.taskTotal, total=newTotal)

    def progressNewFile(self, fileName, fileSize):
        if self.progress:
            if self.taskNow:
                self.progressEndFile()

            self.taskNow = self.progress.add_task(
                f"[dark_goldenrod]XXH128", filename=self.fileNameEllipsis(fileName),
                total=fileSize, start=True, visible=True
            )
                        
            if len(self.history) > self.maxHistory:
                taskToRemove = self.history.pop(0)
                self.progress.remove_task(taskToRemove)

            self.history.append(self.taskNow)

    def progressEndFile(self):
        if self.progress:
            self.progress.stop_task(self.taskNow)
            self.taskNow = None

    def progressAdvance(self, advance):
        if self.progress:
            self.progress.advance(self.taskTotal, advance)
            self.progress.advance(self.taskNow, advance)

    # .................................................................


#############################################################################################################
###### Internal class for providing file hashing
#############################################################################################################
class IChkFileHash():

    def __init__(self, arguments, progress) -> None:
        self.arg         = arguments.args
        self.p           = progress
        self.colorStdOut = arguments.colorStdOut()
        self.colorStdErr = arguments.colorStdErr()

        self.printHeader()

    # .................................................................

    def coloredFileName(self, fileName):
        fileDir  = (os.path.dirname(fileName) + os.sep).replace("[", "\[")
        fileBase = (os.path.basename(fileName)).replace("[", "\[")
        
        return f"[magenta]{fileDir}[bright_magenta italic]{fileBase}[/]"

    def printStdOut(self, text, fileName=""):
        if self.colorStdOut:
            if fileName:
                rprint(text + self.coloredFileName(fileName))
            else:
                rprint(text)
        else:
            text = "".join(re.split("\[|\]", text)[::2])
            print(text + fileName)

    def printHeader(self):
        if not self.arg.quiet and not self.arg.no_header:
            if self.arg.no_stats:
                self.printStdOut(f"[bright_white][u]No.[/]  [u]XXH128[/]                           [u]OSHASH[/]           [u]File name[/]")
            else:
                self.printStdOut(f"[bright_white][u]No.[/]  [u]XXH128[/]                           [u]OSHASH[/]           [u]Read speed[/]   [u]Hash speed[/]   [u]File name[/]")

    def printNewHash(self, fileName, fileXX128Hash, fileOSHash, readBps=None, hashBps=None):
        if not self.arg.quiet:
            if self.arg.no_stats:
                self.printStdOut(f"[bright_cyan]{self.fileNo:<4}[/] [bright_yellow]{fileXX128Hash}[/] [yellow]{fileOSHash}[/] ", fileName)
            else:
                readSpeedStr = ""
                hashSpeedStr = ""
                if readBps: readSpeedStr = f"{HumanBytes.format(readBps)}/s"
                if hashBps: hashSpeedStr = f"{HumanBytes.format(hashBps)}/s"

                self.printStdOut(f"[bright_cyan]{self.fileNo:<4}[/] [bright_yellow]{fileXX128Hash}[/] [yellow]{fileOSHash}[/] {readSpeedStr:<12} {hashSpeedStr:<12} ", fileName)

    def printErrHash(self, fileName, hashType, fileHash, calcHash):
        print(f"{hashType} {fileHash} != {calcHash} {fileName}", file=sys.stderr)

    # .................................................................

    def __sumBytes(self, bytesView: memoryview):
        bsum = 0
        sz = len(bytesView) // 8
        for x in range(sz):
            bsum = (bsum + int.from_bytes(bytesView[8*x : 8*(x+1)], byteorder='little', signed=False)) & 0xFFFFFFFFFFFFFFFF
        
        return bsum

    # .................................................................

    async def calculateOSHASH(self, fileName):
        fs = os.path.getsize(fileName)
        if fs <= 8:
            oshash = 0
            return f"{oshash:016X}".upper()

        oshash    = None
        chunkSize = 64 * 1024
        if fs < chunkSize:
            chunkSize = int((fs // 8) * 8)

        headBytes = bytearray(chunkSize)
        headView  = memoryview(headBytes)
        tailBytes = bytearray(chunkSize)
        tailView  = memoryview(tailBytes)

        async with await trio.open_file(fileName, 'rb', buffering=0) as f:
            headBytesRead = await f.readinto(headView)
            await f.seek(-chunkSize, os.SEEK_END)
            tailBytesRead = await f.readinto(tailView)

            if headBytesRead == tailBytesRead and headBytesRead == chunkSize:
                headBytesSum = self.__sumBytes(headView)
                tailBytesSum = self.__sumBytes(tailView)

                oshash = (headBytesSum + tailBytesSum) & 0xFFFFFFFFFFFFFFFF
                oshash = (oshash + fs) & 0xFFFFFFFFFFFFFFFF

        assert f.closed
        return f"{oshash:016X}".upper()

    async def calculateXXH128(self, fileName):
        self.p.progressNewFile(fileName, os.path.getsize(fileName))

        totalStartTime = time.time()
        totalReadTime  = 0
        totalCalcTime  = 0

        async with await trio.open_file(fileName, "rb", buffering=0) as f:
            __memBytes    = bytearray(1024 * 1024)   # 1'048'576
            memView       = memoryview(__memBytes)           
            xxh128        = xxhash.xxh128()

            readStartTime = time.time()
            bytesRead     = await f.readinto(memView)
            totalReadTime += (time.time() - readStartTime)

            totalRead     = 0
            while bytesRead != None and bytesRead > 0:
                if SIGINT_handler().SIGINT: 
                    return (None, None, None, None)
                
                totalRead += bytesRead

                calcStartTime = time.time()
                xxh128.update(memView[:bytesRead])
                self.p.progressAdvance(bytesRead)
                totalCalcTime += (time.time() - calcStartTime)

                readStartTime = time.time()
                bytesRead     = await f.readinto(memView)
                totalReadTime += (time.time() - readStartTime)
        
        assert f.closed
        self.p.progressEndFile()

        totalTime = time.time() - totalStartTime
        fileSpeed = totalRead / totalTime
        readSpeed = totalRead / totalReadTime
        hashSpeed = totalRead / totalCalcTime

        return (
            xxh128.hexdigest().upper(),
            fileSpeed,
            readSpeed,
            hashSpeed
        )

    # .................................................................

    # async def verifyFSIZE(self, fileName):
    #     try:
    #         fattrFSIZE = int(fileAttr.fileXAttrs.get('ichk.fsize', ''))
    #     except:
    #         fattrFSIZE = -1

    #     if fattrOSHASH.upper() != fileOSHASH.upper():
    #         self.printErrHash(fileName, "OSHASH", fattrOSHASH, fileOSHASH)
    #         return False
        
    #     return True  
    
    async def verifyOSHASH(self, fileName, fileAttr, fileOSHASH):
        fattrOSHASH = fileAttr.fileXAttrs.get('ichk.oshash', '')
        if fattrOSHASH.upper() != fileOSHASH.upper():
            self.printErrHash(fileName, "OSHASH", fattrOSHASH, fileOSHASH)
            return False
        
        return True    

    async def verifyXXH128(self, fileName, fileAttr, fileXXH128):
        fattrXXH128 = fileAttr.fileXAttrs.get('ichk.xxh128', '')
        if fattrXXH128.upper() != fileXXH128.upper():
            self.printErrHash(fileName, "XXH128", fattrXXH128, fileXXH128)
            return False
        
        return True

    # .................................................................

    # TODO: add always checking FSIZE and OSHASH for files

    async def calculate(self, fileName):
        calcStartTime = time.time()

        fileAttr  = IChkFileAttributes(fileName)
        doCalc    = False

        # none argument passed and not quiet also
        if (not self.arg.calculate and 
            not self.arg.verify_xattr and
            not self.arg.get_xattr) and not self.arg.quiet:
            doCalc = True

        # --verify-xattr => calculate for files with checksum data
        if self.arg.verify_xattr:
            doCalc = fileAttr.hasChecksumInfo()

        # --calculate => calculate only files without checksum data
        if self.arg.calculate and not fileAttr.hasChecksumInfo():
            doCalc = True

        # --get-xattr => get data from file and print it
        if self.arg.get_xattr and fileAttr.hasChecksumInfo():
            fattrOSHASH = fileAttr.fileXAttrs.get('ichk.oshash', '')
            fattrXXH128 = fileAttr.fileXAttrs.get('ichk.xxh128', '')
            self.printNewHash(fileName, fattrXXH128, fattrOSHASH)

        #### First OSHASH calculation
        if doCalc:
            fileOSHASH = await self.calculateOSHASH(fileName)
            
            # --verify-xattr => print different things
            if self.arg.verify_xattr and fileAttr.hasChecksumInfo():
                doCalc = await self.verifyOSHASH(fileName, fileAttr, fileOSHASH)

        #### Second HASH calculation
        if doCalc:
            fileXXH128, fileBps, readBps, hashBps = await self.calculateXXH128(fileName)
            if fileXXH128 is None:
                return

            if not self.arg.get_xattr:
                self.printNewHash(fileName, fileXXH128, fileOSHASH, readBps, hashBps)

            # --verify-xattr => print different things
            if self.arg.verify_xattr and fileAttr.hasChecksumInfo():
                await self.verifyXXH128(fileName, fileAttr, fileXXH128)

            # --set-xattr => set extended attributes only for files without checksum data
            if self.arg.set_xattr and not fileAttr.hasChecksumInfo():
                fileAttr.writeXAttr(fileXXH128, fileOSHASH)

                # --lock-file => lock file after setting extended attributes
                if self.arg.lock_file:
                    fileAttr.lockFile()

        # print(f'Time: {time.time() - calcStartTime}')

    # .................................................................

    async def traverse(self, queue):
        self.fileNo = 0
        abort = False
        while not abort:
            try:
                fileName = queue.get_nowait()
                if fileName == "**END**" or SIGINT_handler().SIGINT:
                    abort = True
                else:
                    self.fileNo += 1
                    await self.calculate(fileName)
            except Empty:
                await trio.sleep(0.1)

    # .................................................................