from abc import ABC, abstractmethod

from models import Recipe, RecipeCreate, RecipeDetail, RecipeUpdate


class RecipeRepositoryBase(ABC):
    @abstractmethod
    def search(self, q: str) -> list[Recipe]: ...

    @abstractmethod
    def get_by_id(self, id: int) -> RecipeDetail | None: ...

    @abstractmethod
    def get_by_url(self, url: str) -> Recipe | None: ...

    @abstractmethod
    def create(self, data: RecipeCreate) -> RecipeDetail: ...

    @abstractmethod
    def update(self, id: int, data: RecipeUpdate) -> RecipeDetail | None: ...
