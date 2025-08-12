// Camera control JavaScript for AOF Video Stream
document.addEventListener('DOMContentLoaded', function() {
    console.log('AOF Video Stream - Camera JS Loaded');
    
    // Initialize camera interface
    initializeCameraInterface();
});

let streamActive = false;
let currentCamera = null;
let videoCanvas = null;
let canvasContext = null;

function initializeCameraInterface() {
    // Get DOM elements
    const cameraSelect = document.getElementById('camera-select');
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const refreshDevicesBtn = document.getElementById('refresh-devices-btn');
    const snapshotBtn = document.getElementById('snapshot-btn');
    const fullscreenBtn = document.getElementById('fullscreen-btn');
    const applySettingsBtn = document.getElementById('apply-settings-btn');
    
    videoCanvas = document.getElementById('video-canvas');
    canvasContext = videoCanvas.getContext('2d');
    
    // Set default canvas size
    videoCanvas.width = 640;
    videoCanvas.height = 480;
    
    // Event listeners
    if (startBtn) {
        startBtn.addEventListener('click', startStream);
    }
    
    if (stopBtn) {
        stopBtn.addEventListener('click', stopStream);
    }
    
    if (refreshDevicesBtn) {
        refreshDevicesBtn.addEventListener('click', refreshCameraDevices);
    }
    
    if (snapshotBtn) {
        snapshotBtn.addEventListener('click', takeSnapshot);
    }
    
    if (fullscreenBtn) {
        fullscreenBtn.addEventListener('click', toggleFullscreen);
    }
    
    if (applySettingsBtn) {
        applySettingsBtn.addEventListener('click', applyStreamSettings);
    }
    
    if (cameraSelect) {
        cameraSelect.addEventListener('change', onCameraSelectionChange);
    }
    
    // Initialize camera devices on load
    refreshCameraDevices();
    
    // Update stream info periodically
    setInterval(updateStreamInfo, 1000);
}

function refreshCameraDevices() {
    const cameraSelect = document.getElementById('camera-select');
    const refreshBtn = document.getElementById('refresh-devices-btn');
    
    if (refreshBtn) {
        refreshBtn.disabled = true;
        refreshBtn.textContent = '🔄 Detecting...';
    }
    
    // Call real API to get camera devices
    fetch('/api/cameras/?refresh=true')
        .then(response => response.json())
        .then(data => {
            // Clear existing options
            if (cameraSelect) {
                cameraSelect.innerHTML = '<option value="">Select Camera...</option>';
                
                if (data.success && data.data.cameras) {
                    data.data.cameras.forEach(device => {
                        const option = document.createElement('option');
                        option.value = device.index;
                        option.textContent = `Camera ${device.index}: ${device.name}`;
                        cameraSelect.appendChild(option);
                    });
                    
                    if (window.AOFVideoStream) {
                        window.AOFVideoStream.showNotification(`Found ${data.data.count} camera(s)`, 'success');
                    }
                } else {
                    if (window.AOFVideoStream) {
                        window.AOFVideoStream.showNotification('No cameras found', 'warning');
                    }
                }
            }
        })
        .catch(error => {
            console.error('Error fetching camera devices:', error);
            if (window.AOFVideoStream) {
                window.AOFVideoStream.showNotification('Error detecting cameras', 'error');
            }
        })
        .finally(() => {
            if (refreshBtn) {
                refreshBtn.disabled = false;
                refreshBtn.textContent = '🔄 Refresh Devices';
            }
        });
}

function onCameraSelectionChange() {
    const cameraSelect = document.getElementById('camera-select');
    const startBtn = document.getElementById('start-btn');
    
    if (cameraSelect && startBtn) {
        startBtn.disabled = !cameraSelect.value;
        
        if (cameraSelect.value) {
            updateStreamDevice(`Camera ${cameraSelect.value}`);
        } else {
            updateStreamDevice('None');
        }
    }
}

function startStream() {
    const cameraSelect = document.getElementById('camera-select');
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const snapshotBtn = document.getElementById('snapshot-btn');
    const fullscreenBtn = document.getElementById('fullscreen-btn');
    const resolutionSelect = document.getElementById('resolution-select');
    const fpsSelect = document.getElementById('fps-select');
    
    if (!cameraSelect || !cameraSelect.value) {
        if (window.AOFVideoStream) {
            window.AOFVideoStream.showNotification('Please select a camera first', 'warning');
        }
        return;
    }
    
    currentCamera = cameraSelect.value;
    console.log(`Selected camera: ${currentCamera}`);
    // Get selected resolution and FPS
    let resolution = resolutionSelect ? resolutionSelect.value : '640x480';
    let fps = fpsSelect ? parseInt(fpsSelect.value) : 30;
    
    // Parse resolution
    const [width, height] = resolution.split('x').map(Number);
    
    // Update UI to show starting state
    if (startBtn) startBtn.disabled = true;
    updateStreamStatus('Starting...');
    
    // Call API to start camera stream
    fetch('/api/cameras/start', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            camera_index: parseInt(currentCamera),
            resolution: [width, height],
            fps: fps
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            streamActive = true;
            
            // Update UI
            if (stopBtn) stopBtn.disabled = false;
            if (snapshotBtn) snapshotBtn.disabled = false;
            if (fullscreenBtn) fullscreenBtn.disabled = false;
            if (cameraSelect) cameraSelect.disabled = true;
            
            // Hide placeholder and show canvas
            const placeholder = document.getElementById('video-placeholder');
            if (placeholder) {
                placeholder.style.display = 'none';
            }
            
            // Update stream info
            updateStreamStatus('Active');
            updateStreamResolution(resolution);
            updateStreamFPS(fps.toString());
            
            // Start video feed
            startVideoFeed();
            
            if (window.AOFVideoStream) {
                window.AOFVideoStream.showNotification('Stream started successfully', 'success');
            }
        } else {
            // Reset UI on failure
            if (startBtn) startBtn.disabled = false;
            updateStreamStatus('Failed');
            
            if (window.AOFVideoStream) {
                window.AOFVideoStream.showNotification(data.error?.message || 'Failed to start stream', 'error');
            }
        }
    })
    .catch(error => {
        console.error('Error starting stream:', error);
        // Reset UI on error
        if (startBtn) startBtn.disabled = false;
        updateStreamStatus('Error');
        
        if (window.AOFVideoStream) {
            window.AOFVideoStream.showNotification('Error starting stream', 'error');
        }
    });
}

function stopStream() {
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const snapshotBtn = document.getElementById('snapshot-btn');
    const fullscreenBtn = document.getElementById('fullscreen-btn');
    const cameraSelect = document.getElementById('camera-select');
    
    updateStreamStatus('Stopping...');
    
    // Call API to stop camera stream
    fetch('/api/cameras/stop', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            streamActive = false;
            currentCamera = null;
            
            // Stop video feed
            stopVideoFeed();
            
            // Update UI
            if (startBtn) startBtn.disabled = false;
            if (stopBtn) stopBtn.disabled = true;
            if (snapshotBtn) snapshotBtn.disabled = true;
            if (fullscreenBtn) fullscreenBtn.disabled = true;
            if (cameraSelect) cameraSelect.disabled = false;
            
            // Show placeholder and hide canvas content
            const placeholder = document.getElementById('video-placeholder');
            if (placeholder) {
                placeholder.style.display = 'flex';
            }
            
            // Clear canvas
            if (canvasContext) {
                canvasContext.clearRect(0, 0, videoCanvas.width, videoCanvas.height);
            }
            
            // Update stream info
            updateStreamStatus('Stopped');
            updateStreamResolution('N/A');
            updateStreamFPS('N/A');
            updateStreamDevice('None');
            
            if (window.AOFVideoStream) {
                window.AOFVideoStream.showNotification('Stream stopped successfully', 'success');
            }
        } else {
            updateStreamStatus('Error');
            if (window.AOFVideoStream) {
                window.AOFVideoStream.showNotification(data.error?.message || 'Failed to stop stream', 'error');
            }
        }
    })
    .catch(error => {
        console.error('Error stopping stream:', error);
        updateStreamStatus('Error');
        if (window.AOFVideoStream) {
            window.AOFVideoStream.showNotification('Error stopping stream', 'error');
        }
    });
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
    
    fetch('/api/cameras/frame')
        .then(response => {
            if (response.ok) {
                return response.blob();
            } else {
                throw new Error('Failed to fetch frame');
            }
        })
        .then(blob => {
            const img = new Image();
            img.onload = function() {
                // Draw the image to canvas
                canvasContext.clearRect(0, 0, videoCanvas.width, videoCanvas.height);
                canvasContext.drawImage(img, 0, 0, videoCanvas.width, videoCanvas.height);
                URL.revokeObjectURL(img.src);
            };
            img.src = URL.createObjectURL(blob);
        })
        .catch(error => {
            // Only log errors occasionally to avoid spam
            if (Math.random() < 0.01) { // 1% chance to log
                console.warn('Frame fetch error:', error);
            }
        });
}

function takeSnapshot() {
    if (!streamActive || !videoCanvas) {
        if (window.AOFVideoStream) {
            window.AOFVideoStream.showNotification('No active stream to capture', 'warning');
        }
        return;
    }
    
    // Get current frame from API and save it
    fetch('/api/cameras/frame')
        .then(response => {
            if (response.ok) {
                return response.blob();
            } else {
                throw new Error('Failed to fetch frame for snapshot');
            }
        })
        .then(blob => {
            // Create download link
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `snapshot_${new Date().toISOString().replace(/[:.]/g, '-')}.jpg`;
            a.click();
            URL.revokeObjectURL(url);
            
            if (window.AOFVideoStream) {
                window.AOFVideoStream.showNotification('Snapshot saved', 'success');
            }
        })
        .catch(error => {
            console.error('Snapshot error:', error);
            if (window.AOFVideoStream) {
                window.AOFVideoStream.showNotification('Failed to take snapshot', 'error');
            }
        });
}

function toggleFullscreen() {
    if (!videoCanvas) return;
    
    if (!document.fullscreenElement) {
        videoCanvas.requestFullscreen().then(() => {
            if (window.AOFVideoStream) {
                window.AOFVideoStream.showNotification('Entered fullscreen mode', 'info');
            }
        }).catch(err => {
            console.error('Failed to enter fullscreen:', err);
        });
    } else {
        document.exitFullscreen().then(() => {
            if (window.AOFVideoStream) {
                window.AOFVideoStream.showNotification('Exited fullscreen mode', 'info');
            }
        });
    }
}

function applyStreamSettings() {
    const resolutionSelect = document.getElementById('resolution-select');
    const fpsSelect = document.getElementById('fps-select');
    const qualitySelect = document.getElementById('quality-select');
    
    if (resolutionSelect && fpsSelect && qualitySelect) {
        const resolution = resolutionSelect.value;
        const fps = fpsSelect.value;
        const quality = qualitySelect.value;
        
        // Apply resolution to canvas
        if (videoCanvas) {
            const [width, height] = resolution.split('x').map(Number);
            videoCanvas.width = width;
            videoCanvas.height = height;
        }
        
        // Update display info
        updateStreamResolution(resolution);
        updateStreamFPS(fps);
        
        if (window.AOFVideoStream) {
            window.AOFVideoStream.showNotification(
                `Settings applied: ${resolution} @ ${fps}fps (${quality} quality)`, 
                'success'
            );
        }
    }
}

// Stream info update functions
function updateStreamStatus(status) {
    const statusElement = document.getElementById('stream-status');
    if (statusElement) {
        statusElement.textContent = status;
        statusElement.className = 'info-value';
        
        if (status === 'Active') {
            statusElement.classList.add('status-online');
        }
    }
}

function updateStreamResolution(resolution) {
    const resolutionElement = document.getElementById('stream-resolution');
    if (resolutionElement) {
        resolutionElement.textContent = resolution;
    }
}

function updateStreamFPS(fps) {
    const fpsElement = document.getElementById('stream-fps');
    if (fpsElement) {
        fpsElement.textContent = fps === 'N/A' ? fps : `${fps} FPS`;
    }
}

function updateStreamDevice(device) {
    const deviceElement = document.getElementById('stream-device');
    if (deviceElement) {
        deviceElement.textContent = device;
    }
}

function updateStreamInfo() {
    // This function can be used to periodically update stream information
    // from the backend API once it's implemented
    if (streamActive) {
        // Simulate frame rate calculation or other dynamic info updates
    }
}
