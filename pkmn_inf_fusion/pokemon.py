import json

from typing import List, Dict, Any, Optional


class Pokemon:
    @staticmethod
    def from_json(data: Dict[str, Any]) -> Optional["Pokemon"]:
        try:
            id_ = int(data["id"])
            name = data["name"]["english"]
            stats = data["base"]
            types = data["type"]
            type1 = types[0]
            type2 = type1 if len(types) <= 1 else types[1]

            # don't care about the bool (ability[1]) hinting at hidden abilities
            abilities = [ability[0] for ability in data["profile"]["ability"]]

            return Pokemon(id_, name,
                           int(stats["HP"]), int(stats["Attack"]), int(stats["Defense"]),
                           int(stats["Sp. Attack"]), int(stats["Sp. Defense"]), int(stats["Speed"]),
                           abilities, type1, type2)
        except KeyError:
            return None

    @staticmethod
    def load_from_json(path: str) -> List["Pokemon"]:
        mons = []
        with open(path, encoding='utf-8') as file:
            # Load the JSON data
            data = json.load(file)
            if isinstance(data, list):
                for item in data:
                    mon = Pokemon.from_json(item)
                    if mon is not None:
                        mons.append(mon)
            else:
                mon = Pokemon.from_json(data)
                if mon is not None:
                    mons.append(mon)
        return mons

    def __init__(self, id_: int, name: str, hp: int, atk: int, spatk: int, def_: int, spdef: int, speed: int,
                 abilities: List[str], type1: str, type2: str):
        self.__id = id_
        self.__name = name

        self.__hp = hp
        self.__atk = atk
        self.__spatk = spatk
        self.__def = def_
        self.__spdef = spdef
        self.__speed = speed

        self.__abilities = abilities
        self.__type1 = type1
        self.__type2 = type2

    @property
    def id(self) -> int:
        return self.__id

    @property
    def name(self) -> str:
        return self.__name

    @property
    def hp(self) -> int:
        return self.__hp

    @property
    def atk(self) -> int:
        return self.__atk

    @property
    def spatk(self) -> int:
        return self.__spatk

    @property
    def def_(self) -> int:
        return self.__def

    @property
    def spdef(self) -> int:
        return self.__spdef

    @property
    def speed(self) -> int:
        return self.__speed

    @property
    def type1(self) -> str:
        return self.__type1

    @property
    def type2(self) -> str:
        return self.__type2

    def to_json(self) -> Dict[str, Any]:
        abilities = [[ability, "?"] for ability in self.__abilities]
        return {
            "id": self.__id,
            "name": {
                "english": self.__name,
            },
            "type": [self.__type1, self.__type2],
            "base": {
                "HP": self.__hp,
                "Attack": self.__atk,
                "Defense": self.__def,
                "Sp. Attack": self.__spatk,
                "Sp. Defense": self.__spdef,
                "Speed": self.__speed,
            },
            "profile": {
                "ability": abilities,
            },
        }

    def __str__(self):
        return f"{self.__name} #{self.__id}"