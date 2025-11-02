// Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// DOM Elements
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const monitoringStatus = document.getElementById('monitoring-status');
const totalRecords = document.getElementById('total-records');
const streamUrl = document.getElementById('stream-url');
const recordsTbody = document.getElementById('records-tbody');
const loadingOverlay = document.getElementById('loading-overlay');
const currentDatetime = document.getElementById('current-datetime');

// State
let isMonitoring = false;
let pollInterval = null;
let recordCount = 0;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    updateDateTime();
    setInterval(updateDateTime, 1000);
    checkStatus();
    
    startBtn.addEventListener('click', startMonitoring);
    stopBtn.addEventListener('click', stopMonitoring);
});

// Update current date and time
function updateDateTime() {
    const now = new Date();
    const options = { 
        weekday: 'short', 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    currentDatetime.textContent = now.toLocaleDateString('en-US', options);
}

// Start Monitoring
async function startMonitoring() {
    try {
        // Ask user for M3U8 URL
        const m3u8_url = prompt(
            '🎥 Paste the Fox News rendition.m3u8 URL:\n\n' +
            'Steps to get URL:\n' +
            '1. Open https://www.livenowfox.com/live\n' +
            '2. Press F12 → Go to Network tab\n' +
            '3. Type "m3u8" in filter box\n' +
            '4. Refresh page (F5)\n' +
            '5. Look for "rendition.m3u8" file\n' +
            '6. Right-click → Copy → Copy URL\n' +
            '7. Paste here\n\n' +
            '⚠️ Leave blank to use URL from config file:',
            ''
        );
        
        showLoading('Starting monitoring...');
        
        // Prepare request body
        const requestBody = m3u8_url && m3u8_url.trim() !== '' 
            ? { m3u8_url: m3u8_url.trim() }
            : {};
        
        const response = await fetch(`${API_BASE_URL}/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        
        const data = await response.json();
        
        if (data.success) {
            isMonitoring = true;
            updateUIState();
            startPolling();
            
            // Show success with stream info
            const message = data.m3u8_url 
                ? `✅ Monitoring started!\n\nStream: ${data.m3u8_url.substring(0, 60)}...`
                : '✅ Monitoring started successfully!';
            
            alert(message);
        } else {
            alert(`❌ ${data.message || 'Failed to start monitoring'}`);
        }
    } catch (error) {
        console.error('Error starting monitoring:', error);
        alert('❌ Error connecting to server. Make sure backend is running!');
    } finally {
        hideLoading();
    }
}

// Stop Monitoring
async function stopMonitoring() {
    try {
        showLoading('Stopping monitoring...');
        
        const response = await fetch(`${API_BASE_URL}/stop`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.success) {
            isMonitoring = false;
            updateUIState();
            stopPolling();
            alert('✅ Monitoring stopped');
        } else {
            alert(`❌ ${data.message || 'Failed to stop monitoring'}`);
        }
    } catch (error) {
        console.error('Error stopping monitoring:', error);
        alert('❌ Error connecting to server');
    } finally {
        hideLoading();
    }
}

// Check Status
async function checkStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/status`);
        const data = await response.json();
        
        isMonitoring = data.monitoring_active;
        recordCount = data.total_records;
        
        updateUIState();
        
        if (data.stream_status && data.stream_status.m3u8_url) {
            streamUrl.textContent = 'Connected';
        }
        
        if (isMonitoring && !pollInterval) {
            startPolling();
        }
    } catch (error) {
        console.error('Error checking status:', error);
    }
}

// Start Polling for Records
function startPolling() {
    if (pollInterval) return;
    
    // Poll every 5 seconds
    pollInterval = setInterval(async () => {
        await fetchRecords();
    }, 5000);
    
    // Fetch immediately
    fetchRecords();
}

// Stop Polling
function stopPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

// Fetch Records
async function fetchRecords() {
    try {
        const response = await fetch(`${API_BASE_URL}/records`);
        const data = await response.json();
        
        if (data.success) {
            updateRecordsTable(data.records);
            recordCount = data.count;
            totalRecords.textContent = recordCount;
        }
    } catch (error) {
        console.error('Error fetching records:', error);
    }
}

// Update Records Table
function updateRecordsTable(records) {
    if (!records || records.length === 0) {
        recordsTbody.innerHTML = `
            <tr class="no-data">
                <td colspan="5">No records yet. Click Start to begin monitoring.</td>
            </tr>
        `;
        return;
    }
    
    // Clear existing rows
    recordsTbody.innerHTML = '';
    
    // Add records (newest first)
    const sortedRecords = [...records].reverse();
    
    sortedRecords.forEach((record, index) => {
        const row = document.createElement('tr');
        if (index === 0) {
            row.classList.add('new-record');
        }
        
        row.innerHTML = `
            <td>${record.date_time}</td>
            <td>${record.video_time_start}</td>
            <td>${record.video_time_end}</td>
            <td>${truncateText(record.transcript, 200)}</td>
            <td><strong>${record.summary}</strong></td>
        `;
        
        recordsTbody.appendChild(row);
    });
}

// Update UI State
function updateUIState() {
    startBtn.disabled = isMonitoring;
    stopBtn.disabled = !isMonitoring;
    
    if (isMonitoring) {
        monitoringStatus.textContent = 'Active';
        monitoringStatus.classList.remove('stopped');
        monitoringStatus.classList.add('active');
    } else {
        monitoringStatus.textContent = 'Stopped';
        monitoringStatus.classList.remove('active');
        monitoringStatus.classList.add('stopped');
    }
    
    totalRecords.textContent = recordCount;
}

// Utility Functions
function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function showLoading(message = 'Loading...') {
    loadingOverlay.querySelector('p').textContent = message;
    loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    loadingOverlay.style.display = 'none';
}

// Auto-refresh status every 10 seconds
setInterval(checkStatus, 10000);