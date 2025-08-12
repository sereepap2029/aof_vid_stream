// WebSocket Video Streaming Client for AOF Video Stream
// High-performance, low-latency video streaming using Socket.IO

class WebSocketVideoClient {
  constructor(canvasId, statusElementId) {
    this.canvas = document.getElementById(canvasId);
    this.statusElement = document.getElementById(statusElementId);
    this.context = this.canvas.getContext("2d");
    this.socket = null;
    this.isConnected = false;
    this.isStreaming = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000; // 1 second

    // Performance metrics
    this.frameCount = 0;
    this.startTime = null;
    this.lastFrameTime = 0;
    this.fpsDisplay = 0;
    this.latencyDisplay = 0;

    // Stream settings
    this.currentSettings = {
      camera_index: 1,
      resolution: [640, 480],
      fps: 30,
      quality: 85,
    };

    // Initialize canvas
    this.initCanvas();

    // Setup FPS counter
    this.setupFPSCounter();
  }

  initCanvas() {
    // Set default canvas size
    this.canvas.width = this.currentSettings.resolution[0];
    this.canvas.height = this.currentSettings.resolution[1];

    // Style canvas for responsive design
    this.canvas.style.maxWidth = "100%";
    this.canvas.style.height = "auto";
    this.canvas.style.border = "1px solid #ddd";
    this.canvas.style.borderRadius = "8px";
    this.canvas.style.backgroundColor = "#000";

    // Add loading text
    this.drawMessage("WebSocket Video - Click Start to Connect");
  }

  setupFPSCounter() {
    setInterval(() => {
      if (this.startTime) {
        const elapsed = (Date.now() - this.startTime) / 1000;
        this.fpsDisplay = Math.round(this.frameCount / elapsed);
      }
    }, 1000);
  }

  connect() {
    if (this.socket) {
      this.disconnect();
    }

    this.updateStatus("Connecting to WebSocket server...");
    console.log("Connecting to WebSocket video server...");

    // Create Socket.IO connection
    this.socket = io("/video", {
      transports: ["websocket", "polling"],
      upgrade: true,
      rememberUpgrade: true,
    });

    this.setupSocketHandlers();
  }

  setupSocketHandlers() {
    this.socket.on("connect", () => {
      this.isConnected = true;
      this.reconnectAttempts = 0;
      this.updateStatus("Connected to WebSocket server");
      console.log("WebSocket connected, ID:", this.socket.id);

      this.drawMessage("Connected - Ready to Stream");

      // Emit connection status request
      this.socket.emit("get_stats");
    });

    this.socket.on("disconnect", (reason) => {
      this.isConnected = false;
      this.isStreaming = false;
      this.updateStatus(`Disconnected: ${reason}`);
      console.log("WebSocket disconnected:", reason);

      this.drawMessage("Disconnected from Server");

      // Attempt reconnection
      this.attemptReconnect();
    });

    this.socket.on("connection_status", (data) => {
      console.log("Connection status:", data);
      this.updateStatus(`Connected (ID: ${data.client_id.substring(0, 8)})`);
    });

    this.socket.on("stream_started", (data) => {
      this.isStreaming = true;
      this.frameCount = 0;
      this.startTime = Date.now();
      this.currentSettings = {
        camera_index: data.camera_index,
        resolution: data.resolution,
        fps: data.fps,
        quality: data.quality,
      };

      // Update canvas size if resolution changed
      this.canvas.width = data.resolution[0];
      this.canvas.height = data.resolution[1];

      this.updateStatus(`Streaming: ${data.resolution[0]}x${data.resolution[1]} @ ${data.fps}fps (Q:${data.quality})`);
      console.log("Stream started:", data);

      this.drawMessage("Starting Video Stream...");
    });

    this.socket.on("stream_stopped", (data) => {
      this.isStreaming = false;
      this.updateStatus("Stream stopped");
      console.log("Stream stopped:", data);

      this.drawMessage("Stream Stopped");
    });

    this.socket.on("video_frame", (data) => {
      this.handleVideoFrame(data);
    });

    this.socket.on("video_frame_binary", (data) => {
      this.handleBinaryFrame(data);
    });

    this.socket.on("frame_data", (binaryData) => {
      this.handleFrameData(binaryData);
    });

    this.socket.on("stream_error", (data) => {
      console.error("Stream error:", data);
      this.updateStatus(`Error: ${data.error}`);
      this.drawMessage(`Error: ${data.error}`);
    });

    this.socket.on("stream_stats", (data) => {
      console.log("Stream stats:", data);
    });

    this.socket.on("quality_updated", (data) => {
      this.currentSettings.quality = data.quality;
      this.updateStatus(`Quality updated: ${data.quality}`);
    });

    this.socket.on("fps_updated", (data) => {
      this.currentSettings.fps = data.fps;
      this.updateStatus(`FPS updated: ${data.fps}`);
    });

    this.socket.on("resolution_updated", (data) => {
      this.currentSettings.resolution = data.resolution;
      this.updateStatus(`Resolution updated: ${data.resolution[0]}x${data.resolution[1]}`);
    });

    this.socket.on("encoding_method_updated", (data) => {
      this.currentSettings.encoding = data.method;
      this.updateStatus(`Encoding method updated: ${data.method}`);
    });

    this.socket.on("connect_error", (error) => {
      console.error("WebSocket connection error:", error);
      this.updateStatus(`Connection error: ${error.message}`);
      this.drawMessage("Connection Error");
    });
  }

  handleVideoFrame(data) {
    const frameTime = Date.now();

    // Calculate latency
    this.latencyDisplay = frameTime - data.timestamp * 1000;

    // Performance monitoring
    const frameSize = data.frame_size || 0;
    const encodeTime = data.encode_time || 0;
    const quality = data.quality;

    // Create image from base64 data
    const img = new Image();
    img.onload = () => {
      // Clear canvas and draw frame
      this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
      this.context.drawImage(img, 0, 0, this.canvas.width, this.canvas.height);

      // Update frame counter
      this.frameCount++;
      this.lastFrameTime = frameTime;

      // Enhanced status with performance info
      const sizeKB = Math.round(frameSize / 1024);
      const encodeMs = Math.round(encodeTime * 1000);
      const encoding = data.encoding || 'base64';
      
      const status = `Streaming: ${this.currentSettings.resolution[0]}x${this.currentSettings.resolution[1]} @ ${this.fpsDisplay}fps | ` +
                    `Latency: ${Math.round(this.latencyDisplay)}ms | Quality: ${quality} | ` +
                    `Frame: ${sizeKB}KB | Encode: ${encodeMs}ms | Method: ${encoding}`;
      this.updateStatus(status);

      // Warn about performance issues
      if (this.latencyDisplay > 200) {
        console.warn(`High latency detected: ${Math.round(this.latencyDisplay)}ms`);
      }
      if (encodeTime > 0.05) { // >50ms encoding time
        console.warn(`Slow encoding detected: ${encodeMs}ms`);
      }
    };

    img.onerror = (error) => {
      console.error("Error loading frame:", error);
    };

    img.src = "data:image/jpeg;base64," + data.frame;
  }

  handleBinaryFrame(metadata) {
    // Store metadata for when binary data arrives
    this.pendingBinaryFrame = {
      ...metadata,
      frameTime: Date.now()
    };
  }

  handleFrameData(binaryData) {
    if (!this.pendingBinaryFrame) {
      console.warn('Received binary data without metadata');
      return;
    }

    const metadata = this.pendingBinaryFrame;
    this.pendingBinaryFrame = null;

    // Calculate latency
    this.latencyDisplay = metadata.frameTime - metadata.timestamp * 1000;

    // Create blob and object URL for the image
    const blob = new Blob([binaryData], { type: 'image/jpeg' });
    const imageUrl = URL.createObjectURL(blob);

    const img = new Image();
    img.onload = () => {
      // Clear canvas and draw frame
      this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
      this.context.drawImage(img, 0, 0, this.canvas.width, this.canvas.height);

      // Update frame counter
      this.frameCount++;
      this.lastFrameTime = metadata.frameTime;

      // Enhanced status with performance info
      const sizeKB = Math.round(metadata.frame_size / 1024);
      const encodeMs = Math.round(metadata.encode_time * 1000);
      
      const status = `Streaming: ${this.currentSettings.resolution[0]}x${this.currentSettings.resolution[1]} @ ${this.fpsDisplay}fps | ` +
                    `Latency: ${Math.round(this.latencyDisplay)}ms | Quality: ${metadata.quality} | ` +
                    `Frame: ${sizeKB}KB | Encode: ${encodeMs}ms | Method: ${metadata.encoding}`;
      this.updateStatus(status);

      // Clean up object URL
      URL.revokeObjectURL(imageUrl);
    };

    img.onerror = (error) => {
      console.error("Error loading binary frame:", error);
      URL.revokeObjectURL(imageUrl);
    };

    img.src = imageUrl;
  }

  setEncodingMethod(method) {
    if (!this.isConnected) {
      return false;
    }
    
    console.log('Setting encoding method:', method);
    this.socket.emit('set_encoding_method', { method: method });
    return true;
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

    console.log("Starting stream with settings:", streamSettings);
    this.socket.emit("start_stream", streamSettings);
    return true;
  }

  stopStream() {
    if (!this.isConnected) {
      return false;
    }

    console.log("Stopping stream");
    this.socket.emit("stop_stream");
    return true;
  }
  updateResolution(width, height) {
    if (!this.isConnected) {
      return false;
    }

    console.log("Updating resolution:", width, height);
    this.socket.emit("update_resolution", { resolution: [width, height] });
    return true;
  }

  updateQuality(quality) {
    if (!this.isConnected) {
      return false;
    }

    console.log("Updating quality:", quality);
    this.socket.emit("update_quality", { quality: quality });
    return true;
  }

  updateFPS(fps) {
    if (!this.isConnected) {
      return false;
    }

    console.log("Updating FPS:", fps);
    this.socket.emit("update_fps", { fps: fps });
    return true;
  }

  getStats() {
    if (!this.isConnected) {
      return false;
    }

    this.socket.emit("get_stats");
    return true;
  }

  disconnect() {
    if (this.socket) {
      console.log("Disconnecting WebSocket");
      this.socket.disconnect();
      this.socket = null;
    }

    this.isConnected = false;
    this.isStreaming = false;
    this.updateStatus("Disconnected");
    this.drawMessage("Disconnected");
  }

  attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.updateStatus("Max reconnection attempts reached");
      this.drawMessage("Connection Failed - Please Refresh");
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * this.reconnectAttempts;

    this.updateStatus(`Reconnecting in ${delay / 1000}s... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    setTimeout(() => {
      if (!this.isConnected) {
        this.connect();
      }
    }, delay);
  }

  updateStatus(message) {
    if (this.statusElement) {
      this.statusElement.textContent = message;
    }
    console.log("Status:", message);
  }

  drawMessage(message) {
    // Clear canvas
    this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);

    // Set text properties
    this.context.fillStyle = "#ffffff";
    this.context.font = "20px Arial";
    this.context.textAlign = "center";
    this.context.textBaseline = "middle";

    // Draw message
    const x = this.canvas.width / 2;
    const y = this.canvas.height / 2;
    this.context.fillText(message, x, y);
  }

  // Utility methods
  isConnectionReady() {
    return this.isConnected;
  }

  isStreamingActive() {
    return this.isStreaming;
  }

  getCurrentSettings() {
    return { ...this.currentSettings };
  }

  getPerformanceStats() {
    return {
      fps: this.fpsDisplay,
      latency: this.latencyDisplay,
      frameCount: this.frameCount,
      uptime: this.startTime ? (Date.now() - this.startTime) / 1000 : 0,
    };
  }
}

// Global WebSocket video client instance
let websocketVideoClient = null;

// Initialize WebSocket video client
function initWebSocketVideo(canvasId = "video-canvas", statusElementId = "stream-status") {
  if (websocketVideoClient) {
    websocketVideoClient.disconnect();
  }

  websocketVideoClient = new WebSocketVideoClient(canvasId, statusElementId);
  console.log("WebSocket video client initialized");
  return websocketVideoClient;
}

// Export for use in other modules
if (typeof module !== "undefined" && module.exports) {
  module.exports = { WebSocketVideoClient, initWebSocketVideo };
}
