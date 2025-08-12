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
    
    // Simulate device detection (will be replaced with actual API call)
    setTimeout(() => {
        // Clear existing options
        if (cameraSelect) {
            cameraSelect.innerHTML = '<option value="">Select Camera...</option>';
            
            // Add mock camera devices (will be replaced with real data)
            const mockDevices = [
                { id: 0, name: 'Built-in Camera' },
                { id: 1, name: 'USB Camera' }
            ];
            
            mockDevices.forEach(device => {
                const option = document.createElement('option');
                option.value = device.id;
                option.textContent = `Camera ${device.id}: ${device.name}`;
                cameraSelect.appendChild(option);
            });
        }
        
        if (refreshBtn) {
            refreshBtn.disabled = false;
            refreshBtn.textContent = '🔄 Refresh Devices';
        }
        
        if (window.AOFVideoStream) {
            window.AOFVideoStream.showNotification('Camera devices refreshed', 'success');
        }
    }, 2000);
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
    
    if (!cameraSelect || !cameraSelect.value) {
        if (window.AOFVideoStream) {
            window.AOFVideoStream.showNotification('Please select a camera first', 'warning');
        }
        return;
    }
    
    currentCamera = cameraSelect.value;
    streamActive = true;
    
    // Update UI
    if (startBtn) startBtn.disabled = true;
    if (stopBtn) stopBtn.disabled = false;
    if (snapshotBtn) snapshotBtn.disabled = false;
    if (fullscreenBtn) fullscreenBtn.disabled = false;
    if (cameraSelect) cameraSelect.disabled = true;
    
    // Hide placeholder and show canvas
    const placeholder = document.getElementById('video-placeholder');
    if (placeholder) {
        placeholder.style.display = 'none';
    }
    
    // Update stream status
    updateStreamStatus('Starting...');
    
    // Simulate stream start (will be replaced with actual WebSocket connection)
    setTimeout(() => {
        updateStreamStatus('Active');
        updateStreamResolution('640x480');
        updateStreamFPS('30');
        
        // Start mock video feed
        startMockVideoFeed();
        
        if (window.AOFVideoStream) {
            window.AOFVideoStream.showNotification('Stream started successfully', 'success');
        }
    }, 1000);
}

function stopStream() {
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const snapshotBtn = document.getElementById('snapshot-btn');
    const fullscreenBtn = document.getElementById('fullscreen-btn');
    const cameraSelect = document.getElementById('camera-select');
    
    streamActive = false;
    currentCamera = null;
    
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
    if (canvasContext && videoCanvas) {
        canvasContext.clearRect(0, 0, videoCanvas.width, videoCanvas.height);
    }
    
    // Update stream info
    updateStreamStatus('Stopped');
    updateStreamResolution('N/A');
    updateStreamFPS('N/A');
    updateStreamDevice('None');
    
    if (window.AOFVideoStream) {
        window.AOFVideoStream.showNotification('Stream stopped', 'info');
    }
}

function startMockVideoFeed() {
    // Mock video feed with animated pattern
    let frame = 0;
    
    function drawFrame() {
        if (!streamActive || !canvasContext || !videoCanvas) return;
        
        const width = videoCanvas.width;
        const height = videoCanvas.height;
        
        // Create animated pattern
        canvasContext.fillStyle = `hsl(${frame % 360}, 50%, 20%)`;
        canvasContext.fillRect(0, 0, width, height);
        
        // Add grid pattern
        canvasContext.strokeStyle = `hsl(${(frame + 180) % 360}, 70%, 50%)`;
        canvasContext.lineWidth = 2;
        
        for (let x = 0; x < width; x += 50) {
            canvasContext.beginPath();
            canvasContext.moveTo(x, 0);
            canvasContext.lineTo(x, height);
            canvasContext.stroke();
        }
        
        for (let y = 0; y < height; y += 50) {
            canvasContext.beginPath();
            canvasContext.moveTo(0, y);
            canvasContext.lineTo(width, y);
            canvasContext.stroke();
        }
        
        // Add center text
        canvasContext.fillStyle = 'white';
        canvasContext.font = '24px Arial';
        canvasContext.textAlign = 'center';
        canvasContext.fillText('MOCK VIDEO FEED', width / 2, height / 2 - 20);
        canvasContext.fillText(`Frame: ${frame}`, width / 2, height / 2 + 20);
        
        frame++;
        
        if (streamActive) {
            setTimeout(drawFrame, 1000 / 30); // 30 FPS
        }
    }
    
    drawFrame();
}

function takeSnapshot() {
    if (!streamActive || !videoCanvas) {
        if (window.AOFVideoStream) {
            window.AOFVideoStream.showNotification('No active stream to capture', 'warning');
        }
        return;
    }
    
    // Create download link
    videoCanvas.toBlob(function(blob) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `snapshot_${new Date().toISOString().replace(/[:.]/g, '-')}.png`;
        a.click();
        URL.revokeObjectURL(url);
        
        if (window.AOFVideoStream) {
            window.AOFVideoStream.showNotification('Snapshot saved', 'success');
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
