// Packages for web application
const express = require('express');
const app = express();
const http = require('http');
const server = http.createServer(app);
const {Server} = require('socket.io');
const io = new Server(server);
const bodyParser = require('body-parser');
// Packages for running python script
const {spawn} = require('child_process');
// National Rail web scraper
const {ticketInfoToString, getTickets} = require('./railwayScraperTest.js');
const {pool} = require('./database.js');

// Middleware and static files
app.use(bodyParser.json());   // Using body parser to handle form data
app.use(bodyParser.urlencoded({extended: false}))    // Choosing to parse the URL encoded data with the querystring library
app.use(express.static('public'))    // Sets default file directory to 'public'
app.set('view engine', 'ejs')   // Set default view file type to .ejs

const storeMessage = async (threadID, sender, content) =>
{
  const messageStoreQueryText = 'INSERT INTO messages(thread_id, msg_sender, content) VALUES ($1, $2, $3)';

  const messageStoreQueryValues = [threadID, sender, content];

  const messageStoreQuery = await pool.query(messageStoreQueryText, messageStoreQueryValues);

  // console
};

const modifyPythonOutput = async outputObj =>
{
  const messages = [];
  switch(outputObj.type)
  {
    case 'botMessage':
      messages.push(outputObj.content);
      return [messages, true];
    case 'trainJourney':
      const [cheapestTickets, cheapestTicketUrl, cheapestTicketPrice] = await getTickets(outputObj.content);
      if (cheapestTickets === null)
      {
        messages.push('Unable to get cheapest tickets. Please try again');
      }
      else
      {
        messages.push(cheapestTickets[0]);
        if (outputObj.content.return !== null)
        {
          messages.push(cheapestTickets[1]);
        }
        messages.push(`Cheapest Fare Price:<br>£${cheapestTicketPrice.toFixed(2)}`);
        messages.push(`URL:<br><a href="${cheapestTicketUrl}" target="_blank">${cheapestTicketUrl}</a>`);
      }
      return [messages, true];
    case 'delayInfo':
      messages.push(outputObj.content);
      return [messages, false];
  }
};

app.get('/', (req, res) =>
{
  try
  {
    res.render('index');
  }
  catch (err)
  {
    console.log(err.message);
  }
});

app.get('/chatbot', (req, res) =>
{
  try
  {
    res.render('chatbot');
  }
  catch (err)
  {
    console.log(err.message);
  }
});

app.get('/about', (req, res) =>
{
  try
  {
    res.render('about');
  }
  catch (err)
  {
    console.log(err.message);
  }
});

io.on('connection', async (socket) =>
{
  try
  {
    console.log('User Connected');
    io.emit('clearText');

    // Open python file
    const chatbot_py = spawn('venv/Scripts/python', ['ChatBot6.py']);   // 'venv/Scripts/python' - Links to Python virtual environment 'venv'
    // const chatbot_py = spawn('venv/bin/python', ['ChatBot.py']);   // 'venv/Scripts/python' - Links to Python virtual environment 'venv'
    // const test_py = spawn('venv/Scripts/python', ['test.py']);   // 'venv/Scripts/python'

    chatbot_py.stdout.on('data', async (data) =>
    {
      console.log(`Chatbot Python Output: ${data.toString().trim()}\n`);
      strings = data.toString().split(/\r?\n/).filter(str => str !== '');
      for (let i = 0; i < strings.length; i++)
      {
        const outputObj = JSON.parse(strings[i]);
        console.log(JSON.stringify(outputObj, null, 2))
        const [newStrings, isOutput] = await modifyPythonOutput(outputObj);
        if (isOutput)
        {
          newStrings.forEach(message =>
          {
            io.emit('botMessage', message)
            console.log(`Bot Message (Server): ${message}`);
          });
        }
        else
        {
          console.log(`newStrings for delay: ${JSON.stringify(newStrings)}`);
          const pred_model = spawn('venv/Scripts/python', ['linear_regression2.py', JSON.stringify(newStrings)]);   // Prediction model Python file

          pred_model.stdout.on('data', async (data) =>
          {
            const predModelOutput = data.toString().trim()
            console.log(`Prediction Model Output: ${predModelOutput}\n`);
            io.emit('botMessage', predModelOutput);
            console.log(`Bot Message (Server): ${predModelOutput}`);
          });

          pred_model.stderr.on('data', function (err)
          {
            console.error(`stderr: ${err}`);
          });

          pred_model.on('error', (err) => {
            console.error(`error: ${err.message}`);
          });

          pred_model.on('close', (code) =>
          {
            console.log(`Python exited with code ${code}`);
          });
        }
      }
    });

    chatbot_py.stderr.on('data', function (err)
    {
      console.error(`stderr: ${err}`);
    });

    chatbot_py.on('error', (err) => {
      console.error(`error: ${err.message}`);
    });

    chatbot_py.on('close', (code) =>
    {
      console.log(`Python exited with code ${code}`);
    });

    socket.on('userMessage', (msg) =>
    {
      console.log(`User Message (Server): ${msg}`);
      // storeMessage(1, 'user', msg);
      chatbot_py.stdin.write(`${msg}\n`);
    });
  }
  catch (err)
  {
    console.log(`io.on Error: ${err.message}`);
  }
});

const port = 4000;

async function startServer ()
{
  return new Promise((resolve, reject) =>
  {
    pool.connect(err =>
    {
      if (!err)
      {
        console.log('Connected to database.');
        return resolve();
      }
      else
      {
        console.log('Unable to connect to database.');
        return reject(err);
      }
    });
  });
}

startServer()
  .then(() =>
  {
    // Listening to port 3000 on localhost
    server.listen(port, () =>
    {
      console.log(`Express app listening on port ${port}`);
    });
  })
  .catch(err => { console.log(`Server unable to start. Please try again\nError: ${err.message}`); });
