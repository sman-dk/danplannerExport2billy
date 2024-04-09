#!/usr/bin/env python3
import argparse
from datetime import datetime
import configparser
import os
import sys
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
    parser.add_argument('-s', '--src', help='source file (Danplanner Export file)',
                        default='~/Downloads/Finansposteringer.csv', type=str)
    parser.add_argument('--last-date', help='If last date is not today. Format: YYYY-MM-DD',
                        default=None, type=date)
    args = parser.parse_args()
    return args


def stat_check(args, cfg):
    path = args.src
    full_path = os.path.expanduser(path)
    unixtime_now = datetime.now().timestamp()
    mtime = os.path.getmtime(full_path)
    file_age = int(unixtime_now - mtime)
    max_file_age = int(cfg['files']['maxFileAge'])
    if file_age > max_file_age:
        response = input(f'The input file {args.src} is {file_age} seconds old. '
                         f'This is more than the configured limit of {max_file_age}. Do you want to proceed? (y/n)')
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


def main():
    args = arguments()
    cfg = config(args)
    stat_check(args, cfg)
    # Test parse
    # move file
    # Parse and show numbers, ask to confirm


if __name__ == '__main__':
    main()
