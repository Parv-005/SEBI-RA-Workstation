import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from utils.startup_checks import check_constants_file
from database.db_manager import init_db
from gui.main import run_app

if __name__ == "__main__":
    check_constants_file()
    init_db()
    run_app()
