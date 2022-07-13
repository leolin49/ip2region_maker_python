#  Created by leolin49 on 2022/7/13.
#  Copyright (C) 2022 leolin49. All rights reserved.

# Util function
shift_index = (24, 16, 8, 0)


# checkip convert ip string to integer
def checkip(ip: str) -> int:
    if not is_ipv4(ip):
        return -1
    ps = ip.split(".")
    if len(ps) != 4:
        return 0
    val = 0
    for i in range(len(ps)):
        d = int(ps[i])
        if d < 0 or d > 255:
            return 0
        val |= d << shift_index[i]
    return val


# long2ip convert integer to ip string
def long2ip(num: int) -> str:
    return "{}.{}.{}.{}".format((num >> 24) & 0xFF, (num >> 16) & 0xFF, (num >> 8) & 0xFF, num & 0xFF)


def mid_ip(sip, eip: int):
    return (sip + eip) >> 1


def is_ipv4(ip: str) -> bool:
    p = ip.split(".")
    if len(p) != 4:
        return False
    for pp in p:
        if not pp.isdigit() or len(pp) > 3 or int(pp) > 255:
            return False
    return True
