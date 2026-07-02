from abc import ABC, abstractmethod
from typing import Any


class SportsProvider(ABC):
    """
    Base class for all sports data providers.

    Every provider (football, basketball, etc.)
    must implement these methods.
    """

    @abstractmethod
    def get_competitions(self) -> list[dict[str, Any]]:
        """Return all competitions."""
        pass

    @abstractmethod
    def get_teams(self, competition_id: int) -> list[dict[str, Any]]:
        """Return teams in a competition."""
        pass

    @abstractmethod
    def get_players(self, team_id: int) -> list[dict[str, Any]]:
        """Return players in a team."""
        pass

    @abstractmethod
    def get_fixtures(self) -> list[dict[str, Any]]:
        """Return upcoming fixtures."""
        pass