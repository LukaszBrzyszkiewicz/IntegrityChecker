# ==== BUILT-IN librariers of Python
import os, fcntl, datetime
from array import array
from datetime import datetime as dt

# ==== EXTERNAL librariers installed by PyPI
from xattr import xattr
import dateparser

# ==== Constants
FS_IOC_SETFLAGS = 0x40086602
FS_IOC_GETFLAGS	= 0x80086601
FS_IMMUTABLE_FL	= 0x010

#############################################################################################################
###### Internal class for providing access (read/write) file attributes
#############################################################################################################
class IChkFileAttributes():

    def __init__(self, fileName) -> None:
        self.fileName   = fileName
        self.fileSize   = os.path.getsize(fileName)
        self.xattr      = xattr(fileName)
        self.fileXAttrs = None
        self.wasImmutable = False

    # .................................................................
 
    def readXAttr(self):
        self.fileXAttrs = {}
        for xAttrName in self.xattr.keys():
            if xAttrName.startswith("user.ichk."):
                self.fileXAttrs |= {
                    xAttrName.removeprefix("user."): self.xattr[xAttrName].decode()
                }

        return self.fileXAttrs
    
    def writeXAttr(self, xxh128, oshash):
        self.xattr["user.ichk.fsize"] = str(self.fileSize).encode("ascii")
        self.xattr["user.ichk.xxh128"] = xxh128.encode("ascii")
        self.xattr["user.ichk.oshash"] = oshash.encode("ascii")
        self.xattr["user.ichk.updated"] = dt.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ").encode("ascii")
        self.readXAttr()
    
    # .................................................................

    def hasChecksumInfo(self) -> bool:
        if self.fileXAttrs is None:
            self.readXAttr()
        
        return (self.fileXAttrs.get("ichk.fsize") and 
                self.fileXAttrs.get("ichk.oshash") and
                self.fileXAttrs.get("ichk.xxh128"))
    
    def hasChecksumOlderThan(self, olderThanString) -> bool:
        if olderThanString == None or olderThanString == "" or olderThanString.lower() == "now":
            return True
        
        if self.fileXAttrs is None:
            self.readXAttr()

        fileUpdatedAt = self.fileXAttrs.get("ichk.updated")
        if fileUpdatedAt == None:
            return True
        
        fileUpdatedAt = dt.strptime(fileUpdatedAt, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
        olderThan = dateparser.parse(olderThanString).astimezone(datetime.UTC)

        return fileUpdatedAt < olderThan

    
    # .................................................................

    def isImmutable(self) -> bool:
        with open(self.fileName, 'r') as f:
            arg = array('L', [0])
            fcntl.ioctl(f.fileno(), FS_IOC_GETFLAGS, arg, True)

        return bool(arg[0] & FS_IMMUTABLE_FL)
    
    def setImmutable(self):
        self.wasImmutable = True
        with open(self.fileName, 'r') as f: 
            arg = array('L', [0])
            fcntl.ioctl(f.fileno(), FS_IOC_GETFLAGS, arg, True)

            arg[0] |= FS_IMMUTABLE_FL
            fcntl.ioctl(f.fileno(), FS_IOC_SETFLAGS, arg, True)

    def unsetImmutable(self):
        with open(self.fileName, 'r') as f: 
            arg = array('L', [0])
            fcntl.ioctl(f.fileno(), FS_IOC_GETFLAGS, arg, True)
            arg[0] &= ~FS_IMMUTABLE_FL
            fcntl.ioctl(f.fileno(), FS_IOC_SETFLAGS, arg, True)

    def canSetImmutable(self) -> bool:
        return os.geteuid() == 0

    def relockFile(self):
        if self.wasImmutable and self.canSetImmutable():
            self.setImmutable()

    def unlockFile(self):
        # set "-r--r--r--"
        if self.canSetImmutable() and self.isImmutable():
            self.unsetImmutable()
            self.wasImmutable = True

    def lockFile(self):
        # set "-r--r--r--"
        os.chmod(self.fileName, 0o444)

        # set "+i"
        if self.canSetImmutable():
            self.setImmutable()

    # .................................................................