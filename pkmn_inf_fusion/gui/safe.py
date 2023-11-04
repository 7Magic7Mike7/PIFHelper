from typing import Callable, Set, Optional, Tuple, Union

from pkmn_inf_fusion import FusionRetriever, FusedMon
from pkmn_inf_fusion.gui import safe_prefix, normalize_safe_id


class Safe:
    def __init__(self, retriever: FusionRetriever, insert: Callable[[str, str], None], delete: Callable[[str], None],
                 reset_details: Callable[[], None]):
        self.__retriever = retriever
        self.__insert = insert
        self.__delete = delete
        self.__reset_details = reset_details

        self.__saved_mons: Set[int] = set()

    def is_saved(self, id_: Union[str, int, Tuple[int, Optional[int]]]) -> bool:
        if isinstance(id_, str):
            id_ = int(normalize_safe_id(id_))  # we store the ids without the prefix so let's remove it

        elif isinstance(id_, Tuple):
            head_id, body_id = id_
            if body_id is None:
                id_ = head_id
            else:
                id_ = FusedMon.calculate_id(head_id, body_id)

        return id_ in self.__saved_mons

    def save(self, head_id: int, body_id: Optional[int]):
        if body_id is None:
            pokemon = self.__retriever.get_pokemon(head_id)
        else:
            pokemon = FusionRetriever.from_ids(self.__retriever, head_id, body_id)

        if pokemon.id in self.__saved_mons: return

        self.__saved_mons.add(pokemon.id)  # always save without prefix to avoid unintentional duplicates
        self.__insert(f"{safe_prefix()}{pokemon.id}", pokemon.name)

    def remove(self, head_id: int, body_id: Optional[int]):
        if body_id is None:
            pokemon = self.__retriever.get_pokemon(head_id)
        else:
            pokemon = FusionRetriever.from_ids(self.__retriever, head_id, body_id)

        if pokemon.id in self.__saved_mons:
            # add the prefix because that's how it is saved in the TreeView
            self.__delete(f"{safe_prefix()}{pokemon.id}")

            self.__saved_mons.remove(pokemon.id)
            self.__reset_details()

    def invert_state(self, id_: Union[str, int, Tuple[int, Optional[int]]]):
        """
        Saves the mon corresponding to id_ if it's not already saved, otherwise removes it.

        :param id_: id(s) of the mon we want to save or remove
        :return:
        """
        if isinstance(id_, int):
            head_id, body_id = id_, None

        elif isinstance(id_, Tuple):
            head_id, body_id = id_

        else:
            # we store the ids without the prefix so let's remove it
            head_id, body_id = int(normalize_safe_id(id_)), None

        if self.is_saved(id_):
            self.remove(head_id, body_id)
        else:
            self.save(head_id, body_id)
