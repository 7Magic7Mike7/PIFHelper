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

    def to_leveled_list(self) -> List[Tuple[int, Optional[int]]]:
        """
        Returns a list of tuples describing at what a pokemon in the evolution line evolves. A pokemon that doesn't
        evolve is indicated by None.
        E.g.: the Charizard-line would return [(4, 16), (5, 36), (6, None)]

        :return: list of (id, evolution level)
        """

        lvl1 = None if self.lvl1 is None else self.lvl1
        # don't use 0 because some end-stages evolve with stones and therefore can occur naturally as soon as evo1's lvl
        lvl2 = lvl1 if self.lvl2 is None else self.lvl2

        list_ = [(self.base, lvl1)]
        if self.evo1 is not None:
            list_.append((self.evo1, lvl2))
        if self.evo2 is not None:
            list_.append((self.evo2, None))     # there is no end
        return list_

    def natural_at_level(self, level: int) -> List[int]:
        leveled_list = self.to_leveled_list()
        i = 0
        while i < len(leveled_list):
            mon, lvl = leveled_list[i]
            i += 1
            if lvl is None or level > lvl:
                break
        # i is now either at the last mon that can naturally be at the given level or at the end of leveled_list
        # (meaning that the end stage is the last mon that can naturally be at the given level)

        ret_val = [leveled_list[i][0]]  # add the last mon
        # now check if previous mons can occur at the same level (i.e., don't evolve by level up into the last mon)
        for j in range(i-1, -1, -1):
            if leveled_list[j][1] == leveled_list[i][1]:    # todo check None-cases?
                ret_val.append(leveled_list[j][0])
        ret_val.reverse()   # reverse the list so we have an ascending order
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
    def from_json(data: List[Dict[str, Any]]) -> "EvolutionHelper":
        evolutions: Dict[Optional[int], List[EvolutionLine]] = {}

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


        def test(line1: EvolutionLine, line2: EvolutionLine):
            naturals: List[Tuple[int, int, int]] = []   # (lvl, mon1, mon2)
            # find out which pokemon of line2 can occur at the evolution levels of line1 (simulating line1 evolving)
            for mon1, lvl1 in line1.to_leveled_list():
                for mon2 in line2.natural_at_level(lvl1):
                    naturals.append((lvl1, mon1, mon2))

            # do the same in the other direction (simulating line2 evolving)
            for mon2, lvl2 in line2.to_leveled_list():
                for mon1 in line1.natural_at_level(lvl2):
                    naturals.append((lvl2, mon1, mon2))

            naturals.sort()     # sort by level
            natural_fusions = [(mon1, mon2) for _, mon1, mon2 in naturals]

            nat_set = list(set(natural_fusions))
            if len(nat_set) != len(natural_fusions):
                debug = True

            return natural_fusions

        def check_natural_progression(line1: EvolutionLine, line2: EvolutionLine):
            # fusions that can occur naturally (e.g., Charmander + Venusaur is no natural progression)
            naturals: List[Tuple[int, int]] = []

            ll1 = line1.to_leveled_list()
            ll2 = line2.to_leveled_list()
            i1, i2 = 0, 0
            level1, level2 = 0, 0
            level_up_flag = True
            new_addition = True
            while True:
                mon1, evo_level1 = ll1[i1]
                mon2, evo_level2 = ll2[i2]
                if new_addition:
                    naturals.append((mon1, mon2))
                    new_addition = False

                if evo_level1 is None and evo_level2 is None:
                    break

                if level_up_flag:
                    level1 += 1
                    if evo_level1 is not None and level1 == evo_level1:
                        i1 += 1
                        new_addition = True
                else:
                    level2 += 1
                    if evo_level2 is not None and level2 == evo_level2:
                        i2 += 1
                        new_addition = True

                level_up_flag = not level_up_flag

            return naturals

        self.__naturals = test(evo_line1, evo_line2)
        if not unidirectional:
            self.__naturals += test(evo_line2, evo_line1)

    @property
    def rate(self) -> float:
        return len(self.__existing) / (len(self.__existing) + len(self.__missing))

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
    def naturals(self) -> Iterator[Tuple[int, int]]:
        return iter(self.__naturals)

    @property
    def last(self) -> Tuple[int, int]:
        return self.__existing[-1]

    @property
    def last_mon(self) -> Optional[FusedMon]:
        head, body = self.last
        return FusionRetriever.from_ids(self.__retriever, head, body)

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
