import os
import sys
import ssl
import time
import copy
import json
import shutil
import logging
import tempfile
import subprocess
from urllib import request, parse
from tkinter import messagebox

if sys.platform == "win32":
    from win32com.client import Dispatch
else:
    pass

import smtplib
from email.mime import multipart, text, application


def send_bug_report(subject, error, sender="b06902017@csie.ntu.edu.tw", receiver="hendry0718@gmail.com") -> bool:

    # Create a text/plain message
    msg = multipart.MIMEMultipart()
    msg['Subject'] = "(SinoPath) [bug] {}".format(subject)
    msg['From'] = sender
    msg['To'] = receiver

    body = text.MIMEText(error)
    msg.attach(body)

    if sys.platform == "win32":
        storage_path = os.path.join(os.environ["HOMEPATH"], ".sinopath")
    else:
        storage_path = os.path.join(os.path.expanduser('~'), ".sinopath")

    log_dir = os.path.join(storage_path, ".log")

    force_extend_type = ".txt"
    if os.path.exists(log_dir) and len([x for x in os.listdir(log_dir) if ".log" in x]):
        filename = os.path.join(log_dir, sorted(
            [x for x in os.listdir(log_dir) if ".log" in x])[-1])
        with open(filename, 'rb') as f:
            att = application.MIMEApplication(
                f.read(), _subtype=force_extend_type)
        att.add_header('Content-Disposition', 'attachment',
                       filename=os.path.basename(filename) + force_extend_type)
        msg.attach(att)

    s = smtplib.SMTP('smtp.gmail.com:587')
    s.starttls()
    s.login(sender, 'vybotemhglrzfinv')
    s.sendmail(sender, [receiver], msg.as_string())
    s.quit()


def verify_updates(storage_path, base_url="https://hc07180011.synology.me/"):
    ssl_backup = copy.deepcopy(ssl._create_default_https_context)
    ssl._create_default_https_context = ssl._create_unverified_context
    with tempfile.TemporaryDirectory() as tmp_dir:
        log_path = os.path.join(tmp_dir, "CHANGELOG.json")
        try:
            src = parse.urljoin(base_url, "changelogs/sinopath/CHANGELOG.json")
            logging.info("Fetching {} to {}".format(src, log_path))
            request.urlretrieve(src, log_path)
        except:
            logging.warning("changelog file not available")
            return
        log_info = json.load(open(log_path, "r"))
        latest_version = log_info["version"]
        details = log_info["details"]
        logging.info("Latest version: {}, details: {}".format(
            latest_version, details))
        if sys.platform == "win32":
            try:
                parser = Dispatch("Scripting.FileSystemObject")
                current_version = parser.GetFileVersion(
                    r"C:\Program Files (x86)\SinoPath\app.exe")
            except Exception as e:
                logging.info("win32com dispatch error: {}".format(repr(e)))
                current_version = "0.0.0.0"
        else:
            logging.info("Using Mac, pass version checking")
            ssl._create_default_https_context = ssl_backup
            return
        if [int(x) for x in latest_version.split(".")] > [int(x) for x in current_version.split(".")]:
            if messagebox.askquestion("Update SinoPath?", "You've got version {} of SinoPath for Windows. Would you like to update to the latest version {}?".format(current_version, latest_version)) == "yes":
                logging.info("updating to {}".format(latest_version))
                try:
                    shutil.rmtree(os.path.join(storage_path, ".cache"))
                except FileNotFoundError:
                    logging.debug("Path not exists")
                setup_path = os.path.join(
                    storage_path, "SinoPath-setup-{}.exe".format(latest_version))
                request.urlretrieve(parse.urljoin(
                    base_url, "registry/sinopath/SinoPath-setup-{}.exe".format(latest_version)), setup_path)
                subprocess.Popen([setup_path, "/SILENT"])
                time.sleep(3)
                sys.exit(0)
    ssl._create_default_https_context = ssl_backup
