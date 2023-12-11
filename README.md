# IntegrityChecker v0.1
`ichk` is a simple file integrity tool written in Python.

Tool created for me but can be used also by data hoarders and all peoples who are interested in periodically checking file hashes. Maybe in future this tool will be something more, but for now it just calculating file hashes.

Tool is suitable only for immutable files.

This is done as hobby side project - so many fancy things is missing or even you will find some ugly code inside :)

## Basic functionality
List of basic functionality of the tool.

### Calculate file hash
It can calculate hash of specified file or files and print it to stdout. For now it only supports XXH128 and OSHASH as currently most efficient solution which I know.

File size and OSHASH are for fast check if file was altered after setting extended attributes. This isn't perfect, because it only verifies file size and some part of the file (OSHASH).

### Set file extended attributes
There is possibility to set files extended attributes with calculated hashes. It will store data under `user.ichk.*` entries:

* `user.ichk.fsize` - file size at the scan moment
* `user.ichk.xxh128` - XXH128 hash written as an ASCII HEX
* `user.ichk.oshash` - OSHASH has written as an ASCII HEX

### Verify file hash
Tool will calculate hash of the file and verify with data written inside file extended attributes. Done only when file has attributes set and fast check is OK.

### Get file hash
It differs from calculation - because it will just get XXH128 hash from extended file attributes after verification of file size and OSHASH.

### Update file
After altering file user should execute updating file hashes, because it will have invalid hash data written in extended file attributes.

### Lock file
This functionality will try to set file attributes to read-only and set immutable bit. In general it depends on file system and user grants.

To set file immutability - tool needs to be run under root user.

## Arguments list
**TODO**

## Arguments cheat-sheet
* *all* - done for all files
* *no-xattr* - done for all files without `user.ichk` extended attributes set
* *xattr* - done for all files with `user.ichk` extended attributes set without checking validity
* *ok-xattr* - done for all files with valid (file size and OSHASH) `user.ichk` attributes set

|  description  | arguments set   | calc hash|calc oshash|set xattrs|lock|
|:-------------:|:---------------:|:--------:|:---------:|:--------:|:--:|
| calculate hashes and display to *stdout* |    *none*      |    all   |    yes    |    no    | no |
| calculate hashes for new files and display to *stdout* | `-c`      |    no-xattr   |    yes    |    no    | no |
| display hashes from extended attributes |    `-g`       |    no   |    yes    |    no    | no |
| display hashes from extended attributes and calculate for new files |    `-gc`       |    no-xattr   |    all    |    no    | no |
| calculate hashes for new files and set extended attributes |   `-cs`   | no-xattr | no-xattr  |    yes   | no |
| calculate hashes for new files, set extended attributes and lock file |   `-csl`   | no-xattr | no-xattr  |    yes   | yes |
| calculate hashes for new files and update extended attributes | `-cu`      |    no-xattr   |    yes    |    no    | no |
| verify hashes |   `-v`          |   xattr  |   xattr   |    no    | no |
| verify hashes and lock file |   `-vl`          |   xattr  |   xattr   |    no    | yes |

## Presets
Presets contains all shown flags so it will be easier to use.
Additionally to provided arguments you should also add argument with files list or provide them thru `stdin`.

### Scan
This will be a good starting point for first run on files and also for scanning new files.
This command will show you only progress bars without writing all hashes into *stdout*.

In result all provided new files (without extended attributes set) will be locked and have extended atrributes set with calculated hashes.
* *Preset form*
```bash
ichk --scan
```
* *Short form*
```bash
ichk -qpcsl
```
* *Long form*
```bash
ichk --quiet --progress --calculate --set-xattr --lock-file
```

### Verify
This will verify all already calculates files which have extended attributes set.
This command will show you only progress bars without writing all hashes into *stdout* but *stderr* will have errors if verification will fail.

* *Preset form*
```bash
ichk --verify
```
* *Short form*
```bash
ichk -qpvl
```
* *Long form*
```bash
ichk --quiet --progress --verify-xattr --lock-file
```

### Scan new and verify existing
You can also scan new files and verify existing ones in one pass.

* *Preset form*
```bash
ichk --scan --verify
```
* *Short form*
```bash
ichk -qpcslv
```
* *Long form*
```bash
ichk --quiet --progress --calculate --set-xattr --lock-file --verify-xattr
```

# TODO
This still is in plans:
* support for cooperation with Cronicle (script + proper JSON output with stats and progress)
* test on some bigger data
* update this readme file
* clean the code
* do some release and build as standalone app