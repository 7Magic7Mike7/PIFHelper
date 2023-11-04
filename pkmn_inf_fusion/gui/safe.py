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

        self.__saved_mons: Set[str] = set()

    def _save(self, id_: str, text: str):
        # we are finished if id_ is already saved
        if id_ in self.__saved_mons: return

        self.__saved_mons.add(id_)  # always save without prefix to avoid unintentional duplicates
        self.__insert(f"{safe_prefix()}{id_}", text)

    def is_saved(self, id_: Union[str, int, Tuple[int, Optional[int]]]) -> bool:
        if isinstance(id_, int):
            id_ = str(id_)

        elif isinstance(id_, Tuple):
            head_id, body_id = id_
            if body_id is None:
                id_ = str(head_id)
            else:
                id_ = str(FusedMon.calculate_id(head_id, body_id))

        else:
            id_ = normalize_safe_id(id_)    # we store the ids without the prefix so let's remove it
        return id_ in self.__saved_mons

    def save(self, head_id: int, body_id: Optional[int]):
        if body_id is None:
            pokemon = self.__retriever.get_pokemon(head_id)
        else:
            pokemon = FusionRetriever.from_ids(self.__retriever, head_id, body_id)

        self._save(str(pokemon.id), pokemon.name)

    def remove(self, head_id: int, body_id: Optional[int]):
        if body_id is None:
            pokemon = self.__retriever.get_pokemon(head_id)
        else:
            pokemon = FusionRetriever.from_ids(self.__retriever, head_id, body_id)

        id_ = str(pokemon.id)
        if id_ in self.__saved_mons:
            # add the prefix because that's how it is saved in the TreeView
            self.__delete(f"{safe_prefix()}{id_}")

            self.__saved_mons.remove(id_)
            self.__reset_details()
