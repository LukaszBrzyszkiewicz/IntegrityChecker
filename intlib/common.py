# ==== BUILT-IN librariers of Python
import sys
from typing import List, Union


###################################################################################################################################
###### Singleton meta-class helper
###################################################################################################################################
class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

#############################################################################################################
###### Ctrl+C graceful handler
#############################################################################################################
class SIGINT_handler(metaclass=Singleton):

    def __init__(self):
        self.SIGINT = False

    def signal_handler(self, signal, frame):
        print('Aborting! Pressed Ctrl+C.', file=sys.stderr)
        self.SIGINT = True

#############################################################################################################
###### Internal class for providing human readable bytes convertion
#############################################################################################################
class HumanBytes:
    CUSTOM_LABELS: List[str]       = ["", "k", "M", "G", "T", "P", "E", "Z", "Y"]
    METRIC_LABELS: List[str]       = ["B", "kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    BINARY_LABELS: List[str]       = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]
    BPS_LABELS: List[str]          = ["bps", "kbps", "Mbps", "Gbps", "Tbps", "Pbps", "Ebps", "Zbps", "Ybps"]
    PRECISION_OFFSETS: List[float] = [0.5, 0.05, 0.005, 0.0005] # PREDEFINED FOR SPEED.
    PRECISION_FORMATS: List[str]   = ["{}{:.0f} {}", "{}{:.1f} {}", "{}{:.2f} {}", "{}{:.3f} {}"] # PREDEFINED FOR SPEED.

    @staticmethod
    def format(num: Union[int, float], metric: bool=False, precision: int=1, bps: bool=False, custom: bool=False) -> str:
        assert isinstance(num, (int, float)), "num must be an int or float"
        assert isinstance(metric, bool), "metric must be a bool"
        assert isinstance(precision, int) and precision >= 0 and precision <= 3, "precision must be an int (range 0-3)"

        unit_labels = HumanBytes.METRIC_LABELS if metric else HumanBytes.BINARY_LABELS
        unit_labels = unit_labels if not bps else HumanBytes.BPS_LABELS
        unit_labels = unit_labels if not custom else HumanBytes.CUSTOM_LABELS
        last_label  = unit_labels[-1]
        unit_step   = 1000 if metric or bps or custom else 1024
        unit_step_thresh = unit_step - HumanBytes.PRECISION_OFFSETS[precision]

        is_negative = num < 0
        if is_negative:
            num = abs(num)

        for unit in unit_labels:
            if num < unit_step_thresh:
                # VERY IMPORTANT:
                # Only accepts the CURRENT unit if we're BELOW the threshold where
                # float rounding behavior would place us into the NEXT unit: F.ex.
                # when rounding a float to 1 decimal, any number ">= 1023.95" will
                # be rounded to "1024.0". Obviously we don't want ugly output such
                # as "1024.0 KiB", since the proper term for that is "1.0 MiB".
                break
            if unit != last_label:
                # We only shrink the number if we HAVEN'T reached the last unit.
                # NOTE: These looped divisions accumulate floating point rounding
                # errors, but each new division pushes the rounding errors further
                # and further down in the decimals, so it doesn't matter at all.
                num /= unit_step

        return HumanBytes.PRECISION_FORMATS[precision].format("-" if is_negative else "", num, unit)
