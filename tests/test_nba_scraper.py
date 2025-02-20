import pytest
from unittest.mock import MagicMock, patch
from nba_scraper import NBAScraper
from selenium.common.exceptions import TimeoutException


class TestNBAScraper:
    """Test class for NBAScraper methods."""

    @pytest.fixture
    def scraper(self):
        return NBAScraper("")

    @pytest.fixture
    def mock_webdriver(self):
        with patch("nba_scraper.webdriver.Chrome") as mock:
            yield mock

    @pytest.fixture
    def scraper_with_table(self, scraper):
        mock_table = MagicMock()
        mock_rows = []

        # Create mock rows with the required structure
        for _ in range(1):
            mock_row = MagicMock()
            tds = [MagicMock() for _ in range(28)]  # Create 28 <td> elements

            # Set up specific text for required indices
            tds[1].find.return_value = MagicMock(
                text="Team A"
            )  # Team name in <span>
            tds[5].text = "0.5"  # Win %
            tds[7].text = "100"  # Avg. Points
            tds[10].text = "0.45"  # Field Goal %
            tds[21].text = "7"  # Turnovers
            tds[27].text = "190"  # Spread

            mock_row.find_all.return_value = tds
            mock_rows.append(mock_row)

        mock_table.find_all.return_value = mock_rows
        scraper.table = mock_table
        return scraper

    def test_initialize_driver(self, scraper, mock_webdriver):
        scraper.initialize_driver()
        mock_webdriver.assert_called_once()
        assert scraper.driver is not None

    def test_get_season_table(self, scraper, mock_webdriver):
        # Set up the mock driver and page source
        mock_driver = mock_webdriver.return_value
        mock_driver.page_source = (
            "<html><table class='Crom_table__p1iZz'></table></html>"
        )

        scraper.initialize_driver()
        scraper.get_season_table()

        assert scraper.soup is not None
        assert scraper.table is not None
        assert "Crom_table__p1iZz" in str(scraper.table)

    def test_collect_season_data(self, scraper_with_table):
        """Test if season data is collected correctly."""
        data = scraper_with_table.collect_season_data()

        assert len(data) == 1
        assert data[0]["Team"] == "Team A"
        assert data[0]["Win %"] == 50.0
        assert data[0]["Avg. Points"] == "100"
        assert data[0]["Field Goal %"] == 45.0
        assert data[0]["Turnovers"] == "7"
        assert data[0]["Spread"] == "190"

    def test_scrape_timeout_exception(self, scraper, mock_webdriver):
        mock_driver = mock_webdriver.return_value
        mock_driver.get.side_effect = TimeoutException("Timeout occurred")

        with pytest.raises(
            RuntimeError, match="Scraped data is not available"
        ):
            scraper.scrape()

    def test_scrape_general_exception(self, scraper, mock_webdriver):
        mock_driver = mock_webdriver.return_value
        mock_driver.get.side_effect = Exception("An error occurred")

        with pytest.raises(
            RuntimeError, match="Web driver could not load page source"
        ):
            scraper.scrape()
