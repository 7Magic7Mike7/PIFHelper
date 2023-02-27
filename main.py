import os
from sys import argv

import pkmn_inf_fusion as pif


def console_info(base_path: str, helper: pif.Helper, evo_helper: pif.EvolutionHelper):
    #######################################################################
    pokemon = "Wynaut"
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

    print("########################################")
    print("################  HEAD  ################")
    print("########################################")
    print()

    counter = 0
    for evo_line in evo_lines:
        for other_line in head_fusions:
            fused_line = pif.FusedEvoLine(base_path, helper.retriever, evo_line, other_line, unidirectional=True)
            if fused_line.has_final and fused_line.rate >= min_rate:
                if head_details_for is None:
                    print(fused_line.formatted_string(existing=False, missing=False, headline_ids=False))
                    counter += 1
                    if counter % 5 == 0:
                        print()
                elif head_details_for in other_line:
                    print(fused_line.formatted_string(missing=False, headline_ids=False))
                    counter += 1
                    if counter % 5 == 0:
                        print()
        print()

    print()
    print("########################################")
    print("################  BODY  ################")
    print("########################################")
    print()

    counter = 0
    for evo_line in evo_lines:
        for other_line in body_fusions:
            fused_line = pif.FusedEvoLine(base_path, helper.retriever, other_line, evo_line, unidirectional=True)
            if fused_line.has_final and fused_line.rate >= min_rate:
                if body_details_for is None:
                    print(fused_line.formatted_string(existing=False, missing=False, headline_ids=False))
                    counter += 1
                    if counter % 5 == 0:
                        print()

                elif body_details_for in other_line:
                    print(fused_line.formatted_string(missing=False, headline_ids=False))
                    counter += 1
                    if counter % 5 == 0:
                        print()
        print()


if __name__ == '__main__':
    base_path_ = argv[1]

    helper_ = pif.Helper(base_path_, os.path.join("data", "dex_names.txt"))
    evo_helper_ = pif.EvolutionHelper(os.path.join("data", "evolutions.txt"))

    console_info(base_path_, helper_, evo_helper_)
