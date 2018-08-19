#!/usr/bin/python

"""
backtest_strategy.py
    Effettua il backtest di una strategia di investimento.
"""
import argparse
import datetime
import pathlib
import re

import pandas as pd
import numpy as np

from commons import annualized_sharpe, daterange, FIRST_DATE, PERC_FACTOR, Config

# Configurazione (global)
config = Config()

def log(level, text):
    """
    Logga una stringa su standard output (se il livello è congruo).
    """
    if level <= config.verbosity:
        print (text)

class StrategyConfiguration:
    """
    Definizione della configurazione di una strategia.
    [Strategy configuration parameters.]
    """

    def __init__(self, crypto_number, weight_cap_perc, rebalance_period_weeks, transaction_fee):
        # Numero massimo di valute nel paniere
        self.crypto_number = crypto_number
        # Massimo peso attribuibile ad una singola valuta
        self.weight_cap_perc = weight_cap_perc
        self.rebalance_period_weeks = rebalance_period_weeks
        self.transaction_fee = transaction_fee


    def add_weights_column(self, data):
        """
        Calcola il peso di ciascuna coin.
        """
        total_market_cap = data.loc[:self.crypto_number,['marketcapusd']].astype(float).sum()[0]
        log(4, "Total market cap: %d" % total_market_cap)
        reweight_factor = 1
        weights_sum = 0
        weight_cap = self.weight_cap_perc / 100.0
        data['weight'] = 0.0
        # Il calcolo dei pesi con il cap deve essere effettuato in modo
        # iterativo.
        while weights_sum < 0.999999:
            data.loc[:self.crypto_number, 'weight'] = data['marketcapusd'].astype(float) / total_market_cap * reweight_factor
            data.loc[data.weight > weight_cap, 'weight'] = weight_cap
            weights_sum = data.weight.sum()
            log(4, "weights_sum: %.5f, reweight_factor: %.2f" % (weights_sum, reweight_factor))
            reweight_factor = reweight_factor * (1 / weights_sum)
            log(4, "new reweight_factor: %.2f" % reweight_factor)
        
    def __str__(self):
        """
        Restituisce una descrizione testuale della strategia.
        """
        return "Max num. cripto: %d, Weight cap: %d, Rebalance each %d weeks" % \
                 (self.crypto_number, self.weight_cap_perc, self.rebalance_period_weeks)

class StrategyTestResult:
    """
    Risultati del test di una strategia.
    [Strategy test results.]
    """

    def __init__(self, strategy_configuration):
        self.date = []
        self.amount_usd = []
        self.amount_btc = []
        self.transactions = []
        self.transactions_amount_usd = []
        self.transactions_amount_btc = []
        self.transaction_fees_btc = []
        self.transaction_fees_usd = []
        self.strategy = strategy_configuration

    def add_valueset(self, snapshot):
        """
        Aggiunge ai risultati un set di valori di riepilogo calcolato su un dato snapshot.
        """
        self.date.append(snapshot.date)
        self.amount_usd.append(snapshot.get_amount_usd())
        self.amount_btc.append(snapshot.get_amount_btc())
        self.transactions.append(snapshot.get_transactions_number())
        self.transactions_amount_usd.append(snapshot.get_transactions_amount_usd())
        self.transactions_amount_btc.append(snapshot.get_transactions_amount_btc())
        self.transaction_fees_usd.append(snapshot.get_transaction_fees_usd())
        self.transaction_fees_btc.append(snapshot.get_transaction_fees_btc())

    def end_of_computation(self):
        """
        Notifica la fine dell'analisi. Completa con il calcolo dei valori aggregati.
        """
        self.snapshots = pd.DataFrame(
            {
                'date': self.date,
                'amount_usd': self.amount_usd,
                'amount_btc': self.amount_btc,
                'transactions': self.transactions,
                'transactions_amount_usd': self.transactions_amount_usd,
                'transactions_amount_btc': self.transactions_amount_btc,
                'transaction_fees_usd': self.transaction_fees_usd,
                'transaction_fees_btc': self.transaction_fees_btc
            }
        )
        self.snapshots['profit_usd'] = self.snapshots.amount_usd - config.initial_amount_usd
        self.snapshots['profit_btc'] = self.snapshots.amount_btc - self.snapshots.amount_btc[0]
        self.snapshots['roi_usd'] = self.snapshots.profit_usd / config.initial_amount_usd * PERC_FACTOR
        self.snapshots['roi_btc'] = self.snapshots.profit_btc / self.snapshots.amount_btc[0] * PERC_FACTOR
        self.snapshots['tot_transactions_number'] = self.snapshots.transactions.cumsum()
        self.snapshots['tot_transactions_amount_usd'] = self.snapshots.transactions_amount_usd.cumsum()
        self.snapshots['tot_transactions_amount_btc'] = self.snapshots.transactions_amount_btc.cumsum()
        self.snapshots['tot_transaction_fees_usd'] = self.snapshots.transaction_fees_usd.cumsum()
        self.snapshots['tot_transaction_fees_btc'] = self.snapshots.transaction_fees_btc.cumsum()
        self.snapshots['expanding_max'] = self.snapshots.amount_usd.expanding().max()
        self.snapshots['drawdown'] = self.snapshots.amount_usd - self.snapshots.expanding_max
        self.snapshots['drawdown_perc'] = self.snapshots.drawdown / self.snapshots.expanding_max * PERC_FACTOR
        self.snapshots['max_drawdown'] = self.snapshots.drawdown.expanding().min()
        self.snapshots['max_drawdown_perc'] = self.snapshots.drawdown_perc.expanding().min()
        self.snapshots['amount_usd_weekly_returns'] = self.snapshots.amount_usd.pct_change()
        self.snapshots['amount_btc_weekly_returns'] = self.snapshots.amount_btc.pct_change()
        self.snapshots['amount_usd_sharpe_ratio'] = annualized_sharpe(self.snapshots.amount_usd_weekly_returns)
        self.snapshots['amount_btc_sharpe_ratio'] = annualized_sharpe(self.snapshots.amount_btc_weekly_returns)
        log(1, self.snapshots)


    def export_to_excel(self, excel_file_name):
        """
        Esporta i risultati su un foglio Excel.
        """
        writer = pd.ExcelWriter(excel_file_name)
        self.snapshots.to_excel(writer,'Snapshots')
        writer.save()
        log(2, "Results saved to excel file '%s'" % excel_file_name)

    def export_equity_line_usd_to_json(self, json_file_path):
        """
        Esporta la equity line in usd su file json.
        """
        self.snapshots.loc[:,"amount_usd"].to_json(path_or_buf=json_file_path, orient='values')
        log(2, "Equity line USD saved to json file '%s'" % json_file_path)

    def export_equity_line_btc_to_json(self, json_file_path):
        """
        Esporta la equity line in BTC su file json.
        """
        self.snapshots.loc[:,"amount_btc"].to_json(path_or_buf=json_file_path, orient='values')
        log(2, "Equity line BTC saved to json file '%s'" % json_file_path)

    def get_summary(self):
        """
        Restituisce i principali dati di riepilogo del test.
        """
        result = {}
        result['crypto_number'] = self.strategy.crypto_number
        result['weight_cap_perc'] = self.strategy.weight_cap_perc
        result['rebalance_period_weeks'] = self.strategy.rebalance_period_weeks
        result['initial_amount_usd'] = config.initial_amount_usd
        result['start_date'] = self.snapshots.iloc[0]['date']
        result['end_date'] = self.snapshots.iloc[-1]['date']
        result['profit_usd'] = self.snapshots.iloc[-1]['profit_usd']
        result['profit_btc'] = self.snapshots.iloc[-1]['profit_btc']
        result['roi_usd'] = self.snapshots.iloc[-1]['roi_usd']
        result['roi_btc'] = self.snapshots.iloc[-1]['roi_btc']
        result['tot_transactions_number'] = self.snapshots.iloc[-1]['tot_transactions_number']
        result['tot_transactions_amount_usd'] = self.snapshots.iloc[-1]['tot_transactions_amount_usd']
        result['tot_transactions_amount_btc'] = self.snapshots.iloc[-1]['tot_transactions_amount_btc']
        result['tot_transaction_fees_usd'] = self.snapshots.iloc[-1]['tot_transaction_fees_usd']
        result['tot_transaction_fees_btc'] = self.snapshots.iloc[-1]['tot_transaction_fees_btc']
        result['max_drawdown'] = self.snapshots.iloc[-1]['max_drawdown']
        result['max_drawdown_perc'] = self.snapshots.iloc[-1]['max_drawdown_perc']
        result['amount_usd_sharpe_ratio'] = self.snapshots.iloc[-1]['amount_usd_sharpe_ratio']
        result['amount_btc_sharpe_ratio'] = self.snapshots.iloc[-1]['amount_btc_sharpe_ratio']
        return result

class StrategyTestSnapshot:
    """
    Risultato parziale del test di una strategia.
    """

    def __init__(self, date):
        self.date = date

    def get_amount_usd(self):
        """
        Restituisce l'importo totale attualmente investito (equity) in USD.
        """
        return self.data.allocation_usd.sum()

    def get_amount_btc(self):
        """
        Restituisce l'importo totale attualmente investito (equity) in bitcoin.
        """
        return self.data.allocation_btc.sum()

    def get_transactions_amount_usd(self):
        """
        Restituisce l'importo totale in USD delle transazioni effettuate a seguito del
        ribilanciamento in questo snapshot.
        """
        return self.transactions.amount_usd.sum()

    def get_transactions_amount_btc(self):
        """
        Restituisce l'importo totale in bitcoin delle transazioni effettuate a seguito del
        ribilanciamento in questo snapshot.
        """
        return self.transactions.amount_btc.sum()

    def get_transactions_number(self):
        """
        Restituisce il numero totale di transazioni effettuate a seguito del ribilanciamento
        in questo snapshot.
        """
        return len(self.transactions)

        
    def get_transaction_fees_btc(self):
        """
        Restituisce l'importo totale in BTC delle commissioni per le transazioni effettuate a seguito del ribilanciamento
        in questo snapshot.
        """
        return self.transaction_fees_btc

    def get_transaction_fees_usd(self):
        """
        Restituisce l'importo totale in USD delle commissioni per le transazioni effettuate a seguito del ribilanciamento
        in questo snapshot.
        """
        return self.transaction_fees_usd

    def print_status(self):
        log(2, "\nAsset allocation:\n-----")
        log(2, self.data.loc[self.data.req_allocation_size > 0])
        log(2, "\nTransactions:\n-----")
        log(2, self.transactions)
        log(2, "\nAmount USD:\n-----")
        log(2, self.get_amount_usd())
        log(2, "\nAmount BTC:\n-----")
        log(2, self.get_amount_btc())
        log(2, "\nTransaction fees BTC:\n----")
        log(2, self.get_transaction_fees_btc())
        log(2, "\nTransaction fees USD:\n----")
        log(2, self.get_transaction_fees_usd())
        log(4, "\nData size:\n-----")
        log(4, self.data.shape)
        log(4, "\nSnapshot data memory usage:\n-----")
        log(4, self.data.memory_usage())

    
def test_strategy(strategy):
    """
    Esegue il test della strategia specificata.
    [Performs the test on the specified strategy.]
    """
    result = StrategyTestResult(strategy)
    
    # Creo uno snapshot iniziale fittizio
    prev_snapshot = None
    current_week_idx = 0

    for date in daterange(config.start_date, config.end_date, 7):
        log(1, "Analyzing date: %s" % date)
        csv_file_path = pathlib.Path(config.data_dir, date.strftime("%Y-%m-%d.csv"))
        log(2, "Looking from file: %s" % csv_file_path)
        try:
            df = pd.read_csv(csv_file_path, ";", index_col='rank', nrows=150)
            strategy.add_weights_column(df)
            
            snapshot = StrategyTestSnapshot(date)

            if not prev_snapshot:
                snapshot.initial_amount_usd = config.initial_amount_usd
                snapshot.data = df
                snapshot.data['initial_allocation_size'] = 0
                # Assumo che inizialmente il capitale sia interamente allocato su BTC
                snapshot.data.at[snapshot.data.symbol == 'BTC', 'initial_allocation_size'] = snapshot.initial_amount_usd / snapshot.data.loc[snapshot.data.symbol == 'BTC','priceusd']
            else:
                prev_data = prev_snapshot.data.loc[prev_snapshot.data.allocation_size > 0].filter(items=['symbol','allocation_size'])
                prev_data.columns = ['symbol', 'initial_allocation_size']

                log(4, "Prev data:\n-----\n%s" % str(prev_data))
                log(4, "Prev_data shape: %s" % str(prev_data.shape))
                log(4, "Pre-join data:\n-----\n%s" % str(df))
                log(4, "Pre join data shape: %s" % str(df.shape))
                snapshot.data = df.join(prev_data.set_index('symbol'), on='symbol')
                snapshot.data.initial_allocation_size.fillna(0, inplace=True)
                log(3, "Post-join data:\n-----\n%s" % str(snapshot.data))
                log(3, "Post join data shape: %s" % str(snapshot.data.shape))

            snapshot.data['initial_amount_usd'] = snapshot.data.initial_allocation_size * snapshot.data.priceusd
            snapshot.data['initial_amount_btc'] = snapshot.data.initial_allocation_size * snapshot.data.pricebtc
            snapshot.initial_amount_usd = snapshot.data.initial_amount_usd.sum()                
            
            log(3, snapshot.data.loc[:25])
            
            # Compute required allocations
            snapshot.data['req_allocation_usd'] = snapshot.data.weight * snapshot.initial_amount_usd
            snapshot.data['req_allocation_size'] = snapshot.data.req_allocation_usd / snapshot.data.priceusd
            snapshot.data['req_allocation_btc'] = snapshot.data.req_allocation_size * snapshot.data.pricebtc
            
            do_rebalance = current_week_idx % strategy.rebalance_period_weeks == 0

            if (do_rebalance):
                log(3, "Rebalancing.")
                snapshot.data['diff_allocation_size'] = snapshot.data.req_allocation_size - snapshot.data.initial_allocation_size
                log(2, "Required transactions:")
                log(2, snapshot.data.loc[snapshot.data.diff_allocation_size != 0])
                transactions_sell_to_btc = snapshot.data.loc[(snapshot.data.diff_allocation_size < 0) & (snapshot.data.symbol != 'BTC'), ['date', 'symbol', 'diff_allocation_size', 'priceusd', 'pricebtc']]
                transactions_sell_to_btc.insert(2, 'dest_curr', 'BTC')
                transactions_sell_to_btc.diff_allocation_size = transactions_sell_to_btc.diff_allocation_size.abs()
                transactions_sell_to_btc['amount_usd'] = transactions_sell_to_btc.diff_allocation_size * transactions_sell_to_btc.priceusd
                transactions_sell_to_btc['amount_btc'] = transactions_sell_to_btc.diff_allocation_size * transactions_sell_to_btc.pricebtc
                transactions_sell_to_btc.columns = ['date','source_curr','dest_curr','size','priceusd', 'pricebtc', 'amount_usd', 'amount_btc']
                log(2, "transactions_sell_to_btc:")
                log(2, transactions_sell_to_btc)
                transactions_buy_from_btc = snapshot.data.loc[(snapshot.data.diff_allocation_size > 0) & (snapshot.data.symbol != 'BTC'), ['date', 'symbol', 'diff_allocation_size', 'priceusd', 'pricebtc']]
                transactions_buy_from_btc.insert(1, 'source_curr', 'BTC')
                transactions_buy_from_btc['amount_usd'] = transactions_buy_from_btc.diff_allocation_size * transactions_buy_from_btc.priceusd
                transactions_buy_from_btc['amount_btc'] = transactions_buy_from_btc.diff_allocation_size * transactions_buy_from_btc.pricebtc
                transactions_buy_from_btc.columns = ['date','source_curr','dest_curr','size', 'priceusd', 'pricebtc', 'amount_usd', 'amount_btc']
                log(2, "transactions_buy_from_btc:")
                log(2, transactions_buy_from_btc)
                snapshot.transactions = pd.concat([transactions_sell_to_btc, transactions_buy_from_btc])
                
                # Set current allocation
                snapshot.data['allocation_usd'] = snapshot.data.req_allocation_usd
                snapshot.data['allocation_size'] = snapshot.data.req_allocation_size
                snapshot.data['allocation_btc'] = snapshot.data.req_allocation_btc

                # Compute fees
                if strategy.transaction_fee > 0:
                    snapshot.transaction_fees_btc = snapshot.get_transactions_amount_btc() * strategy.transaction_fee / 100
                    snapshot.transaction_fees_usd = snapshot.get_transactions_amount_usd() * strategy.transaction_fee / 100
                    log(2, "Transaction fees: %.5f BTC (%.2f USD)" % (snapshot.transaction_fees_btc, snapshot.transaction_fees_usd))
                    log(2, "Snapshot data before:\n---")
                    log(2, snapshot.data.head(3))
                    snapshot.data.at[1, 'allocation_usd'] = snapshot.data.iloc[0]['allocation_usd'] - snapshot.transaction_fees_usd
                    snapshot.data.at[1, 'allocation_size'] = snapshot.data.iloc[0]['allocation_size'] - snapshot.transaction_fees_btc
                    snapshot.data.at[1, 'allocation_btc'] = snapshot.data.iloc[0]['allocation_btc'] - snapshot.transaction_fees_btc                    
                    log(2, "Snapshot data after:\n---")
                    log(2, snapshot.data.head(3))
                else:
                    snapshot.transaction_fees_btc = 0.0
                    snapshot.transaction_fees_usd = 0.0

            else:
                log(3, "Not rebalancing.")
                snapshot.data['allocation_usd'] = snapshot.data.initial_amount_usd
                snapshot.data['allocation_size'] = snapshot.data.initial_allocation_size
                snapshot.data['allocation_btc'] = snapshot.data.initial_amount_btc
                snapshot.transactions = pd.DataFrame(columns = ['date','source_curr','dest_curr','size','amount_btc','amount_usd'])
                snapshot.transaction_fees_btc = 0.0
                snapshot.transaction_fees_usd = 0.0

            result.add_valueset(snapshot)
    
            # Preparo per nuova iterazione
            log(1, "End of analysis of date %s" % date)
            if config.interactive:
                input("Press any key")
            #result.snapshots.append(snapshot)
            prev_snapshot = snapshot
            current_week_idx += 1
        except Exception as e:
            print("Exception while analyzing file:")
            print(e)

    result.end_of_computation()
    return result

def parse_options(args):
    """
    Estrae e analizza la configurazione passata come argomento da riga di comando.
    [Extract parameters from command line.]
    """
    global config

    # String validation
    pattern = re.compile('[2][0][1][0-9]-[0-1][0-9]-[0-3][0-9]')

    # Data di inizio
    if args.start_date:
        start_date = args.start_date
        start_date_split = start_date.split('-')
        start_year = int(start_date_split[0])
        if not re.match(pattern, start_date):
            raise ValueError("Invalid format for the start_date: "
                + start_date + ". Should be of the form: yyyy-mm-dd.")
        config.start_date = datetime.date(start_year,int(start_date_split[1]),int(start_date_split[2]))
    else:
        config.start_date = FIRST_DATE

    # Data finale     
    if args.end_date:
        end_date = args.end_date
        end_date_split = end_date.split('-')
        end_year  = int(end_date_split[0])
        if not re.match(pattern, end_date):
            raise ValueError("Invalid format for the end_date: "
                + end_date + ". Should be of the form: yyyy-mm-dd.")
        config.end_date = datetime.date(end_year, int(end_date_split[1]), int(end_date_split[2]))
    else:
        config.end_date = datetime.date.today()

    # Directory dati
    if args.data_dir:
        config.data_dir = pathlib.Path(args.data_dir)
    else:
        config.data_dir = pathlib.Path("data")

    # Periodo di ribilanciamento
    #if args.rebalance_period_weeks < 1:
    #    raise ValueError("Invalid rebalance_period_weeks parameter (must be >= 1)")
    config.rebalance_period_weeks_set = set(args.rebalance_period_weeks)

    # Cap
    #if args.weight_cap_percentage <= 0 or args.weight_cap_percentage > 100:
    #    raise ValueError("Invalid weight_cap_percentage parameter (must be between 1 and 100)")
    config.weight_cap_percentage_set = set(args.weight_cap_percentage)

    # Numero di cripto
    #if args.crypto_number < 1:
    #    raise ValueError("Invalid crypto_number parameter (must be >= 1)")
    config.crypto_number_set = set(args.crypto_number)
    
    # Commissioni di transazione [Transaction fee]
    config.transaction_fee = args.transaction_fee
    if config.transaction_fee < 0 or config.transaction_fee > 100:
        raise ValueError("Invalid transaction_fee parameter (must be between 0.0 and 100.0)")

    # Verbosity
    if args.verbosity_level < 0 or args.verbosity_level > 4:
        raise ValueError("Invalid verbosity level (must be between 0 and 4")
    config.verbosity = args.verbosity_level

    config.initial_amount_usd = args.initial_amount_usd
    config.json_output = args.json_output
    config.interactive = args.interactive

def main(args=None):
    parser = argparse.ArgumentParser()

    parser.add_argument("-d",   "--data_dir", help="Specify data directory. If not specified ./data/ is used.")
    parser.add_argument("-s",   "--start_date", help="Start date from which you wish to test the strategy. For example, "
                                                "'2017-10-01'.", type=str, required=True)
    parser.add_argument("-e",   "--end_date", help="End date for strategy analysis. If not defined, performs the test until today. Same format as in start_date "
                                                "'yyyy-mm-dd'.", type=str)
    parser.add_argument("-au",  "--initial_amount_usd", help="Initial available amount in USD", type=int, required=True)
    parser.add_argument("-i",   "--interactive", help="Interactive mode. Stops at each iteration.", action="store_true")
    parser.add_argument("-rpw", "--rebalance_period_weeks", help="Period in weeks between weights rebalancing", nargs="+", type=int, default=[1])
    parser.add_argument("-cn",  "--crypto_number", help="Number of cryptos composing the index", nargs="+", type=int, required=True)
    parser.add_argument("-wc",  "--weight_cap_percentage", help="Maximum weight (in percentage) of each single crypto", nargs="+", type=int, default=[100])
    parser.add_argument("-f",   "--transaction_fee", help="Transaction fee (as a percentage of tansated BTC", type=float, default=0.0)
    parser.add_argument("-v",   "--verbosity_level", help="Verbosity level (0=None, 1=Minimal, 2=Info, 3=Debug, 4=Trace", type=int, default=1)
    parser.add_argument("-j",   "--json_output", help="Produces json outputs", action="store_true")

    # assert that args is a list
    if(args is not None):
        args = parser.parse_args(args)
    else:
        args = parser.parse_args()
    
    parse_options(args)

    total_tests = len(config.crypto_number_set) * len(config.weight_cap_percentage_set) * len(config.rebalance_period_weeks_set)
    curr_test = 1
    test_suite_results = pd.DataFrame(columns=['start_date', 'end_date', 'initial_amount_usd', 'crypto_number', 'weight_cap_perc',
                'rebalance_period_weeks', 'profit_usd', 'profit_btc', 'roi_usd', 'roi_btc', 'tot_transactions_number',
                'tot_transactions_amount_usd', 'tot_transactions_amount_btc', 
                'tot_transaction_fees_usd', 'tot_transaction_fees_btc',
                'max_drawdown', 'max_drawdown_perc', 'amount_usd_sharpe_ratio', 'amount_btc_sharpe_ratio'])
    for crypto_number in config.crypto_number_set:
        for weight_cap_percentage in config.weight_cap_percentage_set:
            for rebalance_period_weeks in config.rebalance_period_weeks_set:
                strategy = StrategyConfiguration(crypto_number, weight_cap_percentage, rebalance_period_weeks, config.transaction_fee)
                if crypto_number * weight_cap_percentage < 100:
                    log(1, "Ignoring unadmissible strategy %s" % strategy)
                    curr_test += 1
                    continue
                log(1, "Testing strategy %d of %d: %s" % (curr_test, total_tests, strategy))
                curr_test += 1
                result = test_strategy(strategy)

                # Esporto i risultati su Excel
                excel_file_name = "s-%s_e-%s_au-%d_f-%.2f_rpw-%d_cn-%d_wc-%d.xlsx" % (config.start_date, config.end_date, config.initial_amount_usd, config.transaction_fee,
                                                                            rebalance_period_weeks, crypto_number, weight_cap_percentage)
                excel_file_path = pathlib.Path(config.data_dir, excel_file_name)
                result.export_to_excel(excel_file_path)

                # Esporto i risultati su JSON
                if (config.json_output):
                    json_equity_usd_file_name = "equity-usd_s-%s_e-%s_au-%d_f-%.2f_rpw-%d_cn-%d_wc-%d.json" % (config.start_date, config.end_date, config.initial_amount_usd, config.transaction_fee,
                                                                            rebalance_period_weeks, crypto_number, weight_cap_percentage)
                    json_equity_usd_file_path = pathlib.Path(config.data_dir, json_equity_usd_file_name)
                    result.export_equity_line_usd_to_json(json_equity_usd_file_path)
                    json_equity_btc_file_name = "equity-btc_s-%s_e-%s_au-%d_f-%.2f_rpw-%d_cn-%d_wc-%d.json" % (config.start_date, config.end_date, config.initial_amount_usd, config.transaction_fee,
                                                                            rebalance_period_weeks, crypto_number, weight_cap_percentage)
                    json_equity_btc_file_path = pathlib.Path(config.data_dir, json_equity_btc_file_name)
                    result.export_equity_line_btc_to_json(json_equity_btc_file_path)

                test_suite_results = test_suite_results.append(result.get_summary(), ignore_index=True)

    test_suite_results_file_path = pathlib.Path(config.data_dir, "test_suite_results-s-%s_e-%s_au-%d_f-%.2f.xlsx" % (config.start_date, config.end_date, config.initial_amount_usd, config.transaction_fee))
    writer = pd.ExcelWriter(test_suite_results_file_path)
    test_suite_results.to_excel(writer,'Test suite s-%s_e-%s_au-%d_f-%.2f' % (config.start_date, config.end_date, config.initial_amount_usd, config.transaction_fee))
    writer.save()

    log (2, test_suite_results)

if __name__ == "__main__":
    main()