# Copyright 2022 The Ip2Region Authors. All rights reserved.
# Use of this source code is governed by a Apache2.0-style
# license that can be found in the LICENSE file.

# Util function
shift_index = (24, 16, 8, 0)


def check_ip(ip: str):
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


def long_to_ip(num: int):
    return "{}.{}.{}.{}".format((num >> 24) & 0xFF, (num >> 16) & 0xFF, (num >> 8) & 0xFF, num & 0xFF)


def mid_ip(sip, eip: int):
    return (sip + eip) >> 1
