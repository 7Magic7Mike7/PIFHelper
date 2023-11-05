import json
from typing import List, Dict, Optional, Union, Tuple, Set, Iterator, Iterable, Any

from pkmn_inf_fusion import util, FusionRetriever, FusedMon


class _Parser:
    __BASE_SEPARATOR = "->"
    __LINE_SEPARATOR = "|"
    __EVO_SEPARATOR = ","

    @staticmethod
    def evo_list(line: str) -> List[int]:
        return [int(val) for val in line.replace(" ", "").split(_Parser.__EVO_SEPARATOR)]

    @staticmethod
    def base_split(line: str) -> Tuple[int, str]:
        base, evolution_part = line.split(_Parser.__BASE_SEPARATOR)
        return int(base), evolution_part

    @staticmethod
    def is_separable(line: str) -> bool:
        return _Parser.__BASE_SEPARATOR in line

    @staticmethod
    def line_split(evolution_part: str) -> List[str]:
        return evolution_part.split(_Parser.__LINE_SEPARATOR)


class EvolutionLine:
    @staticmethod
    def get_pre_split_ids(evo_lines: List["EvolutionLine"]) -> List[int]:
        if len(evo_lines) < 1: return []

        # check if base is the same pokemon for all evo lines
        base_mon: int = evo_lines[0].base
        for evo_line in evo_lines:
            if base_mon != evo_line.base:
                return []   # return empty list since not even the base is the same for all provided evo lines

        # check if evo1 is still the same pokemon for all evo lines
        evo1_mon: int = evo_lines[0].evo1
        for evo_line in evo_lines:
            if evo1_mon != evo_line.evo1:
                return [base_mon]   # only base is the same

        # check if evo2 is still the same pokemon for all evo lines (meaning evo lines would all be identical)
        evo2_mon: int = evo_lines[0].evo2
        for evo_line in evo_lines:
            if evo2_mon != evo_line.evo2:
                return [base_mon, evo1_mon]

        return [base_mon, evo1_mon, evo2_mon]

    def __init__(self, base_pkmn: Union[int, str], evolutions: Union[List[int], str],
                 levels: Optional[List[int]] = None):
        if isinstance(base_pkmn, str):
            assert util.is_valid_pkmn(base_pkmn), f"Invalid base Pokemon: {base_pkmn}!"
            base_pkmn = int(base_pkmn)
        if isinstance(evolutions, str):
            evos = []
            for pkmn in _Parser.evo_list(evolutions):
                assert util.is_valid_pkmn(pkmn), f"Invalid evolution: {pkmn}!"
                evos.append(int(pkmn))
            evolutions = evos

        self.__base = base_pkmn
        self.__evos = evolutions

        levels = [] if levels is None else levels
        for i in range(1, len(self.__evos)):
            if len(levels) < i:     # fill out missing level information
                if len(levels) == 0:
                    # append 0 because we don't have any specific evolution information
                    levels.append(0)
                else:
                    # append previous level because we don't have any specific evolution information and cannot use 0
                    # because some end-stages evolve with stones and therefore can occur naturally as soon as previous
                    # evolution's lvl
                    levels.append(levels[-1])
        self.__levels = levels

    @property
    def base(self) -> int:
        return self.__base

    @property
    def evo1(self) -> Optional[int]:
        if len(self.__evos) > 0:
            return self.__evos[0]
        return None

    @property
    def evo2(self) -> Optional[int]:
        if len(self.__evos) > 1:
            return self.__evos[1]
        return None

    @property
    def lvl1(self) -> Optional[int]:
        if len(self.__levels) > 0:
            return self.__levels[0]
        return None

    @property
    def lvl2(self) -> Optional[int]:
        if len(self.__levels) > 1:
            return self.__levels[1]
        return None

    @property
    def end_stage(self) -> int:
        if self.evo1 is None:
            return self.base
        elif self.evo2 is None:
            return self.evo1
        else:
            return self.evo2

    @property
    def is_multi_stage(self) -> bool:
        return self.size > 1

    @property
    def size(self) -> int:
        return len(self)

    def named_str(self, fusion_retriever: FusionRetriever) -> str:
        text = fusion_retriever.get_name(self.__base)
        for evo in self.__evos:
            text += f" -> {fusion_retriever.get_name(evo)}"
        return text

    def to_list(self) -> List[int]:
        list_ = [self.base]
        if self.evo1 is not None:
            list_.append(self.evo1)
        if self.evo2 is not None:
            list_.append(self.evo2)
        return list_

    def to_leveled_list(self, as_max_lvl: bool) -> List[Tuple[int, Optional[int]]]:
        """
        Returns a list of tuples either describing at what level a pokemon in the evolution line *will evolve* or when
        it *has evolved*.

        E.g.: the Charizard-line would return
                - as_max_lvl=True:    [(4, 16), (5, 36), (6, None)]

                - as_max_lvl=False:   [(4, 0), (5, 16), (6, 36)]


        :param as_max_lvl: whether to get a list of the max levels (= level when they evolve) or min levels (= level
                            where they evolve*d*)

        :return: list of (id, evolution level)
        """

        lvl1 = None if self.lvl1 is None else self.lvl1
        lvl2 = None if self.lvl2 is None else self.lvl2
        # adapt lvl2 if it's a stone evolution because it cannot exist before the first evolution at lvl1
        if lvl2 == 0: lvl2 = lvl1

        list_ = [(self.base, lvl1 if as_max_lvl else 0)]
        if self.evo1 is not None:
            list_.append((self.evo1, lvl2 if as_max_lvl else lvl1))
        if self.evo2 is not None:
            list_.append((self.evo2, None if as_max_lvl else lvl2))     # there is no end
        return list_

    def natural_at_level(self, level: int, consider_equal_levels: bool = True) -> List[int]:
        """

        :param level: the level we simulate the evolution line to be in
        :param consider_equal_levels: whether we want to consider the state *at* level or *after* level
        :return:
        """
        max_leveled_list = self.to_leveled_list(as_max_lvl=True)

        if level is None:
            # level is None because we want to consider "unlimited level", aka end stage
            i = len(max_leveled_list)
        else:
            i = 0
            while i < len(max_leveled_list):
                mon, lvl = max_leveled_list[i]
                i += 1
                if lvl is None or lvl > level or (consider_equal_levels and lvl == level):
                    break
        i -= 1
        # i is now either at the last mon that can naturally be at the given level or at the end of leveled_list
        # (meaning that the end stage is the last mon that can naturally be at the given level)

        min_leveled_list = self.to_leveled_list(as_max_lvl=False)
        ret_val = []
        lvl_compare = min_leveled_list[i][1]
        for j in range(len(min_leveled_list)):
            if min_leveled_list[j][1] == lvl_compare:
                ret_val.append(min_leveled_list[j][0])

        return ret_val

    def __contains__(self, item):
        if isinstance(item, int):
            return item == self.__base or item in self.__evos
        return False

    def __len__(self) -> int:
        return 1 + len(self.__evos)

    def __str__(self) -> str:
        text = f"{self.__base}"
        for evo in self.__evos:
            text += f" -> {evo}"
        return text

    def __hash__(self):
        val = 17 * self.base
        if self.evo1 is not None:
            val += 311 * self.evo1
        if self.evo2 is not None:
            val += 523 * self.evo2
        return val

    def __eq__(self, other):
        if isinstance(other, EvolutionLine):
            return self.base == other.base and self.evo1 == other.evo1 and self.evo2 == other.evo2
        return False

    def __lt__(self, other):
        if isinstance(other, EvolutionLine):
            if self == other: return False

            if self.base == other.base:
                # if they share the same base but are not equal, both need to have at least one evolution
                if self.evo1 == other.evo1:
                    # if they have the same base and evo1 but are not equal they need to have a different evo2
                    return self.evo2 < other.evo2
                else:
                    return self.evo1 < other.evo1
            else:
                return self.base < other.base
        return False


class EvolutionHelper:
    @staticmethod
    def availability_filter(evolution_lines: Iterable[EvolutionLine], available_ids: Iterable[int]) \
            -> Iterable[EvolutionLine]:
        """

        :param evolution_lines: the list of evolution lines we want to filter
        :param available_ids: ids/dex num of the available pokemon
        :return: a filtered version of evolution_lines
        """
        filtered_lines = []
        for evo_line_ in evolution_lines:
            for mon in available_ids:
                if mon in evo_line_:
                    filtered_lines.append(evo_line_)
                    break
        return filtered_lines

    @staticmethod
    def from_txt(evolutions_file: str) -> "EvolutionHelper":
        evolutions: Dict[Optional[int], List[EvolutionLine]] = {}

        def store_evolution(line: str):
            line = line.replace(" ", "")    # remove whitespace

            if _Parser.is_separable(line):
                # multi stage pokemon (= evolution(s) exist)
                base, evolution_part = _Parser.base_split(line)
                evo_lines = [
                    EvolutionLine(base, val)
                    for val in _Parser.line_split(evolution_part)
                ]

                for evo_line in evo_lines:
                    # store the evolution line for each pokemon in it (still works if evo1 or evo2 are None)
                    evo1, evo2 = evo_line.evo1, evo_line.evo2
                    evolutions[base] = evo_lines
                    evolutions[evo1] = evo_lines
                    evolutions[evo2] = evo_lines
            else:
                # single stage pokemon
                assert util.is_valid_pkmn(line), f"Invalid base Pokemon: {line}!"
                evo_line = EvolutionLine(line, [])
                evolutions[evo_line.base] = [evo_line]

        util.analyze_data_file(evolutions_file, store_evolution)
        return EvolutionHelper(evolutions)

    @staticmethod
    def from_json(path: str) -> "EvolutionHelper":
        evolutions: Dict[Optional[int], List[EvolutionLine]] = {}

        with open(path, encoding='utf-8') as file:
            # Load the JSON data
            data = json.load(file)

        evolution_data: Dict[int, Dict] = {}
        for item in data:
            evolution_data[item["id"]] = item

        # init with all ids and remove all pre-evolutions -> only end stages are left
        end_stages: Set[int] = set(list(range(util.min_id(), util.max_id() + 1)))
        for key in evolution_data.keys():
            pre_evo = evolution_data[key]["pre-evolution"]["id"]
            if pre_evo in end_stages:
                end_stages.remove(pre_evo)

        for val in end_stages:
            evo_list = []
            level_list = []
            cur_mon = val
            while True:
                evo_list.append(cur_mon)
                if cur_mon in evolution_data:
                    pre_evo = evolution_data[cur_mon]["pre-evolution"]["id"]
                    level_list.append(evolution_data[cur_mon]["pre-evolution"]["level"])
                    cur_mon = pre_evo
                else:
                    break   # we reached the end

            evo_list.reverse()
            level_list.reverse()

            # save the new evolution line for every mon in the evolution line
            evo_line = EvolutionLine(evo_list[0], evo_list[1:], level_list)
            for id_ in evo_list:
                if id_ not in evolutions: evolutions[id_] = []
                evolutions[id_].append(evo_line)

        """
        considered_mons: Set[int] = set()
        
        def append_mon(evo_id: int, evo_lvl: int, evo_line: List[int], level_list: List[int]) \
                -> Tuple[List[int], List[int]]:
            considered_mons.add(evo_id)

            if evo_id in evolution_data:
                new_item = evolution_data[evo_id]
                for new_evo in new_item["evolutions"]:
                    append_mon(new_evo, evo_line + [mon_id], level_list + [evo_level])
                return None
            else:
                return evo_line + [evo_id], level_list + [evo_lvl]

        for item in evolution_data.values():
            base_mon = item["id"]
            if base_mon in considered_mons: continue

            for evo in item["evolutions"]:
                evo_lines = append_mon(evo["id"], evo["level"], [base_mon], [])

        """
        # todo add all single stage pokemon

        return EvolutionHelper(evolutions)

    def __init__(self, evolutions: Dict[Optional[int], List[EvolutionLine]]):
        self.__evolutions: Dict[Optional[int], List[EvolutionLine]] = evolutions

    def get_evolution_lines(self, dex_num: int, exclude_parallels: bool = True) -> List[EvolutionLine]:
        """

        :param dex_num:
        :param exclude_parallels: excludes parallel evolution lines (evolution line had to branch already)
        :return:
        """
        assert util.is_valid_pkmn(dex_num), f"Invalid dex number: {dex_num}!"
        assert dex_num in self.__evolutions, f"ERROR! {dex_num} seems not to be stored!"

        if exclude_parallels:
            return list(filter(
                lambda el: dex_num in el,   # only keep lines that involve dex_num
                self.__evolutions[dex_num]
            ))
        return self.__evolutions[dex_num]

    def dex_nums_to_evo_lines(self, dex_nums: List[int]) -> List[EvolutionLine]:
        evo_lines: Set[EvolutionLine] = set()

        for dex_num in dex_nums:
            cur_lines = self.get_evolution_lines(dex_num, exclude_parallels=True)
            for line in cur_lines:
                evo_lines.add(line)

        return list(evo_lines)


class FusedEvoLine:
    def __init__(self, retriever: FusionRetriever, evo_line1: EvolutionLine, evo_line2: EvolutionLine,
                 unidirectional: bool = False):
        """

        :param retriever:
        :param evo_line1: head_line if unidirectional is True
        :param evo_line2: body_line if unidirectional is True
        :param unidirectional: whether evo_line1 can only be the head and evo_line2 only the body or also the other way
                                around
        """
        self.__retriever = retriever
        self.__line1 = evo_line1
        self.__line2 = evo_line2

        existing: List[Tuple[int, int]] = []
        missing: List[Tuple[int, int]] = []

        def check_line(line1: EvolutionLine, line2: EvolutionLine):
            for dex_num in line1.to_list():
                fusions = retriever.get_fusions(dex_num, as_head=True, as_names=False)
                for fused_num in line2.to_list():
                    if fused_num in fusions:
                        existing.append((dex_num, fused_num))
                    else:
                        missing.append((dex_num, fused_num))

        check_line(evo_line1, evo_line2)
        if not unidirectional:
            check_line(evo_line2, evo_line1)

        self.__existing = existing
        self.__missing = missing

        naturals = []   # (lvl, mon1, mon2)
        # find out which pokemon of line2 can occur at the evolution levels of line1 (simulating line1 evolving)
        for mon1, lvl1 in evo_line1.to_leveled_list(as_max_lvl=False):
            for mon2 in evo_line2.natural_at_level(lvl1):
                if lvl1 is None: lvl1 = util.max_lvl()
                naturals.append((lvl1, mon1, mon2))

        # do the same in the other direction (simulating line2 evolving)
        for mon2, lvl2 in evo_line2.to_leveled_list(as_max_lvl=False):
            for mon1 in evo_line1.natural_at_level(lvl2, consider_equal_levels=False):
                if lvl2 is None: lvl2 = util.max_lvl()
                naturals.append((lvl2, mon1, mon2))

        # todo check if this could easily be avoided (maybe only end-stages can be duplicated or they are always duplicated?)
        naturals = list(set([(mon1, mon2) for _, mon1, mon2 in naturals]))  # remove the duplicates that can occur
        naturals.sort()     # sort by level (needs to be done after set()-operation!)

        if not unidirectional:
            all_naturals = []
            for val in naturals:
                mon1, mon2 = val
                all_naturals.append((mon1, mon2))
                all_naturals.append((mon2, mon1))
        else:
            all_naturals: List[Tuple[int, int]] = naturals

        existing_nats = []
        missing_nats = []
        for fusion in all_naturals:
            if fusion in self.__existing:
                existing_nats.append(fusion)
            else:
                missing_nats.append(fusion)
        self.__existing_nats = existing_nats
        self.__missing_nats = missing_nats

    @property
    def rate(self) -> float:
        return len(self.__existing) / (len(self.__existing) + len(self.__missing))

    @property
    def natural_rate(self) -> float:
        return len(self.__existing_nats) / (len(self.__existing_nats) + len(self.__missing_nats))

    @property
    def has_final(self) -> bool:
        return (self.__line1.end_stage, self.__line2.end_stage) in self.__existing

    @property
    def has_stagewise_fusions(self) -> bool:
        # check if both base stages have a custom fusion
        if not (self.__line1.base, self.__line2.base) in self.__existing:
            return False
        # check if there exists a middle stages (only possible if a second evolution exists) for both
        if self.__line1.evo2 is not None and self.__line2.evo2 is not None:
            # in that case check if both middle stages have a custom fusion
            if not (self.__line1.evo1, self.__line2.evo1) in self.__existing:
                return False
        # lastly, there needs to be a final fusion (if both lines don't have any evolution this is the same as the
        # first check)
        return self.has_final

    @property
    def existing(self) -> Iterator[Tuple[int, int]]:
        return iter(self.__existing)

    @property
    def last(self) -> Tuple[int, int]:
        return self.__existing[-1]

    @property
    def last_mon(self) -> Optional[FusedMon]:
        head, body = self.last
        return FusionRetriever.from_ids(self.__retriever, head, body)

    def naturals(self, include_missing: bool = False) -> Iterator[Tuple[int, int]]:
        if include_missing:
            # we have to sort because existing and missing are only sorted among themselves
            sorted_nats = self.__existing_nats + self.__missing_nats
            sorted_nats.sort()
            return iter(sorted_nats)
        else:
            return iter(self.__existing_nats)

    def formatted_string(self, existing: bool = True, missing: bool = True, headline_ids: bool = True,
                         include_rate: bool = False) -> str:
        text = ""
        if headline_ids:
            text += f"#{self.__line1.end_stage} & " \
                    f"#{self.__line2.end_stage}"
        else:
            text += f"{self.__retriever.get_name(self.__line1.end_stage)} & " \
                    f"{self.__retriever.get_name(self.__line2.end_stage)}"

        if include_rate: text += f"\t [{100 * self.rate:.0f}%]"

        if existing and len(self.__existing) > 0:
            text += "\n\tExisting:\n"
            for fusion in self.__existing:
                head, body = fusion
                text += f"\t\t- {self.__retriever.get_name(head)} + {self.__retriever.get_name(body)}\n"
            text = text[:-1]    # remove last \n

        if missing and len(self.__missing) > 0:
            text += "\n\tMissing:\n"
            for fusion in self.__missing:
                head, body = fusion
                text += f"\t\t- {self.__retriever.get_name(head)} + {self.__retriever.get_name(body)}\n"
            text = text[:-1]    # remove last \n

        return text

    def to_mons(self) -> List[FusedMon]:
        mons = []
        for head, body in self.__existing:
            mon = FusionRetriever.from_ids(self.__retriever, head, body)
            if mon is not None:
                mons.append(mon)
        return mons

    def __str__(self) -> str:
        return f"EvoLine-Fusions of #{self.__line1.end_stage} & #{self.__line2.end_stage} " \
               f"({len(self.__existing)} exist, {len(self.__missing)} miss)"
