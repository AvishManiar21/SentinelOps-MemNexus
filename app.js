/* ==============================================================================
   SentinelOps Frontend Controller Integration
   Bridges the Obsidian SRE Console dynamically to the live Python Flask API
   ============================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // Automatically resolve API base URL (local dev or production Cloud Run deployment)
    const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:5000'
        : 'https://sentinelops-api-782741881130.us-central1.run.app';

    // ---------------------------------------------------------
    // 0. Sidebar Toggle (Hamburger Menu)
    // ---------------------------------------------------------
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const body = document.body;

    // Load sidebar state from localStorage
    const savedSidebarState = localStorage.getItem('sidebarState') || 'expanded';
    body.setAttribute('data-sidebar', savedSidebarState);

    // Update hamburger menu active state based on sidebar state
    if (savedSidebarState === 'collapsed') {
        sidebarToggle.classList.add('active');
    }

    // Toggle sidebar on hamburger click
    sidebarToggle.addEventListener('click', () => {
        const currentState = body.getAttribute('data-sidebar');
        const newState = currentState === 'expanded' ? 'collapsed' : 'expanded';

        // Update state
        body.setAttribute('data-sidebar', newState);
        sidebarToggle.classList.toggle('active');

        // Save to localStorage
        localStorage.setItem('sidebarState', newState);

        // Log for debugging
        console.log('Sidebar toggled:', newState);
    });

    // Close sidebar on overlay click (mobile)
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('sidebar-overlay')) {
            body.setAttribute('data-sidebar', 'collapsed');
            sidebarToggle.classList.add('active');
            localStorage.setItem('sidebarState', 'collapsed');
        }
    });

    // ---------------------------------------------------------
    // 0.5. Global Search Functionality - Content Search + Commands + Suggestions
    // ---------------------------------------------------------
    const globalSearch = document.getElementById('global-search');
    const searchResults = document.getElementById('search-results');
    const searchResultsBody = document.getElementById('search-results-body');
    const searchResultsTitle = document.getElementById('search-results-title');
    const searchResultsCount = document.getElementById('search-results-count');

    let searchHistory = JSON.parse(localStorage.getItem('searchHistory') || '[]');

    // Commands palette
    const commands = [
        { name: 'Show Latest Incidents', action: () => switchTab('incident-command'), keywords: ['incident', 'alert', 'show'] },
        { name: 'Open Chat', action: () => switchTab('diagnostic-chat'), keywords: ['chat', 'talk', 'diagnose'] },
        { name: 'View Database', action: () => switchTab('memory-core'), keywords: ['database', 'mongodb', 'memory'] },
        { name: 'Upload Runbook', action: () => switchTab('runbook-ingester'), keywords: ['runbook', 'upload', 'ingest'] },
        { name: 'Clear Chat History', action: () => { document.getElementById('chat-messages-container').innerHTML = ''; }, keywords: ['clear', 'reset', 'delete'] }
    ];

    async function searchContent(query) {
        const results = [];
        const queryLower = query.toLowerCase();

        try {
            // Fetch database collections
            const res = await fetch(`${API_BASE}/api/db/collections`);
            if (res.ok) {
                const data = await res.json();

                // Search in sessions (chat history)
                if (data.sessions) {
                    data.sessions.forEach(session => {
                        const userMsg = (session.user_message || '').toLowerCase();
                        const agentResp = (session.agent_response || '').toLowerCase();

                        if (userMsg.includes(queryLower) || agentResp.includes(queryLower)) {
                            results.push({
                                type: 'chat',
                                title: `Chat: ${session.user_message?.substring(0, 50) || 'Conversation'}...`,
                                preview: session.agent_response?.substring(0, 120) || '',
                                action: () => switchTab('diagnostic-chat')
                            });
                        }
                    });
                }

                // Search in runbooks (knowledge vectors)
                if (data.knowledge_vectors) {
                    data.knowledge_vectors.forEach(doc => {
                        const title = (doc.title || '').toLowerCase();
                        const content = (doc.content || '').toLowerCase();

                        if (title.includes(queryLower) || content.includes(queryLower)) {
                            results.push({
                                type: 'runbook',
                                title: `Runbook: ${doc.title || 'Document'}`,
                                preview: doc.content?.substring(0, 120) || '',
                                action: () => switchTab('memory-core')
                            });
                        }
                    });
                }

                // Search in users
                if (data.users) {
                    data.users.forEach(user => {
                        const username = (user.username || user.user_id || '').toLowerCase();

                        if (username.includes(queryLower)) {
                            results.push({
                                type: 'user',
                                title: `User: ${user.username || user.user_id}`,
                                preview: user.ai_synthesis_summary || user.project_role || '',
                                action: () => switchTab('memory-core')
                            });
                        }
                    });
                }
            }
        } catch (err) {
            console.error('Search error:', err);
        }

        // Search commands
        commands.forEach(cmd => {
            if (cmd.keywords.some(k => queryLower.includes(k)) || cmd.name.toLowerCase().includes(queryLower)) {
                results.push({
                    type: 'command',
                    title: `Command: ${cmd.name}`,
                    preview: `Execute this action`,
                    action: cmd.action
                });
            }
        });

        return results.slice(0, 10); // Limit to 10 results
    }

    function displaySearchResults(results, query) {
        if (results.length === 0) {
            searchResultsBody.innerHTML = '<div class="search-no-results">No results found. Try different keywords.</div>';
            searchResultsTitle.textContent = 'No Results';
            searchResultsCount.textContent = '';
        } else {
            searchResultsTitle.textContent = 'Search Results';
            searchResultsCount.textContent = `${results.length} found`;

            searchResultsBody.innerHTML = results.map(result => `
                <div class="search-result-item" data-action="${result.type}">
                    <div class="search-result-title">
                        <span class="search-result-type">${result.type}</span>
                        ${result.title}
                    </div>
                    ${result.preview ? `<div class="search-result-preview">${result.preview}</div>` : ''}
                </div>
            `).join('');

            // Add click handlers
            document.querySelectorAll('.search-result-item').forEach((item, index) => {
                item.addEventListener('click', () => {
                    results[index].action();
                    searchResults.style.display = 'none';
                    globalSearch.value = '';

                    // Save to history
                    if (!searchHistory.includes(query)) {
                        searchHistory.unshift(query);
                        searchHistory = searchHistory.slice(0, 10);
                        localStorage.setItem('searchHistory', JSON.stringify(searchHistory));
                    }
                });
            });
        }

        searchResults.style.display = 'block';
    }

    function showSuggestions() {
        const suggestions = [
            { type: 'recent', title: 'Recent Searches', items: searchHistory },
            { type: 'suggestion', title: 'Popular Searches', items: ['incident alerts', 'chat history', 'mongodb users', 'upload runbook'] }
        ];

        let html = '';
        suggestions.forEach(section => {
            if (section.items.length > 0) {
                html += `<div class="search-suggestions-section">
                    <div class="search-result-title" style="padding: var(--space-sm) var(--space-lg); background: var(--bg-dark);">
                        ${section.title}
                    </div>`;
                section.items.forEach(item => {
                    html += `<div class="search-result-item search-suggestion" data-query="${item}">
                        <div class="search-result-preview">${item}</div>
                    </div>`;
                });
                html += '</div>';
            }
        });

        if (html) {
            searchResultsTitle.textContent = 'Search Suggestions';
            searchResultsCount.textContent = '';
            searchResultsBody.innerHTML = html;

            document.querySelectorAll('.search-suggestion').forEach(item => {
                item.addEventListener('click', () => {
                    const query = item.dataset.query;
                    globalSearch.value = query;
                    performSearch(query);
                });
            });

            searchResults.style.display = 'block';
        }
    }

    async function performSearch(query) {
        const results = await searchContent(query);
        displaySearchResults(results, query);
    }

    if (globalSearch) {
        // Show suggestions on focus
        globalSearch.addEventListener('focus', () => {
            if (!globalSearch.value.trim()) {
                showSuggestions();
            }
        });

        // Live search as you type
        let searchTimeout;
        globalSearch.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const query = e.target.value.trim();

            if (query.length >= 2) {
                searchTimeout = setTimeout(() => {
                    performSearch(query);
                }, 300);
            } else if (query.length === 0) {
                showSuggestions();
            } else {
                searchResults.style.display = 'none';
            }
        });

        // Keep existing Enter key behavior
        globalSearch.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const query = globalSearch.value.trim();
                const queryLower = query.toLowerCase();
                if (!query) return;

                console.log('Search query:', query);

                // Search keywords for different sections
                const incidentKeywords = ['incident', 'alert', 'cpu', 'latency', 'error', 'spike', 'critical', 'warning'];
                const chatKeywords = ['chat', 'diagnose', 'diagnosis', 'sre', 'agent', 'gemini', 'ask', 'help'];
                const dbKeywords = ['database', 'mongodb', 'memory', 'collection', 'user', 'session', 'vector', 'db'];
                const runbookKeywords = ['runbook', 'manual', 'wiki', 'guide', 'document', 'ingest', 'upload', 'embed'];

                // Determine which tab to navigate to
                let targetTab = null;
                let shouldPopulateChat = false;

                if (incidentKeywords.some(keyword => queryLower.includes(keyword))) {
                    targetTab = 'incident-command';
                } else if (chatKeywords.some(keyword => queryLower.includes(keyword))) {
                    targetTab = 'diagnostic-chat';
                    shouldPopulateChat = true;
                } else if (dbKeywords.some(keyword => queryLower.includes(keyword))) {
                    targetTab = 'memory-core';
                } else if (runbookKeywords.some(keyword => queryLower.includes(keyword))) {
                    targetTab = 'runbook-ingester';
                } else {
                    // Default: use chat for general queries
                    targetTab = 'diagnostic-chat';
                    shouldPopulateChat = true;
                }

                // Clear search first
                globalSearch.value = '';

                // Navigate to the appropriate tab
                if (targetTab) {
                    switchTab(targetTab);

                    // Only populate chat input if it's a chat-related query or general query
                    if (targetTab === 'diagnostic-chat' && shouldPopulateChat) {
                        setTimeout(() => {
                            const chatInput = document.getElementById('chat-user-input');
                            if (chatInput) {
                                chatInput.value = query;
                                chatInput.focus();
                            }
                        }, 100);
                    }
                }
            }
        });

        // Add search icon click handler
        const searchIcon = document.querySelector('.search-icon');
        if (searchIcon) {
            searchIcon.addEventListener('click', () => {
                globalSearch.focus();
            });
        }

        // Close search results when clicking outside
        document.addEventListener('click', (e) => {
            if (!globalSearch.contains(e.target) && !searchResults.contains(e.target) && !e.target.classList.contains('search-icon')) {
                searchResults.style.display = 'none';
            }
        });
    }

    // ---------------------------------------------------------
    // 0.6. Notification Panel System
    // ---------------------------------------------------------
    const notificationBtn = document.getElementById('notification-btn');
    const notificationPanel = document.getElementById('notification-panel');
    const notificationPanelBody = document.getElementById('notification-panel-body');
    const notificationCount = document.getElementById('notification-count');
    const notificationBadge = document.getElementById('notification-badge');

    // Sample notifications data
    let notifications = [
        {
            id: 1,
            type: 'critical',
            title: 'CPU Usage Critical',
            message: 'Server us-central1-a is experiencing 98.4% CPU usage. Immediate action required.',
            time: '2 min ago',
            read: false
        },
        {
            id: 2,
            type: 'warning',
            title: 'Memory Warning',
            message: 'Memory usage on production cluster reached 85%. Consider scaling up.',
            time: '15 min ago',
            read: false
        },
        {
            id: 3,
            type: 'info',
            title: 'Backup Completed',
            message: 'MongoDB Atlas backup completed successfully. 2.4 GB backed up to GCS.',
            time: '1 hour ago',
            read: false
        }
    ];

    function renderNotifications() {
        const unreadCount = notifications.filter(n => !n.read).length;

        // Update badge visibility
        if (unreadCount > 0) {
            notificationBadge.style.display = 'block';
            notificationCount.textContent = `${unreadCount} new`;
        } else {
            notificationBadge.style.display = 'none';
            notificationCount.textContent = 'All read';
        }

        // Render notification items
        if (notifications.length === 0) {
            notificationPanelBody.innerHTML = '<div class="notification-empty">No notifications</div>';
        } else {
            notificationPanelBody.innerHTML = notifications.map(notif => `
                <div class="notification-item ${notif.read ? 'read' : ''}" data-id="${notif.id}">
                    <div class="notification-item-header">
                        <span class="notification-title">${notif.title}</span>
                        <span class="notification-time">${notif.time}</span>
                    </div>
                    <div class="notification-message">${notif.message}</div>
                    <span class="notification-type ${notif.type}">${notif.type}</span>
                </div>
            `).join('');

            // Add click handlers to mark as read
            document.querySelectorAll('.notification-item').forEach(item => {
                item.addEventListener('click', () => {
                    const id = parseInt(item.dataset.id);
                    const notification = notifications.find(n => n.id === id);
                    if (notification) {
                        notification.read = true;
                        renderNotifications();
                    }
                });
            });
        }
    }

    if (notificationBtn && notificationPanel) {
        // Toggle notification panel
        notificationBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isVisible = notificationPanel.style.display === 'block';
            notificationPanel.style.display = isVisible ? 'none' : 'block';

            if (!isVisible) {
                renderNotifications();
            }
        });

        // Close notification panel when clicking outside
        document.addEventListener('click', (e) => {
            if (!notificationPanel.contains(e.target) && !notificationBtn.contains(e.target)) {
                notificationPanel.style.display = 'none';
            }
        });

        // Initial render
        renderNotifications();
    }

    // ---------------------------------------------------------
    // 1. Navigation Tab Switching System
    // ---------------------------------------------------------
    const navItems = document.querySelectorAll('.nav-item');
    const tabPanes = document.querySelectorAll('.tab-pane');

    function switchTab(targetTabId) {
        navItems.forEach(item => {
            if (item.getAttribute('data-tab') === targetTabId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        tabPanes.forEach(pane => {
            if (pane.id === targetTabId) {
                pane.classList.add('active');
            } else {
                pane.classList.remove('active');
            }
        });

        // Scroll to top when switching tabs to prevent layout displacement
        window.scrollTo({ top: 0, behavior: 'smooth' });

        // Trigger dynamic data fetch when opening specific tabs
        if (targetTabId === 'memory-core') {
            fetchDatabaseCollections();
        }
    }

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetTab = item.getAttribute('data-tab');
            switchTab(targetTab);
        });
    });

    // Sub-tab Navigation (Database Collections Explorer)
    const subTabs = document.querySelectorAll('.sub-tab');
    const subtabPanes = document.querySelectorAll('.subtab-pane');

    subTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetSubtab = tab.getAttribute('data-subtab');

            subTabs.forEach(t => t.classList.remove('active'));
            subtabPanes.forEach(p => p.classList.remove('active'));

            tab.classList.add('active');
            document.getElementById(targetSubtab).classList.add('active');
            
            // Refresh database on sub-tab navigation
            fetchDatabaseCollections();
        });
    });

    // ---------------------------------------------------------
    // 2. Terminal Log Capture & Stream Visualizer
    // ---------------------------------------------------------
    const terminalLogs = document.getElementById('live-terminal-logs');

    function clearTerminal() {
        terminalLogs.innerHTML = '';
    }

    function logTerminalLine(message, type = 'info') {
        const time = new Date().toLocaleTimeString();
        let colorClass = '';
        
        if (type === 'success') colorClass = 'text-success';
        else if (type === 'error') colorClass = 'text-error';
        else if (type === 'tool') colorClass = 'text-warning'; // Gold color for tool trigger
        else if (type === 'sys') colorClass = 'text-muted'; // Greyscale for system
        
        const line = document.createElement('div');
        line.className = `log-line ${colorClass}`;
        
        // Highlight tool triggers and success states
        let formattedMessage = message;
        if (message.includes('Tool Triggered:')) {
            line.style.borderLeft = '2px solid var(--accent-orange)';
            line.style.paddingLeft = '6px';
            line.style.background = 'rgba(255, 122, 0, 0.05)';
        } else if (type === 'success') {
            line.style.borderLeft = '2px solid var(--accent-green)';
            line.style.paddingLeft = '6px';
            line.style.background = 'rgba(52, 168, 83, 0.05)';
        }

        line.innerHTML = `[${time}] <span class="text-muted">[${type.toUpperCase()}]</span> ${formattedMessage}`;
        terminalLogs.appendChild(line);
        terminalLogs.scrollTop = terminalLogs.scrollHeight;
    }

    function streamTraces(traces) {
        if (!traces || !Array.isArray(traces)) return;
        traces.forEach(trace => {
            let type = 'info';
            let lower = trace.toLowerCase();
            
            if (lower.includes('[error]') || lower.includes('error')) type = 'error';
            else if (lower.includes('successfully') || lower.includes('complete') || lower.includes('done')) type = 'success';
            else if (lower.includes('tool triggered')) type = 'tool';
            else if (lower.includes('[sys]')) type = 'sys';

            // Clean log prefix if present from Python formatting
            let cleanTrace = trace.replace(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} \[[A-Z]+\] /, '');
            logTerminalLine(cleanTrace, type);
        });
    }

    // ---------------------------------------------------------
    // 3. Database Explorer Controller (Live MongoDB Fetch)
    // ---------------------------------------------------------
    const dbUserCard = document.getElementById('db-user-data');
    const sessionsList = document.getElementById('sessions-list-container');
    const vectorsList = document.getElementById('vectors-list-container');

    async function fetchDatabaseCollections() {
        try {
            const res = await fetch(`${API_BASE}/api/db/collections`);
            if (!res.ok) throw new Error('Database API endpoint error');
            const data = await res.json();

            // 1. Render Users Collection
            dbUserCard.innerHTML = '';
            if (data.users && data.users.length > 0) {
                data.users.forEach(user => {
                    const doc = document.createElement('div');
                    doc.className = 'db-document';
                    doc.innerHTML = `
                        <div class="doc-header">
                            <span class="doc-id">id: "${user._id}"</span>
                            <span class="doc-tag">Collection: users</span>
                        </div>
                        <pre class="doc-body">${JSON.stringify(user, null, 2)}</pre>
                    `;
                    dbUserCard.appendChild(doc);
                });
            } else {
                dbUserCard.innerHTML = '<div class="db-document"><pre class="doc-body">// No user profiles indexed in users collection.</pre></div>';
            }

            // 2. Render Incident Sessions Collection
            sessionsList.innerHTML = '';
            if (data.sessions && data.sessions.length > 0) {
                data.sessions.forEach(sess => {
                    const doc = document.createElement('div');
                    doc.className = 'db-document';
                    doc.innerHTML = `
                        <div class="doc-header">
                            <span class="doc-id">id: "${sess._id}"</span>
                            <span class="doc-tag">Collection: sessions</span>
                        </div>
                        <pre class="doc-body">${JSON.stringify(sess, null, 2)}</pre>
                    `;
                    sessionsList.appendChild(doc);
                });
            } else {
                sessionsList.innerHTML = '<div class="db-document"><pre class="doc-body">// No conversational sessions found.</pre></div>';
            }

            // 3. Render Vector Runbooks Collection
            vectorsList.innerHTML = '';
            if (data.knowledge_vectors && data.knowledge_vectors.length > 0) {
                data.knowledge_vectors.forEach(vec => {
                    const doc = document.createElement('div');
                    doc.className = 'db-document';
                    doc.innerHTML = `
                        <div class="doc-header">
                            <span class="doc-id">id: "${vec._id}"</span>
                            <span class="doc-tag">Collection: knowledge_vectors</span>
                        </div>
                        <pre class="doc-body">${JSON.stringify(vec, null, 2)}</pre>
                    `;
                    vectorsList.appendChild(doc);
                });
            } else {
                vectorsList.innerHTML = '<div class="db-document"><pre class="doc-body">// No vector-embedded runbooks found in grounding collection.</pre></div>';
            }
        } catch (err) {
            console.error('Error fetching database collections:', err);
            dbUserCard.textContent = `// Failed to load live MongoDB data: ${err.message}\n// Ensure Flask API is running on ${API_BASE}`;
        }
    }

    // ---------------------------------------------------------
    // 4. Live Chat Client (Vertex AI Gemini chat endpoint)
    // ---------------------------------------------------------
    const chatInput = document.getElementById('chat-user-input');
    const sendBtn = document.getElementById('send-chat-btn');
    const chatMessages = document.getElementById('chat-messages-container');
    const modelSelector = document.getElementById('model-selector');
    const userIdInput = document.getElementById('user-id-input');

    // Load saved model preference
    const savedModel = localStorage.getItem('selectedModel') || 'gemini-2.5-flash';
    if (modelSelector) {
        modelSelector.value = savedModel;
    }

    // Load saved user ID preference
    const savedUserId = localStorage.getItem('userId') || 'AvishManiar21';
    if (userIdInput) {
        userIdInput.value = savedUserId;
    }

    // Save model preference when changed and update description
    const modelDescription = document.getElementById('model-description');

    function updateModelDescription(model) {
        if (!modelDescription) return;

        if (model === 'gemini-2.5-pro') {
            modelDescription.textContent = 'Deep reasoning & analysis';
        } else {
            modelDescription.textContent = 'Fast & cost-efficient';
        }
    }

    if (modelSelector) {
        // Set initial description
        updateModelDescription(modelSelector.value);

        modelSelector.addEventListener('change', () => {
            localStorage.setItem('selectedModel', modelSelector.value);
            updateModelDescription(modelSelector.value);
            logTerminalLine(`Switched to ${modelSelector.value}`, 'sys');
        });
    }

    // Update sidebar username display
    function updateSidebarUsername(userId) {
        const sidebarUsername = document.getElementById('sidebar-username');
        const sidebarAvatar = document.getElementById('sidebar-avatar');
        if (sidebarUsername) {
            sidebarUsername.textContent = userId;
        }
        if (sidebarAvatar && userId) {
            // Create initials from user ID
            const initials = userId
                .split(/[_\-\.]/)
                .map(part => part[0])
                .join('')
                .toUpperCase()
                .substring(0, 2);
            sidebarAvatar.textContent = initials || 'AM';
        }
    }

    // Initial sidebar update
    updateSidebarUsername(savedUserId);

    // Save user ID when changed
    if (userIdInput) {
        userIdInput.addEventListener('change', () => {
            const newUserId = userIdInput.value.trim() || 'AvishManiar21';
            localStorage.setItem('userId', newUserId);
            updateSidebarUsername(newUserId);
            logTerminalLine(`User ID changed to: ${newUserId}`, 'sys');
        });

        userIdInput.addEventListener('input', () => {
            const newUserId = userIdInput.value.trim() || 'AvishManiar21';
            updateSidebarUsername(newUserId);
        });
    }

    function appendChatMessage(sender, text, modelUsed, groundingSources) {
        const msg = document.createElement('div');
        msg.className = `message ${sender}`;
        let bubble = `<div class="message-bubble">${text}</div>`;
        if (sender === 'agent' && modelUsed) {
            bubble += `<div class="model-badge">${modelUsed === 'gemini-2.5-pro' ? '🧠 Pro' : '⚡ Flash'}</div>`;
        }
        // Add grounding sources if available
        if (sender === 'agent' && groundingSources && groundingSources.length > 0) {
            bubble += '<div class="grounding-sources">';
            bubble += '<div class="grounding-header">📚 MongoDB Atlas Vector Search Results</div>';
            groundingSources.forEach((source, idx) => {
                const scorePercent = Math.round(source.score * 100);
                bubble += `
                    <div class="grounding-item">
                        <span class="grounding-rank">#${idx + 1}</span>
                        <span class="grounding-title">${source.title}</span>
                        <span class="grounding-score">${scorePercent}% match</span>
                    </div>
                `;
            });
            bubble += '</div>';
        }
        msg.innerHTML = bubble;
        chatMessages.appendChild(msg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function handleChat() {
        const query = chatInput.value.trim();
        if (!query) return;

        const selectedModel = modelSelector ? modelSelector.value : 'gemini-2.5-flash';
        const currentUserId = userIdInput ? userIdInput.value.trim() || 'AvishManiar21' : 'AvishManiar21';

        // Append user prompt
        appendChatMessage('user', query);
        chatInput.value = '';

        // Add mock thinking indicator
        const thinkingBubble = document.createElement('div');
        thinkingBubble.className = 'message agent thinking';
        const modelName = selectedModel === 'gemini-2.5-pro' ? 'Gemini Pro' : 'Gemini Flash';
        thinkingBubble.innerHTML = `<div class="message-bubble"><span class="loading-dots">${modelName} is searching runbooks and reasoning...</span></div>`;
        chatMessages.appendChild(thinkingBubble);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        logTerminalLine(`Received SRE request: "${query}" [User: ${currentUserId}, Model: ${selectedModel}]`, 'sys');

        try {
            const res = await fetch(`${API_BASE}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: query,
                    user_id: currentUserId,
                    model: selectedModel
                })
            });

            // Remove thinking bubble
            chatMessages.removeChild(thinkingBubble);

            if (!res.ok) throw new Error('API server returned error');
            const data = await res.json();

            // Render agent completion with model badge and grounding sources
            appendChatMessage('agent', data.response, data.model_used || selectedModel, data.grounding_sources);

            // Stream captured operational traces
            streamTraces(data.traces);
            
            // Auto refresh database explorer collections
            fetchDatabaseCollections();

        } catch (err) {
            chatMessages.removeChild(thinkingBubble);
            appendChatMessage('agent', `❌ <strong>API Server Error</strong>: Could not communicate with SentinelOps backend. Ensure <code>python src/agent.py</code> is running on your machine.`);
            logTerminalLine(`Failed to query SRE API: ${err.message}`, 'error');
        }
    }

    sendBtn.addEventListener('click', handleChat);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleChat();
    });

    // ---------------------------------------------------------
    // 5. Dynatrace Autonomous Incident Diagnostics Simulator
    // ---------------------------------------------------------
    const diagnoseSpikeBtn = document.getElementById('diagnose-spike-btn');
    const approveMrBtn = document.getElementById('approve-mr-btn');
    const hotfixCodeView = document.getElementById('hotfix-code-view');

    diagnoseSpikeBtn.addEventListener('click', async () => {
        // 1. Shift to diagnostic chat view to visualize console traces
        switchTab('diagnostic-chat');

        // Clear log terminals
        clearTerminal();
        logTerminalLine('[sys] Observability webhook trigger intercepted!', 'sys');
        logTerminalLine('[sys] Target: Server Latency Spike — us-central1 CPU Usage 98.4%', 'info');

        appendChatMessage('user', '🔍 <em>[Observability Alert Webhook]</em> Diagnose critical incident: us-central1 latency spike + CPU 98.4%');

        const thinkingBubble = document.createElement('div');
        thinkingBubble.className = 'message agent thinking';
        thinkingBubble.innerHTML = `<div class="message-bubble"><span class="loading-dots">SentinelOps is compiling diagnostic report & hotfix diff...</span></div>`;
        chatMessages.appendChild(thinkingBubble);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const currentUserId = userIdInput ? userIdInput.value.trim() || 'AvishManiar21' : 'AvishManiar21';
            const res = await fetch(`${API_BASE}/api/diagnose`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    incident_id: 'spike',
                    description: 'Server Latency Spike — us-central1 CPU Usage 98.4%',
                    user_id: currentUserId
                })
            });

            chatMessages.removeChild(thinkingBubble);

            if (!res.ok) throw new Error('API server returned error during diagnosis');
            const data = await res.json();

            // Render diagnostic text
            appendChatMessage('agent', `🛡️ <strong>Incident Diagnostics Report</strong>:<br>${data.diagnosis.replace(/\n/g, '<br>')}`);

            // Stream traces
            streamTraces(data.traces);

            // Display generated Git diff patch
            hotfixCodeView.textContent = data.git_diff;
            
            // Enable MR Approve button
            approveMrBtn.removeAttribute('disabled');
            logTerminalLine('GitLab Merge Request !428 successfully generated!', 'success');

            // Refresh collection values
            fetchDatabaseCollections();

        } catch (err) {
            chatMessages.removeChild(thinkingBubble);
            appendChatMessage('agent', `❌ <strong>Diagnostics Failed</strong>: Could not contact backend SRE agent API. Check local server execution logs.`);
            logTerminalLine(`Autonomous diagnosis failure: ${err.message}`, 'error');
        }
    });

    approveMrBtn.addEventListener('click', () => {
        logTerminalLine('GitLab Merge Request !428 APPROVED by AvishManiar21.', 'success');
        logTerminalLine('[sys] Initiating deployment script inside GitLab pipeline...', 'sys');
        logTerminalLine('Pipeline execution successful! hotfix.diff applied to main production branch.', 'success');
        
        approveMrBtn.setAttribute('disabled', 'true');
        hotfixCodeView.textContent = `# MR APPROVED & DEPLOYED\n# Hotfix deployed successfully to us-central1-k8s-cluster.\n# System CPU load stabilized back to 24.2%.`;
        
        // Update metric display in Incident tab
        const cpuMetric = document.getElementById('metric-cpu');
        if (cpuMetric) {
            cpuMetric.textContent = '24.2%';
            cpuMetric.className = 'metric-val text-success';
        }
    });

    // ---------------------------------------------------------
    // 6. SRE Manuals / Wikis Vector Grounding Ingester
    // ---------------------------------------------------------
    const manualTitle = document.getElementById('manual-title');
    const manualContent = document.getElementById('manual-content');
    const chunkSlider = document.getElementById('chunk-slider');
    const sliderOut = document.getElementById('slider-out');
    const embedSubmitBtn = document.getElementById('embed-submit-btn');
    const indexerTerminal = document.getElementById('indexer-terminal-screen');

    chunkSlider.addEventListener('input', () => {
        sliderOut.textContent = chunkSlider.value;
    });

    function logIndexerLine(msg, status = 'info') {
        const time = new Date().toLocaleTimeString();
        const line = document.createElement('div');
        let col = status === 'sys' ? 'text-muted' : status === 'success' ? 'text-success' : '';
        line.innerHTML = `[${time}] [<span class="${col}">${status.toUpperCase()}</span>] ${msg}`;
        indexerTerminal.appendChild(line);
        indexerTerminal.scrollTop = indexerTerminal.scrollHeight;
    }

    embedSubmitBtn.addEventListener('click', async () => {
        const title = manualTitle.value.trim();
        const content = manualContent.value.trim();

        if (!title || !content) {
            alert('Please fill out both the runbook Title and Content.');
            return;
        }

        indexerTerminal.innerHTML = '';
        logIndexerLine('Initializing text grounding ingestion workflow...', 'sys');
        logIndexerLine(`Chunk limits computed at max ${chunkSlider.value} characters.`, 'info');

        try {
            embedSubmitBtn.setAttribute('disabled', 'true');
            embedSubmitBtn.textContent = 'Vectorizing & Uploading...';

            const res = await fetch(`${API_BASE}/api/runbook/ingest`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, content })
            });

            embedSubmitBtn.removeAttribute('disabled');
            embedSubmitBtn.textContent = 'Embed & Upload to MongoDB Atlas';

            if (!res.ok) throw new Error('Ingestion API returned error');
            const data = await res.json();

            // Render log traces inside ingester terminal
            if (data.traces) {
                data.traces.forEach(t => {
                    let clean = t.replace(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} \[[A-Z]+\] /, '');
                    if (clean.includes('Document indexed successfully') || clean.includes('indexed successfully')) {
                        logIndexerLine(clean, 'success');
                    } else if (clean.includes('Generating 768-dimension')) {
                        logIndexerLine(clean, 'info');
                    } else if (clean.includes('GCS') || clean.includes('Cloud Storage')) {
                        logIndexerLine(clean, 'success');
                    } else {
                        logIndexerLine(clean, 'sys');
                    }
                });
            }

            // Show GCS backup URL if available
            if (data.gcs_url && data.gcs_url.startsWith('gs://')) {
                logIndexerLine(`✓ Backup saved to Google Cloud Storage: ${data.gcs_url}`, 'success');
            }

            logIndexerLine(`Pipeline compilation successful. Grounding database synchronized!`, 'success');

            // Reset inputs
            manualTitle.value = '';
            manualContent.value = '';

            // Update database tabs
            fetchDatabaseCollections();

        } catch (err) {
            embedSubmitBtn.removeAttribute('disabled');
            embedSubmitBtn.textContent = 'Embed & Upload to MongoDB Atlas';
            logIndexerLine(`Ingestion pipeline collapsed: ${err.message}`, 'sys');
            logIndexerLine('Error contacting Python grounding service. Check API logs.', 'sys');
        }
    });

    // ---------------------------------------------------------
    // 7. Webhook Alert Tester
    // ---------------------------------------------------------
    const webhookUrlDisplay = document.getElementById('webhook-url');
    const testWebhookBtn = document.getElementById('test-webhook-btn');
    const webhookResponse = document.getElementById('webhook-response');
    const webhookResponseText = document.getElementById('webhook-response-text');

    // Display webhook URL
    if (webhookUrlDisplay) {
        webhookUrlDisplay.textContent = `${API_BASE}/api/webhook/alert`;
    }

    if (testWebhookBtn) {
        testWebhookBtn.addEventListener('click', async () => {
            try {
                testWebhookBtn.setAttribute('disabled', 'true');
                testWebhookBtn.textContent = 'Sending Alert...';

                // Sample webhook payload
                const payload = {
                    alert_name: "CPU Usage Critical",
                    severity: "CRITICAL",
                    description: "Server us-central1-a is experiencing 98.4% CPU usage",
                    source: "SentinelOps-Dashboard-Test",
                    timestamp: new Date().toISOString()
                };

                // Note: Webhook requires X-Webhook-Secret header for authentication
                // Using demo secret that matches Cloud Run WEBHOOK_SECRET env var
                const res = await fetch(`${API_BASE}/api/webhook/alert`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Webhook-Secret': 'sentinelops-demo-webhook-secret-2026'
                    },
                    body: JSON.stringify(payload)
                });

                testWebhookBtn.removeAttribute('disabled');
                testWebhookBtn.textContent = 'Send Test Alert';

                const data = await res.json();

                // Show response
                webhookResponse.style.display = 'block';
                webhookResponseText.textContent = JSON.stringify(data, null, 2);

                if (res.ok) {
                    console.log('Webhook test successful:', data);
                } else {
                    console.error('Webhook test failed:', data);
                }

            } catch (err) {
                testWebhookBtn.removeAttribute('disabled');
                testWebhookBtn.textContent = 'Send Test Alert';
                webhookResponse.style.display = 'block';
                webhookResponseText.textContent = `Error: ${err.message}`;
            }
        });
    }

    // Auto-fetch data on startup
    fetchDatabaseCollections();

    // ---------------------------------------------------------
    // 12. System Status Monitoring
    // ---------------------------------------------------------
    const statusBadge = document.querySelector('.credit-status-badge');
    const statusDot = document.querySelector('.credit-dot');
    const statusText = document.querySelector('.status-text');
    let statusDetailsPanel = null;

    // Create status details panel
    function createStatusDetailsPanel() {
        const panel = document.createElement('div');
        panel.className = 'status-details-panel';
        panel.style.display = 'none';
        panel.innerHTML = `
            <div class="status-details-header">
                <h3>System Health</h3>
                <button class="close-status-panel">×</button>
            </div>
            <div class="status-details-body">
                <div class="status-service">
                    <div class="status-service-header">
                        <span class="status-service-icon" data-service="backend">●</span>
                        <span class="status-service-name">Backend API</span>
                    </div>
                    <span class="status-service-message" data-service="backend">Checking...</span>
                </div>
                <div class="status-service">
                    <div class="status-service-header">
                        <span class="status-service-icon" data-service="vertex_ai">●</span>
                        <span class="status-service-name">Vertex AI / Gemini</span>
                    </div>
                    <span class="status-service-message" data-service="vertex_ai">Checking...</span>
                </div>
                <div class="status-service">
                    <div class="status-service-header">
                        <span class="status-service-icon" data-service="mongodb">●</span>
                        <span class="status-service-name">MongoDB Atlas</span>
                    </div>
                    <span class="status-service-message" data-service="mongodb">Checking...</span>
                </div>
                <div class="status-service">
                    <div class="status-service-header">
                        <span class="status-service-icon" data-service="mcp_server">●</span>
                        <span class="status-service-name">MongoDB MCP Server</span>
                    </div>
                    <span class="status-service-message" data-service="mcp_server">Checking...</span>
                </div>
            </div>
            <div class="status-details-footer">
                <span class="status-timestamp">Last checked: Never</span>
            </div>
        `;
        document.body.appendChild(panel);
        return panel;
    }

    statusDetailsPanel = createStatusDetailsPanel();

    // Update status badge based on health data
    function updateSystemStatus(healthData) {
        const overallStatus = healthData.overall_status || 'unknown';

        // Update badge appearance
        statusBadge.setAttribute('data-status', overallStatus);

        // Update status text
        const statusMessages = {
            'online': 'All Systems Operational',
            'degraded': 'Partial Service Available',
            'offline': 'Service Unavailable',
            'unknown': 'Status Unknown'
        };
        statusText.textContent = `System Status: ${statusMessages[overallStatus] || 'Unknown'}`;

        // Update details panel if exists
        if (healthData.services) {
            Object.keys(healthData.services).forEach(serviceName => {
                const service = healthData.services[serviceName];
                const icon = statusDetailsPanel.querySelector(`[data-service="${serviceName}"].status-service-icon`);
                const message = statusDetailsPanel.querySelector(`[data-service="${serviceName}"].status-service-message`);

                if (icon && message) {
                    icon.setAttribute('data-status', service.status);
                    message.textContent = service.message || 'Unknown';
                }
            });
        }

        // Update timestamp
        const timestamp = statusDetailsPanel.querySelector('.status-timestamp');
        if (timestamp && healthData.timestamp) {
            const date = new Date(healthData.timestamp);
            timestamp.textContent = `Last checked: ${date.toLocaleTimeString()}`;
        }
    }

    // Fetch health status
    async function fetchHealthStatus() {
        try {
            const res = await fetch(`${API_BASE}/api/health`);
            const data = await res.json();
            updateSystemStatus(data);
        } catch (err) {
            console.error('Health check failed:', err);
            updateSystemStatus({
                overall_status: 'offline',
                services: {
                    backend: { status: 'offline', message: 'Cannot reach backend' },
                    vertex_ai: { status: 'unknown', message: 'Not checked' },
                    mongodb: { status: 'unknown', message: 'Not checked' },
                    mcp_server: { status: 'unknown', message: 'Not checked' }
                }
            });
        }
    }

    // Toggle status details panel
    statusBadge.addEventListener('click', () => {
        if (statusDetailsPanel.style.display === 'none') {
            statusDetailsPanel.style.display = 'block';
            fetchHealthStatus(); // Refresh on open
        } else {
            statusDetailsPanel.style.display = 'none';
        }
    });

    // Close panel
    statusDetailsPanel.querySelector('.close-status-panel').addEventListener('click', () => {
        statusDetailsPanel.style.display = 'none';
    });

    // Close panel when clicking outside
    document.addEventListener('click', (e) => {
        if (!statusBadge.contains(e.target) && !statusDetailsPanel.contains(e.target)) {
            statusDetailsPanel.style.display = 'none';
        }
    });

    // Initial health check
    fetchHealthStatus();

    // Auto-refresh every 30 seconds
    setInterval(fetchHealthStatus, 30000);
});
