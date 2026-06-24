from abc import ABC, abstractmethod

from models import Recipe, RecipeDetail


class RecipeRepositoryBase(ABC):
    @abstractmethod
    def search(self, q: str) -> list[Recipe]: ...

    @abstractmethod
    def get_by_id(self, id: int) -> RecipeDetail | None: ...
