#!/usr/bin/env python3

import psycopg2
import csv

# Adjust these for your local environment
DB_HOST = "localhost"
DB_NAME = "market_data"
DB_USER = "postgres"
DB_PASS = "MyStrongDBpass2025!"

# Priority order: (filename, index_label)
INDEX_FILES = [
    ("nasdaq.csv",   "Nasdaq"),
    ("sp500.csv",    "S&P500"),
    ("dow.csv",      "Dow"),
    ("russell.csv",  "Russell")
]

def load_csv(filename, index_label, assigned_tickers, final_list):
    """
    Read the CSV, skip any ticker already assigned,
    and add new ones to final_list with index_label.
    """
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticker = row['ticker'].strip().upper()
            if ticker not in assigned_tickers:
                final_list.append({
                    'ticker': ticker,
                    'company_name': row['company_name'].strip(),
                    'sector': row['sector'].strip(),
                    'index_label': index_label
                })
                assigned_tickers.add(ticker)


def main():
    # (1) Merge in-memory
    assigned_tickers = set()
    final_list = []

    for (filename, index_label) in INDEX_FILES:
        load_csv(filename, index_label, assigned_tickers, final_list)

    # (2) Insert into DB
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    cursor = conn.cursor()

    insert_sql = """
        INSERT INTO master_symbols (ticker, company_name, sector, index_label)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (ticker) DO NOTHING
    """

    for row in final_list:
        cursor.execute(insert_sql, (
            row['ticker'],
            row['company_name'],
            row['sector'],
            row['index_label']
        ))

    conn.commit()
    cursor.close()
    conn.close()

    print(f"Merged {len(final_list)} unique tickers from {len(INDEX_FILES)} CSV files.")

if __name__ == "__main__":
    main()
