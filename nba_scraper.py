import pandas as pd
from bs4 import BeautifulSoup
from loguru import logger
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

DOMAIN = "https://www.nba.com/stats/teams/traditional"


class NBAScraper:
    def __init__(self, url_path: str):
        super().__init__()
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
        """fetches the soup for season table if it's available."""
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
        Collects season data for each team and appends it to the data
        list.
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

    def scrape(self):
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
                # Ensure the driver is closed after scraping
                self.driver.quit()


if __name__ == "__main__":
    try:
        reg_scraper = NBAScraper("")
        pre_scraper = NBAScraper("?SeasonType=Pre+Season")
        preseason_df = pre_scraper.scrape()
        regular_season_df = reg_scraper.scrape()

        regular_season_df.to_csv("nba_regular_season_24-25.csv", index=False)
        preseason_df.to_csv("nba_pre_season_24-25.csv", index=False)
    except Exception as e:
        logger.exception(
            "Something went wrong. At least one of the scrapers "
            f"didn't return a dataframe: {e}"
        )
