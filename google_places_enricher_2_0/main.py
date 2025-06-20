
from multiprocessing import freeze_support, Process
from logging.handlers import RotatingFileHandler
from threading import Thread
from google_places_enricher_2_0.app import app

import logging
import signal
import os
import sys
import socket
import requests
import webview
# import shutil

# # Ensure resource folders exist next to the executable
# def ensure_resource_folder(folder):
#     exe_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
#     target = os.path.join(exe_dir, folder)
#     internal = os.path.join(exe_dir, '_internal', 'google_places_enricher_2_0', folder)
#     if not os.path.exists(target) and os.path.exists(internal):
#         shutil.copytree(internal, target)

if getattr(sys, 'frozen', False):
    exe_dir = os.path.dirname(sys.executable)
    internal_dir = os.path.join(exe_dir, '_internal', 'google_places_enricher_2_0')
    if os.path.exists(internal_dir):
        os.chdir(internal_dir)
    #for folder in ['templates', 'static', 'uploads']:
    #   ensure_resource_folder(folder)

APP_NAME="Google Places Enricher 2.0"

logger = logging.getLogger(__name__)

stdout = sys.stdout
def write_log(buf):
    stdout.write(buf)
    for line in buf.rstrip().splitlines():
          logger.info(line.rstrip())

logger.write = write_log
logger.flush = lambda: None
logger.setLevel("INFO")

sys.stdout = logger
sys.stderr = logger

if not os.path.exists('logs'):
    os.makedirs('logs')

handler = RotatingFileHandler('logs/google_places_enricher.log', maxBytes=5 * 1024 * 1024, backupCount=10)
logger.addHandler(handler)

def exception_handler(type, value, tb):
    logger.exception("Uncaught exception: {0}".format(str(value)))

sys.excepthook = exception_handler

def get_open_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    # s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port

def pywebview_process(port=5000):
    webview.create_window(APP_NAME, f'http://localhost:{port}')
    webview.start()

def pywebview_thread(port=5000):
    process = Process(target=pywebview_process, args=(port,))
    process.daemon = True
    process.start()
    process.join()
    os.kill(os.getpid(), signal.CTRL_C_EVENT)
    while True:
        logger.info("Shutting down...")
        try:
            requests.get(f"http://localhost:{port}/", timeout=1)
        except requests.exceptions.ConnectionError:
            break

def flask_app(port=5000):
    app.run(port=port)

def main():
    port = get_open_port()

    webview_thread = Thread(target=pywebview_thread, args=(port,))
    webview_thread.daemon = True
    webview_thread.start()
    flask_app(port=port)

if __name__ == "__main__":
    freeze_support()
    main()
