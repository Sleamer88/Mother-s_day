import sys
import os
import subprocess
import webview
import socket
import time

# ✅ Required for PyInstaller one-file apps
def resource_path(relative_path):
    try:
        # When bundled by PyInstaller
        base_path = sys._MEIPASS
    except AttributeError:
        # When running normally
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ✅ Needed so we know when Streamlit is ready
def wait_for_port(host, port, timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)
    return False

def main():
    global streamlit_process

    app_path = resource_path("mom_bot_app.py")
    port = 8501
    url = f"http://127.0.0.1:{port}"

    # ✅ THIS is how you start Streamlit
    streamlit_process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            app_path,
            "--server.port=8501",
            "--server.headless=true",
            "--browser.serverAddress=127.0.0.1",
        ],
        env={**os.environ, "MOM_BOT_CHILD": "1"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    if not wait_for_port("127.0.0.1", port):
        raise RuntimeError("Mom-Bot failed to wake up!")

    window = webview.create_window(
        title="Happy Mother's Day! ❤️",
        url=url,
        width=1000,
        height=750,
        resizable=True,
    )

    def on_close():
        if streamlit_process and streamlit_process.poll() is None:
            streamlit_process.terminate()

    window.events.closed += on_close
    webview.start(gui="edgechromium", debug=False)

if __name__ == "__main__":
    main()