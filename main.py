import os
from sys import argv
from typing import List, Tuple, Union

import pkmn_inf_fusion as pif


def console_info(base_path: str, helper: pif.Helper, evo_helper: pif.EvolutionHelper):
    #######################################################################
    pokemon = "Eevee"
    min_rate = 0.4  # how much of the possible fusion evolutions must exist
    head_details_for = None
    body_details_for = head_details_for
    #######################################################################
    if head_details_for is not None and head_details_for != "None":
        head_details_for = helper.retriever.get_id(head_details_for)
    if body_details_for is not None and body_details_for != "None":
        body_details_for = helper.retriever.get_id(body_details_for)

    dex_num = helper.retriever.get_id(pokemon)
    evo_lines = evo_helper.get_evolution_lines(dex_num)

    head_fusions = helper.retriever.get_fusions(base_path, dex_num, as_head=True, as_names=False)
    head_fusions.sort()
    head_fusions = evo_helper.dex_nums_to_evo_lines(head_fusions)
    body_fusions = helper.retriever.get_fusions(base_path, dex_num, as_head=False, as_names=False)
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
                fused_line = pif.FusedEvoLine(base_path, helper.retriever, evo_line, other_line, unidirectional=False)
                if fused_line.has_final and fused_line.rate >= min_rate:
                    if head_details_for is None:
                        filtered_fusions.append((fused_line, False))
                    elif head_details_for in other_line:
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


if __name__ == '__main__':
    base_path_ = argv[1]

    helper_ = pif.Helper(base_path_, os.path.join("data", "dex_names.txt"))
    evo_helper_ = pif.EvolutionHelper(os.path.join("data", "evolutions.txt"))

    console_info(base_path_, helper_, evo_helper_)
