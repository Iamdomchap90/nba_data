# NBA Stat Scraper

A simple application that runs in your local terminal to acquire some basic performance stats over various seasons of the 24/25 nba calendar.
These stats would be used to potentially highlight any undervalued teams that may be worth betting on.

# Getting Started 

Dependencies are managed with poetry so after cd-ing into the repository run:

    poetry shell
    poetry install

the environment should be ready to simply run the scraper so:

    python3 src/nba_scraper.py

run tests with following command (from inside shell):

    poetry run test

# S3 config 

There is an option to save the timestamped version to S3 which allows for a version 
control history of the scraped data. To run the mock S3 (by default) with a date, use:

    python3 src/nba_scraper.py -d YYYYmmdd

To configure a specific S3 account in production add the following config under [s3]: 

    access_key_id = "YOUR_AWS_ACCESS_KEY_ID"  # Add your AWS Access Key ID
    secret_access_key = "YOUR_AWS_SECRET_ACCESS_KEY"  # Add your AWS Secret Access Key
    region = "us-west-2"
