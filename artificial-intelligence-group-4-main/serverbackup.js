// Packages for web application
const express = require('express');
const app = express();
const bodyParser = require('body-parser');

// Middleware and static files
app.use(bodyParser.json());   // Using body parser to handle form data
app.use(bodyParser.urlencoded({extended: false}))    // Choosing to parse the URL encoded data with the querystring library
app.use(express.static('public'))    // Sets default file directory to 'public'
app.set('view engine', 'ejs')   // Set default view file type to .ejs

const port = 3000;

app.listen(port, () =>
{
  console.log(`Express app listening on port ${port}`);
});

const {Pool} = require('pg');

let currentThread = 1;

const pool = new Pool({
  host: "localhost",
  user: "postgres",   // Your PostgreSQL username
  port: 5432,
  password: "?postugreseqla55?",  // Change password to your own master password
  database: "aiDatabase"    // Your database with the 'users' table
});



pool.connect(err =>
{
  if (!err)
  {
    console.log('Connected to database.');
  }
  else
  {
    console.log(err.message);
  }
});

app.get('/', async (req, res) =>
{
  try
  {
    const result = await pool.query('SELECT * FROM threads');

    res.render('index',
    {
      thread: currentThread
    });
  }
  catch (err)
  {
    console.log(err.message);
  }
});

app.post('/chat', async (req, res) =>
{
  try
  {
    const sender = req.body.sender;
    const message = req.body.message;

    const query_text = 'INSERT INTO messages (thread_id, msg_sender, content)'+
                       'VALUES (1, $1, $2)';
    const query_values = [sender, message];

    const result = await pool.query(query_text, query_values);
  }
  catch (err)
  {
    console.log(err.message);
  }
});

app.post('/change-thread', async (req, res) =>
{
  console.log(`Thread button value: ${JSON.stringify(req.body)}`);
  console.log(`Current Thread: ${currentThread}`);

  try
  {
    const result = await pool.query('SELECT * FROM threads WHERE thread_id = $1', [req.body.threadValue]);
    currentThread = result.rows[0].thread_id;
  }
  catch (err)
  {
    console.log(err.message);
  }
});
