// static/js/chat.js

function toggleChat() {
  const chatPopup = document.getElementById("chat-window-popup");
  const spriteContainer = document.getElementById("sprite-ask-container");

  if (chatPopup.classList.contains("hidden")) {
    chatPopup.classList.remove("hidden");
    if (spriteContainer) spriteContainer.classList.add("chat-open");
  } else {
    chatPopup.classList.add("hidden");
    if (spriteContainer) spriteContainer.classList.remove("chat-open");
  }
}

async function sendMessage() {
  const input = document.getElementById("user-input");
  const display = document.getElementById("chat-display");
  const sendButton = document.getElementById("send-btn-icon"); // Updated to match your HTML ID

  const msg = input.value.trim();

  if (!msg) return;

  input.disabled = true;
  if (sendButton) {
    sendButton.disabled = true;
    sendButton.style.opacity = "0.5";
  }

  if (window.SpriteBot) SpriteBot.setState("thinking");

  const userDiv = document.createElement("div");
  userDiv.className = "msg user";
  userDiv.innerText = msg;
  display.appendChild(userDiv);
  input.value = "";

  const typingDiv = document.createElement("div");
  typingDiv.id = "typing";
  typingDiv.className = "msg bot";
  typingDiv.innerText = "...";
  display.appendChild(typingDiv);
  display.scrollTop = display.scrollHeight;

  try {
    const payload = { message: msg };

    //for widgets
    if (window.EMBEDDED_BOT_ID) {
      payload.bot_id = window.EMBEDDED_BOT_ID;
    }

    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    console.log("SERVER SENT THIS:", data);

    if (document.getElementById("typing")) {
      document.getElementById("typing").remove();
    }

    const botDiv = document.createElement("div");
    botDiv.className = "msg bot";

    if (data.error) {
      if (window.SpriteBot) SpriteBot.setState("idle");
      botDiv.innerText = "SYSTEM ERROR: " + data.error;
    } else if (data.response) {
      if (window.SpriteBot) {
        SpriteBot.setState("talking");
        setTimeout(() => {
          if (SpriteBot.currentState === "talking") {
            SpriteBot.setState("idle");
          }
        }, 8000);
      }
      botDiv.innerText = data.response;
    } else {
      if (window.SpriteBot) SpriteBot.setState("idle");
      botDiv.innerText = "SYSTEM ERROR: Unrecognized data format.";
    }

    display.appendChild(botDiv);
  } catch (error) {
    if (window.SpriteBot) SpriteBot.setState("idle");
    if (document.getElementById("typing")) {
      document.getElementById("typing").innerText =
        "Error connecting to server.";
    }
  } finally {
    input.disabled = false;
    if (sendButton) {
      sendButton.disabled = false;
      sendButton.style.opacity = "1";
    }
    input.focus();
    display.scrollTop = display.scrollHeight;
  }
}
