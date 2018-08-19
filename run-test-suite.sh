#!/bin/sh
#
# run-test-suite.sh
# -----------------
#
# Esegue tutta la suite di test.
#
# Per i test sono state considerate le seguenti combinazioni.
# - Intervallo di ribilanciamento portafoglio: 1 settimana, 2 settimane, 4 settimane, 3 mesi, 6 mesi
# - Numero di coin nel portafoglio: 5, 10, 15, 20, 25
# - Limite massimo in percentuale al peso di ogni coin (weight cap): 15%, 20%, 30%, 50%
# - Fee di transazione: 0%, 0.10%, 0.20%
#
# I test sono effettuati assumendo un invesimento iniziale di 10000 USD.


# Test con data di inizio 3/1/2016
# ---
# Fee = 0.00%
python3 backtest_strategy.py -s 2016-01-03 -e 2018-07-01 -au 10000 -f 0.0 -rpw 1 2 4 13 26 -cn 5 10 15 20 25 -wc 15 20 30 50 -v 1 -j
# Fee = 0.10%
python3 backtest_strategy.py -s 2016-01-03 -e 2018-07-01 -au 10000 -f 0.1 -rpw 1 2 4 13 26 -cn 5 10 15 20 25 -wc 15 20 30 50 -v 1 -j
# Fee = 0.20%
python3 backtest_strategy.py -s 2016-01-03 -e 2018-07-01 -au 10000 -f 0.2 -rpw 1 2 4 13 26 -cn 5 10 15 20 25 -wc 15 20 30 50 -v 1 -j

# Test con data di inizio 1/1/2017
# ---
# Fee = 0.00%
python3 backtest_strategy.py -s 2017-01-01 -e 2018-07-01 -au 10000 -f 0.0 -rpw 1 2 4 13 26 -cn 5 10 15 20 25 -wc 15 20 30 50 -v 1 -j
# Fee = 0.10%
python3 backtest_strategy.py -s 2017-01-01 -e 2018-07-01 -au 10000 -f 0.1 -rpw 1 2 4 13 26 -cn 5 10 15 20 25 -wc 15 20 30 50 -v 1 -j
# Fee = 0.20%
python3 backtest_strategy.py -s 2017-01-01 -e 2018-07-01 -au 10000 -f 0.2 -rpw 1 2 4 13 26 -cn 5 10 15 20 25 -wc 15 20 30 50 -v 1 -j

# Test con data di inizio 7/1/2018
# ---
# Fee = 0.00%
python3 backtest_strategy.py -s 2018-01-07 -e 2018-07-01 -au 10000 -f 0.0 -rpw 1 2 4 13 26 -cn 5 10 15 20 25 -wc 15 20 30 50 -v 1 -j
# Fee = 0.10%
python3 backtest_strategy.py -s 2018-01-07 -e 2018-07-01 -au 10000 -f 0.1 -rpw 1 2 4 13 26 -cn 5 10 15 20 25 -wc 15 20 30 50 -v 1 -j
# Fee = 0.20%
python3 backtest_strategy.py -s 2018-01-07 -e 2018-07-01 -au 10000 -f 0.2 -rpw 1 2 4 13 26 -cn 5 10 15 20 25 -wc 15 20 30 50 -v 1 -j

# Converto risultati
python3 convert_excel_results_to_json.py

