# Copyright 2022 The Ip2Region Authors. All rights reserved.
# Use of this source code is governed by a Apache2.0-style
# license that can be found in the LICENSE file.
#
# ----
# ip2region database v2.0 structure
#
# +----------------+-------------------+---------------+--------------+
# | header space   | speed up index    |  data payload | block index  |
# +----------------+-------------------+---------------+--------------+
# | 256 bytes      | 512 KiB (fixed)   | dynamic size  | dynamic size |
# +----------------+-------------------+---------------+--------------+
#
# 1. padding space : for header info like block index ptr, version, release date eg ... or any other temporary needs.
# -- 2bytes: version number, different version means structure update, it fixed to 2 for now
# -- 2bytes: index algorithm code.
# -- 4bytes: generate unix timestamp (version)
# -- 4bytes: index block start ptr
# -- 4bytes: index block end ptr
#
#
# 2. data block : region or whatever data info.
# 3. segment index block : binary index block.
# 4. vector index block  : fixed index info for block index search speed up.
# space structure table:
# -- 0   -> | 1rt super block | 2nd super block | 3rd super block | ... | 255th super block
# -- 1   -> | 1rt super block | 2nd super block | 3rd super block | ... | 255th super block
# -- 2   -> | 1rt super block | 2nd super block | 3rd super block | ... | 255th super block
# -- ...
# -- 255 -> | 1rt super block | 2nd super block | 3rd super block | ... | 255th super block
#
#
# super block structure:
# +-----------------------+----------------------+
# | first index block ptr | last index block ptr |
# +-----------------------+----------------------+
#
# data entry structure:
# +--------------------+-----------------------+
# | 2bytes (for desc)	| dynamic length		|
# +--------------------+-----------------------+
#  data length   whatever in bytes
#
# index entry structure
# +------------+-----------+---------------+------------+
# | 4bytes		| 4bytes	| 2bytes		| 4 bytes    |
# +------------+-----------+---------------+------------+
#  start ip 	  end ip	  data length     data ptr
import os
import struct
import sys
sys.path.append(os.path.realpath(os.path.dirname(os.path.realpath(__file__))))
import logging
import time
import segment as seg
import index as idx
import util

ZeroCnt=0

VersionNo = 2
HeaderInfoLength = 256
VectorIndexRows = 256
VectorIndexCols = 256
VectorIndexSize = 8
VectorIndexLength = VectorIndexRows * VectorIndexCols * VectorIndexSize


class Maker:
    src_handle = None
    dst_handle = None
    index_policy = 0
    segments = []
    region_pool = {}
    vector_index = None

    def __init__(self, sh, dh, ip, sg, rp, vi):
        self.src_handle = open(sh, mode='r', encoding='utf-8')
        self.dst_handle = open(dh, mode='wb')
        self.index_policy = ip
        self.segments = sg
        self.region_pool = rp
        self.vector_index = vi

    # init the binary file
    def init(self):
        # init the db header
        self.init_db_header()

        # load all the segments
        self.load_segments()

    def init_db_header(self):
        logging.info("try to init the db header ... ")
        self.src_handle.seek(0, 0)

        header = bytearray([0]*256)
        # struct.pack_into("<HHIII", header, 0, VersionNo, self.index_policy, int(time.time()), 0, 0)
        # make and write the header space
        # 1. version number
        header[0:2] = VersionNo.to_bytes(2, byteorder="little")
        # 2. index policy code
        header[2:4] = int(self.index_policy).to_bytes(2, byteorder="little")
        # 3. generate unix timestamp
        header[4:8] = int(time.time()).to_bytes(4, byteorder="little")
        # 4. index block start ptr
        header[8:12] = int(0).to_bytes(4, byteorder="little")
        # 5. index block end ptr
        header[12:16] = int(0).to_bytes(4, byteorder="little")

        self.dst_handle.write(header)
        return

    def load_segments(self):
        logging.info("try to load the segments ... ")
        last = seg.Segment()
        s_tm = time.time()

        lines = self.src_handle.read().splitlines()
        for line in lines:
            line = str(line)
            logging.info("load segment: `{}`".format(line))
            ps = line.split("|", maxsplit=2)
            if len(ps) != 3:
                logging.error("invalid ip segment line `{}`, {}".format(line, ps))
                return
            sip = util.check_ip(ps[0])
            eip = util.check_ip(ps[1])
            if sip > eip:
                print("start ip({}) should not be greater than end ip({})".format(ps[0], ps[1]))
                return
            if len(ps[2]) < 1:
                print("empty region info in segment line `{}`".format(line))
                return
            segment = seg.Segment(
                sip=sip,
                eip=eip,
                reg=ps[2]
            )

            # check the continuity of data segment
            # todo

            self.segments.append(segment)

        print("all segments loaded, length: {}, elapsed: {}".format(len(self.segments), time.time() - s_tm))

    def set_vector_index(self, ip, ptr):
        row, col = (ip >> 24) & 0xFF, (ip >> 16) & 0xFF
        vi_block = self.vector_index[row][col]
        if vi_block.first_ptr == 0:
            vi_block.first_ptr = ptr
            vi_block.last_ptr = ptr + idx.SegmentIndexBlockSize
        else:
            vi_block.last_ptr = ptr + idx.SegmentIndexBlockSize
        self.vector_index[row][col] = vi_block

    # start to make the binary file
    def start(self):
        if len(self.segments) < 1:
            logging.error("empty segment list")
            return

        # 1. write all the region/data to the binary file
        self.dst_handle.seek(HeaderInfoLength+VectorIndexLength, 0)

        logging.info("try to write the data block ... ")
        for s in self.segments:
            logging.info("try to write region '{}'...".format(s.region))
            if s.region in self.region_pool:
                logging.info(" --[Cached] with ptr={}".format(self.region_pool[s.region]))
                continue
            region = bytes(s.region, encoding="utf-8")
            if len(region) > 0xFFFF:
                logging.error("too long region info `{}`: should be less than {} bytes".format(s.region, 0xFFFF))
                return

            # get the first ptr of the next region
            pos = self.dst_handle.seek(0, 1)
            self.dst_handle.write(region)
            self.region_pool[s.region] = pos
            logging.info(" --[Added] with ptr={}".format(pos))

        # 2. write the index block and cache the super index block
        logging.info("try to write the segment index block ... ")
        counter, start_index_ptr, end_index_ptr = 0, -1, -1
        for sg in self.segments:
            if sg.region not in self.region_pool:
                logging.error("missing ptr cache for region `{}`".format(sg.region))
                return

            data_len = len(bytes(sg.region, encoding="utf-8"))
            if data_len < 1:
                logging.error("empty region info for segment '{}'".format(sg.region))
                return

            seg_list = sg.split()
            logging.info("try to index segment({} split) {} ...".format(len(seg_list), sg.string()))
            for s in seg_list:
                pos = self.dst_handle.seek(0, 1)

                s_index = idx.SegmentIndexBlock(
                    sip=s.start_ip,
                    eip=s.end_ip,
                    dl=data_len,
                    dp=pos
                )
                self.dst_handle.write(s_index.encode())
                logging.info("|-segment index: {}, ptr: {}, segment: {}".format(counter, pos, s.string()))
                self.set_vector_index(s.start_ip, pos)
                counter += 1

                # check and record the start index ptr
                if start_index_ptr == -1:
                    start_index_ptr = pos
                end_index_ptr = pos

        # synchronized the vector index block
        logging.info("try to write the vector index block ... ")
        self.dst_handle.seek(HeaderInfoLength, 0)
        for i in range(0, len(self.vector_index)):
            for j in range(0, len(self.vector_index[i])):
                vi = self.vector_index[i][j]
                self.dst_handle.write(vi.encode())

        # synchronized the segment index info
        logging.info("try to write the segment index ptr ... ")
        buff = struct.pack("<II", start_index_ptr, end_index_ptr)
        self.dst_handle.seek(8, 0)
        self.dst_handle.write(buff)

        logging.info("write done, dataBlocks: {}, indexBlocks: ({}, {}), indexPtr: ({}, {})".format(
            len(self.region_pool), len(self.segments), counter, start_index_ptr, end_index_ptr
        ))
        return

    def end(self):
        self.src_handle.close()
        self.dst_handle.close()
        return


def new_maker(policy: int, srcfile, dstfile: str) -> Maker:
    return Maker(
        srcfile, dstfile, policy, sg=[], rp={},
        vi=[[idx.VectorIndexBlock() for _ in range(VectorIndexRows)] for _ in range(VectorIndexCols)],
    )