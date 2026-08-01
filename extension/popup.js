const statusConnected = document.getElementById("status-connected");
const statusDisconnected = document.getElementById("status-disconnected");
const apiUrlDisplay = document.getElementById("api-url-display");
const apiBaseUrlInput = document.getElementById("api-base-url");
const loginForm = document.getElementById("login-form");
const loginError = document.getElementById("login-error");
const signoutBtn = document.getElementById("signout-btn");
const saveUrlBtn = document.getElementById("save-url-btn");
const saveUrlConfirm = document.getElementById("save-url-confirm");

function sendMessage(message) {
  return new Promise((resolve) => chrome.runtime.sendMessage(message, resolve));
}

async function refreshStatus() {
  const { apiBaseUrl, connected } = await sendMessage({ type: "GET_STATUS" });
  apiBaseUrlInput.value = apiBaseUrl;
  apiUrlDisplay.textContent = apiBaseUrl;

  if (connected) {
    statusConnected.classList.remove("hidden");
    statusDisconnected.classList.add("hidden");
  } else {
    statusConnected.classList.add("hidden");
    statusDisconnected.classList.remove("hidden");
  }
}

loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  loginError.classList.add("hidden");
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  const result = await sendMessage({ type: "LOGIN", email, password });
  if (result.ok) {
    await refreshStatus();
  } else {
    loginError.textContent = result.error || "Sign in failed.";
    loginError.classList.remove("hidden");
  }
});

signoutBtn.addEventListener("click", async () => {
  await sendMessage({ type: "LOGOUT" });
  await refreshStatus();
});

saveUrlBtn.addEventListener("click", async () => {
  const value = apiBaseUrlInput.value.trim().replace(/\/$/, "");
  if (!value) return;
  await sendMessage({ type: "SET_API_BASE_URL", apiBaseUrl: value });
  saveUrlConfirm.classList.remove("hidden");
  setTimeout(() => saveUrlConfirm.classList.add("hidden"), 1500);
  await refreshStatus();
});

refreshStatus();
