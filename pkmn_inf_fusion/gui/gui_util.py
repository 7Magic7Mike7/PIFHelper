from typing import Optional, Tuple

from pkmn_inf_fusion import util, FusedMon


def safe_prefix() -> str:
    return "safe_"


def normalize_safe_id(id_: str) -> str:
    """
    Returns a version if id_ without safe_prefix() as prefix.
    :param id_:
    :return:
    """
    prefix = safe_prefix()
    if id_.startswith(prefix):
        id_ = id_[len(prefix):]
    return id_


def parse_ids_from_tree(encoded_id: str) -> Optional[Tuple[int, Optional[int]]]:
    try:
        # since pokemon are stored a bit different in safe, we need to first check this
        if encoded_id.startswith(safe_prefix()):
            encoded_id = int(normalize_safe_id(encoded_id))
            if encoded_id > util.max_id():
                return FusedMon.ids_from_fusion(encoded_id)
            else:
                return encoded_id, None
        else:
            if "_" in encoded_id:
                # we selected a concrete fusion
                data = encoded_id.split("_")[1]  # first part is evolution line, second part is concrete
                data = data.split("-")
                head_id = int(data[0])
                body_id = int(data[1])

                return head_id, body_id

            elif "-" in encoded_id:
                # we selected a fusion line -> showcase base mon since the concrete fusion can be seen by expanding
                # skip prefix ("h" or "b") indicating for this case irrelevant fusion position
                data = encoded_id[1:].split("-")  # split ids separated by "-"
                mon_id = int(data[1])
                return mon_id, None

            elif encoded_id in ["head", "body", "safe"]:
                pass  # nothing to do
            else:
                # we selected a single pokemon
                # skip prefix ("h" or "b") indicating for this case irrelevant fusion position
                mon_id = int(encoded_id[1:])
                return mon_id, None
    except:
        print(f"Selection error for id: {encoded_id}")

    return None
