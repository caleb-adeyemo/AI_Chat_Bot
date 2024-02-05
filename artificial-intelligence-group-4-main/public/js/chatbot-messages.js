const socket = io();

console.log("Script loaded successfully");
// Get a reference to the button, chat container, and message input elements
const sendButton = document.getElementById("send-button");
const chatContainer = document.getElementById("chat-container");
const messageInput = document.getElementById("user-input");

// Attach an event listener to the button and input field
sendButton.addEventListener("click", sendMessage);
messageInput.addEventListener("keypress", function(event) {
  // Check if the key code is the enter key
  if (event.keyCode === 13) {
    sendMessage();
  }
});

function sendMessage() {
  // Get the message from the message input field
  const message = messageInput.value;

  // Call the addUserMessage function to add the message to the chat container
  addUserMessage(message);

  // Clear the message input field
  messageInput.value = "";

  console.log(`User Message (Client): ${message}`);
  socket.emit('userMessage', message);
}

function addUserMessage(message, type = "user") {
    const userMessage = document.createElement("div");

    userMessage.classList.add("chat-item", type);

    let node = document.createTextNode(message);
    userMessage.appendChild(node);

    chatContainer.appendChild(userMessage);
}

function addBotMessage(message, type = "bot", delay = 2000) {
  const botMessage = document.createElement("div");

  // botMessage.classList.add("chat-item", type);
  botMessage.className = `chat-item ${type}`

  botMessage.innerHTML = message
  // let node = document.createTextNode(message);
  // botMessage.appendChild(node);

  setTimeout(function() {
    chatContainer.appendChild(botMessage);
  }, delay);
}


function returnMessage(message) {
    return message;
}

socket.on('botMessage', (msg) =>
{
  console.log(`Bot Message (Client): ${msg}`);
  addBotMessage(msg);
});

socket.on('clearText', () =>
{
  console.log('Clearing text')
  chatContainer.innerHTML = '';
});
