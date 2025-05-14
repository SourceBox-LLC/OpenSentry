// OpenSentry Remote Viewer Application
document.addEventListener('DOMContentLoaded', () => {
    // Snapshots management state
    let snapshots = [];
    let currentSnapshot = null;
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
    
    // Snapshot DOM Elements
    const loadSnapshotsBtn = document.getElementById('load-snapshots-btn');
    const deleteAllBtn = document.getElementById('delete-all-btn');
    const snapshotsGrid = document.getElementById('snapshots-grid');
    const snapshotsLoading = document.getElementById('snapshots-loading');
    const noSnapshotsEl = document.getElementById('no-snapshots');
    const snapshotModal = document.getElementById('snapshot-modal');
    const closeModalBtn = document.getElementById('close-modal-btn');
    const modalTitle = document.getElementById('modal-title');
    const modalImage = document.getElementById('modal-image');
    const modalObject = document.getElementById('modal-object');
    const modalTime = document.getElementById('modal-time');
    const modalFilename = document.getElementById('modal-filename');
    const downloadSnapshotBtn = document.getElementById('download-snapshot-btn');
    const deleteSnapshotBtn = document.getElementById('delete-snapshot-btn');

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
    
    // Event listeners for snapshot management
    loadSnapshotsBtn.addEventListener('click', loadSnapshots);
    deleteAllBtn.addEventListener('click', confirmDeleteAllSnapshots);
    closeModalBtn.addEventListener('click', closeSnapshotModal);
    deleteSnapshotBtn.addEventListener('click', deleteCurrentSnapshot);
    
    // Close modal when clicking outside of it
    snapshotModal.addEventListener('click', (e) => {
        if (e.target === snapshotModal) {
            closeSnapshotModal();
        }
    });

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
    
    // Load snapshots from server
    async function loadSnapshots() {
        if (!serverUrl) {
            updateServerStatus('Please connect to a server first', 'error');
            return;
        }
        
        // Show loading state
        snapshotsLoading.style.display = 'flex';
        noSnapshotsEl.style.display = 'none';
        // Clear existing snapshots
        const existingSnapshots = snapshotsGrid.querySelectorAll('.snapshot-item');
        existingSnapshots.forEach(item => item.remove());
        
        try {
            const response = await fetch(`${serverUrl}/snapshots`);
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }
            
            const data = await response.json();
            snapshots = data.snapshots || [];
            
            // Hide loading state
            snapshotsLoading.style.display = 'none';
            
            // Show no snapshots message if needed
            if (snapshots.length === 0) {
                noSnapshotsEl.style.display = 'flex';
                deleteAllBtn.disabled = true;
                return;
            }
            
            // Enable delete all button if we have snapshots
            deleteAllBtn.disabled = false;
            
            // Render snapshots
            renderSnapshots();
            
        } catch (error) {
            console.error('Error loading snapshots:', error);
            snapshotsLoading.style.display = 'none';
            noSnapshotsEl.style.display = 'flex';
            noSnapshotsEl.innerHTML = `
                <svg viewBox="0 0 24 24" width="48" height="48" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
                </svg>
                <p>Error loading snapshots: ${error.message}</p>
            `;
        }
    }
    
    // Render snapshots in the grid
    function renderSnapshots() {
        snapshots.forEach(snapshot => {
            const item = document.createElement('div');
            item.className = 'snapshot-item';
            item.dataset.filename = snapshot.filename;
            
            // Format timestamp
            const date = new Date(snapshot.timestamp * 1000);
            const formattedDate = date.toLocaleString();
            
            item.innerHTML = `
                <img src="${serverUrl}/static/snapshots/${snapshot.filename}" alt="${snapshot.detected_object}">
                <div class="snapshot-info">
                    <div class="snapshot-object">${snapshot.detected_object}</div>
                    <div class="snapshot-time">${formattedDate}</div>
                </div>
            `;
            
            // Add click event to open modal
            item.addEventListener('click', () => openSnapshotModal(snapshot));
            
            snapshotsGrid.appendChild(item);
        });
    }
    
    // Open modal with snapshot details
    function openSnapshotModal(snapshot) {
        currentSnapshot = snapshot;
        
        // Format timestamp
        const date = new Date(snapshot.timestamp * 1000);
        const formattedDate = date.toLocaleString();
        
        // Set modal content
        modalTitle.textContent = `${snapshot.detected_object} Detection`;
        modalImage.src = `${serverUrl}/static/snapshots/${snapshot.filename}`;
        modalObject.textContent = snapshot.detected_object;
        modalTime.textContent = formattedDate;
        modalFilename.textContent = snapshot.filename;
        
        // Set download link
        downloadSnapshotBtn.href = `${serverUrl}/static/snapshots/${snapshot.filename}`;
        downloadSnapshotBtn.download = snapshot.filename;
        
        // Show modal
        snapshotModal.style.display = 'flex';
        
        // Add body class to prevent scrolling
        document.body.classList.add('modal-open');
    }
    
    // Close snapshot modal
    function closeSnapshotModal() {
        snapshotModal.style.display = 'none';
        currentSnapshot = null;
        
        // Remove body class to allow scrolling
        document.body.classList.remove('modal-open');
    }
    
    // Delete current snapshot
    async function deleteCurrentSnapshot() {
        if (!currentSnapshot) return;
        
        try {
            const response = await fetch(`${serverUrl}/snapshots/${currentSnapshot.filename}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }
            
            // Close modal
            closeSnapshotModal();
            
            // Remove snapshot from UI
            const snapshotEl = snapshotsGrid.querySelector(`[data-filename="${currentSnapshot.filename}"]`);
            if (snapshotEl) {
                snapshotEl.remove();
            }
            
            // Remove from snapshots array
            snapshots = snapshots.filter(s => s.filename !== currentSnapshot.filename);
            
            // Show no snapshots message if needed
            if (snapshots.length === 0) {
                noSnapshotsEl.style.display = 'flex';
                deleteAllBtn.disabled = true;
            }
            
            // Show success message
            updateServerStatus(`Deleted snapshot: ${currentSnapshot.filename}`, 'success');
            
        } catch (error) {
            console.error('Error deleting snapshot:', error);
            updateServerStatus(`Error deleting snapshot: ${error.message}`, 'error');
        }
    }
    
    // Confirm and delete all snapshots
    function confirmDeleteAllSnapshots() {
        if (snapshots.length === 0) return;
        
        if (confirm(`Are you sure you want to delete all ${snapshots.length} snapshots? This cannot be undone.`)) {
            deleteAllSnapshots();
        }
    }
    
    // Delete all snapshots
    async function deleteAllSnapshots() {
        try {
            const response = await fetch(`${serverUrl}/snapshots`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }
            
            // Clear UI
            const existingSnapshots = snapshotsGrid.querySelectorAll('.snapshot-item');
            existingSnapshots.forEach(item => item.remove());
            
            // Clear snapshots array
            snapshots = [];
            
            // Show no snapshots message
            noSnapshotsEl.style.display = 'flex';
            deleteAllBtn.disabled = true;
            
            // Show success message
            updateServerStatus('All snapshots deleted successfully', 'success');
            
        } catch (error) {
            console.error('Error deleting all snapshots:', error);
            updateServerStatus(`Error deleting all snapshots: ${error.message}`, 'error');
        }
    }
});
