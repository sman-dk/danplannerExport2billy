#!/usr/bin/env python3
# Copyright (c) 2024 Georg Sluyterman <georg@sman.dk>
# See the LICENSE file for licensing information

import argparse
from datetime import datetime
import configparser
import os
import sys
import csv
from babel.numbers import parse_decimal
import requests
from pprint import PrettyPrinter
pp = PrettyPrinter(indent=4)


# Some of the Billy API functions are derived from https://www.billy.dk/api/#code-examples
# API doc: https://www.billy.dk/api/#resource-documentation
#
# Reusable class for sending requests to the Billy API
class BillyClient:
    def __init__(self, api_token):
        self.apiToken = api_token

    def request(self, method, url, body, params):
        base_url = 'https://api.billysbilling.com/v2'
        try:
            response = {
                'GET': requests.get(
                    base_url + url,
                    headers={'X-Access-Token': self.apiToken},
                    params=params
                ),
                'POST': requests.post(
                    base_url + url,
                    json=body,
                    headers={'X-Access-Token': self.apiToken},
                    params=params,
                ),
                'DELETE': requests.delete(
                    base_url + url,
                    json=body,
                    headers={'X-Access-Token': self.apiToken},
                    params=params,
                ),

            }[method]
            status_code = response.status_code
            raw_body = response.text
            if status_code >= 400:
                raise requests.exceptions.RequestException(
                    '{}: {} failed with {:d} - {}'
                    .format(method, url, status_code, raw_body)
                )
            return response.json()
        except requests.exceptions.RequestException as e:
            print(e)
            raise e


# Billy functions
# Get id of organization associated with the API token.
def get_organization(client):
    response = client.request('GET', '/organization', None, None)
    return response['organization']


def get_daybook_balance_accounts(client, daybook_id):
    response = client.request('GET', '/daybookBalanceAccounts?daybookId=%s' % daybook_id, None, None)
    return response


def get_daybook_transaction_lines(client, daybook_transaction_id):
    response = client.request('GET', '/daybookTransactionLines?daybookTransactionId=%s'
                              % daybook_transaction_id, None, None)
    return response


def post_daybook_transactions(client, daybook_id, entry_date, organization_id, from_date, to_date, desc_prefix):
    body = {'daybookTransaction': {
                                   'entryDate': entry_date,
                                   'organizationId': organization_id,
                                   'state': 'draft',
                                   'daybookId': daybook_id,
                                   'description': f'{desc_prefix} {from_date} til {to_date}',
                                   'priority': 22
                                   }}

    response = client.request('POST', '/daybookTransactions', body, None)
    return response


def post_daybook_transaction_lines(client, account_id, amount, daybook_transaction_id, side, taxrate_id,
                                   from_date_str, to_date_str, desc_prefix):
    body_line = {
        'accountId': account_id,
        'amount': amount,
        'baseAmount': None,
        'currencyId': 'DKK',
        'daybookTransactionId': daybook_transaction_id,
        'priority': 1,
        'side': side,
        'taxRateId': taxrate_id,
        'text': '%s %s til %s' % (desc_prefix, from_date_str, to_date_str)
    }
    body = {'daybookTransactionLine': body_line}
    response = client.request('POST', '/daybookTransactionLines', body, None)
    return response


# List accounts ("kontoplan")
def get_accounts(client):
    response = client.request('GET', '/accounts', None, None)
    return response


# Basically it lists the "Standardklassekladde"
def get_daybooks(client):
    response = client.request('GET', '/daybooks', None, None)
    return response


def get_tax_rates(client):
    response = client.request('GET', '/taxRates', None, None)
    return response


def check_date(string):
    """ Type function for argparse - check if date is parsable"""
    try:
        datetime.fromisoformat(string)
    except ValueError:
        raise argparse.ArgumentTypeError('Must be in ISO8601 date format of the type YYYY-MM-DD, e.g. 2024-04-09'
                                         'or 2024-04-09T14:56:12')
    return string


def arguments():
    # Argument parsing
    parser = argparse.ArgumentParser(prog='danplannerExport2billy.py',
                                     description='A tool to import daybook lines to Billy based on '
                                                 'Danplanner financial export files')
    parser.add_argument('-c', '--cfg', help='Configuration file',
                        default='~/github/danplannerExport2billy/danplannerExport2billy.cfg',
                        type=str)
    parser.add_argument('-f', '--file', help='input file (Danplanner Export file)',
                        required=True, type=str)
    parser.add_argument('-t', '--to-date', help='If the to date is not today. A timestamp may be included. '
                                                'ISO8601 format: E.g. 2024-04-09 or 2024-04-09T14:56:12',
                        default=None, type=check_date)
    args = parser.parse_args()
    return args


def mtime_check(args, cfg):
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


def parse_danplanner_file(args, cfg, path=None):
    if not path:
        full_path = os.path.expanduser(args.file)
    else:
        full_path = path
    print(f'Checking the file {full_path}')
    with open(full_path, 'r', newline='') as f:
        csvreader = csv.reader(f, delimiter=';', quotechar='"')
        first_line = True
        dp_data = []
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
                    'account_no': int(row[0]),
                    'account_name': row[1],
                    'amount_ex_vat': amount_ex_vat,
                    'amount_vat': amount_vat,
                    'amount_incl_vat': amount_ex_vat + amount_vat
                }
                dp_data.append(row_dict)
    balance_check(dp_data)
    print('Danplanner file ok!')
    return dp_data


def balance_check(dp_data):
    balance = parse_decimal('0')
    for row in dp_data:
        balance += row['amount_incl_vat']
    if balance != 0:
        print(f'The transactions seems to be out of balance with a difference of {balance}\n'
              f'Please check the data in the exported file from Danplanner.\nExiting!', file=sys.stderr)
        sys.exit(1)


def move_file(args, cfg):
    src_full_path = os.path.expanduser(args.file)
    # If a date is manually set. I.e. not today
    if args.to_date:
        to_date = datetime.fromisoformat(args.to_date)
    else:
        to_date = datetime.now()
    # Year is used for the destination folder path
    year = to_date.strftime("%Y")
    dst_folder = os.path.join(os.path.expanduser(cfg['files']['dstFolder']), year)
    # List files in dst_folder, alphabetically sorted
    files = [f for f in os.listdir(dst_folder) if os.path.isfile(os.path.join(dst_folder, f))]
    files.sort()
    if len(files) == 0:
        # If no previous files in folder
        from_date_str = 'unknown'
    else:
        last_file = files[-1]
        from_date_str = last_file.split('_-_')[-1].split('.csv')[0]
    # Sanity check of from date
    print(f'Sanity checking from date ({from_date_str})')
    check_date(from_date_str)
    from_date = datetime.fromisoformat(from_date_str)
    if args.to_date:
        to_date_str = args.to_date
    else:
        to_date_str = to_date.strftime("%Y-%m-%d")
    if from_date == to_date:
        print(f'ERROR when parsing dates the from_date (str: {from_date_str}) and to_date (str: {to_date_str}) '
              f'are the same. This looks like an error.\nExiting!', file=sys.stderr)
        sys.exit(1)
    dst_filename = "financeexport_%s_-_%s.csv" % (from_date_str, to_date_str)
    dst_full_path = os.path.join(dst_folder, dst_filename)
    print(f'Moving file from {src_full_path} to {dst_full_path}')
    if os.path.exists(dst_full_path):
        print(f'ERROR the destination path {dst_full_path} already exists!\nExiting!', file=sys.stderr)
        sys.exit(1)
    os.rename(src_full_path, dst_full_path)
    return dst_full_path, from_date_str, to_date_str, to_date


def billy_stuff(cfg, from_date_str, to_date_str, to_date, dp_data):
    entry_date = to_date.strftime('%Y-%m-%d')
    print('\n** Preparing Billy data **\n')
    apikey = cfg['billy']['apikey']
    client = BillyClient(apikey)
    organization = get_organization(client)
    organization_id, organization_name = organization['id'], organization['name']
    print(f'{organization_name} id: {organization_id}')
    # lists "standardkasseklade" - What else would there be than that? :
    response = get_daybooks(client)
    daybook_id = response['daybooks'][0]['id']
    daybook_name = response['daybooks'][0]['name']
    print(f'{daybook_name} id: {daybook_id}')
    # Get taxrate ids
    print('Fetching TAX/VAT rates')
    taxrates = get_tax_rates(client)['taxRates']
    taxrates_dict = {t['id']: t for t in taxrates}
    # Get account numbers
    accounts = get_accounts(client)
    # Lookup accounts in Billy and prepare for import
    print('Lookup Billy account numbers')
    accounts_dict = {a_dict['accountNo']: a_dict for a_dict in accounts['accounts']}
    for d in dp_data:
        account_no = d['account_no']
        dp_account_name = d['account_name']
        if account_no not in accounts_dict:
            print(f'{account_no} not found in Billy.\nExiting!', file=sys.stderr)
            sys.exit(1)
        else:
            billy_account_name = accounts_dict[account_no]['name']
            print(f'* Account no {account_no} found in Billy:')
            print(f'  Danplanner name: {dp_account_name}')
            print(f'  Billy name:      {billy_account_name}')
    print('\nParsed Danplanner data:')
    print('(Please note only the amount_incl_vat is used)')
    pp.pprint(dp_data)
    print('\n * The following transaction will be uploaded to Billy:\n')
    transaction_lines = []
    for d in dp_data:
        account_no = d['account_no']
        account_id = accounts_dict[account_no]['id']
        account_name = accounts_dict[account_no]['name']
        taxrate_id = accounts_dict[account_no]['taxRateId']
        if taxrate_id:
            taxrate_name = taxrates_dict[taxrate_id]['name']
        else:
            taxrate_name = None
        amount = d['amount_incl_vat']
        # Prepare for debit/credit
        if d['amount_incl_vat'] < 0:
            side = 'credit'
            amount *= -1
        else:
            side = 'debit'
        transaction_line = {
            'account_no': account_no,
            'account_id': account_id,
            'account_name': account_name,
            'amount': amount,
            'side': side,
            'taxrate_id': taxrate_id,
            'taxrate_name': taxrate_name
        }
        transaction_lines.append(transaction_line)
        print(f'   {account_no}: {amount} {side} (VAT: {taxrate_name}) ({account_name})')
    user_ok = input('\nWould you like to proceed and upload data to Billy? (y/n): ')
    if not user_ok == 'y':
        print('*** Data is NOT uploaded to Billy ***')
        return
    response = post_daybook_transactions(client, daybook_id, entry_date, organization_id, from_date_str, to_date_str, cfg['billy']['prefix'])
    pp.pprint(response)
    daybook_transaction_id = response['daybookTransactions'][0]['id']
    print(f'** post_daybook_transactions daybook_transaction_id: {daybook_transaction_id}')
    for t in transaction_lines:
        account_id = t['account_id']
        amount = float(t['amount'])
        side = t['side']
        taxrate_id = t['taxrate_id']
        response = post_daybook_transaction_lines(client, account_id, amount, daybook_transaction_id, side, taxrate_id,
                                                  from_date_str, to_date_str, cfg['billy']['prefix'])
        pp.pprint(response)


def main():
    args = arguments()
    cfg = config(args)
    # Test parse the file before moving it
    mtime_check(args, cfg)
    parse_danplanner_file(args, cfg)
    # Move the danplanner file
    dst_full_path, from_date_str, to_date_str, to_date = move_file(args, cfg)
    # Parse file (this time no dryrun)
    dp_data = parse_danplanner_file(args, cfg, path=dst_full_path)
    # Play around with Billy
    billy_stuff(cfg, from_date_str, to_date_str, to_date, dp_data)
    print("\nFinished!\n")


if __name__ == '__main__':
    main()
