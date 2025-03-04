from dataclasses import dataclass


@dataclass
class SyncBlock():
    ref_start: float
    ref_end: float
    eval_start: float
    eval_end: float
