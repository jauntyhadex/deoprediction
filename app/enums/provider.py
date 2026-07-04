from enum import Enum


class Provider(str, Enum):
    FOOTBALL_DATA = "football-data"
    API_FOOTBALL = "api-football"
    SPORTMONKS = "sportmonks"