# danplannerExport2billy
Import financial exports from the danish booking system "Danplanner" into the draft daybook of the danish accounting system "Billy".

This is a "it works for us" piece of software, that is made specifically for integrating the booking system and the accounting system used by us on the danish music and nature campsite [Vammen Camping](https://vammencamping.dk). If you use the same booking system and the same accounting system, then this script could spare you some time.

## Preconditions
You need a [Billy](https://billy.dk) account. Under settings create an API key and insert it into the configuration file.

You also need a [Danplanner](https://danline.dk) account.

Preferrably create a virtual environment with python and install the following packages:

`pip3 install babel requests`

## Usage
```$ ./danplannerExport2billy.py -h
usage: danplannerExport2billy.py [-h] [-c CFG] -f FILE [-t TO_DATE]

A tool to import daybook lines to Billy based on Danplanner financial export files

options:
  -h, --help            show this help message and exit
  -c CFG, --cfg CFG     Configuration file
  -f FILE, --file FILE  input file (Danplanner Export file)
  -t TO_DATE, --to-date TO_DATE
                        If the to date is not today. A timestamp may be included. ISO8601 format: E.g. 2024-04-09 or 2024-04-09T14:56:12
```
## Example
In Danplanner go to Finans -> Eksternt finanssystem. Then create an export and click the rightmost icon for exporting. You will then get a file called e.g.:
FinanceExport_4_11_2024.csv

The date in the filename is the current date, not the end date selected in Danplanner (maybe that will change in the future). That is why you can set the "to date" with the script, in order to deviate from today.

`./danplannerExport2billy.py -f ~/Downloads/FinanceExport_4_11_2024.csv`
