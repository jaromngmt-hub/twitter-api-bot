// Twitter Monitor Bot - Frontend JavaScript

const API_URL = '/api';

// State
let users = [];
let channels = [];
let isRunning = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadData();
    setInterval(loadData, 5000); // Refresh every 5 seconds
});

// Load all data
async function loadData() {
    try {
        await Promise.all([
            loadStatus(),
            loadUsers(),
            loadChannels()
        ]);
    } catch (error) {
        console.error('Error loading data:', error);
        addLog('Failed to load data from API', 'error');
    }
}

// Load status
async function loadStatus() {
    try {
        const response = await fetch(`${API_URL}/status`);
        const data = await response.json();
        
        isRunning = data.running;
        updateStatusUI(data);
    } catch (error) {
        console.error('Error loading status:', error);
    }
}

// Update status UI
function updateStatusUI(data) {
    document.getElementById('usersCount').textContent = data.users_count;
    document.getElementById('channelsCount').textContent = data.channels_count;
    document.getElementById('creditsCount').textContent = formatNumber(data.credits_remaining);
    
    const interval = data.interval;
    const intervalText = interval < 60 ? `${interval}s` : 
                        interval < 3600 ? `${Math.floor(interval/60)}m` : 
                        `${Math.floor(interval/3600)}h`;
    document.getElementById('intervalDisplay').textContent = intervalText;
    
    // Update status indicator
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    
    if (data.running) {
        statusDot.className = 'status-dot running';
        statusText.textContent = 'Running';
        document.getElementById('startBtn').disabled = true;
        document.getElementById('stopBtn').disabled = false;
    } else {
        statusDot.className = 'status-dot stopped';
        statusText.textContent = 'Stopped';
        document.getElementById('startBtn').disabled = false;
        document.getElementById('stopBtn').disabled = true;
    }
}

// Load users
async function loadUsers() {
    try {
        const response = await fetch(`${API_URL}/users`);
        users = await response.json();
        renderUsers();
        updateChannelFilter();
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

// Render users table
function renderUsers() {
    const filter = document.getElementById('userFilter').value.toLowerCase();
    const channelFilter = document.getElementById('channelFilter').value;
    
    const filteredUsers = users.filter(u => {
        const matchesFilter = u.username.toLowerCase().includes(filter);
        const matchesChannel = !channelFilter || u.channel_name === channelFilter;
        return matchesFilter && matchesChannel;
    });
    
    const tbody = document.getElementById('usersTableBody');
    
    if (filteredUsers.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="empty-state">
                    <i class="fas fa-inbox"></i>
                    <p>No users found</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = filteredUsers.map(user => `
        <tr>
            <td><strong>@${user.username}</strong></td>
            <td>${user.channel_name}</td>
            <td>
                <span class="status-badge ${user.is_active ? 'active' : 'inactive'}">
                    ${user.is_active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td>${user.last_tweet_id ? user.last_tweet_id.substring(0, 15) + '...' : '-'}</td>
            <td>${formatDate(user.added_at)}</td>
            <td>
                <button class="btn btn-danger btn-small" onclick="deleteUser('${user.username}')">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

// Load channels
async function loadChannels() {
    try {
        const response = await fetch(`${API_URL}/channels`);
        channels = await response.json();
        renderChannels();
        updateChannelSelect();
    } catch (error) {
        console.error('Error loading channels:', error);
    }
}

// Render channels table
function renderChannels() {
    const tbody = document.getElementById('channelsTableBody');
    
    if (channels.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="empty-state">
                    <i class="fas fa-inbox"></i>
                    <p>No channels found</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = channels.map(channel => `
        <tr>
            <td><strong>${channel.name}</strong></td>
            <td class="webhook-url" title="${channel.webhook_url}">${channel.webhook_url}</td>
            <td>${channel.user_count}</td>
            <td>${formatDate(channel.created_at)}</td>
            <td>
                <button class="btn btn-danger btn-small" onclick="deleteChannel('${channel.name}')">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

// Update channel select dropdown
function updateChannelSelect() {
    const select = document.getElementById('channelSelect');
    const currentValue = select.value;
    
    select.innerHTML = '<option value="">Select Channel...</option>' +
        channels.map(c => `<option value="${c.name}">${c.name}</option>`).join('');
    
    if (currentValue) {
        select.value = currentValue;
    }
}

// Update channel filter dropdown
function updateChannelFilter() {
    const select = document.getElementById('channelFilter');
    const currentValue = select.value;
    
    select.innerHTML = '<option value="">All Channels</option>' +
        channels.map(c => `<option value="${c.name}">${c.name}</option>`).join('');
    
    if (currentValue) {
        select.value = currentValue;
    }
}

// Add user
async function addUser() {
    const username = document.getElementById('newUsername').value.trim();
    const channelName = document.getElementById('channelSelect').value;
    
    if (!username) {
        showToast('Please enter a username', 'error');
        return;
    }
    if (!channelName) {
        showToast('Please select a channel', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/users`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, channel_name: channelName })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message, 'success');
            addLog(data.message, 'success');
            document.getElementById('newUsername').value = '';
            loadUsers();
        } else {
            showToast(data.detail || 'Failed to add user', 'error');
        }
    } catch (error) {
        console.error('Error adding user:', error);
        showToast('Failed to add user', 'error');
    }
}

// Delete user
async function deleteUser(username) {
    if (!confirm(`Are you sure you want to remove @${username}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/users/${username}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message, 'success');
            addLog(data.message, 'success');
            loadUsers();
        } else {
            showToast(data.detail || 'Failed to remove user', 'error');
        }
    } catch (error) {
        console.error('Error deleting user:', error);
        showToast('Failed to remove user', 'error');
    }
}

// Add channel
async function addChannel() {
    const name = document.getElementById('newChannelName').value.trim();
    const webhookUrl = document.getElementById('newWebhookUrl').value.trim();
    
    if (!name) {
        showToast('Please enter a channel name', 'error');
        return;
    }
    if (!webhookUrl) {
        showToast('Please enter a webhook URL', 'error');
        return;
    }
    if (!webhookUrl.startsWith('https://discord.com/api/webhooks/')) {
        showToast('Please enter a valid Discord webhook URL', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/channels`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, webhook_url: webhookUrl })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message, 'success');
            addLog(data.message, 'success');
            document.getElementById('newChannelName').value = '';
            document.getElementById('newWebhookUrl').value = '';
            loadChannels();
        } else {
            showToast(data.detail || 'Failed to add channel', 'error');
        }
    } catch (error) {
        console.error('Error adding channel:', error);
        showToast('Failed to add channel', 'error');
    }
}

// Delete channel
async function deleteChannel(channelName) {
    if (!confirm(`Are you sure you want to delete channel '${channelName}' and all its users?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/channels/${channelName}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message, 'success');
            addLog(data.message, 'success');
            loadChannels();
            loadUsers();
        } else {
            showToast(data.detail || 'Failed to delete channel', 'error');
        }
    } catch (error) {
        console.error('Error deleting channel:', error);
        showToast('Failed to delete channel', 'error');
    }
}

// Start monitor
async function startMonitor() {
    try {
        const response = await fetch(`${API_URL}/monitor/start`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
            addLog('Monitor started', 'success');
            loadStatus();
        } else {
            showToast(data.message, 'info');
        }
    } catch (error) {
        console.error('Error starting monitor:', error);
        showToast('Failed to start monitor', 'error');
    }
}

// Stop monitor
async function stopMonitor() {
    try {
        const response = await fetch(`${API_URL}/monitor/stop`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
            addLog('Monitor stopped', 'warning');
            loadStatus();
        } else {
            showToast(data.message, 'info');
        }
    } catch (error) {
        console.error('Error stopping monitor:', error);
        showToast('Failed to stop monitor', 'error');
    }
}

// Run once
async function runOnce() {
    try {
        const response = await fetch(`${API_URL}/monitor/run-once`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
            addLog('Single check started', 'info');
        }
    } catch (error) {
        console.error('Error running once:', error);
        showToast('Failed to run check', 'error');
    }
}

// Filter users
function filterUsers() {
    renderUsers();
}

// Filter by channel
function filterByChannel() {
    renderUsers();
}

// Refresh all data
function refreshData() {
    showToast('Refreshing...', 'info');
    loadData();
}

// Show toast notification
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = type === 'success' ? 'check-circle' : 
                 type === 'error' ? 'exclamation-circle' : 'info-circle';
    
    toast.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Add log entry
function addLog(message, type = 'info') {
    const container = document.getElementById('logsContainer');
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    
    const time = new Date().toLocaleTimeString();
    entry.textContent = `[${time}] ${message}`;
    
    container.appendChild(entry);
    container.scrollTop = container.scrollHeight;
}

// Format number
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'k';
    }
    return num.toString();
}

// Format date
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Handle Enter key in inputs
document.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        if (e.target.id === 'newUsername') {
            addUser();
        } else if (e.target.id === 'newChannelName' || e.target.id === 'newWebhookUrl') {
            addChannel();
        }
    }
});
