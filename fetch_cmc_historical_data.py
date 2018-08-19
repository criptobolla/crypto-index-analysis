#!/usr/bin/python

"""
fetch_cmc_historical_data.py
    Recupera i dati storici da CoinMarketCap e li salva in file CSV.
    Il formato di ogni riga è:
    data;rank;nome;simbolo;market cap;prezzo in usd;prezzo in btc;circolante;volumi 24h;% 1h; %24h; %7d
"""

# TODO Possibilità di generare JSON

import sys
import re
import argparse
import datetime
import pathlib

import requests
from bs4 import BeautifulSoup

from commons import daterange, make_dir_if_not_exists, FIRST_DATE

def parse_options(args):
    """
    Estrae e analizza la configurazione passata come argomento da riga di comando.
    [Extract parameters from command line.]
    """

    # String validation
    pattern = re.compile('[2][0][1][0-9]-[0-1][0-9]-[0-3][0-9]')

    # Data di inizio
    if args.start_date:
        start_date = args.start_date
        start_date_split = start_date.split('-')
        start_year = int(start_date_split[0])
        if not re.match(pattern, start_date):
            raise ValueError('Invalid format for the start_date: '
                + start_date + ". Should be of the form: yyyy-mm-dd.")
        start_date = datetime.date(start_year,int(start_date_split[1]),int(start_date_split[2]))
    else:
        start_date = FIRST_DATE

    # Data finale     
    if args.end_date:
        end_date = args.end_date
        end_date_split = end_date.split('-')
        end_year  = int(end_date_split[0])
        if not re.match(pattern, end_date):
            raise ValueError('Invalid format for the end_date: '
                + end_date + ". Should be of the form: yyyy-mm-dd.")
        end_date = datetime.date(end_year, int(end_date_split[1]), int(end_date_split[2]))
    else:
        end_date = datetime.date.today()

    if args.data_dir:
        data_dir = pathlib.Path(args.data_dir)
    else:
        data_dir = pathlib.Path("data")

    return start_date, end_date, data_dir


def download_html(date):
    """
    Download HTML MarketCap snapshots from CoinMarketCap.
    """

    datestring = date.strftime("%Y%m%d")
    url = "https://coinmarketcap.com/historical/" + datestring + "/"

    try:
        print("Opening url: %s" % url)
        page = requests.get(url,timeout=10)
        if page.status_code != 200:
            raise Exception("Failed to load page") 
        html = page.text
        #page.close()

    except Exception as e:
        print("Error fetching historical snapshot data from " + url)
        print(e)        
        html = None
    return html


def extract_data(html, date):
    """
    Extract the price history from the HTML.
    The CoinMarketCap historical data page has just one HTML table.
    This table contains the data we want.
    It's got one header row with the column names.
    """

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", attrs={"class":"summary-table"})

    # The first tr contains the field names.
    headings = ["date", "rank", "name", "symbol", "marketcapusd","priceusd",
        "pricebtc","circulatingsupply","volume24h","perf1h","perf24h","perf7d"]

    rows = []
    for row in table.find_all("tr")[1:]:
        dataset = {}
        dataset["date"] = date.strftime("%Y-%m-%d")
        dataset["rank"] = row.find("td").get_text().replace("\n", "").strip()
        dataset["name"] = row.find("a", attrs = {"class": "currency-name-container"}).get_text().strip()
        dataset["symbol"] = row.find("td", attrs = {"class": "col-symbol"}).get_text().strip()
        dataset["marketcapusd"] = row.find("td", attrs = {"class": "market-cap"})['data-usd']
        if dataset["marketcapusd"].strip() == "?":
            dataset["marketcapusd"] = "0.0"
        dataset["priceusd"] = row.find("a", attrs = {"class": "price"})['data-usd']
        dataset["pricebtc"] = row.find("a", attrs = {"class": "price"})['data-btc']
        dataset["circulatingsupply"] = row.find("td", attrs = {"class": "circulating-supply"})['data-sort']
        dataset["volume24h"] = row.find("a", attrs = {"class": "volume"})['data-usd']
        try:
            dataset["perf1h"] = row.find("td",
                attrs = {"class": "percent-change", "data-timespan": "1h"})['data-sort']
        except:
            dataset["perf1h"] = ""
        try:
            dataset["perf24h"] = row.find("td",
                attrs = {"class": "percent-change", "data-timespan": "24h"})['data-sort']
        except:
            dataset["perf24h"] = ""
        try:
            dataset["perf7d"] = row.find("td",
                attrs = {"class": "percent-change", "data-timespan": "7d"})['data-sort']
        except:
            dataset["perf7d"] = ""
        
        rows.append(dataset)

    return headings, rows


def generate_csv_file(outfile, headings, rows):
    """
    Render the data in CSV format.
    """
    outfile.write(";".join(headings))
    outfile.write("\n")

    for row in rows:
        for heading in headings[:-1]:
            outfile.write(row[heading] + ";")
        outfile.write(row[headings[-1]])
        outfile.write("\n")


def generate_json_file(outfile, headings, rows):
    """
    Render the data in Json format.
    """
    print("")


def main(args=None):
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--data_dir", help="Specify data directory. If not specified ./data/ is used.")
    parser.add_argument("-s", "--start_date", help="Start date from which you wish to retrieve the historical data. For example, "
                                                "'2017-10-01'.", type=str)
    parser.add_argument("-e", "--end_date", help="End date for the historical data retrieval. If not defined, retrieve all the "
                                                "data until today. Same format as in start_date "
                                                "'yyyy-mm-dd'.", type=str)
    parser.add_argument("--json", help="If present, produces json files instead of a csv", action="store_true")

    # assert that args is a list
    if(args is not None):
        args = parser.parse_args(args)
    else:
        args = parser.parse_args()
    
    start_date, end_date, data_dir = parse_options(args)
    make_dir_if_not_exists(data_dir)

    for date in daterange(start_date, end_date):
        print("Fetching date: %s" % date)
        html = download_html(date)
        if html:
            headings, rows = extract_data(html, date)
            basefilename = date.strftime("%Y-%m-%d")
            if args.json:
                with pathlib.Path(data_dir, basefilename + ".json").open('w') as outfile:
                    generate_json_file(outfile, headings, rows)
            else:
                with pathlib.Path(data_dir, basefilename + ".csv").open('w') as outfile:
                    generate_csv_file(outfile, headings, rows)

if __name__ == "__main__":
    main()