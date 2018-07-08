ch_id = -1001320601139

group = None


def set_group(_group):
    global group
    if _group == "spying":
        group = None
    else:
        group = _group


def get_forward_group():
    global group
    return group
