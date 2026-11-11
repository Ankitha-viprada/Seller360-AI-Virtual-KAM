
const API = "http://127.0.0.1:8000/api";

let conversation = [];
let recognition = null;
let listening = false;
let soundOn = true;
let busy = false;
let greetingPlayed = false;

const $ = (id) => document.getElementById(id);
const messagesEl = $("chatMessages");

function addMessage(role, text) {
  const row = document.createElement("div");
  row.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = role === "assistant" ? "✦" : "AF";

  const body = document.createElement("div");

  const name = document.createElement("span");
  name.className = "message-name";
  name.textContent = role === "assistant"
    ? "SELLER360 · AI KAM"
    : "YOU · SELLER";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  const time = document.createElement("small");
  time.textContent = new Date().toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit"
  });

  body.append(name, bubble, time);
  row.append(avatar, body);

  messagesEl.appendChild(row);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function speak(text) {
  if (!soundOn || !("speechSynthesis" in window)) return;

  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);

  utterance.rate = 1.02;
  utterance.pitch = 1.0;
  utterance.lang = "en-IN";

  window.speechSynthesis.speak(utterance);
}

// OPENING GREETING
function playOpeningGreeting() {
  if (greetingPlayed) return;

  greetingPlayed = true;

  const greeting =
    "Hello Aarav! Welcome to Seller360. " +
    "I'm your AI Virtual Key Account Manager. " +
    "I noticed your sales have dropped from two lakh rupees last month " +
    "to one lakh thirty-five thousand rupees this month. " +
    "I'm here to help you understand what's happening " +
    "and build a practical recovery plan. " +
    "Have you noticed any issues with product availability, " +
    "order cancellations, or deliveries?";

  if (conversation.length === 0) {
    conversation.push({
      role: "assistant",
      content: greeting
    });
  }

  $("voiceState").textContent = "Your AI KAM is greeting you...";

  speak(greeting);

  $("voiceState").textContent =
    "Your AI KAM has greeted you · Ready to listen";
}

// SEND MESSAGE TO AI
async function sendMessage(text) {
  const message = (text || "").trim();

  if (!message || busy) return;

  busy = true;

  addMessage("user", message);

  conversation.push({
    role: "user",
    content: message
  });

  $("voiceState").textContent =
    "Thinking through your business...";

  try {
    const response = await fetch(`${API}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        message,
        history: conversation.slice(-10),
        session_id: "demo-seller"
      })
    });

    if (!response.ok) {
      throw new Error("Backend unavailable");
    }

    const data = await response.json();

    addMessage("assistant", data.reply);

    conversation.push({
      role: "assistant",
      content: data.reply
    });

    $("voiceState").textContent =
      data.mode === "gemini"
        ? "AI KAM responded · Gemini"
        : "AI KAM responded · Demo mode";

    speak(data.reply);

    if (data.actions) {
      renderActions(data.actions);
    }

  } catch (error) {
    const fallback =
      "I'm unable to reach the AI service right now. " +
      "Please make sure the Seller360 backend is running, then try again.";

    addMessage("assistant", fallback);

    $("voiceState").textContent = "Connection issue";

    speak(fallback);

  } finally {
    busy = false;
  }
}

// RENDER ACTION CARDS
function renderActions(actions) {
  const list = $("actionList");

  if (!list || !actions?.length) return;

  list.innerHTML = "";

  actions.forEach((action) => {
    const card = document.createElement("article");
    card.className = "action-card";

    const check = document.createElement("div");
    check.className = "action-check";

    const input = document.createElement("input");
    input.type = "checkbox";

    check.appendChild(input);

    const main = document.createElement("div");
    main.className = "action-main";

    const meta = document.createElement("div");
    meta.className = "action-meta";

    const priority = document.createElement("span");

    priority.className =
      `priority ${action.priority === "HIGH" ? "high" : "medium"}`;

    priority.textContent = `${action.priority} PRIORITY`;

    const tag = document.createElement("span");
    tag.textContent = "SELLER GROWTH";

    meta.append(priority, tag);

    const title = document.createElement("h3");
    title.textContent = action.title;

    const detail = document.createElement("p");
    detail.textContent = action.detail;

    const why = document.createElement("small");
    why.textContent = `Why it matters: ${action.why}`;

    main.append(meta, title, detail, why);
    card.append(check, main);

    list.appendChild(card);
  });
}

// SPEECH RECOGNITION SETUP
function setupSpeechRecognition() {
  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    $("voiceNotice").textContent =
      "Speech recognition is not supported in this browser. Use Chrome or Edge, or type in the conversation box.";

    $("micButton").disabled = true;
    $("micButton").style.opacity = ".45";

    return;
  }

  recognition = new SpeechRecognition();

  recognition.lang = "en-IN";
  recognition.continuous = false;
  recognition.interimResults = true;

  recognition.onstart = () => {
    listening = true;

    $("micButton").classList.add("listening");
    $("waveform").classList.add("active");

    $("voiceState").textContent = "Listening... speak now";
    $("micHint").textContent = "I'm listening — speak naturally";
  };

  recognition.onresult = (event) => {
    let finalText = "";
    let interim = "";

    for (let i = event.resultIndex; i < event.results.length; i++) {
      if (event.results[i].isFinal) {
        finalText += event.results[i][0].transcript;
      } else {
        interim += event.results[i][0].transcript;
      }
    }

    if (interim) {
      $("voiceState").textContent = `Hearing: “${interim}”`;
    }

    if (finalText.trim()) {
      stopListening();
      sendMessage(finalText.trim());
    }
  };

  recognition.onerror = (event) => {
    $("voiceState").textContent =
      event.error === "not-allowed"
        ? "Microphone permission denied"
        : `Voice input: ${event.error}`;

    stopListening();
  };

  recognition.onend = () => stopListening();
}

// STOP MICROPHONE
function stopListening() {
  listening = false;

  $("micButton").classList.remove("listening");
  $("waveform").classList.remove("active");

  $("micHint").textContent = "Tap to speak · Tap again to stop";

  try {
    if (recognition) recognition.stop();
  } catch (e) {}
}

// MICROPHONE BUTTON
$("micButton").addEventListener("click", () => {
  if (!recognition) return;

  if (listening) {
    stopListening();
  } else {
    window.speechSynthesis?.cancel();

    try {
      recognition.start();
    } catch (e) {
      $("voiceState").textContent =
        "Please wait a moment and try again";
    }
  }
});

// TEXT CHAT
$("chatForm").addEventListener("submit", (e) => {
  e.preventDefault();

  const input = $("chatInput");

  sendMessage(input.value);

  input.value = "";
});

// SOUND CONTROL
$("muteButton").addEventListener("click", () => {
  soundOn = !soundOn;

  $("muteButton").textContent =
    soundOn ? "◖ Sound on" : "◖ Sound off";

  if (!soundOn) {
    window.speechSynthesis?.cancel();
  }
});

// END CONVERSATION
$("endButton").addEventListener("click", async () => {
  stopListening();

  window.speechSynthesis?.cancel();

  try {
    const res = await fetch(`${API}/summary`);
    const data = await res.json();

    addMessage("assistant", data.summary);

    conversation.push({
      role: "assistant",
      content: data.summary
    });

    $("voiceState").textContent =
      "Conversation summary ready";

    speak(data.summary);

    $("summaryText").textContent = data.summary;
    $("summaryBox").classList.remove("hidden");

  } catch (e) {}
});

// CLEAR CONVERSATION
$("clearChat").addEventListener("click", () => {
  conversation = [];
  greetingPlayed = false;

  window.speechSynthesis?.cancel();

  messagesEl.innerHTML = "";

  const greeting =
    "Welcome back! I'm your Seller360 Virtual KAM. " +
    "What would you like to investigate first — inventory, cancellations, pricing or product visibility?";

  addMessage("assistant", greeting);

  conversation.push({
    role: "assistant",
    content: greeting
  });

  $("voiceState").textContent = "Ready when you are";
});

// SUMMARY BUTTON
$("summaryButton").addEventListener("click", async () => {
  try {
    const res = await fetch(`${API}/summary`);
    const data = await res.json();

    $("summaryText").textContent = data.summary;
    $("summaryBox").classList.remove("hidden");

  } catch (e) {
    $("summaryText").textContent =
      "Could not load summary. Check that the backend is running.";
  }
});

// COPY SUMMARY
$("copySummary").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(
      $("summaryText").textContent
    );

    $("copySummary").textContent = "Copied ✓";

  } catch (e) {
    $("copySummary").textContent = "Select and copy the text";
  }
});

// SWITCH TABS
function switchTab(tab) {
  document.querySelectorAll(".tab-panel").forEach((p) => {
    p.classList.toggle("active", p.id === tab);
  });

  document.querySelectorAll(".nav-item").forEach((b) => {
    b.classList.toggle("active", b.dataset.tab === tab);
  });

  const labels = {
    overview: [
      "OVERVIEW",
      "Good evening, Aarav",
      "Here's what's happening with your business this month."
    ],
    voice: [
      "AI VOICE KAM",
      "Let's talk business, Aarav",
      "A natural conversation with your Virtual Key Account Manager."
    ],
    insights: [
      "BUSINESS INSIGHTS",
      "Here's what the numbers are telling us",
      "Evidence-led signals to help you investigate the sales decline."
    ],
    actions: [
      "ACTION PLANNER",
      "Your next moves, made clearer",
      "A prioritised recovery plan based on your business data."
    ]
  };

  $("crumb").textContent = labels[tab][0];

  $("pageTitle").innerHTML =
    `${labels[tab][1]} <span class="wave">✦</span>`;

  $("pageSub").textContent = labels[tab][2];

  // PLAY GREETING WHEN VOICE TAB OPENS
  if (tab === "voice") {
    playOpeningGreeting();
  }
}

// NAVIGATION EVENTS
document.querySelectorAll(".nav-item").forEach((b) => {
  b.addEventListener("click", () => {
    switchTab(b.dataset.tab);
  });
});

document.querySelectorAll("[data-go]").forEach((b) => {
  b.addEventListener("click", () => {
    switchTab(b.dataset.go);
  });
});

$("sidebarTalk").addEventListener("click", () => {
  switchTab("voice");
});

// LOAD DASHBOARD
async function loadDashboard() {
  try {
    const response = await fetch(`${API}/dashboard`);
    const data = await response.json();

    $("salesValue").textContent =
      `₹${Number(data.metrics.this_month.sales).toLocaleString("en-IN")}`;

    renderActions(data.actions);

  } catch (e) {
    $("voiceState").textContent =
      "Start the backend to connect your seller data";
  }
}

// INITIALIZE
setupSpeechRecognition();
loadDashboard();
