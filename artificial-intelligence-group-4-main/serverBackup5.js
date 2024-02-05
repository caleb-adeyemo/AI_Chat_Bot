// Packages for web application
const express = require('express');
const app = express();
const http = require('http');
const server = http.createServer(app);
const {Server} = require('socket.io');
const io = new Server(server)

const bodyParser = require('body-parser');

// Middleware and static files
app.use(bodyParser.json());   // Using body parser to handle form data
app.use(bodyParser.urlencoded({extended: false}))    // Choosing to parse the URL encoded data with the querystring library
app.use(express.static('public'))    // Sets default file directory to 'public'
app.set('view engine', 'ejs')   // Set default view file type to .ejs

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

io.on('connection', (socket) =>
{
  console.log('User Connected');
  socket.on('userMessage', (msg) =>
  {
    console.log(`User Message (Server): ${msg}`);
    io.emit('botMessage', msg);
    console.log(`Bot Message (Server): ${msg}`);
  });
})

const port = 3000;

server.listen(port, () =>
{
  console.log(`HTTP server listening on port ${port}`);
});
