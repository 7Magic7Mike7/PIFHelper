import os
from sys import argv
from typing import List, Tuple, Union, Optional

import pkmn_inf_fusion as pif
from pkmn_inf_fusion import util


def console_info(helper: pif.Helper, evo_helper: pif.EvolutionHelper):
    #######################################################################
    pokemon = "Crobat"
    min_rate = 0.1  # how much of the possible fusion evolutions must exist
    details_for = "Weavile"
    #######################################################################

    if details_for is not None:
        if details_for == "None" or len(details_for) <= 0:
            details_for = None
        else:
            details_for = helper.retriever.get_id(details_for)

    dex_num = helper.retriever.get_id(pokemon)
    evo_lines = evo_helper.get_evolution_lines(dex_num)

    head_fusions = helper.retriever.get_fusions(dex_num, as_head=True, as_names=False)
    head_fusions.sort()
    head_fusions = evo_helper.dex_nums_to_evo_lines(head_fusions)
    body_fusions = helper.retriever.get_fusions(dex_num, as_head=False, as_names=False)
    body_fusions.sort()
    body_fusions = evo_helper.dex_nums_to_evo_lines(body_fusions)

    def get_headline(info: Union[int, str]) -> str:
        if isinstance(info, int):
            return "\n" \
                "-----------------------------------------\n" \
                f"Line: {helper.retriever.get_name(info)}\n" \
                "-----------------------------------------"
        else:
            return \
                "########################################\n" \
                f"################  {info}  ################\n" \
                "########################################"

    split_index: List[Tuple[int, str]] = []
    filtered_fusions: List[Tuple[pif.FusedEvoLine, bool]] = []
    for evo_line in evo_lines:
        split_index.append((len(filtered_fusions), get_headline(evo_line.end_stage)))

        for fusions_data in [(head_fusions, get_headline("HEAD")), (body_fusions, get_headline("BODY"))]:
            fusions, description = fusions_data
            split_index.append((len(filtered_fusions), description))

            for other_line in fusions:
                fused_line = pif.FusedEvoLine(helper.retriever, evo_line, other_line, unidirectional=False)
                if fused_line.has_final and fused_line.rate >= min_rate:
                    if details_for is None:
                        filtered_fusions.append((fused_line, False))
                    elif details_for in other_line:
                        filtered_fusions.append((fused_line, True))

    cur_split = 0
    for i, val in enumerate(filtered_fusions):
        while i == split_index[cur_split][0]:
            print(split_index[cur_split][1])
            print()
            if cur_split + 1 < len(split_index):
                cur_split += 1
            else:
                break

        fused_line, details = val
        print(fused_line.formatted_string(existing=details, missing=False, headline_ids=False))
        if i % 5 == 4:
            print()
    print()


def console_info2(helper: pif.Helper, evo_helper: pif.EvolutionHelper, main_mon: Union[str, int],
                  detail_mon: Optional[Union[str, int]] = None, available_mons: Optional[List[str]] = None,
                  detail_rate: float = 0.5, check_stagewise: bool = True, check_final: bool = False):
    # check validity of rate
    assert 0 <= detail_rate <= 1, f"detail_rate not a ratio: {detail_rate}!"

    # check validity of main_mon
    if isinstance(main_mon, str):
        main_mon = helper.retriever.get_id(main_mon)
    assert util.min_id() <= main_mon <= util.max_id(), f"Invalid id for main_mon: {util.min_id()} <= {main_mon} " \
                                                       f"<= {util.max_id()} is False!"

    # check validity of detail_mon
    if detail_mon is not None and isinstance(detail_mon, str):
        if len(detail_mon) <= 0: detail_mon = None
        else:
            temp_name = detail_mon
            detail_mon = helper.retriever.get_id(detail_mon)

            assert util.min_id() <= detail_mon <= util.max_id(), f"Invalid id for {temp_name}: {util.min_id()} <= " \
                                                                 f"{detail_mon} <= {util.max_id()} is False!"

    # final is implicitly checked during stagewise check
    if check_stagewise: check_final = False

    if detail_mon is None:
        # retrieve all head and body fusions for main_mon
        head_fusions = helper.retriever.get_fusions(main_mon, as_head=True, as_names=False)
        body_fusions = helper.retriever.get_fusions(main_mon, as_head=False, as_names=False)

        # ignore "duplicates" based on evolution lines (e.g. pikachu/doduo is ignored for raichu/dodrio)
        head_fusions = evo_helper.dex_nums_to_evo_lines(head_fusions)
        body_fusions = evo_helper.dex_nums_to_evo_lines(body_fusions)

        # sort (based on dex)
        head_fusions.sort()
        body_fusions.sort()

        if available_mons is not None and len(available_mons) > 0:
            available_ids = []
            for av_mon in available_mons:
                av_id = helper.retriever.get_id(av_mon)
                if av_id != -1: available_ids.append(av_id)
            head_fusions = pif.EvolutionHelper.availability_filter(head_fusions, available_ids)
            body_fusions = pif.EvolutionHelper.availability_filter(body_fusions, available_ids)

        main_lines = evo_helper.get_evolution_lines(main_mon)
        for main_line in main_lines:
            for data in [(head_fusions, True), (body_fusions, False)]:
                fusions, as_head = data
                print("########################################\n"
                      f"################  {'HEAD' if as_head else 'BODY'}  ################\n"
                      "########################################")
                counter = 0
                for other_line in fusions:
                    l1 = main_line if as_head else other_line
                    l2 = other_line if as_head else main_line
                    fused_line = pif.FusedEvoLine(helper.retriever, l1, l2, unidirectional=True)

                    # skip if the rate or stagewise- or final-pairing is not fulfilled
                    if fused_line.rate < detail_rate or \
                            (check_stagewise and not fused_line.has_stagewise_fusions) or \
                            (check_final and not fused_line.has_final):
                        continue
                    # print our found candidate
                    print(fused_line.formatted_string(existing=False, missing=False, headline_ids=False,
                                                      include_rate=True))
                    counter += 1
                    if counter % 5 == 0: print()
                if counter % 5 != 0: print()    # print an empty line if it wasn't already printed in the inner loop
    else:
        main_lines = evo_helper.get_evolution_lines(main_mon)
        detail_lines = evo_helper.get_evolution_lines(detail_mon)

        for mel in main_lines:  # main evolution lines
            for del_ in detail_lines:  # detail evolution lines
                fusion_line = pif.FusedEvoLine(helper.retriever, mel, del_, unidirectional=False)
                print(fusion_line.formatted_string(existing=True, missing=False, headline_ids=False, include_rate=True))


if __name__ == '__main__':
    USE_GUI = True

    if len(argv) <= 1:
        with open(os.path.join("data", "default_path")) as file:
            base_path_ = file.readline()
    else:
        base_path_ = argv[1]

    helper_ = pif.Helper(base_path_, os.path.join("data", "dex_names.txt"))
    evo_helper_ = pif.EvolutionHelper(os.path.join("data", "evolutions.txt"))

    main_mon_ = "Eevee"
    available_mons_ = [
    ]

    if USE_GUI:
        gui = pif.GUI(helper_.retriever, evo_helper_, main_mon_, available_mons_)
        gui.start()
    else:
        detail_mon_ = ""
        # console_info(helper_, evo_helper_)
        console_info2(helper_, evo_helper_, main_mon_, detail_mon_, available_mons_, detail_rate=0.5,
                      check_stagewise=True,
                      check_final=False)    # final is implicitly checked in stagewise
