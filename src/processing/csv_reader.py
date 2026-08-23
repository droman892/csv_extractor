import csv

def read_csv(filename):
    with open(filename, mode='r', newline='', encoding='utf-8-sig') as file:
        raw_rows = csv.DictReader(file)
        return list(raw_rows)