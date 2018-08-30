from dataclasses import dataclass
from typing import List
from utt import Utt


@dataclass
class EventLog(object):
    utts: List[Utt]

    def add(self, utt):
        self.utts.append(utt)
