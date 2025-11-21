import yahooFinance from 'yahoo-finance2';
import { Client } from 'pg';

const client = new Client({
    user: 'your_pg_user',
    host: 'localhost',
    database: 'market_data',
    password: 'your_pg_password',
    port: 5432,
});

const NASDAQ100_SYMBOLS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "FB", "NFLX", "INTC", "AMD",
    "CSCO", "ADBE", "PYPL", "CMCSA", "PEP", "COST", "AVGO", "TXN", "QCOM", "SBUX",
    "AMAT", "ISRG", "VRTX", "REGN", "MU", "LRCX", "MDLZ", "BKNG", "GILD", "ADP",
    "TMUS", "FISV", "ILMN", "ADI", "MRNA", "KLAC", "CDNS", "SNPS", "MCHP", "KDP",
    "IDXX", "CTAS", "MAR", "PAYX", "XEL", "ORLY", "PCAR", "DLTR", "WBA", "ROST",
    "EXC", "CSX", "AEP", "ALGN", "BIIB", "EA", "WDAY", "DXCM", "SGEN", "FAST"
];

async function fetchAndStoreStockData() {
    try {
        await client.connect();

        for (const symbol of NASDAQ100_SYMBOLS) {
            const data = await yahooFinance.quoteSummary(symbol, { modules: ["price"] });
            const quote = data.price;

            const currentPrice = quote.regularMarketPrice;
            const previousClose = quote.regularMarketPreviousClose;
            const priceChange = currentPrice - previousClose;
            const volumeToday = quote.regularMarketVolume;
            const volumeYesterday = quote.volume24Hr || 1;
            const volumePercentage = (volumeToday / volumeYesterday) * 100;

            const query = `
                INSERT INTO asset_prices (asset_symbol, datetime, current_price, previous_close_price, price_change, volume_current_day, volume_previous_day, volume_percentage, preferred)
                VALUES ($1, NOW(), $2, $3, $4, $5, $6, $7, FALSE)
                ON CONFLICT (asset_symbol) DO UPDATE
                SET datetime = NOW(), current_price = EXCLUDED.current_price, price_change = EXCLUDED.price_change, volume_current_day = EXCLUDED.volume_current_day, volume_percentage = EXCLUDED.volume_percentage;
            `;

            await client.query(query, [symbol, currentPrice, previousClose, priceChange, volumeToday, volumeYesterday, volumePercentage]);
            console.log(`Stored data for: ${symbol}`);
        }
    } catch (err) {
        console.error("Error fetching/storing stock data:", err);
    } finally {
        await client.end();
    }
}

fetchAndStoreStockData();
