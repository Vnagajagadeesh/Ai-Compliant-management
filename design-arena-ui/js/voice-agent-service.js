/**
 * SmartCampus AI — Voice Agent Service Layer
 * 
 * Manages natural voice conversation lifecycle using Voice Agent ID: -P2vKX2Tc3Zk_oW6XcnI / P2YJQU8i3wOC75sAJ3f
 * 
 * Features:
 * - Real state machine (idle, connecting, connected, listening, speaking, processing, disconnecting, disconnected, permission_denied, connection_error)
 * - Microphone permission request and WebAudio AnalyserNode integration for real audio visualizer level computation
 * - ElevenLabs Conversational AI WebSocket/WebRTC connection lifecycle & event listeners
 * - Real-time transcript tracking and listener callbacks
 * - Clean audio context and media stream resource teardown
 */

class SmartCampusVoiceAgentService {
  constructor(config = {}) {
    // Configured Voice Agent IDs
    this.primaryAgentId = config.agentId || "-P2vKX2Tc3Zk_oW6XcnI";
    this.fallbackAgentId = config.fallbackAgentId || "P2YJQU8i3wOC75sAJ3f";
    this.agentName = config.agentName || "Sammy";

    // Session State
    this.state = "idle"; // idle, connecting, connected, listening, speaking, processing, disconnecting, disconnected, permission_denied, connection_error, unsupported
    this.isMuted = false;

    // WebAudio & Microphone
    this.audioContext = null;
    this.mediaStream = null;
    this.analyser = null;
    this.audioLevel = 0;
    this.animationFrameId = null;

    // WebSocket / Connection
    this.socket = null;
    this.transcripts = [];

    // Event Listeners
    this.listeners = {
      stateChange: [],
      transcriptUpdate: [],
      audioLevel: [],
      error: []
    };
  }

  // Subscribe to service events
  on(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event].push(callback);
    }
    return () => this.off(event, callback);
  }

  off(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }
  }

  setState(newState, detail = null) {
    console.log(`[SmartCampus VoiceAgent] State: ${this.state} -> ${newState}`, detail || '');
    this.state = newState;
    this.listeners.stateChange.forEach(cb => cb(newState, detail));
  }

  emitTranscript(message) {
    this.transcripts.push(message);
    this.listeners.transcriptUpdate.forEach(cb => cb([...this.transcripts], message));
  }

  emitError(error) {
    console.error("[SmartCampus VoiceAgent Error]", error);
    this.listeners.error.forEach(cb => cb(error));
  }

  // Request Microphone Access & Initialize WebAudio Analyser
  async requestMicrophone() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      this.setState("unsupported", "Browser does not support microphone input");
      throw new Error("Browser does not support mediaDevices API.");
    }

    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      // Initialize WebAudio context for live frequency analysis
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.audioContext = new AudioCtx();
        if (this.audioContext.state === "suspended") {
          await this.audioContext.resume();
        }
        const source = this.audioContext.createMediaStreamSource(this.mediaStream);
        this.analyser = this.audioContext.createAnalyser();
        this.analyser.fftSize = 64;
        source.connect(this.analyser);
        this.startAudioAnalyzer();
      }

      return true;
    } catch (err) {
      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        this.setState("permission_denied", "Microphone access denied by user.");
      } else {
        this.setState("connection_error", err.message || "Failed to access microphone");
      }
      throw err;
    }
  }

  // Start real-time audio volume level computation
  startAudioAnalyzer() {
    if (!this.analyser) return;

    const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
    const updateLevel = () => {
      if (this.state === "disconnected" || !this.analyser) return;

      this.analyser.getByteFrequencyData(dataArray);
      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) {
        sum += dataArray[i];
      }
      const average = sum / dataArray.length;
      // Normalize to 0 - 100
      this.audioLevel = Math.min(100, Math.round((average / 255) * 100 * 2.5));

      this.listeners.audioLevel.forEach(cb => cb(this.audioLevel));
      this.animationFrameId = requestAnimationFrame(updateLevel);
    };

    updateLevel();
  }

  // Connect to ElevenLabs Conversational AI Agent
  async startSession() {
    if (this.state === "connecting" || this.state === "connected") return;

    this.setState("connecting");

    try {
      // Step 1: Ensure Microphone Access
      await this.requestMicrophone();

      // Step 2: Establish ElevenLabs Conversational AI Connection
      const agentId = this.primaryAgentId;
      const wsUrl = `wss://api.elevenlabs.io/v1/convai/conversation?agent_id=${encodeURIComponent(agentId)}`;

      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = () => {
        console.log("[SmartCampus VoiceAgent] Connected to ElevenLabs Agent", agentId);
        this.setState("connected");
        this.setState("listening");

        // Send initial connection handshake if required
        const handshake = {
          type: "conversation_initiation_client_data",
          conversation_config_override: {
            agent: {
              prompt: {
                prompt: "You are Sammy, the SmartCampus AI voice support assistant for university students and staff."
              }
            }
          }
        };
        this.socket.send(JSON.stringify(handshake));
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleServerEvent(data);
        } catch (e) {
          console.warn("[SmartCampus VoiceAgent] Received raw audio/text frame:", event.data);
        }
      };

      this.socket.onerror = (err) => {
        console.error("[SmartCampus VoiceAgent] WebSocket error:", err);
        // Fallback retry with secondary agent ID if primary fails
        if (agentId === this.primaryAgentId && this.fallbackAgentId) {
          console.log("[SmartCampus VoiceAgent] Retrying with secondary agent ID:", this.fallbackAgentId);
          this.retryWithFallback();
        } else {
          this.setState("connection_error", "Failed to establish agent socket connection.");
        }
      };

      this.socket.onclose = (event) => {
        console.log("[SmartCampus VoiceAgent] Socket closed:", event.code, event.reason);
        if (this.state !== "disconnected") {
          this.setState("disconnected", "Session closed by server or user");
        }
      };

    } catch (err) {
      console.error("[SmartCampus VoiceAgent] Session initialization failed:", err);
      if (this.state !== "permission_denied" && this.state !== "unsupported") {
        this.setState("connection_error", err.message || "Initialization failed");
      }
    }
  }

  retryWithFallback() {
    if (this.socket) {
      try { this.socket.close(); } catch(e){}
    }
    const wsUrl = `wss://api.elevenlabs.io/v1/convai/conversation?agent_id=${encodeURIComponent(this.fallbackAgentId)}`;
    this.socket = new WebSocket(wsUrl);
    this.socket.onopen = () => {
      this.setState("connected");
      this.setState("listening");
    };
    this.socket.onmessage = (event) => {
      try { this.handleServerEvent(JSON.parse(event.data)); } catch(e){}
    };
    this.socket.onerror = () => {
      this.setState("connection_error", "Unable to connect to Voice Assistant server.");
    };
    this.socket.onclose = () => {
      if (this.state !== "disconnected") this.setState("disconnected");
    };
  }

  // Handle incoming server events from ElevenLabs SDK / WebSocket
  handleServerEvent(data) {
    if (!data) return;

    switch (data.type) {
      case "conversation_initiation_metadata":
        this.setState("connected");
        break;

      case "user_transcript":
        if (data.user_transcript_event?.user_transcript) {
          const text = data.user_transcript_event.user_transcript.trim();
          if (text) {
            this.setState("processing");
            this.emitTranscript({
              sender: "user",
              text: text,
              time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            });
          }
        }
        break;

      case "agent_response":
        if (data.agent_response_event?.agent_response) {
          const text = data.agent_response_event.agent_response.trim();
          if (text) {
            this.setState("speaking");
            this.emitTranscript({
              sender: "assistant",
              text: text,
              time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            });
          }
        }
        break;

      case "agent_response_correction":
        // Real-time transcript correction
        if (data.agent_response_correction_event?.corrected_agent_response) {
          const text = data.agent_response_correction_event.corrected_agent_response;
          if (this.transcripts.length > 0 && this.transcripts[this.transcripts.length - 1].sender === "assistant") {
            this.transcripts[this.transcripts.length - 1].text = text;
            this.listeners.transcriptUpdate.forEach(cb => cb([...this.transcripts]));
          }
        }
        break;

      case "audio":
        this.setState("speaking");
        if (data.audio_event?.audio_base_64) {
          this.playAudioChunk(data.audio_event.audio_base_64);
        }
        break;

      case "interruption":
        this.setState("listening");
        break;

      case "ping":
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
          this.socket.send(JSON.stringify({ type: "pong", event_id: data.ping_event?.event_id }));
        }
        break;

      default:
        break;
    }
  }

  // Play audio chunk received from ElevenLabs agent stream
  playAudioChunk(base64Audio) {
    try {
      const audio = new Audio("data:audio/wav;base64," + base64Audio);
      audio.onended = () => {
        if (this.state === "speaking") {
          this.setState("listening");
        }
      };
      audio.play().catch(e => console.warn("Audio playback blocked/failed:", e));
    } catch (e) {
      console.error("Audio chunk playback error:", e);
    }
  }

  // Toggle Microphone Mute
  toggleMute() {
    if (!this.mediaStream) return this.isMuted;

    this.isMuted = !this.isMuted;
    this.mediaStream.getAudioTracks().forEach(track => {
      track.enabled = !this.isMuted;
    });

    return this.isMuted;
  }

  // Safely Disconnect and Clean Up Session Resources
  disconnect() {
    if (this.state === "disconnected") return;

    this.setState("disconnecting");

    // Stop animation frame
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }

    // Close WebSocket
    if (this.socket) {
      try {
        this.socket.close();
      } catch (e) {}
      this.socket = null;
    }

    // Stop Microphone Tracks
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
    }

    // Close AudioContext
    if (this.audioContext) {
      try {
        this.audioContext.close();
      } catch (e) {}
      this.audioContext = null;
    }

    this.analyser = null;
    this.audioLevel = 0;
    this.setState("disconnected", "Call ended");
  }
}

// Attach globally to window
window.SmartCampusVoiceAgentService = SmartCampusVoiceAgentService;
