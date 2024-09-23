# main.py

import sys
from gui import DuoQGUI
from logger import logger
from PyQt5.QtWidgets import QApplication
import qasync
import asyncio

def main():
    try:
        app = QApplication(sys.argv)
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        with loop:
            gui = DuoQGUI()
            gui.show()
            loop.run_forever()
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
