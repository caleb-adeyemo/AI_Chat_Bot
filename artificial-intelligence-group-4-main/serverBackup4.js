// Packages for web application
const express = require('express');
const {spawn} = require('child_process');
const readline = require('readline');
const app = express();

rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

// const python = spawn('venv/Scripts/python', ['ChatBot.py']);
const python = spawn('venv/Scripts/python', ['test.py']);

// rl.input.setEncoding('utf-8');
// rl.input.pipe(python.stdin);
//
// process.stdin.pipe(python.stdin);

// rl.on('line', function (line)
// {
//   console.log(`Node Input: ${line}`);
// });

python.stdout.on('data', function (data)
{
  console.log(data.toString());
});

python.stderr.on('data', function (err)
{
  console.error(`stderr: ${err}`);
});

python.on('error', (err) => {
  console.error(`error: ${error.message}`);
});

python.on('close', (code) =>
{
  console.log(`Python exited with code ${code}`);
});

python.stdin.write('Hi there\n');

python.stdin.write('World\n');

// process.stdin.end();
