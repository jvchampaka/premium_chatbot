// static/script.js
let recognition = null;
let isRecording = false;

const chatbox = document.getElementById("chatbox");
const htmlOut = document.getElementById("htmlOut");
const textInput = document.getElementById("textInput");
const sendBtn = document.getElementById("sendBtn");
const micBtn = document.getElementById("micBtn");

// Initialize browser speech recognition (Chrome / Edge)
if ('webkitSpeechRecognition' in window) {
  recognition = new webkitSpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = 'en-IN';

  recognition.onresult = function(event) {
    const transcript = event.results[0][0].transcript;
    sendToChatbot(transcript);
  };

  recognition.onerror = function(event) {
    console.error("Speech recognition error:", event.error);
    appendBot("Speech recognition error: " + event.error);
    micBtn.classList.remove("recording");
    isRecording = false;
  };

  recognition.onend = function() {
    micBtn.classList.remove("recording");
    isRecording = false;
  };
} else {
  appendBot("Note: Your browser does not support the built-in speech recognizer. Use the text box to type.");
  micBtn.disabled = true;
}

// Event listeners for send
sendBtn.addEventListener('click', () => {
  const txt = textInput.value.trim();
  if (txt) {
    sendToChatbot(txt);
    textInput.value = "";
  }
});

textInput.addEventListener('keydown', (e) => {
  if (e.key === "Enter") {
    const txt = textInput.value.trim();
    if (txt) {
      sendToChatbot(txt);
      textInput.value = "";
    }
  }
});

// Press-and-hold (desktop)
micBtn.addEventListener('mousedown', (e) => {
  if (!recognition || isRecording) return;
  isRecording = true;
  micBtn.classList.add("recording");
  recognition.start();
});

// Release (desktop)
micBtn.addEventListener('mouseup', (e) => {
  if (!recognition || !isRecording) return;
  recognition.stop();
});

// Touch support (mobile)
micBtn.addEventListener('touchstart', (e) => {
  e.preventDefault();
  if (!recognition || isRecording) return;
  isRecording = true;
  micBtn.classList.add("recording");
  recognition.start();
}, {passive:false});

micBtn.addEventListener('touchend', (e) => {
  e.preventDefault();
  if (!recognition || !isRecording) return;
  recognition.stop();
}, {passive:false});

// Send text to backend
function sendToChatbot(text) {
  appendUser(text);
  
  // ✅ Use your full Render backend URL here
  fetch("https://premium-chatbot.onrender.com/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text })
  })
  .then(res => res.json())
  .then(data => {
    appendBot(data.reply || "No reply from bot.");
    if (data.html) {
      htmlOut.innerHTML = data.html;
    }
  })
  .catch(err => {
    console.error(err);
    appendBot("Server error: " + err);
  });
}

function appendUser(msg) {
  const d = document.createElement("div");
  d.classList.add("user");
  d.textContent = "You: " + msg;
  chatbox.appendChild(d);
  chatbox.scrollTop = chatbox.scrollHeight;
}

function appendBot(msg) {
  const d = document.createElement("div");
  d.classList.add("bot");
  d.textContent = "Bot: " + msg;
  chatbox.appendChild(d);
  chatbox.scrollTop = chatbox.scrollHeight;
}
