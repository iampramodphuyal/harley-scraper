from utils.helpers import init_tmp_path
from core.api_scraper import api_scraper
from core.ui_scraper import ui_scraper


def main():
    init_tmp_path()
    # api_scraper()
    ui_scraper()

if __name__ == "__main__":
    main()
