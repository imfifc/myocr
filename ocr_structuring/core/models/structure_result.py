from abc import abstractmethod, ABCMeta

from typing import Dict


class StructureResult(metaclass=ABCMeta):
    @abstractmethod
    def to_dict(self) -> Dict:
        pass
