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
            if (data.users && data.users.length > 0) {
                dbUserCard.textContent = JSON.stringify(data.users[0], null, 2);
            } else {
                dbUserCard.textContent = '// No user profiles indexed in users collection.';
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

    function appendChatMessage(sender, text) {
        const msg = document.createElement('div');
        msg.className = `message ${sender}`;
        msg.innerHTML = `<div class="message-bubble">${text}</div>`;
        chatMessages.appendChild(msg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function handleChat() {
        const query = chatInput.value.trim();
        if (!query) return;

        // Append user prompt
        appendChatMessage('user', query);
        chatInput.value = '';

        // Add mock thinking indicator
        const thinkingBubble = document.createElement('div');
        thinkingBubble.className = 'message agent thinking';
        thinkingBubble.innerHTML = `<div class="message-bubble"><span class="loading-dots">SentinelOps is searching runbooks and reasoning...</span></div>`;
        chatMessages.appendChild(thinkingBubble);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        logTerminalLine(`Received SRE request: "${query}"`, 'sys');

        try {
            const res = await fetch(`${API_BASE}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: query, user_id: 'AvishManiar21' })
            });

            // Remove thinking bubble
            chatMessages.removeChild(thinkingBubble);

            if (!res.ok) throw new Error('API server returned error');
            const data = await res.json();

            // Render agent completion
            appendChatMessage('agent', data.response);
            
            // Stream captured operational traces
            streamTraces(data.traces);
            
            // Auto refresh database explorer collections
            fetchDatabaseCollections();

        } catch (err) {
            chatMessages.removeChild(thinkingBubble);
            appendChatMessage('agent', `❌ <strong>API Server Error</strong>: Could not communicate with SentinelOps backend. Ensure <code>python agent.py</code> is running on your machine.`);
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
            const res = await fetch(`${API_BASE}/api/diagnose`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    incident_id: 'spike',
                    description: 'Server Latency Spike — us-central1 CPU Usage 98.4%',
                    user_id: 'AvishManiar21'
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
                    } else {
                        logIndexerLine(clean, 'sys');
                    }
                });
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

    // Auto-fetch data on startup
    fetchDatabaseCollections();
});
