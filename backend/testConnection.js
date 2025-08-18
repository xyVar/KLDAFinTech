const pool = require('./database'); // ✅ CORRECT
async function testDB() {
    try {
        const result = await pool.query('SELECT NOW()');
        console.log('Connected to PostgreSQL:', result.rows[0]);
    } catch (error) {
        console.error('Database connection error:', error);
    }
}

testDB();
