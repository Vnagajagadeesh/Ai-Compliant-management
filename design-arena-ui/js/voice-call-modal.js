/**
 * SmartCampus AI — Voice Call Interface Modal Component
 * 
 * Redesigns the voice interaction overlay to display a full, premium voice-call interface.
 * Preserves SmartCampus AI design language, accessibility, responsive rules, and security.
 */

class SmartCampusVoiceCallModal {
  constructor() {
    this.service = null;
    this.modalContainer = null;
    this.isOpen = false;
    this.unsubscribeState = null;
    this.unsubscribeTranscript = null;
    this.unsubscribeAudio = null;
    this.unsubscribeError = null;
    this.isMuted = false;
  }

  // Initialize Modal HTML Container and Append to Body
  init() {
    if (document.getElementById('voiceCallModalOverlay')) return;

    const modalMarkup = `
      <div id="voiceCallModalOverlay" class="fixed inset-0 z-[160] hidden flex items-center justify-center p-4 sm:p-6 transition-all duration-300">
        <!-- Backdrop with Blur -->
        <div class="absolute inset-0 bg-slate-950/80 backdrop-blur-md transition-opacity" id="voiceCallBackdrop"></div>

        <!-- Central Modal Card -->
        <div class="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden flex flex-col text-slate-100 max-h-[92vh] sm:max-h-[85vh] z-10 transition-transform duration-300 scale-95" id="voiceCallCard">
          
          <!-- Top Header -->
          <div class="px-6 py-4 border-b border-slate-800/80 flex items-center justify-between bg-slate-900/90 sticky top-0 z-20">
            <div class="flex items-center gap-3">
              <span class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-[11px] font-extrabold tracking-wider uppercase bg-brand-500/10 text-brand-400 border border-brand-500/20" id="voiceHeaderBadge">
                <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" id="voiceStatusDot"></span>
                <span id="voiceHeaderStatusText">VOICE CALL · SMARTCAMPUS AI</span>
              </span>
            </div>
            
            <button id="voiceCloseBtn" class="w-9 h-9 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white flex items-center justify-center transition font-bold text-lg" title="Close Voice Call">
              ✕
            </button>
          </div>

          <!-- Main Call View -->
          <div class="flex-1 overflow-y-auto p-6 flex flex-col items-center justify-between space-y-6">
            
            <!-- Agent Identity & Avatar Area -->
            <div class="flex flex-col items-center text-center mt-2 w-full">
              <div class="relative flex items-center justify-center my-4">
                <!-- Outer Pulsing Rings for Audio Activity -->
                <div id="voicePulseRing2" class="absolute w-36 h-36 rounded-full bg-brand-500/10 transition-all duration-150 scale-100 opacity-50"></div>
                <div id="voicePulseRing1" class="absolute w-28 h-28 rounded-full bg-brand-500/20 transition-all duration-150 scale-100 opacity-70"></div>
                
                <!-- Central Avatar Circle -->
                <div class="relative w-20 h-20 rounded-full grad-bg p-1 shadow-xl flex items-center justify-center z-10">
                  <div class="w-full h-full rounded-full bg-slate-900 flex items-center justify-center overflow-hidden">
                    <svg width="36" height="36" viewBox="0 0 24 24" fill="none" class="text-brand-400">
                      <path d="M12 2C6.48 2 2 6.48 2 12c0 5.52 4.48 10 10 10s10-4.48 10-10c0-5.52-4.48-10-10-10zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z" fill="currentColor" opacity="0.3"/>
                      <path d="M12 6a3 3 0 0 0-3 3v4a3 3 0 0 0 6 0V9a3 3 0 0 0-3-3z" fill="currentColor"/>
                      <path d="M17 11a1 1 0 0 0-2 0 3 3 0 0 1-6 0 1 1 0 0 0-2 0 5 5 0 0 0 4 4.9V18h-2a1 1 0 1 0 0 2h6a1 1 0 1 0 0-2h-2v-2.1A5 5 0 0 0 17 11z" fill="currentColor"/>
                    </svg>
                  </div>
                </div>
              </div>

              <!-- Identity Info -->
              <h3 class="font-display font-bold text-xl text-white tracking-tight" id="voiceAgentName">Sammy</h3>
              <p class="text-xs text-slate-400 font-medium mt-0.5">Campus Support Assistant · SmartCampus AI</p>

              <!-- Real Status Subtitle -->
              <div class="mt-3 px-4 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700/60 text-xs font-semibold text-brand-300 flex items-center gap-2" id="voiceStatusBadge">
                <span class="w-2 h-2 rounded-full bg-brand-400 animate-ping"></span>
                <span id="voiceStatusText">Connecting to SmartCampus AI...</span>
              </div>
            </div>

            <!-- Conversation Transcript Area -->
            <div class="w-full bg-slate-950/60 border border-slate-800 rounded-2xl p-4 flex flex-col h-48 sm:h-56">
              <div class="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between border-b border-slate-800 pb-2">
                <span>Live Transcript</span>
                <span class="text-[10px] text-slate-500 font-normal">Real-time SDK Sync</span>
              </div>
              
              <div id="voiceTranscriptList" class="flex-1 overflow-y-auto space-y-3 pr-1 text-xs font-normal">
                <div class="text-center text-slate-500 py-6 italic text-[11px]">
                  Listening for your request... Speak naturally to ask about complaints, campus departments, or SLA status.
                </div>
              </div>
            </div>

            <!-- Error Notification Banner (Hidden by default) -->
            <div id="voiceErrorBanner" class="hidden w-full bg-rose-500/10 border border-rose-500/30 rounded-xl p-3 text-rose-300 text-xs font-medium flex items-center justify-between">
              <span id="voiceErrorText">Unable to connect to Voice Assistant</span>
              <button id="voiceRetryBtn" class="px-3 py-1 rounded-lg bg-rose-600 text-white font-bold hover:bg-rose-500 transition text-[11px]">
                Retry
              </button>
            </div>

            <!-- Controls Panel -->
            <div class="w-full flex items-center justify-center gap-4 pt-2 border-t border-slate-800/80">
              
              <!-- Mute / Mic Toggle -->
              <button id="voiceMicToggleBtn" class="flex items-center gap-2 px-5 py-3 rounded-2xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 font-semibold text-xs transition shadow-lg disabled:opacity-50" title="Mute / Unmute Microphone">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" id="voiceMicIcon">
                  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                  <line x1="12" y1="19" x2="12" y2="23"/>
                  <line x1="8" y1="23" x2="16" y2="23"/>
                </svg>
                <span id="voiceMicText">Mute</span>
              </button>

              <!-- End Call Main Action -->
              <button id="voiceEndCallBtn" class="flex items-center gap-2 px-7 py-3 rounded-2xl bg-gradient-to-r from-rose-600 to-rose-700 hover:from-rose-500 hover:to-rose-600 text-white font-bold text-xs shadow-lg shadow-rose-900/30 transition transform active:scale-95">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 9c-1.6 0-3.15.25-4.6.72v3.1c0 .39-.23.74-.56.9-.98.49-1.87 1.12-2.66 1.85-.18.18-.43.28-.7.28-.28 0-.53-.11-.71-.29L.29 13.08c-.18-.17-.29-.42-.29-.7 0-.28.11-.53.29-.71C3.34 8.78 7.46 7 12 7s8.66 1.78 11.71 4.67c.18.18.29.43.29.71 0 .28-.11.53-.29.71l-2.48 2.48c-.18.18-.43.29-.71.29-.27 0-.52-.11-.7-.28-.79-.74-1.69-1.36-2.67-1.85-.33-.16-.56-.5-.56-.9v-3.1C15.15 9.25 13.6 9 12 9z"/>
                </svg>
                <span>End Call</span>
              </button>

            </div>

          </div>

        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalMarkup);
    this.modalContainer = document.getElementById('voiceCallModalOverlay');
    this.bindDOMEvents();
  }

  // Bind UI Modal Buttons & Backdrop Handlers
  bindDOMEvents() {
    const backdrop = document.getElementById('voiceCallBackdrop');
    const closeBtn = document.getElementById('voiceCloseBtn');
    const endCallBtn = document.getElementById('voiceEndCallBtn');
    const micToggleBtn = document.getElementById('voiceMicToggleBtn');
    const retryBtn = document.getElementById('voiceRetryBtn');

    backdrop.addEventListener('click', () => this.close());
    closeBtn.addEventListener('click', () => this.close());
    endCallBtn.addEventListener('click', () => this.endCall());
    
    micToggleBtn.addEventListener('click', () => {
      if (this.service) {
        this.isMuted = this.service.toggleMute();
        this.updateMicUI();
      }
    });

    retryBtn.addEventListener('click', () => {
      document.getElementById('voiceErrorBanner').classList.add('hidden');
      if (this.service) {
        this.service.startSession();
      }
    });

    // Keyboard ESC binding
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen) {
        this.close();
      }
    });
  }

  // Update Microphone Button Text & Icon
  updateMicUI() {
    const micText = document.getElementById('voiceMicText');
    const micIcon = document.getElementById('voiceMicIcon');
    const micBtn = document.getElementById('voiceMicToggleBtn');

    if (this.isMuted) {
      micText.textContent = "Unmute";
      micBtn.classList.remove('bg-slate-800', 'text-slate-200');
      micBtn.classList.add('bg-amber-500/20', 'text-amber-400', 'border-amber-500/40');
      micIcon.innerHTML = `<line x1="1" y1="1" x2="23" y2="23"/><path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6"/>`;
    } else {
      micText.textContent = "Mute";
      micBtn.classList.remove('bg-amber-500/20', 'text-amber-400', 'border-amber-500/40');
      micBtn.classList.add('bg-slate-800', 'text-slate-200');
      micIcon.innerHTML = `<path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/>`;
    }
  }

  // Open Modal and Start Real Voice Session
  open() {
    this.init();
    this.isOpen = true;

    const overlay = document.getElementById('voiceCallModalOverlay');
    const card = document.getElementById('voiceCallCard');
    
    overlay.classList.remove('hidden');
    requestAnimationFrame(() => {
      card.classList.remove('scale-95');
      card.classList.add('scale-100');
    });

    // Reset UI state
    document.getElementById('voiceErrorBanner').classList.add('hidden');
    document.getElementById('voiceTranscriptList').innerHTML = `
      <div class="text-center text-slate-500 py-6 italic text-[11px]">
        Listening for your request... Speak naturally to ask about complaints, campus departments, or SLA status.
      </div>
    `;

    // Instantiate or reuse Voice Service
    if (!this.service) {
      this.service = new window.SmartCampusVoiceAgentService();
    }

    // Unsubscribe previous listeners if any
    if (this.unsubscribeState) this.unsubscribeState();
    if (this.unsubscribeTranscript) this.unsubscribeTranscript();
    if (this.unsubscribeAudio) this.unsubscribeAudio();
    if (this.unsubscribeError) this.unsubscribeError();

    // Subscribe to Service Events
    this.unsubscribeState = this.service.on('stateChange', (state, detail) => this.handleStateChange(state, detail));
    this.unsubscribeTranscript = this.service.on('transcriptUpdate', (transcripts) => this.renderTranscripts(transcripts));
    this.unsubscribeAudio = this.service.on('audioLevel', (level) => this.updateAudioVisualizer(level));
    this.unsubscribeError = this.service.on('error', (err) => this.handleError(err));

    // Start Session
    this.service.startSession();
  }

  // Handle State Machine Transitions in UI
  handleStateChange(state, detail) {
    const statusText = document.getElementById('voiceStatusText');
    const statusDot = document.getElementById('voiceStatusDot');
    const headerStatusText = document.getElementById('voiceHeaderStatusText');

    switch (state) {
      case "connecting":
        statusText.textContent = "Connecting to SmartCampus AI...";
        statusDot.className = "w-2 h-2 rounded-full bg-amber-400 animate-ping";
        headerStatusText.textContent = "CONNECTING · SMARTCAMPUS AI";
        break;

      case "connected":
      case "listening":
        statusText.textContent = "Listening... Speak now";
        statusDot.className = "w-2 h-2 rounded-full bg-emerald-400 animate-pulse";
        headerStatusText.textContent = "CONNECTED · SMARTCAMPUS AI";
        break;

      case "speaking":
        statusText.textContent = `${this.service.agentName} is speaking...`;
        statusDot.className = "w-2 h-2 rounded-full bg-brand-400 animate-pulse";
        headerStatusText.textContent = "AGENT SPEAKING · SMARTCAMPUS AI";
        break;

      case "processing":
        statusText.textContent = "Thinking...";
        statusDot.className = "w-2 h-2 rounded-full bg-violet-400 animate-bounce";
        headerStatusText.textContent = "PROCESSING · SMARTCAMPUS AI";
        break;

      case "permission_denied":
        statusText.textContent = "Microphone access denied.";
        statusDot.className = "w-2 h-2 rounded-full bg-rose-500";
        this.handleError("Microphone access is required for voice conversations. Please grant microphone permission in your browser.");
        break;

      case "connection_error":
        statusText.textContent = "Unable to connect";
        statusDot.className = "w-2 h-2 rounded-full bg-rose-500";
        this.handleError(detail || "We couldn't connect to the voice assistant. Check network connection.");
        break;

      case "disconnected":
        statusText.textContent = "Call ended";
        statusDot.className = "w-2 h-2 rounded-full bg-slate-500";
        headerStatusText.textContent = "CALL ENDED · SMARTCAMPUS AI";
        this.updateAudioVisualizer(0);
        break;

      default:
        break;
    }
  }

  // Render Real Transcripts Received from SDK
  renderTranscripts(transcripts) {
    const list = document.getElementById('voiceTranscriptList');
    if (!transcripts || transcripts.length === 0) return;

    list.innerHTML = transcripts.map(t => {
      const isUser = t.sender === "user";
      return `
        <div class="flex gap-2.5 ${isUser ? 'justify-end' : 'justify-start'}">
          ${!isUser ? `<div class="w-6 h-6 rounded-full grad-bg text-[10px] font-bold text-white flex items-center justify-center shrink-0">AI</div>` : ''}
          <div class="max-w-[80%] rounded-2xl px-3.5 py-2 leading-relaxed ${isUser ? 'bg-brand-600 text-white rounded-br-none' : 'bg-slate-800 text-slate-200 border border-slate-700/80 rounded-bl-none'}">
            <div class="text-[11.5px] font-medium">${t.text}</div>
            <div class="text-[9px] ${isUser ? 'text-brand-200' : 'text-slate-400'} font-semibold mt-1 text-right">${t.time || ''}</div>
          </div>
          ${isUser ? `<div class="w-6 h-6 rounded-full bg-slate-700 text-[10px] font-bold text-white flex items-center justify-center shrink-0">You</div>` : ''}
        </div>
      `;
    }).join('');

    list.scrollTop = list.scrollHeight;
  }

  // Animate Outer Avatar Rings Based on Live WebAudio Level
  updateAudioVisualizer(level) {
    const ring1 = document.getElementById('voicePulseRing1');
    const ring2 = document.getElementById('voicePulseRing2');
    if (!ring1 || !ring2) return;

    const scale1 = 1 + (level / 100) * 0.45;
    const scale2 = 1 + (level / 100) * 0.85;

    ring1.style.transform = `scale(${scale1})`;
    ring2.style.transform = `scale(${scale2})`;
  }

  // Handle and Display Errors
  handleError(errMsg) {
    const errorBanner = document.getElementById('voiceErrorBanner');
    const errorText = document.getElementById('voiceErrorText');
    if (errorBanner && errorText) {
      errorText.textContent = typeof errMsg === 'string' ? errMsg : "An unexpected error occurred.";
      errorBanner.classList.remove('hidden');
    }
  }

  // End Active Call
  endCall() {
    if (this.service) {
      this.service.disconnect();
    }
  }

  // Close Modal and Ensure Session Cleanup
  close() {
    if (!this.isOpen) return;

    this.endCall();

    const overlay = document.getElementById('voiceCallModalOverlay');
    const card = document.getElementById('voiceCallCard');

    card.classList.remove('scale-100');
    card.classList.add('scale-95');
    
    setTimeout(() => {
      overlay.classList.add('hidden');
      this.isOpen = false;
    }, 200);
  }
}

// Instantiate global modal instance
window.SmartCampusVoiceCallModal = new SmartCampusVoiceCallModal();

// Public helper launcher
window.openVoiceAssistant = function() {
  window.SmartCampusVoiceCallModal.open();
};
