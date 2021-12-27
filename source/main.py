import os
import sys
import time
import signal
import logging
import datetime
import traceback
import coloredlogs
import matplotlib.pyplot as plt

from rich import print
from rich.console import Console
from rich.logging import RichHandler
from tkinter import Tk
from typing import List
from argparse import ArgumentParser

from building import Building


def signal_handler(sig, frame):
    logging.critical("程式被 ctrl+c 強制結束！")
    os._exit(1)


def signal_handler_stop(sig, frame):
    logging.critical("程式被 ctrl+z 強制結束！")
    os.system("kill -9 {}".format(os.getpid()))  # suicide


def main():

    signal.signal(signal.SIGINT, signal_handler)
    if sys.platform != "win32":
        signal.signal(signal.SIGTSTP, signal_handler_stop)

    start_time = time.perf_counter()

    plt.switch_backend('Agg')

    parser = ArgumentParser()
    parser.add_argument("-e", "--extended_gbxml_path", type=str, default="LG10_Extended_gbXML_20210913.xml",
                        help="Extended gbXML 的檔名（放在 xml/ 資料夾下）")
    parser.add_argument("-d", "--density", type=float, default=(0.2 ** 0.5),
                        help="格子點的間距（公尺）")
    parser.add_argument("-g", "--gui", action="store_true", default=False)
    parser.add_argument("-l", "--log", type=str, default=".log",
                        help="日誌（log）的資料夾位置")
    parser.add_argument("-c", "--cache", type=str, default=".cache",
                        help="快取（cache）的資料夾位置")
    parser.add_argument("-od", "--output_dir", type=str,
                        default=".outputs", help="輸出（output）的資料夾位置")
    parser.add_argument("-dc", "--disable_cache", action="store_true", default=False,
                        help="whether to disable cache function")
    parser.add_argument("-v", "--verbose", type=bool,
                        default=True, help="輸出日誌層級")
    args = parser.parse_args()
    print(args)

    logger = logging.getLogger("rich")

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s %(name)s[%(process)d] %(levelname)s %(processName)s(%(threadName)s) %(module)s:%(lineno)d  %(message)s",
        datefmt='%Y%m%d %H:%M:%S')

    ch = logging.StreamHandler()
    if args.verbose:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)

    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")

    os.makedirs(args.log, exist_ok=True)
    os.makedirs(args.cache, exist_ok=True)
    os.makedirs(args.output_dir, exist_ok=True)
    log_filename = os.path.join(
        args.log, datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S.log"))
    fh = logging.FileHandler(log_filename, "w", encoding="utf-8")
    if args.verbose:
        fh.setLevel(logging.DEBUG)
    else:
        fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)

    # logger.addHandler(ch)
    logger.addHandler(RichHandler())
    logger.addHandler(fh)

    logging.getLogger('matplotlib').setLevel(logging.WARNING)

    coloredlogs.install(
        fmt="%(asctime)s %(hostname)s %(name)s[%(process)d] %(levelname)s %(processName)s(%(threadName)s) %(module)s:%(lineno)d  %(message)s", level="DEBUG")

    logging.info("程式開始：")

    extended_gbxml_path = os.path.join("xml", args.extended_gbxml_path)
    # extended_gbxml_path = "D:/Prj/Python/sinotech-escape/source/xml/LG10_Extended_gbXML_20210913.xml"

    root = Tk()
    root.withdraw()

    def check_files_exists(paths: List[str]):
        for path in paths:
            if not os.path.exists(path):
                logging.critical("沒有 \"{}\" 這個檔案".format(path))

    check_files_exists([extended_gbxml_path, ])

    LG10 = Building(
        density=args.density,
        use_cache=(not args.disable_cache),
        cache_dir=args.cache,
        output_dir=args.output_dir
    )
    LG10.load_infos(
        contours_path=extended_gbxml_path
    )

    LG10.to_grid_graph()
    if args.gui:
        LG10.edit_graph_gui()
    LG10.connect_floors()
    LG10.instances_analysis()
    LG10.calculate_reverse_table()
    LG10.dump_sol_table()

    while True:
        LG10.real_time_escape()
    exit()

    while True:
        mode = input("給定一點提供到所有終點的最短逃生路徑請輸入1，離開程式請輸入q: ")
        plot_mode = input("有點有線請輸入1，沒點沒線請輸入2，有點沒線請輸入3: ")
        if mode == "1":
            instance_str = input("Please key in instance string: ")
            start_point = input("Please input a start point: ")
            try:
                LG10.plot_sol(plot_mode, start_point, instance_str)
            except ValueError as err:
                logging.error(err)

        elif mode == "q":
            break
        else:
            logging.warning("invalid input")

    end_time = time.perf_counter()
    logging.info("執行結束！共花費 {} 秒。".format(end_time - start_time))


if __name__ == "__main__":
    console = Console()
    try:
        main()
    except Exception as e:
        print(repr(e))
        error = traceback.format_exc()
        print(error)
        # console.print_exception(show_locals=True)
