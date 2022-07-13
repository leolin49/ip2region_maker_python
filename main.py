import logging
import sys
import time
import xdb.maker
import xdb.index
import xdb.searcher
import xdb.util
import xdb

logging.basicConfig(level=logging.INFO, format='%(asctime)s-%(name)s-%(lineno)s-%(levelname)s - %(message)s')
log = logging.getLogger(__name__)


def print_help():
    print("ip2region xdb maker")
    print("{} [command] [command options]".format(sys.argv[0]))
    print("Command: ")
    print("  gen      generate the binary db file")
    print("  search   binary xdb search test")
    print("  bench    binary xdb bench test")


def gen_db():
    src_file, dst_file = "", ""
    index_policy = xdb.index.VectorIndexPolicy
    # check input argv
    for i in range(2, len(sys.argv)):
        r = sys.argv[i]
        if len(r) < 5:
            continue
        if not r.startswith("--"):
            continue
        s_idx = r.index("=")
        if s_idx < 0:
            print("missing = for args pair '{}'".format(r))
            return
        if r[2:s_idx] == "src":
            src_file = r[s_idx+1:]
        elif r[2:s_idx] == "dst":
            dst_file = r[s_idx+1:]
        elif r[2:s_idx] == "index":
            index_policy = xdb.index.index_policy_from_string(r[s_idx+1:])
        else:
            print("undefined option `{}`".format(r))
            return
    if src_file == "" or dst_file == "":
        print("{} gen [command options]".format(sys.argv[0]))
        print("options:")
        print(" --src string    source ip text file path")
        print(" --dst string    destination binary xdb file path")
        return
    # make the binary file
    start_time = time.time()
    maker = xdb.maker.new_maker(index_policy, src_file, dst_file)

    maker.init()
    maker.start()
    maker.end()

    logging.info("Done, elapsed: {}".format(time.time() - start_time))


def test_search():
    db_file = ""
    for i in range(2, len(sys.argv)):
        r = sys.argv[i]
        if len(r) < 5:
            continue
        if not r.startswith("--"):
            continue
        e_idx = r.index("=")
        if e_idx < 0:
            print("missing = for args pair '{}'".format(r))
            return
        if r[2:e_idx] == "db":
            db_file = r[e_idx+1:]
        else:
            print("undefined option `{}`".format(r))
            return
    if db_file == "":
        print("{} search [command options]".format(sys.argv[0]))
        print("options:")
        print(" --db string    ip2region binary xdb file path")
        return
    cb = xdb.searcher.XdbSearcher.loadContentFromFile(dbfile=db_file)
    searcher = xdb.searcher.XdbSearcher(contentBuff=cb)
    print("ip2region xdb search test program, commands:\nloadIndex : load the vector index for search "
          "speedup.\nclearIndex: clear the vector index.\nquit      : exit the test program")
    while True:
        print("ip2region>> ", end="")
        line = input()

        # command interception and execution
        if line == "loadIndex":
            searcher.loadVectorIndexFromFile(dbfile=db_file)
            print("vector index cached")
            continue
        elif line == "clearIndex":
            searcher.clearVectorIndex()
            continue
        elif line == "quit":
            break

        ip = xdb.util.check_ip(line)

        s_tm = time.time()
        region = searcher.search(ip)
        print("\x1b[0;32m[region:{}, iocount:{}, took:{}s]\x1b[0m\n".format(region, 0, time.time() - s_tm))


def main():
    if len(sys.argv) < 2:
        print_help()
        return

    cmd = sys.argv[1].lower()
    if cmd == "gen":
        gen_db()
    elif cmd == "search":
        test_search()
    elif cmd == "bench":
        # test_bench()
        pass
    else:
        print_help()


if __name__ == '__main__':
    main()
