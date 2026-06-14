from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelInfo:
    id: str
    name: str
    icon: str
    description: str


class AIModel(ABC):

    @property
    @abstractmethod
    def info(self) -> ModelInfo:
        ...

    @abstractmethod
    async def chat(self, history: list[dict]) -> str:
        ...

    @abstractmethod
    async def generate_design(
        self, description: str, style: str, wishes: Optional[str] = None
    ) -> str:
        ...

    @abstractmethod
    async def repair_advice(self, question: str) -> str:
        ...

    @abstractmethod
    async def interior_tip(self, question: str) -> str:
        ...
