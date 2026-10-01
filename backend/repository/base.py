from abc import ABC, abstractmethod

from models import Recipe, RecipeCreate, RecipeDetail, RecipeUpdate


class RecipeRepositoryBase(ABC):
    @abstractmethod
    def search(self, q: str, category_ids: list[int] | None = None) -> list[Recipe]: ...

    @abstractmethod
    def get_by_id(self, id: int) -> RecipeDetail | None: ...

    @abstractmethod
    def get_by_url(self, url: str) -> Recipe | None: ...

    @abstractmethod
    def create(self, data: RecipeCreate, created_by: str | None = None) -> RecipeDetail: ...

    @abstractmethod
    def update(self, id: int, data: RecipeUpdate) -> RecipeDetail | None: ...

    @abstractmethod
    def delete(self, id: int) -> bool: ...
