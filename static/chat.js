const messages = document.getElementById("messages");
const form = document.getElementById("chatForm");
const input = document.getElementById("text");

function add(role, text) {
  const div = document.createElement("div");
  div.className = "msg " + role;
  div.textContent = text;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  add("user", text);
  input.value = "";

  const r = await fetch("/api/chat", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ session_id: window.SESSION_ID, message: text })
  });

  const data = await r.json();
  add("bot", data.reply);
});