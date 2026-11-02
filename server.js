const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');

const app = express();
const PORT = 5000;

app.use(cors());

const pool = new Pool({
    user: 'postgres',
    host: 'localhost',
    database: 'market_data',
    password: 'MyStrongDBpass2025!',
    port: 5432,
});

app.get('/api/assets', async (req, res) => {
    try {
        const result = await pool.query('SELECT ticker, close, date, volume FROM stock_prices ORDER BY date DESC LIMIT 50');
        res.json(result.rows);
    } catch (error) {
        console.error("Error executing query", error.stack);
        res.status(500).json({error: "Database error"});
    }
});

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});
