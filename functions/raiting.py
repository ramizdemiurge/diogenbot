ids = [0, 0]


def check_rate_flood(sender, recipient):
    global ids
    if sender == recipient:
        return True
    elif sender == ids[0] and recipient == ids[1]:
        return True
    elif sender == ids[1] and recipient == ids[0]:
        return True
    ids = [sender, recipient]
    return False


def check_rate_flood_hard_mode(sender, recipient):
    global ids
    if sender == recipient:
        return True
    elif sender == ids[0] and recipient == ids[1]:
        return True
    elif sender == ids[1]:
        return True
    ids = [sender, recipient]
    return False
