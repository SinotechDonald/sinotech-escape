import os
import sys
import time
import logging
import gettext
import datetime
import traceback
import matplotlib.pyplot as plt

from tkinter import messagebox

from gui.tk import TkApp
from util.app_utils import send_bug_report, verify_updates


# lang = gettext.translation('base', localedir='locales', languages=["{}".format(locale.getdefaultlocale()[0])])
# lang.install()
# _ = lang.gettext


def main():

    start_time = time.perf_counter()

    plt.switch_backend('Agg')

    logger = logging.getLogger()

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s %(name)s[%(process)d] %(levelname)s %(processName)s(%(threadName)s) %(module)s:%(lineno)d  %(message)s",
        datefmt='%Y%m%d %H:%M:%S')

    if sys.platform == "win32":
        storage_path = os.path.join(os.environ["HOMEPATH"], ".sinopath")
    else:
        storage_path = os.path.join(os.path.expanduser('~'), ".sinopath")
    os.makedirs(storage_path, exist_ok=True)

    log_dir = os.path.join(storage_path, ".log")
    cache_dir = os.path.join(storage_path, ".cache")
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)

    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)

    log_filename = os.path.join(
        log_dir, datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S.log"))
    fh = logging.FileHandler(log_filename, "w", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)

    logging.getLogger('matplotlib').setLevel(logging.WARNING)

    # verify_updates(storage_path)

    logging.info("程式開始：")

    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    tk_app = TkApp(base_path, log_dir, cache_dir)

    messagebox.showinfo("執行結束", "Click to close")

    end_time = time.perf_counter()
    spendTime = time.strftime("%H:%M:%S", time.gmtime(end_time - start_time))
    logging.info("執行結束！共花費 " + spendTime + " 秒。")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        subject = repr(e).split("(")[0]
        error = traceback.format_exc()
        if messagebox.askquestion("Crash", "Something went wrong, send a crash report?") == "yes":
            send_bug_report(subject, error)
            messagebox.showinfo("OK", "Crash report has been sent.")
        print(error)
