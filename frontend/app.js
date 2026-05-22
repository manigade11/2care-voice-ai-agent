const elements = {
  apiBaseUrl: document.getElementById("apiBaseUrl"),
  wsUrl: document.getElementById("wsUrl"),
  sessionId: document.getElementById("sessionId"),

  apiHealthValue: document.getElementById("apiHealthValue"),
  apiHealthHint: document.getElementById("apiHealthHint"),
  wsStatusValue: document.getElementById("wsStatusValue"),
  wsStatusHint: document.getElementById("wsStatusHint"),
  latencyValue: document.getElementById("latencyValue"),
  latencyHint: document.getElementById("latencyHint"),
  lastAppointmentValue: document.getElementById("lastAppointmentValue"),
  lastAppointmentHint: document.getElementById("lastAppointmentHint"),

  refreshStatusBtn: document.getElementById("refreshStatusBtn"),
  connectWsBtn: document.getElementById("connectWsBtn"),
  disconnectWsBtn: document.getElementById("disconnectWsBtn"),
  themeToggle: document.getElementById("themeToggle"),

  bookForm: document.getElementById("bookForm"),
  rescheduleForm: document.getElementById("rescheduleForm"),
  cancelForm: document.getElementById("cancelForm"),
  bookPatientId: document.getElementById("bookPatientId"),
  bookDoctorId: document.getElementById("bookDoctorId"),
  bookDate: document.getElementById("bookDate"),
  bookTime: document.getElementById("bookTime"),
  bookLanguage: document.getElementById("bookLanguage"),

  rescheduleAppointmentId: document.getElementById("rescheduleAppointmentId"),
  rescheduleDate: document.getElementById("rescheduleDate"),
  rescheduleTime: document.getElementById("rescheduleTime"),

  cancelAppointmentId: document.getElementById("cancelAppointmentId"),

  agentMessageForm: document.getElementById("agentMessageForm"),
  agentMessageInput: document.getElementById("agentMessageInput"),
  clearConversationBtn: document.getElementById("clearConversationBtn"),
  conversationLog: document.getElementById("conversationLog"),
  systemLog: document.getElementById("systemLog"),
  apiResponseViewer: document.getElementById("apiResponseViewer"),
  liveWsBadge: document.getElementById("liveWsBadge"),

  // VOICE CONTROLS
  startRecordBtn: document.getElementById("startRecordBtn"),
  stopRecordBtn: document.getElementById("stopRecordBtn"),
  recordingWave: document.getElementById("recordingWave"),
  audioPlayer: document.getElementById("audioPlayer"),

  // LATENCY BARS
  sttBar: document.getElementById("sttBar"),
  sttTime: document.getElementById("sttTime"),
  langBar: document.getElementById("langBar"),
  langTime: document.getElementById("langTime"),
  agentBar: document.getElementById("agentBar"),
  agentTime: document.getElementById("agentTime"),
  ttsBarChart: document.getElementById("ttsBarChart"),
  ttsTime: document.getElementById("ttsTime"),
  totalBar: document.getElementById("totalBar"),
  totalTime: document.getElementById("totalTime"),

  // CAMPAIGN
  campaignPatientId: document.getElementById("campaignPatientId"),
  triggerCampaignBtn: document.getElementById("triggerCampaignBtn"),

  // SCHEDULES TABLE
  appointmentsTableBody: document.getElementById("appointmentsTableBody"),
};

let socket = null;
let mediaRecorder = null;
let audioChunks = [];
let currentTheme = "dark";
document.documentElement.setAttribute("data-theme", currentTheme);

setDefaultDates();
initializeLogs();
bindEvents();
checkHealth();
loadAppointmentsTable();

function setDefaultDates() {
  const today = new Date();
  const tomorrow = new Date(today);
  tomorrow.setDate(today.getDate() + 1);

  const yyyy = tomorrow.getFullYear();
  const mm = String(tomorrow.getMonth() + 1).padStart(2, "0");
  const dd = String(tomorrow.getDate()).padStart(2, "0");
  const defaultDate = `${yyyy}-${mm}-${dd}`;

  elements.bookDate.value = defaultDate;
  elements.rescheduleDate.value = defaultDate;
}

function initializeLogs() {
  elements.conversationLog.innerHTML = `<p class="empty-state-note">No conversation yet. Speak or type to start.</p>`;
  elements.systemLog.innerHTML = `<p class="empty-state-note">No transaction payloads yet.</p>`;
}

function bindEvents() {
  elements.refreshStatusBtn.addEventListener("click", () => {
    checkHealth();
    loadAppointmentsTable();
  });
  elements.connectWsBtn.addEventListener("click", connectWebSocket);
  elements.disconnectWsBtn.addEventListener("click", disconnectWebSocket);
  elements.themeToggle.addEventListener("click", toggleTheme);

  elements.bookForm.addEventListener("submit", handleBook);
  elements.rescheduleForm.addEventListener("submit", handleReschedule);
  elements.cancelForm.addEventListener("submit", handleCancel);

  elements.agentMessageForm.addEventListener("submit", handleSendAgentMessage);
  elements.clearConversationBtn.addEventListener("click", clearConversationLog);

  // MICROPHONE EVENTS
  elements.startRecordBtn.addEventListener("click", startRecording);
  elements.stopRecordBtn.addEventListener("click", stopRecording);

  // CAMPAIGN EVENTS
  elements.triggerCampaignBtn.addEventListener("click", triggerCampaignCall);
}

function toggleTheme() {
  currentTheme = currentTheme === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", currentTheme);
}

function getApiBase() {
  return elements.apiBaseUrl.value.trim().replace(/\/$/, "");
}

function getWsUrl() {
  return elements.wsUrl.value.trim();
}

function getSessionId() {
  return elements.sessionId.value.trim() || "demo-session-001";
}

function getPatientId() {
  // Use selected patient from booking form as current context
  return elements.bookPatientId.value;
}

async function checkHealth() {
  try {
    const response = await fetch(`${getApiBase()}/health`);
    const data = await response.json();

    elements.apiHealthValue.textContent = data.status || "Running";
    elements.apiHealthHint.textContent = "FastAPI backend active";
    appendSystemLog("REST API Health Check", data, "success");
    showApiResponse(data);
  } catch (error) {
    elements.apiHealthValue.textContent = "Offline";
    elements.apiHealthHint.textContent = "Check terminal logs";
    appendSystemLog("REST API Health Failed", { error: error.message }, "error");
  }
}

async function loadAppointmentsTable() {
  try {
    const response = await fetch(`${getApiBase()}/appointments`);
    const data = await response.json();
    
    if (data.success && data.appointments) {
      if (data.appointments.length === 0) {
        elements.appointmentsTableBody.innerHTML = `
          <tr>
            <td colspan="7" class="empty-state-note" style="text-align: center;">No active appointments in DB.</td>
          </tr>
        `;
        return;
      }
      
      elements.appointmentsTableBody.innerHTML = data.appointments
        .map(apt => {
          const statusClass = apt.status === "booked" ? "chip-success" : "chip-neutral";
          return `
            <tr>
              <td style="font-family: monospace; font-size: 10px;">${apt.appointment_id.substring(0, 8)}...</td>
              <td><strong>${apt.patient_id}</strong></td>
              <td>${apt.doctor_id}</td>
              <td>${apt.date}</td>
              <td><strong>${apt.time}</strong></td>
              <td><span class="chip chip-neutral">${apt.language}</span></td>
              <td><span class="chip ${statusClass}">${apt.status}</span></td>
            </tr>
          `;
        })
        .join("");
    }
  } catch (error) {
    console.error("Failed to load appointments:", error);
  }
}

function connectWebSocket() {
  if (socket && socket.readyState === WebSocket.OPEN) {
    appendSystemLog("WebSocket connection is already alive", {}, "info");
    return;
  }

  appendSystemLog("Initiating WebSocket connection...", { url: getWsUrl() }, "info");
  socket = new WebSocket(getWsUrl());

  socket.onopen = () => {
    elements.wsStatusValue.textContent = "Connected";
    elements.wsStatusHint.textContent = "Voice Agent active";
    elements.liveWsBadge.textContent = "Online";
    elements.liveWsBadge.className = "chip chip-success";
    appendSystemLog("WebSocket Connected", { ws_url: getWsUrl() }, "success");
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      appendSystemLog("WebSocket Turn Response", data, "success");
      showApiResponse(data);

      // Play synthesized agent voice if present
      if (data.audio) {
        playAgentVoice(data.audio);
      }

      // Append speech turn bubbles
      if (data.transcription) {
        appendConversationLog("You", data.transcription, data.detected_language);
      }
      if (data.reply_text) {
        appendConversationLog("2Care Voice Agent", data.reply_text, data.detected_language);
      }

      // Sync metrics
      if (data.latency_ms !== undefined) {
        elements.latencyValue.textContent = `${data.latency_ms} ms`;
        elements.latencyHint.textContent = `Turn roundtrip processing`;
      }

      if (data.latency_breakdown) {
        renderLatencyChart(data.latency_breakdown);
      }

      if (data.appointment && data.appointment.appointment_id) {
        syncAppointmentIdAcrossForms(data.appointment.appointment_id);
        updateLastAppointment(data.appointment.appointment_id, data.appointment.status || "booked");
      }
      
      // Auto refresh table schedules
      loadAppointmentsTable();
      
    } catch (error) {
      console.error("Error processing websocket frame:", error);
      appendSystemLog("Frame parsing error", { raw: event.data }, "error");
    }
  };

  socket.onerror = (err) => {
    appendSystemLog("WebSocket connection error", {}, "error");
    console.error("WebSocket error:", err);
  };

  socket.onclose = (event) => {
    elements.wsStatusValue.textContent = "Disconnected";
    elements.wsStatusHint.textContent = `Code ${event.code}`;
    elements.liveWsBadge.textContent = "Offline";
    elements.liveWsBadge.className = "chip chip-neutral";
    appendSystemLog("WebSocket Closed", { code: event.code, reason: event.reason }, "info");
    socket = null;
  };
}

function disconnectWebSocket() {
  if (socket) {
    socket.close();
  }
}

function playAgentVoice(base64Audio) {
  try {
    const audioDataUrl = `data:audio/mp3;base64,${base64Audio}`;
    elements.audioPlayer.src = audioDataUrl;
    elements.audioPlayer.play().catch(e => {
      console.warn("Auto-play blocked or audio failed:", e);
      appendSystemLog("Audio Player Blocked", { hint: "Interact with the page first to allow sounds." }, "info");
    });
  } catch (err) {
    console.error("Failed to play audio:", err);
  }
}

function renderLatencyChart(breakdown) {
  const stt = breakdown.stt_ms || 0;
  const lang = breakdown.lang_detect_ms || 0;
  const agent = breakdown.agent_ms || 0;
  const tts = breakdown.tts_ms || 0;
  const total = breakdown.total_ms || 1;

  // Render widths proportional to a logical max budget (800ms)
  const maxScale = Math.max(total, 800);
  
  elements.sttBar.style.width = `${(stt / maxScale) * 100}%`;
  elements.sttTime.textContent = `${stt} ms`;

  elements.langBar.style.width = `${(lang / maxScale) * 100}%`;
  elements.langTime.textContent = `${lang} ms`;

  elements.agentBar.style.width = `${(agent / maxScale) * 100}%`;
  elements.agentTime.textContent = `${agent} ms`;

  elements.ttsBarChart.style.width = `${(tts / maxScale) * 100}%`;
  elements.ttsTime.textContent = `${tts} ms`;

  elements.totalBar.style.width = `${(total / maxScale) * 100}%`;
  elements.totalTime.textContent = `${total} ms`;
  
  // Highlight target latency achievement
  if (total < 450) {
    elements.totalBar.style.backgroundColor = "var(--color-success)";
  } else {
    elements.totalBar.style.backgroundColor = "var(--total-color)";
  }
}

// REST OPERATIONS
async function handleBook(event) {
  event.preventDefault();

  const payload = {
    patient_id: elements.bookPatientId.value,
    doctor_id: elements.bookDoctorId.value,
    date: elements.bookDate.value,
    time: elements.bookTime.value,
    language: elements.bookLanguage.value,
  };

  const data = await postJson("/appointments/book", payload, "REST Appointment Booking");

  if (data && data.appointment && data.appointment.appointment_id) {
    const appointmentId = data.appointment.appointment_id;
    syncAppointmentIdAcrossForms(appointmentId);
    updateLastAppointment(appointmentId, data.appointment.status || "booked");
  }
  loadAppointmentsTable();
}

async function handleReschedule(event) {
  event.preventDefault();

  const payload = {
    appointment_id: elements.rescheduleAppointmentId.value.trim(),
    new_date: elements.rescheduleDate.value,
    new_time: elements.rescheduleTime.value,
  };

  const data = await postJson("/appointments/reschedule", payload, "REST Appointment Reschedule");

  if (data && data.appointment && data.appointment.appointment_id) {
    updateLastAppointment(data.appointment.appointment_id, data.appointment.status || "booked");
  }
  loadAppointmentsTable();
}

async function handleCancel(event) {
  event.preventDefault();

  const payload = {
    appointment_id: elements.cancelAppointmentId.value.trim(),
  };

  const data = await postJson("/appointments/cancel", payload, "REST Appointment Cancellation");

  if (data && data.appointment && data.appointment.appointment_id) {
    updateLastAppointment(data.appointment.appointment_id, data.appointment.status || "cancelled");
  }
  loadAppointmentsTable();
}

// WebSocket Send text query
function handleSendAgentMessage(event) {
  event.preventDefault();

  const text = elements.agentMessageInput.value.trim();
  if (!text) {
    appendSystemLog("Validation failed", "Input text query is empty", "error");
    return;
  }

  if (!socket || socket.readyState !== WebSocket.OPEN) {
    appendSystemLog("Gateway offline", "Connect WebSocket Gateway first.", "error");
    return;
  }

  const payload = {
    session_id: getSessionId(),
    patient_id: getPatientId(),
    text,
  };

  socket.send(JSON.stringify(payload));
  // Optimistically log user speech bubble
  appendConversationLog("You (Text Input)", text);
  elements.agentMessageInput.value = "";
}

// OUTBOUND REMINDER CAMPAIGN
async function triggerCampaignCall() {
  const patientId = elements.campaignPatientId.value;
  const sessionId = getSessionId(); // Reuse configure session

  appendSystemLog("Initiating Proactive Outbound Call Campaign", { patient_id: patientId }, "info");
  
  const payload = {
    patient_id: patientId,
    session_id: sessionId
  };

  try {
    const response = await fetch(`${getApiBase()}/appointments/campaign/trigger`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    showApiResponse(data);

    if (data.success) {
      appendSystemLog("Proactive Outbound Call Launched", data, "success");
      
      // Auto-connect gateway if disconnected
      if (!socket || socket.readyState !== WebSocket.OPEN) {
        connectWebSocket();
      }
      
      // Give connection a tiny window to establish, then inject speech turn
      setTimeout(() => {
        // Clear log and prep campaign view
        elements.conversationLog.innerHTML = "";
        
        // Log Agent's outbound speech turn bubble
        appendConversationLog("2Care Voice Agent (Outbound Dial)", data.injected_text, "hi");
        
        // Synthesize agent greeting if supported
        // In fallback mode, we can show it verbally
        // If a real API key is ready later, backend pre-loads it.
        // Alert user
        const alertMsg = `Simulating campaign call... Agent speaks: "${data.injected_text}"`;
        console.log(alertMsg);
      }, 800);
      
    } else {
      appendSystemLog("Campaign trigger failed", data, "error");
    }
  } catch (error) {
    appendSystemLog("Campaign Dial Failed", { error: error.message }, "error");
  }
}

// MICROPHONE RECORDING (SPEECH CAPTURE)
async function startRecording() {
  audioChunks = [];
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    appendSystemLog("Hardware block", "Browser does not support audio recording.", "error");
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.push(event.data);
      }
    };

    mediaRecorder.onstop = async () => {
      // Create audio blob
      const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
      
      // Read audio blob as Base64 encoded string
      const reader = new FileReader();
      reader.readAsDataURL(audioBlob);
      reader.onloadend = () => {
        const base64DataUrl = reader.result;
        // Strip data header to get raw base64 string
        const base64Payload = base64DataUrl.split(",")[1];
        
        // Transmit speech via WebSocket
        transmitSpeechAudio(base64Payload);
      };
      
      // Stop microphone stream tracks to release device
      stream.getTracks().forEach(track => track.stop());
    };

    mediaRecorder.start();
    
    // Toggle recording UI state
    elements.startRecordBtn.style.display = "none";
    elements.stopRecordBtn.style.display = "inline-flex";
    elements.recordingWave.style.display = "flex";
    
    appendSystemLog("Microphone Active", "Recording speech audio...", "info");
    
  } catch (err) {
    appendSystemLog("Hardware permissions refused", { error: err.message }, "error");
    console.error("Recording start failed:", err);
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
  }
  
  // Restore recording UI state
  elements.startRecordBtn.style.display = "inline-flex";
  elements.stopRecordBtn.style.display = "none";
  elements.recordingWave.style.display = "none";
}

function transmitSpeechAudio(base64Audio) {
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    appendSystemLog("Speech transmission blocked", "Connect WebSocket Gateway first.", "error");
    return;
  }

  const payload = {
    session_id: getSessionId(),
    patient_id: getPatientId(),
    audio: base64Audio,
    text: "" // direct STT synthesis
  };

  socket.send(JSON.stringify(payload));
  appendSystemLog("Speech Transmitting", { size_bytes: base64Audio.length }, "info");
  
  // Optimistic UI loading bubble
  appendConversationLog("You (Speech captured)", "Transcribing vocal input...");
}

// UTILITY FUNCTIONS
async function postJson(path, payload, successLabel) {
  try {
    const response = await fetch(`${getApiBase()}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    showApiResponse(data);

    if (data.success) {
      appendSystemLog(successLabel, data, "success");
    } else {
      appendSystemLog(`${successLabel} Failed`, data, "error");
    }

    return data;
  } catch (error) {
    appendSystemLog("Transaction Request Failed", { error: error.message, path }, "error");
    return null;
  }
}

function appendConversationLog(title, message, lang = "en") {
  if (elements.conversationLog.querySelector(".empty-state-note")) {
    elements.conversationLog.innerHTML = "";
  }

  const entry = document.createElement("div");
  entry.className = "log-entry";
  
  // Style user vs agent bubbles differently
  const isAgent = title.includes("Agent");
  const avatar = isAgent ? "🤖" : "👤";
  const bgStyle = isAgent 
    ? "background: rgba(16, 185, 129, 0.05); border-left: 4px solid var(--color-primary);" 
    : "background: rgba(255, 255, 255, 0.01); border-left: 4px solid var(--color-text-muted);";

  entry.setAttribute("style", bgStyle);
  entry.innerHTML = `
    <strong>${avatar} ${escapeHtml(title)} <span class="chip chip-neutral" style="font-size:8px; padding:1px 4px; min-height:16px;">${lang}</span></strong>
    <p style="font-size: var(--text-sm); line-height: 1.4; margin-top: 4px;">${escapeHtml(message)}</p>
  `;
  
  elements.conversationLog.prepend(entry);
}

function appendSystemLog(title, data = {}, type = "info") {
  if (elements.systemLog.querySelector(".empty-state-note")) {
    elements.systemLog.innerHTML = "";
  }

  const entry = document.createElement("div");
  entry.className = "log-entry";
  
  let chipClass = "chip-neutral";
  if (type === "success") chipClass = "chip-success";
  if (type === "error") chipClass = "chip-warning";

  const summary = typeof data === "object" ? JSON.stringify(data) : String(data);

  entry.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center;">
      <strong>${escapeHtml(title)}</strong>
      <span class="chip ${chipClass}">${type}</span>
    </div>
    <p style="font-family: monospace; font-size:10px; opacity:0.8; margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(summary)}</p>
  `;
  elements.systemLog.prepend(entry);
}

function showApiResponse(data) {
  elements.apiResponseViewer.textContent = JSON.stringify(data, null, 2);
}

function syncAppointmentIdAcrossForms(appointmentId) {
  elements.rescheduleAppointmentId.value = appointmentId;
  elements.cancelAppointmentId.value = appointmentId;
}

function updateLastAppointment(appointmentId, status) {
  elements.lastAppointmentValue.textContent = appointmentId.substring(0, 18) + "...";
  elements.lastAppointmentHint.textContent = `Status: ${status.toUpperCase()}`;
}

function clearConversationLog() {
  elements.conversationLog.innerHTML = `<p class="empty-state-note">No conversation yet. Speak or type to start.</p>`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}