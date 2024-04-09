#!/usr/bin/env python3
import argparse
from datetime import datetime
import configparser
import os
import sys
import csv
from babel.numbers import parse_decimal
from pprint import PrettyPrinter
pp = PrettyPrinter(indent=4)
# Parse file (dryrun)
# Move file
# Parse file
# Lookup accounts in Billy and prepare for import
# Ask to upload if ok?
# Upload to Billy
# Perhaps save some output in a log file?


def date(string):
    """ Type function for argparse - check if date is parsable"""
    try:
        datetime.fromisoformat(string)
    except ValueError:
        raise argparse.ArgumentTypeError('Must be in ISO8601 date format of the type YYYY-MM-DD, e.g. 2024-04-09')
    return string


def arguments():
    # Argument parsing
    parser = argparse.ArgumentParser(prog='danplannerExport2billy.py',
                                     description='A tool to import daybook lines to Billy based on '
                                                 'Danplanner financial export files')
    parser.add_argument('-c', '--cfg', help='Configuration file',
                        default='~/Nextcloud/p/vammen/regnskab/danplanner_finanseksport/danplannerExport2billy.cfg',
                        type=str)
    parser.add_argument('-f', '--file', help='input file (Danplanner Export file)',
                        required=True, type=str)
    parser.add_argument('--last-date', help='If last date is not today. Format: YYYY-MM-DD',
                        default=None, type=date)
    args = parser.parse_args()
    return args


def stat_check(args, cfg):
    path = args.file
    full_path = os.path.expanduser(path)
    unixtime_now = datetime.now().timestamp()
    mtime = os.path.getmtime(full_path)
    file_age = int(unixtime_now - mtime)
    max_file_age = int(cfg['files']['maxFileAge'])
    if file_age > max_file_age:
        response = input(f'The input file {args.file} is {file_age} seconds old. '
                         f'This is more than the configured limit of {max_file_age}. Do you want to proceed? (y/n): ')
        if response == 'y':
            pass
        else:
            print('Exiting!\n', file=sys.stderr)
            sys.exit(1)


def config(args):
    cfg = configparser.ConfigParser()
    full_path = os.path.expanduser(args.cfg)
    cfg.read(full_path)
    return cfg


def parse_danplanner_file(args, cfg):
    full_path = os.path.expanduser(args.file)
    print(f'Checking the file {full_path}')
    with open(full_path, 'r', newline='') as f:
        csvreader = csv.reader(f, delimiter=';', quotechar='"')
        first_line = True
        dp_rows = []
        for row in csvreader:
            if first_line:
                first_line = False
                first_row_expectation = ['Konti', 'Navn', 'Beløb eks. moms', 'Moms']
                if not row == first_row_expectation:
                    print(f'The first row in the file {args.file} does not match the '
                          f'expected sections: {first_row_expectation}\nExiting!', file=sys.stderr)
                    sys.exit(1)
                else:
                    continue
            else:
                locale = cfg['files']['currencyLocale']
                amount_ex_vat = parse_decimal(row[2], locale=locale)
                amount_vat = parse_decimal(row[3], locale=locale)
                row_dict = {
                    'account': row[0],
                    'danplanner_account_descr': row[1],
                    'amount_ex_vat': amount_ex_vat,
                    'amount_vat': amount_vat,
                    'amount_incl_vat': amount_ex_vat + amount_vat
                }
                dp_rows.append(row_dict)
    balance_check(dp_rows)
    print('Danplanner file ok!')
    return dp_rows


def balance_check(dp_rows):
    balance = parse_decimal('0')
    for row in dp_rows:
        balance += row['amount_incl_vat']
    if balance != 0:
        print(f'The transactions seems to be out of balance with a difference of {balance}\n'
              f'Please check the data in the exported file from Danplanner.\nExiting!', file=sys.stderr)
        sys.exit(1)


def main():
    args = arguments()
    cfg = config(args)
    # Test parse the file before moving it
    stat_check(args, cfg)
    parse_danplanner_file(args, cfg)
    # Move the danplanner file
    # Parse and show numbers, ask to confirm
    # Upload it to Billys daybook


if __name__ == '__main__':
    main()
