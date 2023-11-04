import json

from typing import List, Dict, Any, Optional, Tuple

from pkmn_inf_fusion import util


class Pokemon:
    @staticmethod
    def types() -> List[str]:
        return [
            "Bug", "Dark", "Dragon", "Electric", "Fairy",
            "Fighting", "Fire", "Flying", "Ghost", "Grass",
            "Ground", "Ice", "Normal", "Poison", "Psychic",
            "Rock", "Steel", "Water",
        ]

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
    def is_dual_type(self) -> bool:
        return self.__type1 != self.__type2

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
    def bst(self) -> int:
        return self.__hp + self.__atk + self.__spatk + self.__def + self.__spdef + self.__speed

    @property
    def type1(self) -> str:
        return self.__type1

    @property
    def type2(self) -> str:
        return self.__type2

    @property
    def abilities(self) -> List[str]:
        return self.__abilities.copy()

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


class FusedMon(Pokemon):
    @staticmethod
    def calculate_id(head: int, body: int) -> int:
        return head * util.max_id() + body

    @staticmethod
    def ids_from_fusion(fusion: int) -> Optional[Tuple[int, int]]:
        """

        :param fusion: id of the fusion we want to know the head and body of
        :return: None for invalid ids, else (head_id, body_id)
        """
        # minimal id: head_id = 1, body_id = 1 -> fusion_id = 1 * max_id + 1
        # maximal id: head_id = max_id, body_id = max_id -> fusion_id = max_id * max_id + max_id
        if fusion <= util.max_id() or fusion > util.max_id() * util.max_id() + util.max_id():
            return None  # invalid id
        head_id = int(fusion / util.max_id())
        body_id = fusion % util.max_id()
        return head_id, body_id

    def __init__(self, head: Pokemon, body: Pokemon):
        id_ = FusedMon.calculate_id(head.id, body.id)
        name = head.name + body.name #f"?{head.name[:3]}{body.name[3:]}?"  # incorrect but doesn't matter

        hp = int((2 * head.hp + body.hp) / 3)
        spatk = int((2 * head.spatk + body.spatk) / 3)
        spdef = int((2 * head.spdef + body.spdef) / 3)
        atk = int((2 * body.atk + head.atk) / 3)
        def_ = int((2 * body.def_ + head.def_) / 3)
        speed = int((2 * body.speed + head.speed) / 3)

        abilities = head.abilities + body.abilities
        # types not always true since there are some exceptions (e.g., kanto starters and some birds)
        type1 = head.type1
        type2 = body.type2

        super().__init__(id_, name, hp, atk, spatk, def_, spdef, speed, abilities, type1, type2)
