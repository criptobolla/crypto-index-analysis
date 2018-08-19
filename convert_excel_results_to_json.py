#!/usr/bin/python

"""
convert_excel_results_to_json.py
    Converte i file con i risultati in excel in corrispondenti file json.
"""

import argparse
import pandas as pd
import pathlib
from commons import Config


# Configurazione (global)
config = Config()

def log(level, text):
    """
    Logga una stringa su standard output (se il livello è congruo).
    """
    if level <= config.verbosity:
        print (text)

def main(args=None):
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--data_dir", help="Specify data directory. If not specified ./data/ is used.")

    # assert that args is a list
    if(args is not None):
        args = parser.parse_args(args)
    else:
        args = parser.parse_args()
    
    parse_options(args)

    for file_name in config.data_dir.glob("test_suite_results-*.xlsx"):
        json_file_name = file_name.with_suffix('.json')
        print("Converting file '%s' to '%s'" % (file_name, json_file_name))
        dataframe = pd.read_excel(file_name)
        dataframe.to_json(path_or_buf=json_file_name, orient='records')
        

def parse_options(args):
    """
    Estrae e analizza la configurazione passata come argomento da riga di comando.
    [Extract parameters from command line.]
    """
    global config

    if args.data_dir:
        config.data_dir = pathlib.Path(args.data_dir)
    else:
        config.data_dir = pathlib.Path("data")

if __name__ == "__main__":
    main()