# main.py

import asyncio
from gui import run_app
from logger import logger

def main():
    try:
        run_app()
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
