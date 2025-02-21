import boto3
import pandas as pd
import argparse
import datetime as dt
from utils import get_scaper_config, write_data_to_s3
from bs4 import BeautifulSoup
from loguru import logger
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from moto import mock_aws


class NBAScraper:
    def __init__(self, DOMAIN: str, url_path: str):
        self.url = DOMAIN + url_path
        self.driver = None
        self.soup = ""
        self.table = None
        self.data = []

    def initialize_driver(self):
        """Initializes the WebDriver and navigates to the URL."""
        self.driver = webdriver.Chrome()
        self.driver.get(self.url)

    def get_season_table(self):
        """Fetches the soup for season table if it's available."""
        wait = WebDriverWait(self.driver, 10)
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//th[@field='TEAM_NAME']")
            )
        )
        self.soup = BeautifulSoup(self.driver.page_source, "html.parser")
        self.table = self.soup.find("table", class_="Crom_table__p1iZz")

    def collect_season_data(self):
        """
        Collects season data for each team and appends it to the data list.
        """
        rows = self.table.find_all("tr", class_=False)
        for row in rows:
            tds = row.find_all("td")
            self.data.append(
                {
                    "Team": tds[1].find("span").text,
                    "Win %": round(float(tds[5].text) * 100, 1),
                    "Avg. Points": tds[7].text,
                    "Field Goal %": round(float(tds[10].text) * 100, 1),
                    "Turnovers": tds[21].text,
                    "Spread": tds[27].text,
                }
            )
        return self.data

    def scrape(self) -> pd.DataFrame:
        """Orchestrates the scraping process."""
        try:
            self.initialize_driver()
            self.get_season_table()
            self.collect_season_data()
            return pd.DataFrame(self.data)
        except TimeoutException as e:
            raise RuntimeError(
                "Scraped data is not available. The page structure might "
                f"have changed:\n{e}"
            ) from e
        except Exception as e:
            raise RuntimeError(
                "Web driver could not load page source due to the "
                f"following error:\n{e}"
            ) from e
        finally:
            if self.driver:
                self.driver.quit()


def main(args):
    try:
        config = get_scaper_config(args.config)
        DOMAIN = config["scraper"]["DOMAIN"]
        S3_BUCKET = config["s3"]["bucket"]
        endpoints = config["scraper"]["endpoints"]
        use_moto = config["s3"].get("use_moto", False)

        if use_moto:
            logger.info("Using Moto to mock S3.")
            with mock_aws():
                s3_client = boto3.client("s3", region_name="us-east-1")
                s3_client.create_bucket(Bucket=S3_BUCKET)

                for endpoint in endpoints:
                    url_path = endpoint["url_path"]
                    s3_key = endpoint["s3_key"].format(date=args.date)
                    logger.info(
                        f"Scraping endpoint: {endpoint.get('name', url_path)}"
                    )
                    scraper = NBAScraper(DOMAIN, url_path)
                    df = scraper.scrape()
                    write_data_to_s3(df, S3_BUCKET, s3_key)
        else:
            s3_client = boto3.client("s3", region_name="us-east-1")
            for endpoint in endpoints:
                url_path = endpoint["url_path"]
                s3_key = endpoint["s3_key"].format(date=args.date)
                logger.info(
                    f"Scraping endpoint: {endpoint.get('name', url_path)}"
                )
                scraper = NBAScraper(DOMAIN, url_path)
                df = scraper.scrape()
                write_data_to_s3(df, S3_BUCKET, s3_key)

    except Exception as e:
        logger.exception(
            "Something went wrong. At least one of the scrapers "
            f"didn't return a dataframe: {e}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NBA Scraper")

    parser.add_argument(
        "-d",
        "--date",
        type=lambda d: dt.datetime.strptime(d, "%Y%m%d").date(),
        help="Date",
    )
    parser.add_argument(
        "--config", required=False, default="config_uat", help="Config to use"
    )

    args = parser.parse_args()
    main(args)
