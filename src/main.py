from multiprocessing import freeze_support, Process
from threading import Thread
from app import app
import webview
import signal
import os

def pywebview_process(port=5000):
    window = webview.create_window('Hello world', f'http://localhost:{port}')
    webview.start(gui="qt")

def pywebview_thread():
    process = Process(target=pywebview_process)
    process.daemon = True
    process.start()
    process.join()
    
    # Send SIGINT (CTRL+C) to the main thread when webview closes
    os.kill(os.getpid(), signal.SIGINT) #TODO: Test if working correctly in windows
    print("Killing SIGINT.")

def flask_app():
    app.run()

def main():
    webview_thread = Thread(target=pywebview_thread) #TODO: Find available port for flask and pass to webview
    webview_thread.daemon = True
    webview_thread.start()

    flask_app()

freeze_support()

if __name__ == "__main__":
    main()