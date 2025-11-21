const { Pool } = require('pg'); // <-- Fix: Import Pool

const pool = new Pool({
    user: 'postgres',
    host: 'localhost',
    database: 'market_data',
    password: 'MyStrongDBpass2025!',
    port: 5432,
});

module.exports = pool;
