import requests, psycopg2, time
conn = psycopg2.connect(host="localhost", database="market_data", user="postgres", password="MyStrongDBpass2025!")
cursor = conn.cursor()
POLYGON_API_KEY = "6jz28QKAKxUSJAMC8FvaOkEzRKUcRfIT"

nasdaq_50 = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "AMD", "COST", "NFLX", "QCOM", "INTC",
             "PYPL", "PEP", "CSCO", "AMGN", "CMCSA", "ASML", "NVAX", "INTU", "MU", "BIDU", "SBUX", "EBAY", "ORLY",
             "FISV", "LRCX", "MRNA", "ISRG", "MAR", "REGN", "KLAC", "ADP", "ATVI", "JD", "SNPS", "NXPI", "PANW",
             "CDNS", "MELI", "PAYX", "ADSK"]

def convert_fiscal_to_date(fiscal_period, fiscal_year):
    mapping = {"Q1": "-03-31", "Q2": "-06-30", "Q3": "-09-30", "Q4": "-12-31"}
    return f"{fiscal_year}{mapping.get(fiscal_period)}" if fiscal_period in mapping else None

def fetch_fundamentals():
    for ticker in nasdaq_50:
        print(f"Fetching fundamentals for: {ticker}")
        response = requests.get(
            f"https://api.polygon.io/vX/reference/financials?ticker={ticker}&timeframe=quarterly&limit=4&apiKey={POLYGON_API_KEY}"
        )
        data = response.json()

        if response.status_code == 200 and 'results' in data:
            for report in data['results']:
                report_date = convert_fiscal_to_date(report['fiscal_period'], report['fiscal_year'])
                if not report_date:
                    continue

                cursor.execute("""
                    INSERT INTO fundamentals (ticker, report_date, revenue, net_income, earnings_per_share, eps_estimate, surprise, company_name, sector, market_cap)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ticker, report_date) DO UPDATE SET 
                        revenue=EXCLUDED.revenue, net_income=EXCLUDED.net_income,
                        earnings_per_share=EXCLUDED.earnings_per_share,
                        eps_estimate=EXCLUDED.eps_estimate, surprise=EXCLUDED.surprise,
                        company_name=EXCLUDED.company_name, sector=EXCLUDED.sector, market_cap=EXCLUDED.market_cap;
                """, (
                    ticker, report_date, report.get('revenue'), report.get('net_income'),
                    report.get('earnings_per_share'), report.get('eps_estimate'), report.get('surprise'),
                    report.get('company_name'), report.get('sector'), report.get('market_cap')
                ))

            conn.commit()
            print(f"✅ Updated fundamentals for {ticker}")
        else:
            print(f"❌ Error fetching fundamentals for {ticker}")
        time.sleep(12)

fetch_fundamentals()
