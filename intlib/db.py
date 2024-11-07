# ==== BUILT-IN librariers of Python
import os, datetime, uuid

# ==== EXTERNAL librariers installed by PyPI
from peewee import *
from playhouse.shortcuts import ThreadSafeDatabaseMetadata
from rich import inspect

###################################################################################################################################
###### Globals
###################################################################################################################################
ichkDb   = SqliteDatabase(None)
ichkDbStorage = None

def IChkDbInit(dbFileName: str, storageName: str, test: bool = False, ro: bool = False):
    if test:
        ichkDb.init(":memory:")
    elif ro:
        ichkDb.init(f"file:{dbFileName}?mode=ro", uri=True)
        ichkDb.connect()
        return
    else:
        ichkDb.init(dbFileName)

    ichkDb.connect()
    ichkDb.create_tables([Storage, Path, File])

    global ichkDbStorage
    ichkDbStorage = Storage.get_or_none(Storage.name==storageName, Storage.uuid==uuid.UUID(int=uuid.getnode()))
    if not ichkDbStorage:
        ichkDbStorage = Storage.create(
            name=storageName,
            uuid=uuid.UUID(int=uuid.getnode()),
            timestamp=datetime.datetime.now()
        )

    inspect(ichkDbStorage)

def IChkDbFile(localFileName: str, oshash: str):
    if not ichkDbStorage:
        return None
    
    realFileName = os.path.realpath(localFileName)
    filePathName = os.path.dirname(realFileName)
    fileNameWoExt = os.path.splitext(os.path.basename(realFileName))[0]
    fileExtension = os.path.splitext(realFileName)[1].removeprefix('.')

    path = Path.get_or_none(Path.storage_id==ichkDbStorage, Path.storage_path==filePathName)
    if not path:
        path = Path.create(
            storage_id=ichkDbStorage,
            storage_path=filePathName,
            timestamp=datetime.datetime.now()
        )

    fileSize = os.path.getsize(realFileName)
    fileMTime = datetime.datetime.fromtimestamp(os.path.getmtime(realFileName))
    fileCTime = datetime.datetime.fromtimestamp(os.path.getctime(realFileName))

    file = File.get_or_none(
        File.path_id==path, File.file_name==fileNameWoExt, File.file_ext==fileExtension,
        File.size==fileSize, File.oshash==oshash
    )
    if not file:
        file = File.create(
            file_name=fileNameWoExt,
            file_ext=fileExtension,
            size=fileSize,
            path_id=path,
            oshash=oshash,
            timestamp=datetime.datetime.now(),
            last_seen=datetime.datetime.now(),
            mtime=fileMTime,
            ctime=fileCTime
        )
    else:
        file.last_seen = datetime.datetime.now()
        file.mtime = fileMTime
        file.ctime = fileCTime
        file.save()

    return file

###################################################################################################################################
###### Database models
###################################################################################################################################
class idbModel(Model):
    class Meta:
        database = ichkDb
        model_metadata_class = ThreadSafeDatabaseMetadata

# .................................................................................................................................

class Storage(idbModel):
    id          = AutoField()
    uuid        = UUIDField()
    name        = TextField()
    base_path   = TextField(null=True)
    timestamp   = DateTimeField()
    class Meta:
        indexes = ((('uuid', 'name'), True),)

# .................................................................................................................................

class Path(idbModel):
    id           = AutoField()
    storage_id   = ForeignKeyField(Storage)
    storage_path = TextField()
    timestamp    = DateTimeField()
    class Meta:
        indexes = ((('storage_id', 'storage_path'), True),)

# .................................................................................................................................

class File(idbModel):
    id              = AutoField()
    file_name       = TextField()
    file_ext        = TextField()
    size            = IntegerField()
    oshash          = TextField()
    xxhash          = TextField(null=True)
    file_type       = IntegerField(null=True)

    path_id         = ForeignKeyField(Path)
    
    last_seen       = DateTimeField()
    timestamp       = DateTimeField()

    mtime           = DateTimeField(null=True)
    ctime           = DateTimeField(null=True)

    parent_id       = IntegerField(null=True)

    class Meta:
        # indexes     = ((('path_id', 'file_name'), True),)
        constraints = [
            SQL("FOREIGN KEY(parent_id) REFERENCES file(id)")
        ]

# .................................................................................................................................

