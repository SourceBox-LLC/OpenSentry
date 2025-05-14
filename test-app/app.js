// OpenSentry Remote Viewer Application
document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const cameraFeed = document.getElementById('camera-feed');
    const serverUrlInput = document.getElementById('server-url');
    const connectBtn = document.getElementById('connect-btn');
    const fullscreenBtn = document.getElementById('fullscreen-btn');
    const refreshBtn = document.getElementById('refresh-btn');
    const retryBtn = document.getElementById('retry-btn');
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    const loadingOverlay = document.getElementById('loading-overlay');
    const errorOverlay = document.getElementById('error-overlay');
    const serverStatus = document.getElementById('server-status');
    const detectionStatus = document.getElementById('detection-status');

    // State
    let serverUrl = '';
    let isConnected = false;
    let connectionCheckInterval = null;

    // Try to load last used server URL from localStorage
    const savedUrl = localStorage.getItem('opensentry_server_url');
    if (savedUrl) {
        serverUrlInput.value = savedUrl;
    }

    // Initialize UI
    loadingOverlay.classList.add('hidden');
    
    // Event Listeners
    connectBtn.addEventListener('click', connectToServer);
    refreshBtn.addEventListener('click', refreshStream);
    retryBtn.addEventListener('click', retryConnection);
    fullscreenBtn.addEventListener('click', toggleFullscreen);
    
    // Auto-connect if URL is saved
    if (savedUrl) {
        setTimeout(() => {
            connectToServer();
        }, 500);
    }

    // Connect to the specified server
    function connectToServer() {
        serverUrl = serverUrlInput.value.trim();
        
        if (!serverUrl) {
            updateServerStatus('Please enter a valid server URL', 'error');
            return;
        }
        
        // Remove trailing slash if present
        if (serverUrl.endsWith('/')) {
            serverUrl = serverUrl.slice(0, -1);
        }
        
        // Add protocol if missing
        if (!serverUrl.startsWith('http://') && !serverUrl.startsWith('https://')) {
            serverUrl = 'http://' + serverUrl;
            serverUrlInput.value = serverUrl;
        }
        
        // Save URL to localStorage
        localStorage.setItem('opensentry_server_url', serverUrl);
        
        // Update UI to connecting state
        updateConnectionStatus('connecting');
        loadingOverlay.classList.remove('hidden');
        errorOverlay.classList.add('hidden');
        
        // Check server status first
        checkServerStatus()
            .then(status => {
                if (status.ok) {
                    // Connect to video stream
                    connectToStream();
                    // Start periodic status checks
                    startStatusChecks();
                    updateServerStatus(`Connected to OpenSentry server. Detecting: ${status.detecting.join(', ')}`, 'success');
                    updateDetectionStatus(status.detecting);
                } else {
                    throw new Error('Server status check failed');
                }
            })
            .catch(error => {
                console.error('Server connection error:', error);
                connectionFailed('Could not connect to server. Please check the URL and try again.');
            });
    }

    // Connect to the video stream
    function connectToStream() {
        // Set the camera feed source to the stream endpoint
        cameraFeed.src = `${serverUrl}/stream`;
        
        // Handle successful connection
        cameraFeed.onload = () => {
            loadingOverlay.classList.add('hidden');
            updateConnectionStatus('connected');
            isConnected = true;
        };
        
        // Handle connection errors
        cameraFeed.onerror = () => {
            connectionFailed('Failed to load video stream.');
        };
    }

    // Check server status
    async function checkServerStatus() {
        try {
            const response = await fetch(`${serverUrl}/status`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                },
                timeout: 5000
            });
            
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }
            
            const data = await response.json();
            return {
                ok: true,
                status: data.status,
                timestamp: data.timestamp,
                detecting: data.detecting
            };
        } catch (error) {
            console.error('Status check failed:', error);
            return { ok: false };
        }
    }

    // Start periodic status checks
    function startStatusChecks() {
        if (connectionCheckInterval) {
            clearInterval(connectionCheckInterval);
        }
        
        connectionCheckInterval = setInterval(async () => {
            try {
                const status = await checkServerStatus();
                if (!status.ok && isConnected) {
                    // Connection was lost
                    connectionFailed('Connection to server lost.');
                } else if (status.ok && !isConnected) {
                    // Reconnected
                    loadingOverlay.classList.add('hidden');
                    errorOverlay.classList.add('hidden');
                    updateConnectionStatus('connected');
                    isConnected = true;
                    updateDetectionStatus(status.detecting);
                }
            } catch (error) {
                console.error('Status check error:', error);
            }
        }, 10000); // Check every 10 seconds
    }

    // Handle connection failure
    function connectionFailed(message) {
        loadingOverlay.classList.add('hidden');
        errorOverlay.classList.remove('hidden');
        updateConnectionStatus('disconnected');
        updateServerStatus(message, 'error');
        isConnected = false;
    }

    // Refresh the video stream
    function refreshStream() {
        if (!serverUrl) return;
        
        loadingOverlay.classList.remove('hidden');
        updateConnectionStatus('connecting');
        
        // Reset the stream by changing the src
        const currentSrc = cameraFeed.src;
        cameraFeed.src = '';
        
        // Short delay before reconnecting
        setTimeout(() => {
            cameraFeed.src = currentSrc;
        }, 1000);
    }

    // Retry connection after failure
    function retryConnection() {
        errorOverlay.classList.add('hidden');
        loadingOverlay.classList.remove('hidden');
        connectToServer();
    }

    // Toggle fullscreen mode
    function toggleFullscreen() {
        if (!document.fullscreenElement) {
            if (cameraFeed.requestFullscreen) {
                cameraFeed.requestFullscreen();
            } else if (cameraFeed.webkitRequestFullscreen) {
                cameraFeed.webkitRequestFullscreen();
            } else if (cameraFeed.msRequestFullscreen) {
                cameraFeed.msRequestFullscreen();
            }
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            }
        }
    }

    // Update connection status indicators
    function updateConnectionStatus(status) {
        statusIndicator.className = 'status-indicator';
        
        switch(status) {
            case 'connected':
                statusIndicator.classList.add('status-connected');
                statusText.textContent = 'Connected';
                break;
            case 'connecting':
                statusIndicator.classList.add('status-connecting');
                statusText.textContent = 'Connecting...';
                break;
            case 'disconnected':
            default:
                statusIndicator.classList.add('status-disconnected');
                statusText.textContent = 'Disconnected';
                break;
        }
    }

    // Update server status message
    function updateServerStatus(message, type = 'info') {
        serverStatus.innerHTML = `<p class="status-${type}">${message}</p>`;
    }

    // Update detection status information
    function updateDetectionStatus(detecting) {
        if (!detecting || detecting.length === 0) {
            detectionStatus.textContent = 'No objects configured for detection';
            return;
        }
        
        const detectionHTML = `
            <p>The server is currently configured to detect:</p>
            <ul class="detection-list">
                ${detecting.map(item => `<li>${item}</li>`).join('')}
            </ul>
            <p class="detection-note">Objects will be highlighted with bounding boxes when detected in the video feed.</p>
        `;
        
        detectionStatus.innerHTML = detectionHTML;
    }
});
