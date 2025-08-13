// Camera control JavaScript for AOF Video Stream
// Enhanced with WebSocket streaming support
document.addEventListener("DOMContentLoaded", function () {
  console.log("AOF Video Stream - Camera JS Loaded");

  // Initialize camera interface
  initializeCameraInterface();
});

let streamActive = false;
let currentCamera = null;
let videoCanvas = null;
let canvasContext = null;
let streamingMode = "websocket"; // 'websocket', 'webrtc', or 'polling'
let wsVideoClient = null;
let webrtcClient = null;

function initializeCameraInterface() {
  // Get DOM elements
  const cameraSelect = document.getElementById("camera-select");
  const startBtn = document.getElementById("start-btn");
  const stopBtn = document.getElementById("stop-btn");
  const refreshDevicesBtn = document.getElementById("refresh-devices-btn");
  const snapshotBtn = document.getElementById("snapshot-btn");
  const fullscreenBtn = document.getElementById("fullscreen-btn");
  const applySettingsBtn = document.getElementById("apply-settings-btn");

  videoCanvas = document.getElementById("video-canvas");
  canvasContext = videoCanvas.getContext("2d");

  // Set default canvas size
  videoCanvas.width = 640;
  videoCanvas.height = 480;

  // Initialize WebSocket video client
  wsVideoClient = initWebSocketVideo("video-canvas", "stream-status");
  
  // Initialize WebRTC video client (if available)
  if (typeof initWebRTCVideo === 'function') {
    webrtcClient = initWebRTCVideo("video-canvas", "stream-status");
  }

  // Event listeners
  if (startBtn) {
    startBtn.addEventListener("click", startStream);
  }

  if (stopBtn) {
    stopBtn.addEventListener("click", stopStream);
  }

  if (refreshDevicesBtn) {
    refreshDevicesBtn.addEventListener("click", refreshCameraDevices);
  }

  if (snapshotBtn) {
    snapshotBtn.addEventListener("click", takeSnapshot);
  }

  if (fullscreenBtn) {
    fullscreenBtn.addEventListener("click", toggleFullscreen);
  }

  if (applySettingsBtn) {
    applySettingsBtn.addEventListener("click", applyStreamSettings);
  }

  // Hardware encoding toggle
  const hardwareEncodingToggle = document.getElementById("hardware-encoding-toggle");
  if (hardwareEncodingToggle) {
    hardwareEncodingToggle.addEventListener("change", toggleHardwareEncoding);
  }

  if (cameraSelect) {
    cameraSelect.addEventListener("change", onCameraSelectionChange);
  }

  // Add real-time resolution update listener
  const resolutionSelect = document.getElementById("resolution-select");
  if (resolutionSelect) {
    resolutionSelect.addEventListener("change", function () {
      let resolution = resolutionSelect ? resolutionSelect.value : "640x480";
      const [width, height] = resolution.split("x").map(Number);
      console.log("Resolution changed to:", resolution);

      // Update resolution in real-time if streaming
      if (streamActive) {
        if (streamingMode === "websocket" && wsVideoClient) {
          wsVideoClient.updateResolution(width, height);
          window.AOFVideoStream.showNotification(`Resolution updated to ${this.value}`, "info");
        } else if (streamingMode === "webrtc" && webrtcClient) {
          webrtcClient.updateResolution(width, height);
          window.AOFVideoStream.showNotification(`Resolution updated to ${this.value}`, "info");
        }
      }
    });
  }

  // Add real-time quality update listener
  const qualitySelect = document.getElementById("quality-select");
  if (qualitySelect) {
    qualitySelect.addEventListener("change", function () {
      const quality = getQualityValue(this.value);
      console.log("Quality changed to:", quality);

      // Update quality in real-time if streaming
      if (streamActive) {
        if (streamingMode === "websocket" && wsVideoClient) {
          wsVideoClient.updateQuality(quality);
          window.AOFVideoStream.showNotification(`Quality updated to ${this.value}`, "info");
        } else if (streamingMode === "webrtc" && webrtcClient) {
          webrtcClient.updateQuality(quality);
          window.AOFVideoStream.showNotification(`Quality updated to ${this.value}`, "info");
        }
      }
    });
  }

  // Add codec selection listener
  const codecSelect = document.getElementById("codec-select");
  if (codecSelect) {
    codecSelect.addEventListener("change", onCodecSelectionChange);
  }

  // Add real-time FPS update listener
  const fpsSelect = document.getElementById("fps-select");
  if (fpsSelect) {
    fpsSelect.addEventListener("change", function () {
      const fps = parseInt(this.value);
      console.log("FPS changed to:", fps);

      // Update FPS in real-time if streaming
      if (streamActive) {
        if (streamingMode === "websocket" && wsVideoClient) {
          wsVideoClient.updateFPS(fps);
          window.AOFVideoStream.showNotification(`FPS updated to ${fps}`, "info");
        } else if (streamingMode === "webrtc" && webrtcClient) {
          webrtcClient.updateFPS(fps);
          window.AOFVideoStream.showNotification(`FPS updated to ${fps}`, "info");
        }
      }
    });
  }

  // Add real-time encoding method update listener
  const encodingSelect = document.getElementById("encoding-select");
  if (encodingSelect) {
    encodingSelect.addEventListener("change", function () {
      const encoding = this.value;
      console.log("Encoding method changed to:", encoding);

      // Update encoding method in real-time if streaming
      if (streamActive) {
        if (streamingMode === "websocket" && wsVideoClient) {
          wsVideoClient.setEncodingMethod(encoding);
          const methodName = encoding === 'binary' ? 'Binary (Fastest)' : 
                            encoding === 'compressed' ? 'Compressed' : 'Base64';
          window.AOFVideoStream.showNotification(`Encoding updated to ${methodName}`, "info");
        } else if (streamingMode === "webrtc" && webrtcClient) {
          webrtcClient.setEncodingMethod(encoding);
          const methodName = encoding === 'binary' ? 'Binary (Fastest)' : 
                            encoding === 'compressed' ? 'Compressed' : 'Base64';
          window.AOFVideoStream.showNotification(`Encoding updated to ${methodName}`, "info");
        }
      }
    });
  }

  // Add streaming mode toggle
  addStreamingModeToggle();

  // Initialize camera devices on load
  refreshCameraDevices();

  // Load available codecs
  loadAvailableCodecs();

  // Load hardware encoding status
  loadEncodingStatus();

  // Update stream info periodically
  setInterval(updateStreamInfo, 1000);
  
  // Update encoding performance periodically
  setInterval(updateEncodingStatus, 2000);
}

function refreshCameraDevices() {
  const cameraSelect = document.getElementById("camera-select");
  const refreshBtn = document.getElementById("refresh-devices-btn");

  if (refreshBtn) {
    refreshBtn.disabled = true;
    refreshBtn.textContent = "🔄 Detecting...";
  }

  // Call real API to get camera devices with quick scan for faster response
  fetch("/api/cameras/?refresh=true&quick_scan=true")
    .then((response) => response.json())
    .then((data) => {
      // Clear existing options
      if (cameraSelect) {
        cameraSelect.innerHTML = '<option value="">Select Camera...</option>';

        if (data.success && data.data.cameras) {
          data.data.cameras.forEach((device) => {
            const option = document.createElement("option");
            option.value = device.index;
            option.textContent = `Camera ${device.index}: ${device.name}`;
            cameraSelect.appendChild(option);
          });

          if (window.AOFVideoStream) {
            window.AOFVideoStream.showNotification(`Found ${data.data.count} camera(s) - Quick Scan`, "success");
          }
        } else {
          if (window.AOFVideoStream) {
            window.AOFVideoStream.showNotification("No cameras found", "warning");
          }
        }
      }
    })
    .catch((error) => {
      console.error("Error fetching camera devices:", error);
      if (window.AOFVideoStream) {
        window.AOFVideoStream.showNotification("Error detecting cameras", "error");
      }
    })
    .finally(() => {
      if (refreshBtn) {
        refreshBtn.disabled = false;
        refreshBtn.textContent = "🔄 Refresh Devices";
      }
    });
}

function onCameraSelectionChange() {
  const cameraSelect = document.getElementById("camera-select");
  const startBtn = document.getElementById("start-btn");

  if (cameraSelect && startBtn) {
    startBtn.disabled = !cameraSelect.value;

    if (cameraSelect.value) {
      updateStreamDevice(`Camera ${cameraSelect.value}`);
    } else {
      updateStreamDevice("None");
    }
  }
}

function onCodecSelectionChange() {
  const codecSelect = document.getElementById("codec-select");
  if (!codecSelect) return;

  const selectedCodec = codecSelect.value;
  console.log("Codec changed to:", selectedCodec);

  // If streaming is active, update codec in real-time
  if (streamActive && currentCamera) {
    updateCodec(selectedCodec);
  }

  // Update codec status display
  updateCodecStatus(selectedCodec);
  
  // Show notification
  if (window.AOFVideoStream) {
    window.AOFVideoStream.showNotification(`Codec changed to ${selectedCodec}`, "info");
  }
}

function startStream() {
  const cameraSelect = document.getElementById("camera-select");
  const startBtn = document.getElementById("start-btn");
  const stopBtn = document.getElementById("stop-btn");
  const snapshotBtn = document.getElementById("snapshot-btn");
  const fullscreenBtn = document.getElementById("fullscreen-btn");
  const resolutionSelect = document.getElementById("resolution-select");
  const fpsSelect = document.getElementById("fps-select");
  const qualitySelect = document.getElementById("quality-select");
  const codecSelect = document.getElementById("codec-select");

  if (!cameraSelect || !cameraSelect.value) {
    if (window.AOFVideoStream) {
      window.AOFVideoStream.showNotification("Please select a camera first", "warning");
    }
    return;
  }

  currentCamera = cameraSelect.value;
  console.log(`Starting ${streamingMode} stream for camera: ${currentCamera}`);

  // Get selected settings
  let resolution = resolutionSelect ? resolutionSelect.value : "640x480";
  let fps = fpsSelect ? parseInt(fpsSelect.value) : 30;
  let quality = qualitySelect ? getQualityValue(qualitySelect.value) : 85;
  let codec = codecSelect ? codecSelect.value : "";

  // Parse resolution
  const [width, height] = resolution.split("x").map(Number);

  // Update UI to show starting state
  if (startBtn) startBtn.disabled = true;
  updateStreamStatus("Starting...");

  if (streamingMode === "websocket") {
    startWebSocketStream({
      camera_index: parseInt(currentCamera),
      resolution: [width, height],
      fps: fps,
      quality: quality,
      codec: codec,
    });
  } else if (streamingMode === "webrtc") {
    startWebRTCStream({
      camera_index: parseInt(currentCamera),
      resolution: [width, height],
      fps: fps,
      quality: quality,
      codec: codec,
    });
  } else {
    startPollingStream({
      camera_index: parseInt(currentCamera),
      resolution: [width, height],
      fps: fps,
      quality: quality,
      codec: codec,
    });
  }
}

function startWebSocketStream(settings) {
  // Connect to WebSocket if not connected
  if (!wsVideoClient.isConnectionReady()) {
    wsVideoClient.connect();

    // Wait for connection before starting stream
    setTimeout(() => {
      if (wsVideoClient.isConnectionReady()) {
        wsVideoClient.startStream(settings);
        handleStreamStartSuccess(settings);
      } else {
        handleStreamStartError("Failed to connect to WebSocket server");
      }
    }, 1000);
  } else {
    wsVideoClient.startStream(settings);
    handleStreamStartSuccess(settings);
  }

  // Set up success/error handling via event monitoring
  setTimeout(() => {
    if (wsVideoClient.isStreamingActive()) {
      handleStreamStartSuccess(settings);
    }
  }, 2000);
}

function startWebRTCStream(settings) {
  // Connect to WebRTC if not connected and client is available
  if (!webrtcClient) {
    handleStreamStartError("WebRTC client not available");
    return;
  }

  if (!webrtcClient.isConnectionReady()) {
    webrtcClient.connect();

    // Wait for connection before starting stream
    setTimeout(() => {
      if (webrtcClient.isConnectionReady()) {
        webrtcClient.startStream(settings);
        handleStreamStartSuccess(settings);
        // Show performance stats for WebRTC
        showPerformanceStats(true);
      } else {
        handleStreamStartError("Failed to connect to WebRTC server");
      }
    }, 1000);
  } else {
    webrtcClient.startStream(settings);
    handleStreamStartSuccess(settings);
    // Show performance stats for WebRTC
    showPerformanceStats(true);
  }

  // Set up success/error handling via event monitoring
  setTimeout(() => {
    if (webrtcClient.isStreamingActive()) {
      handleStreamStartSuccess(settings);
    }
  }, 2000);
}

function startPollingStream(settings) {
  // Call REST API to start camera stream
  fetch("/api/cameras/start", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      camera_index: settings.camera_index,
      resolution: settings.resolution,
      fps: settings.fps,
      quick_start: true,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        handleStreamStartSuccess(settings);
        // Start polling for frames
        startVideoFeed();
      } else {
        handleStreamStartError(data.error?.message || "Failed to start stream");
      }
    })
    .catch((error) => {
      console.error("Error starting polling stream:", error);
      handleStreamStartError("Error starting stream");
    });
}

function handleStreamStartSuccess(settings) {
  streamActive = true;

  const stopBtn = document.getElementById("stop-btn");
  const snapshotBtn = document.getElementById("snapshot-btn");
  const fullscreenBtn = document.getElementById("fullscreen-btn");
  const cameraSelect = document.getElementById("camera-select");

  // Update UI
  if (stopBtn) stopBtn.disabled = false;
  if (snapshotBtn) snapshotBtn.disabled = false;
  if (fullscreenBtn) fullscreenBtn.disabled = false;
  if (cameraSelect) cameraSelect.disabled = true;

  // Hide placeholder and show canvas
  const placeholder = document.getElementById("video-placeholder");
  if (placeholder) {
    placeholder.style.display = "none";
  }

  // Update stream info
  updateStreamStatus("Active");
  updateStreamResolution(`${settings.resolution[0]}x${settings.resolution[1]}`);
  updateStreamFPS(settings.fps.toString());

  if (window.AOFVideoStream) {
    const mode = streamingMode === "websocket" ? "WebSocket" : "HTTP Polling";
    window.AOFVideoStream.showNotification(`${mode} stream started successfully`, "success");
  }
}

function handleStreamStartError(errorMessage) {
  const startBtn = document.getElementById("start-btn");

  // Reset UI on failure
  if (startBtn) startBtn.disabled = false;
  updateStreamStatus("Failed");

  if (window.AOFVideoStream) {
    window.AOFVideoStream.showNotification(errorMessage, "error");
  }
}

function stopStream() {
  const startBtn = document.getElementById("start-btn");
  const stopBtn = document.getElementById("stop-btn");
  const snapshotBtn = document.getElementById("snapshot-btn");
  const fullscreenBtn = document.getElementById("fullscreen-btn");
  const cameraSelect = document.getElementById("camera-select");

  if (startBtn) startBtn.disabled = false;
  if (stopBtn) stopBtn.disabled = true;
  if (snapshotBtn) snapshotBtn.disabled = true;
  if (fullscreenBtn) fullscreenBtn.disabled = true;
  if (cameraSelect) cameraSelect.disabled = false;

  updateStreamStatus("Stopping...");

  if (streamingMode === "websocket") {
    stopWebSocketStream();
  } else if (streamingMode === "webrtc") {
    stopWebRTCStream();
  } else {
    stopPollingStream();
  }
}

function stopWebSocketStream() {
  if (wsVideoClient) {
    wsVideoClient.stopStream();
  }

  // Handle UI updates
  setTimeout(() => {
    handleStreamStopSuccess();
  }, 500);
}

function stopWebRTCStream() {
  if (webrtcClient) {
    webrtcClient.stopStream();
  }

  // Hide performance stats
  showPerformanceStats(false);

  // Handle UI updates
  setTimeout(() => {
    handleStreamStopSuccess();
  }, 500);
}

function stopPollingStream() {
  // Call API to stop camera stream
  fetch("/api/cameras/stop", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        handleStreamStopSuccess();
      } else {
        updateStreamStatus("Error");
        if (window.AOFVideoStream) {
          window.AOFVideoStream.showNotification(data.error?.message || "Failed to stop stream", "error");
        }
      }
    })
    .catch((error) => {
      console.error("Error stopping stream:", error);
      updateStreamStatus("Error");
      if (window.AOFVideoStream) {
        window.AOFVideoStream.showNotification("Error stopping stream", "error");
      }
    });
}

function handleStreamStopSuccess() {
  streamActive = false;
  currentCamera = null;

  const startBtn = document.getElementById("start-btn");
  const stopBtn = document.getElementById("stop-btn");
  const snapshotBtn = document.getElementById("snapshot-btn");
  const fullscreenBtn = document.getElementById("fullscreen-btn");
  const cameraSelect = document.getElementById("camera-select");

  // Stop video feed if polling
  if (streamingMode === "polling") {
    stopVideoFeed();
  }

  // Update UI
  if (startBtn) startBtn.disabled = false;
  if (stopBtn) stopBtn.disabled = true;
  if (snapshotBtn) snapshotBtn.disabled = true;
  if (fullscreenBtn) fullscreenBtn.disabled = true;
  if (cameraSelect) cameraSelect.disabled = false;

  // Show placeholder and hide canvas content
  const placeholder = document.getElementById("video-placeholder");
  if (placeholder) {
    placeholder.style.display = "flex";
  }

  // Clear canvas
  if (canvasContext) {
    canvasContext.clearRect(0, 0, videoCanvas.width, videoCanvas.height);
  }

  // Update stream info
  updateStreamStatus("Stopped");
  updateStreamResolution("N/A");
  updateStreamFPS("N/A");
  updateStreamDevice("None");

  if (window.AOFVideoStream) {
    const mode = streamingMode === "websocket" ? "WebSocket" : "HTTP Polling";
    window.AOFVideoStream.showNotification(`${mode} stream stopped successfully`, "success");
  }
}

// Video feed management
let videoFeedInterval = null;

function startVideoFeed() {
  // Clear any existing video feed
  stopVideoFeed();

  // Start polling for video frames
  videoFeedInterval = setInterval(() => {
    if (streamActive) {
      fetchVideoFrame();
    }
  }, 33); // ~30 FPS (1000ms / 30fps = 33ms)
}

function stopVideoFeed() {
  if (videoFeedInterval) {
    clearInterval(videoFeedInterval);
    videoFeedInterval = null;
  }
}

function fetchVideoFrame() {
  if (!streamActive || !canvasContext || !videoCanvas) return;

  fetch("/api/cameras/frame")
    .then((response) => {
      if (response.ok) {
        return response.blob();
      } else {
        throw new Error("Failed to fetch frame");
      }
    })
    .then((blob) => {
      const img = new Image();
      img.onload = function () {
        // Draw the image to canvas
        canvasContext.clearRect(0, 0, videoCanvas.width, videoCanvas.height);
        canvasContext.drawImage(img, 0, 0, videoCanvas.width, videoCanvas.height);
        URL.revokeObjectURL(img.src);
      };
      img.src = URL.createObjectURL(blob);
    })
    .catch((error) => {
      // Only log errors occasionally to avoid spam
      if (Math.random() < 0.01) {
        // 1% chance to log
        console.warn("Frame fetch error:", error);
      }
    });
}

function takeSnapshot() {
  if (!streamActive || !videoCanvas) {
    if (window.AOFVideoStream) {
      window.AOFVideoStream.showNotification("No active stream to capture", "warning");
    }
    return;
  }

  // Get current frame from API and save it
  fetch("/api/cameras/frame")
    .then((response) => {
      if (response.ok) {
        return response.blob();
      } else {
        throw new Error("Failed to fetch frame for snapshot");
      }
    })
    .then((blob) => {
      // Create download link
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `snapshot_${new Date().toISOString().replace(/[:.]/g, "-")}.jpg`;
      a.click();
      URL.revokeObjectURL(url);

      if (window.AOFVideoStream) {
        window.AOFVideoStream.showNotification("Snapshot saved", "success");
      }
    })
    .catch((error) => {
      console.error("Snapshot error:", error);
      if (window.AOFVideoStream) {
        window.AOFVideoStream.showNotification("Failed to take snapshot", "error");
      }
    });
}

function toggleFullscreen() {
  if (!videoCanvas) return;

  if (!document.fullscreenElement) {
    videoCanvas
      .requestFullscreen()
      .then(() => {
        if (window.AOFVideoStream) {
          window.AOFVideoStream.showNotification("Entered fullscreen mode", "info");
        }
      })
      .catch((err) => {
        console.error("Failed to enter fullscreen:", err);
      });
  } else {
    document.exitFullscreen().then(() => {
      if (window.AOFVideoStream) {
        window.AOFVideoStream.showNotification("Exited fullscreen mode", "info");
      }
    });
  }
}

function applyStreamSettings() {
  const resolutionSelect = document.getElementById("resolution-select");
  const fpsSelect = document.getElementById("fps-select");
  const qualitySelect = document.getElementById("quality-select");
  const maxBitrateInput = document.getElementById("max-bitrate-input");

  if (resolutionSelect && fpsSelect && qualitySelect && maxBitrateInput) {
    const resolution = resolutionSelect.value;
    const fps = fpsSelect.value;
    const quality = qualitySelect.value;
    const maxBitrate = parseInt(maxBitrateInput.value) || 0;

    // Apply resolution to canvas
    if (videoCanvas) {
      const [width, height] = resolution.split("x").map(Number);
      videoCanvas.width = width;
      videoCanvas.height = height;
    }

    // Update display info
    updateStreamResolution(resolution);
    updateStreamFPS(fps);

    // Apply maximum bitrate setting if WebSocket is active
    if (wsVideoClient && wsVideoClient.isConnected) {
      wsVideoClient.setMaxBitrate(maxBitrate);
    }

    let settingsMessage = `Settings applied: ${resolution} @ ${fps}fps (${quality} quality)`;
    if (maxBitrate > 0) {
      settingsMessage += `, Max bitrate: ${maxBitrate} kbps`;
    }

    if (window.AOFVideoStream) {
      window.AOFVideoStream.showNotification(settingsMessage, "success");
    }
  }
}

// Stream info update functions
function updateStreamStatus(status) {
  const statusElement = document.getElementById("stream-status");
  if (statusElement) {
    statusElement.textContent = status;
    statusElement.className = "info-value";

    if (status === "Active") {
      statusElement.classList.add("status-online");
    }
  }
}

function updateStreamResolution(resolution) {
  const resolutionElement = document.getElementById("stream-resolution");
  if (resolutionElement) {
    resolutionElement.textContent = resolution;
  }
}

function updateStreamFPS(fps) {
  const fpsElement = document.getElementById("stream-fps");
  if (fpsElement) {
    fpsElement.textContent = fps === "N/A" ? fps : `${fps} FPS`;
  }
}

function updateStreamDevice(device) {
  const deviceElement = document.getElementById("stream-device");
  if (deviceElement) {
    deviceElement.textContent = device;
  }
}

function updateCodecStatus(codec) {
  const codecElement = document.getElementById("stream-codec");
  if (codecElement) {
    codecElement.textContent = codec;
  }
}

async function updateCodec(codec) {
  if (!currentCamera) {
    console.error("No camera selected for codec update");
    return;
  }

  try {
    const response = await fetch(`/api/cameras/codec`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ codec: codec }),
    });

    const result = await response.json();
    
    if (response.ok && result.success) {
      console.log("Codec updated successfully:", result);
      updateCodecStatus(codec);
      
      if (window.AOFVideoStream) {
        window.AOFVideoStream.showNotification(`Codec updated to ${codec}`, "success");
      }
    } else {
      console.error("Failed to update codec:", result.error);
      if (window.AOFVideoStream) {
        window.AOFVideoStream.showNotification(`Failed to update codec: ${result.error?.message || 'Unknown error'}`, "error");
      }
    }
  } catch (error) {
    console.error("Error updating codec:", error);
    if (window.AOFVideoStream) {
      window.AOFVideoStream.showNotification("Error updating codec", "error");
    }
  }
}

async function loadAvailableCodecs() {
  try {
    const response = await fetch("/api/cameras/codecs");
    const result = await response.json();
    
    if (response.ok && result.success && result.data.available_codecs) {
      const codecSelect = document.getElementById("codec-select");
      if (codecSelect) {
        // Clear existing options
        codecSelect.innerHTML = '<option value="">Auto</option>';
        
        // Add available codecs
        Object.entries(result.data.available_codecs).forEach(([category, codecs]) => {
          if (Array.isArray(codecs)) {
            codecs.forEach(codec => {
              const option = document.createElement("option");
              option.value = codec.fourcc;
              option.textContent = `${codec.name} (${codec.fourcc})${codec.hardware_accelerated ? ' - HW' : ''}`;
              codecSelect.appendChild(option);
            });
          }
        });
        
        // Select the current codec if available
        if (result.data.current_codec && result.data.current_codec.fourcc) {
          codecSelect.value = result.data.current_codec.fourcc;
          updateCodecStatus(result.data.current_codec.fourcc);
        }
      }
    }
  } catch (error) {
    console.error("Error loading available codecs:", error);
  }
}

function addStreamingModeToggle() {
  // Use the existing stream-mode-select element from HTML
  const modeSelect = document.getElementById("stream-mode-select");
  if (!modeSelect) return;

  // Add event listener to the existing select element
  modeSelect.addEventListener("change", function () {
    streamingMode = this.value;
    console.log("Streaming mode changed to:", streamingMode);

    if (window.AOFVideoStream) {
      const modeName = streamingMode === "websocket" ? "WebSocket (Standard)" : 
                      streamingMode === "webrtc" ? "WebRTC (High Performance)" :
                      "HTTP Polling (Compatible)";
      window.AOFVideoStream.showNotification(`Switched to ${modeName} mode`, "info");
    }

    // If currently streaming, restart with new mode
    if (streamActive) {
      const shouldRestart = confirm("Switching streaming mode will restart the current stream. Continue?");
      if (shouldRestart) {
        stopStream();
        setTimeout(() => {
          startStream();
        }, 1000);
      }
    }
  });
}

function getQualityValue(qualityString) {
  const qualityMap = {
    low: 60,
    medium: 85,
    high: 95,
    ultra: 98,
  };
  return qualityMap[qualityString] || 85;
}

function updateStreamInfo() {
  // This function can be used to periodically update stream information
  // from the backend API once it's implemented
  if (streamActive) {
    // Simulate frame rate calculation or other dynamic info updates
  }
}

function showPerformanceStats(show) {
  const performanceStats = document.getElementById('performance-stats');
  if (performanceStats) {
    performanceStats.style.display = show ? 'block' : 'none';
  }
}

// Update bitrate and quality display
function updateBitrateDisplay(bitrate, quality) {
  const bitrateElement = document.getElementById('stream-bitrate');
  const qualityElement = document.getElementById('stream-quality');
  
  if (bitrateElement) {
    bitrateElement.textContent = `${bitrate.toFixed(2)} Mbps`;
  }
  
  if (qualityElement) {
    qualityElement.textContent = `${quality}%`;
  }
}

// Update performance stats (for WebRTC)
function updatePerformanceStats(stats) {
  const chunkRate = document.getElementById('chunk-rate');
  const bufferSize = document.getElementById('buffer-size');
  const lostChunks = document.getElementById('lost-chunks');
  const reassemblyTime = document.getElementById('reassembly-time');
  
  if (chunkRate && stats.chunkRate !== undefined) {
    chunkRate.textContent = `${stats.chunkRate} chunks/s`;
  }
  
  if (bufferSize && stats.bufferSize !== undefined) {
    bufferSize.textContent = `${(stats.bufferSize / 1024).toFixed(1)} KB`;
  }
  
  if (lostChunks && stats.lostChunks !== undefined) {
    lostChunks.textContent = stats.lostChunks;
  }
  
  if (reassemblyTime && stats.reassemblyTime !== undefined) {
    reassemblyTime.textContent = `${stats.reassemblyTime} ms`;
  }
}

// Hardware Encoding Functions
function loadEncodingStatus() {
  fetch('/api/cameras/encoding/status')
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        const toggle = document.getElementById('hardware-encoding-toggle');
        if (toggle) {
          toggle.checked = data.data.hardware_encoding_enabled;
        }
        updateEncodingDisplay(data.data.performance);
      }
    })
    .catch(error => {
      console.error('Error loading encoding status:', error);
    });
}

function toggleHardwareEncoding() {
  const toggle = document.getElementById('hardware-encoding-toggle');
  const enabled = toggle.checked;
  
  const url = enabled ? '/api/cameras/encoding/enable' : '/api/cameras/encoding/disable';
  
  // Get current stream settings for encoder initialization
  const resolution = document.getElementById('resolution-select')?.value || '1920x1080';
  const fps = parseInt(document.getElementById('fps-select')?.value) || 60;
  const [width, height] = resolution.split('x').map(Number);
  
  const requestData = enabled ? { width, height, fps } : {};
  
  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(requestData)
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      const message = enabled ? 
        `Hardware encoding enabled (${data.data.performance?.encoding_method || 'Unknown'})` :
        'Hardware encoding disabled (using software)';
      
      if (window.AOFVideoStream) {
        window.AOFVideoStream.showNotification(message, 'success');
      }
      
      if (data.data.performance) {
        updateEncodingDisplay(data.data.performance);
      }
    } else {
      if (window.AOFVideoStream) {
        window.AOFVideoStream.showNotification(data.error.message || 'Failed to toggle hardware encoding', 'error');
      }
      // Revert toggle state
      toggle.checked = !enabled;
    }
  })
  .catch(error => {
    console.error('Error toggling hardware encoding:', error);
    if (window.AOFVideoStream) {
      window.AOFVideoStream.showNotification('Network error while toggling hardware encoding', 'error');
    }
    // Revert toggle state
    toggle.checked = !enabled;
  });
}

function updateEncodingStatus() {
  fetch('/api/cameras/encoding/performance')
    .then(response => response.json())
    .then(data => {
      if (data.success && data.data.performance) {
        updateEncodingDisplay(data.data.performance);
      }
    })
    .catch(error => {
      console.debug('Error updating encoding status:', error);
    });
}

function updateEncodingDisplay(performance) {
  const methodElement = document.getElementById('encoding-method');
  const framesElement = document.getElementById('frames-encoded');
  const avgTimeElement = document.getElementById('avg-encode-time');
  const capabilityElement = document.getElementById('encoding-fps-capability');
  
  if (methodElement) {
    const method = performance.encoding_method || 'Unknown';
    methodElement.textContent = method;
    
    // Add color coding
    if (method.includes('NVENC') || method.includes('QuickSync') || method.includes('VA-API')) {
      methodElement.className = 'status-value hardware-enabled';
    } else {
      methodElement.className = 'status-value hardware-disabled';
    }
  }
  
  if (framesElement) {
    framesElement.textContent = performance.frames_encoded || 0;
  }
  
  if (avgTimeElement) {
    const avgTime = performance.avg_encode_time || 0;
    avgTimeElement.textContent = `${(avgTime * 1000).toFixed(2)} ms`;
  }
  
  if (capabilityElement) {
    const capability = performance.fps_capability || 0;
    capabilityElement.textContent = `${capability.toFixed(1)} FPS`;
  }
}

// Make functions available globally for WebRTC client
window.updateBitrateDisplay = updateBitrateDisplay;
window.updatePerformanceStats = updatePerformanceStats;
