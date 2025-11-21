const { Pool } = require("pg");

const pool = new Pool({
    user: "postgres",
    host: "localhost",
    database: "market_data",
    password: "your_newpassword",  // Replace with your actual password
    port: 5432,
});

module.exports = pool;
