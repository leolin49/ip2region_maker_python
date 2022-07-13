# Copyright 2022 The Ip2Region Authors. All rights reserved.
# Use of this source code is governed by a Apache2.0-style
# license that can be found in the LICENSE file.
import struct

VectorIndexPolicy = 1
BTreeIndexPolicy = 2
SegmentIndexBlockSize = 14


class VectorIndexBlock:
    first_ptr = 0
    last_ptr = 0

    def encode(self) -> bytes:
        return struct.pack("<II", self.first_ptr, self.last_ptr)

    def string(self) -> str:
        return "FirstPtr: {}, LastPrt: {}".format(self.first_ptr, self.last_ptr)


class SegmentIndexBlock:
    start_ip = 0
    end_ip = 0
    data_len = 0
    data_ptr = 0

    def __init__(self, sip, eip, dl, dp):
        self.start_ip = sip
        self.end_ip = eip
        self.data_len = dl
        self.data_ptr = dp

    def encode(self) -> bytes:
        return struct.pack("<IIHI", self.start_ip, self.end_ip, self.data_len, self.data_ptr)

    def string(self) -> str:
        return "{sip: {}, eip: {}, len: {}, ptr: {}}".format(self.start_ip, self.end_ip, self.data_len, self.data_ptr)
