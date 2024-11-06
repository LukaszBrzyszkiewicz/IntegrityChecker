# ==== EXTERNAL librariers installed by PyPI
from peewee import *
from playhouse.shortcuts import ThreadSafeDatabaseMetadata

###################################################################################################################################
###### Globals
###################################################################################################################################
bssDb   = SqliteDatabase(None)

def bssDbInit(dbFileName: str, test: bool = False, ro: bool = False):
    # global bssDb
    if test:
        bssDb.init(":memory:")
    elif ro:
        bssDb.init(f"file:{dbFileName}?mode=ro", uri=True)
        bssDb.connect()
        return
    else:
        bssDb.init(dbFileName)

    # bssDbBackup()
    bssDb.connect()
    bssDb.create_tables([Storage, Path, File])

###################################################################################################################################
###### Database models
###################################################################################################################################
class idbModel(Model):
    class Meta:
        database = bssDb
        model_metadata_class = ThreadSafeDatabaseMetadata

# .................................................................................................................................

class Storage(idbModel):
    id          = AutoField()
    uuid        = UUIDField(unique = True)
    name        = TextField()
    base_path   = TextField()
    timestamp   = DateTimeField()

# .................................................................................................................................

class Path(idbModel):
    id           = AutoField()
    storage_id   = ForeignKeyField(Storage)
    storage_path = TextField()
    timestamp    = DateTimeField()
    class Meta:
        indexes = ((('storage_id', 'base_path'), True),)

# .................................................................................................................................

class File(idbModel):
    id              = AutoField()
    file_name       = TextField()
    file_ext        = TextField()
    size            = IntegerField()
    oshash          = TextField()
    xxhash          = TextField(null=True)

    path_id         = ForeignKeyField(Path)
    
    last_seen       = DateTimeField()
    timestamp       = DateTimeField()

    atime           = DateTimeField(null=True)
    mtime           = DateTimeField(null=True)
    ctime           = DateTimeField(null=True)

    parent_id       = IntegerField(null=True)

    class Meta:
        # indexes     = ((('path_id', 'file_name'), True),)
        constraints = [
            SQL("FOREIGN KEY(parent_id) REFERENCES file(id)")
        ]

# .................................................................................................................................