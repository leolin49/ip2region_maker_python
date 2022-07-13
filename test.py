f = open("ip2region.xdb", mode="rb")

# ver = f.read(2)
# idx = f.read(2)
# tm = f.read(4)
# sptr = f.read(4)
# eptr = f.read(4)
# print(ver, idx, tm, sptr, eptr)

f.seek(256, 1)
tmp = f.read(8)
tmp1 = f.read(8)
tmp2 = f.read(8)
tmp3 = f.read(8)
print(tmp, tmp1, tmp2, tmp3)

# b'0|0|0|\xe5\x86\x85\xe7\xbd\x91IP|\xe5\x86\x85\xe7\xbd\x91IP\xe6\xbe\xb3\xe5\xa4\xa7\xe5\x88\xa9\xe4\xba\x9a|0|0|'
# b'0|0|0|\xe5\x86\x85\xe7\xbd\x91IP|\xe5\x86\x85\xe7\xbd\x91IP\xe6\xbe\xb3\xe5\xa4\xa7\xe5\x88\xa9\xe4\xba\x9a|0|0|'

