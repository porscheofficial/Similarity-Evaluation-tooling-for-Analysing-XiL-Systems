from gui.GUI import start
from measurement.measurement import Measurement
import matplotlib.pyplot as plt
import numpy as np

import logging
from colorama import Fore, Style


class ColoredFormatter(logging.Formatter):

    LOG_COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        log_color = self.LOG_COLORS.get(record.levelno, Fore.RESET)

        record.levelname = f"{log_color}{record.levelname}{Fore.RESET}"

        return super().format(record)


if __name__ == "__main__":
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = ColoredFormatter(
        "%(levelname)s (%(name)s,%(funcName)s)- %(message)s")
    console_handler.setFormatter(formatter)

    logging.basicConfig(level=logging.INFO, handlers=[console_handler])
    start()

    print("Application Closed")
