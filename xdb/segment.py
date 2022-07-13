# Copyright 2022 The Ip2Region Authors. All rights reserved.
# Use of this source code is governed by a Apache2.0-style
# license that can be found in the LICENSE file.
import util


class Segment:
    start_ip = 0
    end_ip = 0
    region = ""

    def __init__(self, sip=0, eip=0, reg=""):
        self.start_ip, self.end_ip = sip, eip
        self.region = reg

    # split the segment based on the pre-two bytes
    def split(self) -> list:
        # 1, split the segment with the first byte
        t_list_1 = []
        s_byte_1, e_byte_1 = (self.start_ip >> 24) & 0xFF, (self.end_ip >> 24) & 0xFF
        n_sip = self.start_ip
        for i in range(s_byte_1, e_byte_1 + 1):
            sip = (i << 24) | (n_sip & 0xFFFFFF)
            eip = (i << 24) | 0xFFFFFF
            if eip < self.end_ip:
                n_sip = (i + 1) << 24
            else:
                eip = self.end_ip

            # append the new segment (maybe)
            t_list_1.append(Segment(sip, eip))

        # 2, split the segments with the second byte
        t_list_2 = []
        for s in t_list_1:
            base = s.start_ip & 0xFF000000
            n_sip = s.start_ip
            s_byte_2, e_byte_2 = (s.start_ip >> 16) & 0xFF, (s.end_ip >> 16) & 0xFF
            for i in range(s_byte_2, e_byte_2 + 1):
                sip = base | (i << 16) | (n_sip & 0xFFFF)
                eip = base | (i << 16) | 0xFFFF
                if eip < self.end_ip:
                    n_sip = 0
                else:
                    eip = self.end_ip

                t_list_2.append(Segment(sip, eip, self.region))

        return t_list_2

    def string(self) -> str:
        return util.long_to_ip(self.start_ip) + "|" + util.long_to_ip(self.end_ip) + "|" + self.region


def segment_from(seg: str) -> Segment:
    segment = Segment()
    ps = seg.split("|", 3)
    if len(ps) != 3:
        return segment

    sip = util.check_ip(ps[0])
    if sip == 0:
        return segment
    eip = util.check_ip(ps[1])
    if eip == 0:
        return segment

    segment.start_ip, segment.end_ip = sip, eip
    segment.region = ps[2]
    return segment
