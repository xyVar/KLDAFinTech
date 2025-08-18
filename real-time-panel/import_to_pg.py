import os
import pandas as pd
import psycopg2

# ✅ PostgreSQL Connection Settings
DB_NAME = "market_data"
DB_USER = "postgres"
DB_PASSWORD = "MyStrongDBpass2025!"
DB_HOST = "localhost"
DB_PORT = "5432"

# ✅ Connect to PostgreSQL
try:
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )
    cursor = conn.cursor()
    print("✅ Connected to PostgreSQL!")
except Exception as e:
    print(f"❌ Connection error: {e}")
    exit()

# ✅ Folder containing CSV files
csv_folder = "C:\\Users\\PC\\Desktop\\real-time-panel"

# ✅ Loop through all CSV files in the folder
for file in os.listdir(csv_folder):
    if file.endswith(".csv"):
        file_path = os.path.join(csv_folder, file)
        asset_symbol = file.replace("_historical.csv", "")  # Extract asset name

        print(f"📂 Importing {file}...")

        # ✅ Check if file is empty
        if os.stat(file_path).st_size == 0:
            print(f"⚠️ Skipping {file}: File is empty.")
            continue

        try:
            # ✅ Read CSV file, skipping first 3 rows (junk headers)
            df = pd.read_csv(file_path, skiprows=3, header=None)

            # ✅ Manually assign correct column names
            df.columns = ["datetime", "close_price", "high_price", "low_price", "open_price", "volume"]

            # ✅ Convert 'datetime' to actual timestamp format
            df["datetime"] = pd.to_datetime(df["datetime"])

            # ✅ Print detected columns for debugging
            print(f"🔍 Detected columns in {file}: {list(df.columns)}")

            # ✅ Ensure all required columns exist
            required_columns = ["datetime", "open_price", "high_price", "low_price", "close_price", "volume"]
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                print(f"⚠️ Skipping {file}: Missing columns {missing_columns}")
                continue

            # ✅ Insert data into PostgreSQL
            for _, row in df.iterrows():
                cursor.execute(
                    """
                    INSERT INTO asset_prices (asset_symbol, datetime, open_price, high_price, low_price, close_price, volume)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (asset_symbol, datetime) DO NOTHING;
                    """,
                    (asset_symbol, row["datetime"], row["open_price"], row["high_price"], row["low_price"], row["close_price"], row["volume"]),
                )

            conn.commit()
            print(f"✅ {file} imported successfully!")

        except pd.errors.EmptyDataError:
            print(f"⚠️ Skipping {file}: No columns found in the file.")
        except Exception as e:  
            print(f"⚠️ Error processing {file}: {e}")

# ✅ Close connection
cursor.close()
conn.close()
print("🎉 All CSV files imported into PostgreSQL successfully!")
