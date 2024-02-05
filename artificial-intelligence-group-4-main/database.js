const {Pool} = require('pg');   // PostgreSQL database
const dotenv = require('dotenv');   // For database variables
dotenv.config();

const pool = new Pool({
  // All variables are defined in the .env file
  host: process.env.PGHOST,
  user: process.env.PGUSER,
  password: process.env.PGPASSWORD,
  database: process.env.PGDATABASE,
  port: process.env.PGPORT
});

// (async () =>
// {
//   pool.connect(err =>
//   {
//     if (!err)
//     {
//       console.log('Connected to database.');
//     }
//     else
//     {
//       console.log(err.message);
//     }
//   });
//
//   const testQuery = await pool.query('SELECT * FROM threads');
//   console.log(`Threads: ${JSON.stringify(testQuery.rows, null, 2)}`);
// })();

module.exports = {pool};
