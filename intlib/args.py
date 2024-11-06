# ==== BUILT-IN librariers of Python
import sys
from argparse import ArgumentParser, SUPPRESS



#############################################################################################################
###### Internal class for providing access to argument parsing
#############################################################################################################
class IChkArgumentParser():

    def __init__(self, args) -> None:
        self.args     = self.parse(args)
        self.canColorStdOut = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
        self.canColorStdErr = hasattr(sys.stderr, "isatty") and sys.stderr.isatty()

    # .................................................................

    def parse_jobs(self, args):
        if args.job_scan:
            args.progress  = True
            args.calculate = True
            args.set_xattr = True
            args.lock_file = True

        elif args.job_iscan:
            args.progress  = True
            args.calculate = True
            args.set_xattr = True
            args.immutable = True

        return args

    # .................................................................

    def parse(self, args):
        argParser = ArgumentParser()
        argParser.add_argument('inputFiles', type=str, nargs='*', default=sys.stdin, help="Input files list - if empty, provide list thru stdin", metavar='filename')
        argParser.add_argument('-r', '--recursive',  action='store_true', help="Process folders recursively")
        
        argParser.add_argument('-c', '--calculate', action='store_true', help="Calculate hashes for new files")
        argParser.add_argument('-g', '--get-xattr', action='store_true', help="Get 'user.ichk.*' extended attributes for file and print to stdout")
        argParser.add_argument('-s', '--set-xattr', action='store_true', help="Set 'user.ichk.*' extended attributes for file with calculated checksum")
        argParser.add_argument('-v', '--verify-xattr', action='store_true', help="Verify calculated checksum with file extended attributes")
        argParser.add_argument('--verify-older-than', type=str, help="Verify calculated checksum with files verified more tan specified time (you can use human date repr like '1 day')")
        argParser.add_argument('-l', '--lock-file', action='store_true', help="Lock file to read-only. Set also immutable bit if run also as a root user")
        argParser.add_argument('-i', '--immutable', action='store_true', help="Lock file to read-only and immutable. If not run as root it will return error")
        argParser.add_argument('--rate-limit', type=float, help="Limit read data rate to specified speed in MB/s")

        argParser.add_argument('-q', '--quiet', action='store_true', help="Quiet mode - don't print calculated hashes")
        argParser.add_argument('-Q', '--no-stats', action='store_true', help="Don't print performance data")
        argParser.add_argument('-H', '--no-header', action='store_true', help="Don't print header")
        argParser.add_argument('-E', '--no-ellipsis', action='store_true', help="Don't shrink file path and name to fit in terminal window. This is automatically enabled for non color output.")
        argParser.add_argument('-p', '--progress', action='store_true', help="Show progress bar")
        argParser.add_argument('--cronicle', action='store_true', help="Show progress and status for cronicle/cronicle-edge")
        argParser.add_argument('--color',        dest='color_always', action='store_true', help='when to use terminal colours (none | =always, =auto [default], =never)')
        argParser.add_argument('--color=always', dest='color_always', action='store_true', help=SUPPRESS)
        argParser.add_argument('--color=auto',   dest='color_auto',   action='store_true', help=SUPPRESS)
        argParser.add_argument('--color=never',  dest='color_never',  action='store_true', help=SUPPRESS)

        argParser.add_argument('-V', '--version', action='store_true', help="Print version and exit")

        argGroups = argParser.add_argument_group("Predefined jobs")
        argGroup  = argGroups.add_mutually_exclusive_group(required=False)
        argGroup.add_argument('--scan', dest='job_scan', action='store_true', help='set of arguments equal to "--progress --calculate --set-xattr --lock-file"')
        argGroup.add_argument('--iscan', dest='job_iscan', action='store_true', help='set of arguments equal to "--progress --calculate --set-xattr --immutable"')        

# TODO: Arguments to add and support
# --fast

# TODO: Set file copy support (?)
# TODO: Set compare support

        args = argParser.parse_args(args)
        args = self.parse_jobs(args)
        return args

    # .................................................................

    def colorStdOut(self) -> bool:
        if self.args.color_never:
            return False
        
        if self.args.color_always:
            return True
        
        return self.canColorStdOut

    def colorStdErr(self) -> bool:
        if self.args.color_never:
            return False
        
        if self.args.color_always:
            return True

        return self.canColorStdErr
        
    # .................................................................
