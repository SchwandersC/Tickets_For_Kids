# inside your Docker image (e.g. entrypoint)
import sys
from mlb_scraper import main as mlb_extract
from nba_scraper import main as nba_extract
from wnba_scraper import main as wnba_extract
from nhl_scraper import main as nhl_extract

if __name__ == "__main__":
    league = sys.argv[1]
    if league == "nba":
        nba_extract()
    elif league == "wnba":
        wnba_extract()
    elif league == "nhl":
        nhl_extract()
    elif league == "mlb":
        mlb_extract()
