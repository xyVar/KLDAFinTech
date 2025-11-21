import yfinance as yf
import pandas as pd

# ✅ Define asset categories
nasdaq_stocks = ["AAPL", "MSFT", "GOOG", "NVDA", "TSLA", "AMZN", "META", "NFLX", "AMD"]  # Add full NASDAQ list
germany_stocks = ["DTE.DE", "BMW.DE", "BAS.DE", "VOW3.DE", "SAP.DE"]
france_stocks = ["OR.PA", "SAN.PA", "AIR.PA", "BNP.PA", "MC.PA"]
uk_stocks = ["BARC.L", "HSBA.L", "BP.L", "RIO.L", "VOD.L"]
italy_stocks = ["ENEL.MI", "ISP.MI", "UCG.MI", "LUX.MI", "STM.MI"]

indices = ["^GSPC", "^IXIC", "^DJI", "^DAX", "^FCHI", "^FTSE", "^STOXX50E"]
commodities = ["GC=F", "SI=F", "CL=F", "NG=F", "BZ=F", "ZW=F", "ZC=F", "ZS=F", "KC=F", "SB=F", "CT=F", "LE=F"]
energy = ["CL=F", "NG=F", "BZ=F"]
metals = ["GC=F", "SI=F", "HG=F", "PA=F", "PL=F"]
agriculture = ["ZW=F", "ZC=F", "ZS=F", "KC=F", "SB=F"]

# ✅ Combine all assets into one list
all_assets = nasdaq_stocks + germany_stocks + france_stocks + uk_stocks + italy_stocks + indices + commodities + energy + metals + agriculture

# ✅ Set historical date range
start_date = "2010-01-01"
end_date = "2024-03-10"

# ✅ Download stock data for all assets
for asset in all_assets:
    try:
        print(f"Downloading data for {asset}...")
        df = yf.download(asset, start=start_date, end=end_date, interval="1d")
        df.to_csv(f"{asset}_historical.csv")  # Save each asset as CSV
        print(f"✅ Downloaded {asset} successfully.")
    except Exception as e:
        print(f"⚠️ Error downloading {asset}: {e}")

print("🎉 All data downloaded successfully!")
