import os
from sys import argv

import pkmn_inf_fusion as pif


if __name__ == '__main__':
    base_path = argv[1]
    dex_names = os.path.join("data", "dex_names.txt")
    helper = pif.Helper(base_path, dex_names)

    id_ = helper.retriever.get_id("Raichu")
    heads = helper.get_head_fusions(id_)
    # heads.sort()
    bodies = helper.get_body_fusions(id_)
    # bodies.sort()
    print(f"As head #{len(heads)}:")
    print(", ".join([f"{body}" for body in heads]))
    print()
    print(f"As body #{len(bodies)}:")
    print(", ".join([f"{head}" for head in bodies]))

