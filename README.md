# Introduzione

Il codice di questo progetto è stato utilizzato per effettuare le analisi presentate nell'articolo
[https://www.criptobolla.it/un-paniere-ottimale-di-criptovalute.html].

Vi sono 3 script Python eseguibili.

* **fetch_cmc_historical_data.py** - Recupera i dati storici settimanali da CoinMarketCap e li
  salva su file CSV nella cartella dei dati. Genera un file per ogni settimana recuperata.

* **backtest_strategy.py** - Effettua l'analisi di una o più specifiche strategie. Tramite
  riga di comando è possibile definire il periodo di analisi ed i parametri delle strategie
  da analizzare. Per ogni strategia viene generato un file Excel con i risultati (settimana per
  settimana) della strategia e, se richiesto, una coppia di file JSON contenenti i valori settimanali
  della equity line (valore complessivo del portafoglio) in USD e BTC.
  A fine esecuzione viene anche generato un singolo file Excel con suffisso 'test_suite_results_'
  contenente i dati aggregati dell'analisi.
  
* **convert_excel_results_to_json.py** - Converte i risultati generati nel file Excel 'test_suite_results_'
  in un file JSON, utilizzato per la visualizzazione dei risultati sulle tabelle nella pagina Web.

Il file *commons.py* contiene delle funzioni di supporto per i 3 eseguibili summenzionati.


# TODO

Verificare se è possibile aggiungere altri indicatori da http://www.turingfinance.com/computational-investing-with-python-week-one/
