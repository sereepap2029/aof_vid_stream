// WebRTC Video Streaming Client with Frame Chunking
// Optimized for high-resolution, high-framerate streaming

class WebRTCVideoClient {
  constructor(canvasId, statusElementId) {
    this.canvas = document.getElementById(canvasId);
    this.statusElement = document.getElementById(statusElementId);
    this.context = this.canvas.getContext("2d");
    this.socket = null;
    this.isConnected = false;
    this.isStreaming = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;

    // Performance metrics
    this.frameCount = 0;
    this.startTime = null;
    this.lastFrameTime = 0;
    this.fpsDisplay = 0;
    this.latencyDisplay = 0;

    // Frame chunking support
    this.chunkCache = new Map(); // frame_id -> chunks
    this.frameReassembler = new Map(); // frame_id -> frame data
    this.chunkTimeouts = new Map(); // frame_id -> timeout
    this.maxChunkWaitTime = 1000; // 1 second max wait for chunks

    // Stream settings optimized for WebRTC
    this.currentSettings = {
      camera_index: 1,
      resolution: [1920, 1080], // Default to 1080p
      fps: 60, // Default to 60fps
      quality: 85,
      chunk_size: 32768, // 32KB chunks
      enable_chunking: true,
    };

    // Performance tracking
    this.performanceStats = {
      totalFrames: 0,
      chunkedFrames: 0,
      chunksReceived: 0,
      chunksLost: 0,
      averageLatency: 0,
      frameReassemblyTime: 0,
    };

    // Initialize canvas for high resolution
    this.initCanvas();
    this.setupFPSCounter();
    this.setupChunkCleanup();
  }

  initCanvas() {
    // Set canvas size to match stream resolution
    this.canvas.width = this.currentSettings.resolution[0];
    this.canvas.height = this.currentSettings.resolution[1];

    // Style canvas for responsive design while maintaining aspect ratio
    this.canvas.style.maxWidth = "100%";
    this.canvas.style.height = "auto";
    this.canvas.style.border = "1px solid #ddd";
    this.canvas.style.borderRadius = "8px";
    this.canvas.style.backgroundColor = "#000";

    // Add loading text
    this.drawMessage("WebRTC Video Stream - Ready");
  }

  setupFPSCounter() {
    setInterval(() => {
      if (this.startTime && this.frameCount > 0) {
        const elapsed = (Date.now() - this.startTime) / 1000;
        this.fpsDisplay = Math.round(this.frameCount / elapsed);
      }
    }, 1000);
  }

  setupChunkCleanup() {
    // Clean up old incomplete frames every 2 seconds
    setInterval(() => {
      this.cleanupOldFrames();
    }, 2000);
  }

  isConnectionReady() {
    return this.isConnected;
  }

  connect() {
    if (this.isConnected) {
      return;
    }

    console.log("Connecting to WebRTC video server...");
    this.socket = io("/webrtc", {
      transports: ["websocket"],
      upgrade: true,
      rememberUpgrade: true,
    });

    this.setupEventHandlers();
  }

  setupEventHandlers() {
    this.socket.on("connect", () => {
      console.log("WebRTC connected to server");
      this.isConnected = true;
      this.reconnectAttempts = 0;
      this.updateStatus("Connected to WebRTC server");
    });

    this.socket.on("disconnect", () => {
      console.log("WebRTC disconnected from server");
      this.isConnected = false;
      this.isStreaming = false;
      this.updateStatus("Disconnected from server");
      this.drawMessage("Disconnected");
      this.attemptReconnect();
    });

    this.socket.on("webrtc_connected", (data) => {
      console.log("WebRTC capabilities:", data.capabilities);
      this.updateStatus(`WebRTC Ready - Max: ${data.capabilities.max_resolution.join('x')}@${data.capabilities.max_fps}fps`);
    });

    // Single frame handling (no chunking)
    this.socket.on("webrtc_frame_single", (metadata) => {
      this.pendingFrameMetadata = {
        ...metadata,
        frameTime: Date.now(),
        chunked: false
      };
    });

    this.socket.on("webrtc_frame_data", (binaryData) => {
      if (this.pendingFrameMetadata && !this.pendingFrameMetadata.chunked) {
        this.handleSingleFrame(this.pendingFrameMetadata, binaryData);
        this.pendingFrameMetadata = null;
      }
    });

    // Chunked frame handling
    this.socket.on("webrtc_frame_chunked", (metadata) => {
      console.log(`Receiving chunked frame ${metadata.frame_id}: ${metadata.total_chunks} chunks, ${Math.round(metadata.total_size/1024)}KB`);
      
      this.chunkCache.set(metadata.frame_id, {
        metadata: { ...metadata, frameTime: Date.now() },
        chunks: new Map(),
        receivedChunks: 0,
        startTime: Date.now()
      });

      // Set timeout for frame completion
      const timeout = setTimeout(() => {
        this.handleFrameTimeout(metadata.frame_id);
      }, this.maxChunkWaitTime);
      
      this.chunkTimeouts.set(metadata.frame_id, timeout);
    });

    this.socket.on("webrtc_chunk", (chunkMeta) => {
      // Chunk metadata received, waiting for binary data
      this.pendingChunkMeta = chunkMeta;
    });

    this.socket.on("webrtc_chunk_data", (binaryData) => {
      if (this.pendingChunkMeta) {
        this.handleChunk(this.pendingChunkMeta, binaryData);
        this.pendingChunkMeta = null;
      }
    });

    this.socket.on("webrtc_stream_started", (data) => {
      console.log("WebRTC stream started:", data);
      this.isStreaming = true;
      this.startTime = Date.now();
      this.frameCount = 0;
      this.updateStatus(`WebRTC Streaming: ${data.resolution.join('x')}@${data.fps}fps`);
    });

    this.socket.on("webrtc_stream_stopped", () => {
      console.log("WebRTC stream stopped");
      this.isStreaming = false;
      this.updateStatus("Stream stopped");
      this.drawMessage("Stream Stopped");
    });

    this.socket.on("webrtc_error", (data) => {
      console.error("WebRTC error:", data);
      this.updateStatus(`Error: ${data.error}`);
      this.drawMessage(`Error: ${data.error}`);
    });
  }

  handleSingleFrame(metadata, binaryData) {
    // Calculate latency
    this.latencyDisplay = metadata.frameTime - metadata.timestamp * 1000;

    // Create blob and render frame
    const blob = new Blob([binaryData], { type: 'image/jpeg' });
    const imageUrl = URL.createObjectURL(blob);

    const img = new Image();
    img.onload = () => {
      this.renderFrame(img);
      
      // Update performance stats
      this.frameCount++;
      this.performanceStats.totalFrames++;
      this.lastFrameTime = metadata.frameTime;

      // Enhanced status
      const sizeKB = Math.round(metadata.frame_size / 1024);
      const status = `WebRTC: ${this.currentSettings.resolution.join('x')}@${this.fpsDisplay}fps | ` +
                    `Latency: ${Math.round(this.latencyDisplay)}ms | Quality: ${metadata.quality} | ` +
                    `Frame: ${sizeKB}KB | Mode: Single`;
      this.updateStatus(status);

      URL.revokeObjectURL(imageUrl);
    };

    img.onerror = () => {
      console.error("Error loading single frame");
      URL.revokeObjectURL(imageUrl);
    };

    img.src = imageUrl;
  }

  handleChunk(chunkMeta, binaryData) {
    const frameId = chunkMeta.frame_id;
    
    if (!this.chunkCache.has(frameId)) {
      console.warn(`Received chunk for unknown frame ${frameId}`);
      return;
    }

    const frameData = this.chunkCache.get(frameId);
    frameData.chunks.set(chunkMeta.chunk_index, binaryData);
    frameData.receivedChunks++;

    this.performanceStats.chunksReceived++;

    // Send acknowledgment (optional, for debugging)
    if (Math.random() < 0.1) { // Only send 10% of acks to reduce traffic
      this.socket.emit('chunk_received', {
        frame_id: frameId,
        chunk_index: chunkMeta.chunk_index
      });
    }

    // Check if all chunks received
    if (frameData.receivedChunks >= frameData.metadata.total_chunks) {
      this.reassembleAndRenderFrame(frameId);
    }
  }

  reassembleAndRenderFrame(frameId) {
    const reassemblyStart = Date.now();
    const frameData = this.chunkCache.get(frameId);
    
    if (!frameData) {
      console.error(`Frame data not found for ${frameId}`);
      return;
    }

    const metadata = frameData.metadata;
    
    // Reassemble frame from chunks
    const frameArray = new Uint8Array(metadata.total_size);
    let offset = 0;
    
    for (let i = 0; i < metadata.total_chunks; i++) {
      const chunkData = frameData.chunks.get(i);
      if (!chunkData) {
        console.error(`Missing chunk ${i} for frame ${frameId}`);
        this.performanceStats.chunksLost++;
        this.cleanupFrame(frameId);
        return;
      }
      
      const chunkArray = new Uint8Array(chunkData);
      frameArray.set(chunkArray, offset);
      offset += chunkArray.length;
    }

    // Create blob and render
    const blob = new Blob([frameArray], { type: 'image/jpeg' });
    const imageUrl = URL.createObjectURL(blob);

    const img = new Image();
    img.onload = () => {
      this.renderFrame(img);
      
      // Update performance stats
      this.frameCount++;
      this.performanceStats.totalFrames++;
      this.performanceStats.chunkedFrames++;
      this.performanceStats.frameReassemblyTime = Date.now() - reassemblyStart;
      this.lastFrameTime = metadata.frameTime;
      
      // Calculate latency
      this.latencyDisplay = metadata.frameTime - metadata.timestamp * 1000;

      // Enhanced status for chunked frames
      const sizeKB = Math.round(metadata.total_size / 1024);
      const chunkCount = metadata.total_chunks;
      const reassemblyMs = this.performanceStats.frameReassemblyTime;
      
      const status = `WebRTC: ${this.currentSettings.resolution.join('x')}@${this.fpsDisplay}fps | ` +
                    `Latency: ${Math.round(this.latencyDisplay)}ms | Quality: ${metadata.quality} | ` +
                    `Frame: ${sizeKB}KB (${chunkCount} chunks) | Reassembly: ${reassemblyMs}ms`;
      this.updateStatus(status);

      URL.revokeObjectURL(imageUrl);
      this.cleanupFrame(frameId);
    };

    img.onerror = () => {
      console.error("Error loading reassembled frame");
      URL.revokeObjectURL(imageUrl);
      this.cleanupFrame(frameId);
    };

    img.src = imageUrl;
  }

  renderFrame(img) {
    // Clear canvas and draw frame
    this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
    this.context.drawImage(img, 0, 0, this.canvas.width, this.canvas.height);
  }

  handleFrameTimeout(frameId) {
    console.warn(`Frame timeout for ${frameId}`);
    this.cleanupFrame(frameId);
  }

  cleanupFrame(frameId) {
    // Clear timeout
    if (this.chunkTimeouts.has(frameId)) {
      clearTimeout(this.chunkTimeouts.get(frameId));
      this.chunkTimeouts.delete(frameId);
    }

    // Remove from cache
    this.chunkCache.delete(frameId);
  }

  cleanupOldFrames() {
    const now = Date.now();
    const maxAge = 5000; // 5 seconds

    for (const [frameId, frameData] of this.chunkCache.entries()) {
      if (now - frameData.startTime > maxAge) {
        console.warn(`Cleaning up old frame ${frameId}`);
        this.cleanupFrame(frameId);
      }
    }
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      setTimeout(() => {
        this.connect();
      }, this.reconnectDelay * this.reconnectAttempts);
    } else {
      console.error("Max reconnection attempts reached");
      this.updateStatus("Connection failed - please refresh");
    }
  }

  startStream(settings = {}) {
    if (!this.isConnected) {
      this.updateStatus("Not connected to server");
      return false;
    }

    const streamSettings = {
      ...this.currentSettings,
      ...settings,
    };

    console.log("Starting WebRTC stream with settings:", streamSettings);
    this.socket.emit("start_webrtc_stream", streamSettings);
    return true;
  }

  stopStream() {
    if (!this.isConnected) {
      return false;
    }

    console.log("Stopping WebRTC stream");
    this.socket.emit("stop_webrtc_stream");
    
    // Clear all cached frames
    this.chunkCache.clear();
    this.chunkTimeouts.forEach(timeout => clearTimeout(timeout));
    this.chunkTimeouts.clear();
    
    return true;
  }

  updateSettings(newSettings) {
    this.currentSettings = { ...this.currentSettings, ...newSettings };
    
    // Update canvas size if resolution changed
    if (newSettings.resolution) {
      this.canvas.width = newSettings.resolution[0];
      this.canvas.height = newSettings.resolution[1];
    }
  }

  updateStatus(message) {
    if (this.statusElement) {
      this.statusElement.textContent = message;
    }
    console.log("WebRTC Status:", message);
  }

  drawMessage(message) {
    this.context.fillStyle = "#333";
    this.context.fillRect(0, 0, this.canvas.width, this.canvas.height);
    
    this.context.fillStyle = "#fff";
    this.context.font = "24px Arial";
    this.context.textAlign = "center";
    this.context.fillText(
      message,
      this.canvas.width / 2,
      this.canvas.height / 2
    );
  }

  getPerformanceStats() {
    return {
      ...this.performanceStats,
      fps: this.fpsDisplay,
      latency: this.latencyDisplay,
      frameCount: this.frameCount,
      uptime: this.startTime ? (Date.now() - this.startTime) / 1000 : 0,
      cacheSize: this.chunkCache.size,
      chunkSuccessRate: this.performanceStats.chunksReceived > 0 ? 
        ((this.performanceStats.chunksReceived - this.performanceStats.chunksLost) / this.performanceStats.chunksReceived * 100) : 100
    };
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.isConnected = false;
    this.isStreaming = false;
  }
}

// Global WebRTC video client instance
let webrtcVideoClient = null;

// Initialize WebRTC video client
function initWebRTCVideo(canvasId = "video-canvas", statusElementId = "stream-status") {
  if (webrtcVideoClient) {
    webrtcVideoClient.disconnect();
  }

  webrtcVideoClient = new WebRTCVideoClient(canvasId, statusElementId);
  console.log("WebRTC video client initialized");
  return webrtcVideoClient;
}

// Export for use in other modules
if (typeof module !== "undefined" && module.exports) {
  module.exports = { WebRTCVideoClient, initWebRTCVideo };
}
