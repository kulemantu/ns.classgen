        const threadId = localStorage.getItem('classgen_thread_id') || ("chat_" + Math.random().toString(36).substring(2, 10));
        localStorage.setItem('classgen_thread_id', threadId);

        const chatFeed    = document.getElementById('chat-feed');
        const inputField  = document.getElementById('mainInput');
        const sendBtn     = document.getElementById('send-btn');
        const headerStatus= document.getElementById('header-status');
        const contextPath = [];

        // ── Theme ─────────────────────────────────────────────

        function applyTheme(dark) {
            document.documentElement.classList.add('theme-transitioning');
            document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
            localStorage.setItem('classgen_theme', dark ? 'dark' : 'light');
            setTimeout(() => document.documentElement.classList.remove('theme-transitioning'), 300);
        }

        function toggleDarkMode() {
            const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
            applyTheme(!isDark);
            const toggle = document.getElementById('dark-toggle');
            if (toggle) toggle.classList.toggle('on', !isDark);
        }

        function isDarkMode() {
            return document.documentElement.getAttribute('data-theme') === 'dark';
        }

        // ── Helpers ───────────────────────────────────────────

        function getTimestamp() {
            const d = new Date();
            return d.getHours().toString().padStart(2,'0') + ':' + d.getMinutes().toString().padStart(2,'0');
        }

        function triggerHaptic(type = 'light') {
            if (navigator.vibrate) navigator.vibrate(type === 'medium' ? 20 : 10);
        }

        function escapeHtml(str) {
            const d = document.createElement('div');
            d.textContent = str;
            return d.innerHTML;
        }

        function scrollToBottom() {
            setTimeout(() => chatFeed.scrollTo({ top: chatFeed.scrollHeight, behavior: 'smooth' }), 50);
        }

        function setThinking(on) {
            headerStatus.textContent = on ? 'typing...' : 'online';
            sendBtn.disabled   = on;
            inputField.disabled= on;
        }

        // ── Message Rendering ─────────────────────────────────

        function createAiGroup(contentHtml, buttons = []) {
            const group = document.createElement('div');
            group.className = 'msg-group ai';

            const bubble = document.createElement('div');
            bubble.className = 'message-bubble bubble-ai';
            bubble.innerHTML = `${contentHtml}<div class="bubble-footer"><span class="bubble-time">${getTimestamp()}</span></div>`;
            group.appendChild(bubble);

            if (buttons.length > 0) {
                const btns = document.createElement('div');
                btns.className = 'msg-buttons';
                buttons.forEach(text => {
                    const btn = document.createElement('button');
                    btn.className = 'wa-reply-btn';
                    btn.textContent = text;
                    btn.addEventListener('click', () => submitPromptWithText(text));
                    btns.appendChild(btn);
                });
                group.appendChild(btns);
            }

            return group;
        }

        function createUserGroup(text) {
            const group = document.createElement('div');
            group.className = 'msg-group user';

            const bubble = document.createElement('div');
            bubble.className = 'message-bubble bubble-user';
            bubble.innerHTML = `${escapeHtml(text)}<div class="bubble-footer"><span class="bubble-time">${getTimestamp()}</span><span class="bubble-ticks"><svg viewBox="0 0 16 11" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M11.07 0.66L4.98 6.75L2.91 4.68L1.5 6.09L4.98 9.57L12.48 2.07L11.07 0.66Z" fill="currentColor"/><path d="M14.07 0.66L7.98 6.75L6.69 5.47L5.28 6.88L7.98 9.57L15.48 2.07L14.07 0.66Z" fill="currentColor"/></svg></span></div>`;
            group.appendChild(bubble);

            return group;
        }

        function createTypingGroup() {
            const group = document.createElement('div');
            group.className = 'msg-group ai';
            const bubble = document.createElement('div');
            bubble.className = 'message-bubble bubble-ai';
            bubble.innerHTML = `<div class="typing-indicator"><span></span><span></span><span></span></div>`;
            group.appendChild(bubble);
            return group;
        }

        // ── Toast notification ────────────────────────────────

        function showToast(msg, duration = 3500) {
            const el = document.getElementById('toast');
            el.textContent = msg;
            el.classList.add('show');
            setTimeout(() => el.classList.remove('show'), duration);
        }

        // ── Conversation persistence ─────────────────────────

        function saveConversation(userMsg, data) {
            try {
                const history = JSON.parse(localStorage.getItem('classgen_chat_history') || '[]');
                history.push({ role: 'user', text: userMsg, ts: Date.now() });
                history.push({ role: 'ai', data: data, ts: Date.now() });
                // Keep last 20 messages (10 exchanges)
                const trimmed = history.slice(-20);
                localStorage.setItem('classgen_chat_history', JSON.stringify(trimmed));
            } catch (e) { /* localStorage full or disabled */ }
        }

        function restoreConversation() {
            try {
                const history = JSON.parse(localStorage.getItem('classgen_chat_history') || '[]');
                if (history.length === 0) return;
                history.forEach(entry => {
                    if (entry.role === 'user') {
                        chatFeed.appendChild(createUserGroup(entry.text));
                    } else if (entry.role === 'ai' && entry.data) {
                        renderAiResponse(entry.data);
                    }
                });
                scrollToBottom();
            } catch (e) { /* corrupted data — ignore */ }
        }

        // ── Formatting helpers ────────────────────────────────

        function humanize(str) {
            if (!str) return '';
            return str.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
        }

        function formatDetails(text, structured) {
            if (!text) return '';
            let html = escapeHtml(text);
            // Paragraphs: split on double newlines or sentence boundaries for long blocks
            html = html.replace(/\n\n+/g, '</p><p>');
            html = html.replace(/\n/g, '<br>');
            // Bold: **text** or text between quotes used for emphasis
            html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            // Italic: single quotes around terms
            html = html.replace(/&#x27;(.*?)&#x27;/g, '<em>\'$1\'</em>');
            html = '<p>' + html + '</p>';

            // Append structured metadata as styled sections
            if (structured) {
                if (structured.equation) {
                    html += '<div style="margin:1rem 0;padding:0.75rem 1rem;background:var(--bg-main);border-radius:8px;font-family:monospace;font-size:0.95rem;text-align:center">' + escapeHtml(structured.equation) + '</div>';
                }
                if (structured.key_terms && structured.key_terms.length > 0) {
                    html += '<div style="margin-top:1rem"><strong style="font-size:0.8rem;text-transform:uppercase;letter-spacing:0.05em;color:var(--modal-accent)">Key Terms</strong>';
                    structured.key_terms.forEach(kt => {
                        html += '<div style="margin:0.4rem 0;font-size:0.9rem"><strong>' + escapeHtml(kt.term) + '</strong> &mdash; ' + escapeHtml(kt.definition) + '</div>';
                    });
                    html += '</div>';
                }
                if (structured.materials && structured.materials.length > 0) {
                    html += '<div style="margin-top:0.8rem;font-size:0.85rem;color:#666"><strong>Materials:</strong> ' + structured.materials.map(escapeHtml).join(', ') + '</div>';
                }
                if (structured.expected_outcome) {
                    html += '<div style="margin-top:0.8rem;font-size:0.85rem;color:#666"><strong>Expected outcome:</strong> ' + escapeHtml(structured.expected_outcome) + '</div>';
                }
            }
            return html;
        }

        // ── Block icons ───────────────────────────────────────
        const BLOCK_ICONS = {
            OPENER:       '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>',
            EXPLAIN:      '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>',
            ACTIVITY:     '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>',
            HOMEWORK:     '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" /></svg>',
            TEACHER_NOTES:'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" /></svg>'
        };

        function renderBlock(blockType, title, summary, details, structured) {
            const icon = BLOCK_ICONS[blockType] || BLOCK_ICONS.OPENER;
            const block = document.createElement('div');
            block.className = 'encyclopedia-block';
            block.innerHTML = `
                <div class="encyclopedia-title">${icon} ${escapeHtml(title)}</div>
                <div class="encyclopedia-summary">${escapeHtml(summary)}</div>
            `;
            block.addEventListener('click', () => {
                openEncyclopedia(title, formatDetails(details, structured));
            });
            return block;
        }

        // ── Encyclopedia Modal ────────────────────────────────

        function openEncyclopedia(title, detailsHtml) {
            triggerHaptic('light');
            document.getElementById('encyclopedia-body').innerHTML = `
                <div style="font-family:'DM Serif Display',serif;color:var(--modal-accent);margin-bottom:1rem;font-size:1.1rem;font-weight:400;letter-spacing:-0.01em">${escapeHtml(title)}</div>
                <div style="line-height:1.7;font-size:0.95rem">${detailsHtml}</div>
            `;
            document.getElementById('encyclopedia-modal').classList.add('active');
        }

        function closeEncyclopedia(e) {
            if (e && e.target !== document.getElementById('encyclopedia-modal') && !e.target.classList.contains('close-modal')) return;
            document.getElementById('encyclopedia-modal').classList.remove('active');
        }

        // ── Input Handlers ────────────────────────────────────

        function handleEnter(e) { if (e.key === 'Enter') submitPrompt(); }

        function submitPromptWithText(text) {
            inputField.value = text;
            submitPrompt();
        }

        // ── Lesson notification ───────────────────────────────

        function notifyLesson(lessonName) {
            const msg = 'Lesson "' + lessonName + '" Ready';
            showToast(msg);
            // Native notification if permission granted
            if ('Notification' in window && Notification.permission === 'granted') {
                new Notification('ClassGen', { body: msg, icon: '/static/icon-192.png' });
            }
        }

        // ── AI Response Renderer ─────────────────────────────

        function renderAiResponse(data) {
            let rawText = data.reply || '';
            let buttons = [];

            const suggestsMatch = rawText.match(/SUGGESTIONS:\s*(.*)/i);
            if (suggestsMatch) {
                buttons = suggestsMatch[1].split('|')
                    .map(o => o.trim().replace(/^\[|\]$/g, '').trim())
                    .filter(Boolean).slice(0, 3);
                rawText = rawText.replace(/SUGGESTIONS:\s*(.*)/i, '').trim();
            }

            // Parse blocks: prefer structured lesson_pack, fall back to regex
            const blocks = [];
            if (data.lesson_pack && data.lesson_pack.blocks) {
                data.lesson_pack.blocks.forEach(b => {
                    let summary = '';
                    if (b.type === 'explain' && b.wow_fact) summary = b.wow_fact;
                    else if (b.type === 'activity' && b.format) summary = humanize(b.format) + (b.duration_minutes ? ' \u2014 ' + b.duration_minutes + ' minutes' : '');
                    else if (b.type === 'homework' && b.format) summary = humanize(b.format) + (b.narrative ? ' \u2014 ' + b.narrative.substring(0, 80) + '\u2026' : '');
                    else if (b.type === 'opener' && b.format) summary = humanize(b.format);
                    else if (b.wow_fact) summary = b.wow_fact;
                    blocks.push({
                        type:    (b.type || '').toUpperCase(),
                        title:   b.title || b.type || '',
                        summary: summary,
                        details: b.body || b.narrative || '',
                        structured: b
                    });
                });
            } else {
                const blockRegex = /\[BLOCK_START_(.*?)\](.*?)\[BLOCK_END\]/gs;
                let match;
                while ((match = blockRegex.exec(rawText)) !== null) {
                    const blockType = match[1].trim();
                    const blockContent = match[2];
                    const titleMatch   = blockContent.match(/Title:\s*\*{0,2}(.*?)\*{0,2}\s*(?:\n|$)/i);
                    const summaryMatch = blockContent.match(/Summary:\s*(.*?)(?:\n|$)/i);
                    const detailsMatch = blockContent.match(/Details:\s*([\s\S]*?)$/i);
                    blocks.push({
                        type:    blockType,
                        title:   titleMatch   ? titleMatch[1].replace(/\*\*/g,'').trim() : blockType,
                        summary: summaryMatch ? summaryMatch[1].trim() : '',
                        details: detailsMatch ? detailsMatch[1].trim() : ''
                    });
                }
            }

            if (blocks.length > 0) {
                const wrapper = document.createElement('div');
                wrapper.className = 'lesson-pack-wrapper';

                const label = document.createElement('div');
                label.className = 'lesson-pack-label';
                label.textContent = 'Lesson Pack';
                wrapper.appendChild(label);

                blocks.forEach(b => wrapper.appendChild(renderBlock(b.type, b.title, b.summary, b.details, b.structured)));

                const actions = document.createElement('div');
                actions.className = 'lesson-actions';
                if (data.pdf_url) {
                    const pdfLink = document.createElement('a');
                    pdfLink.href = data.pdf_url; pdfLink.target = '_blank';
                    pdfLink.className = 'lesson-action-btn';
                    pdfLink.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg> Download PDF';
                    actions.appendChild(pdfLink);
                }
                if (data.homework_code) {
                    const hwLink = document.createElement('a');
                    hwLink.href = '/h/' + encodeURIComponent(data.homework_code); hwLink.target = '_blank';
                    hwLink.className = 'lesson-action-btn';
                    hwLink.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" /></svg> Homework: ' + escapeHtml(data.homework_code);
                    actions.appendChild(hwLink);
                }
                if (actions.children.length > 0) wrapper.appendChild(actions);
                chatFeed.appendChild(wrapper);

                // Notify: use opener title as lesson name
                const lessonName = blocks[0].title || 'Untitled';
                notifyLesson(lessonName);
            } else {
                let formattedHtml = escapeHtml(rawText).replace(/\n/g, '<br>');
                formattedHtml = formattedHtml.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                chatFeed.appendChild(createAiGroup(formattedHtml, buttons));
            }
        }

        // ── Main Submit ───────────────────────────────────────

        async function submitPrompt() {
            const text = inputField.value.trim();
            if (!text || inputField.disabled) return;

            inputField.value = '';
            setThinking(true);
            triggerHaptic('medium');

            // Breadcrumb
            contextPath.push(text);
            const bar = document.getElementById('breadcrumb-bar');
            bar.classList.add('visible');
            const trunc = s => s.length > 20 ? s.slice(0, 20) + '…' : s;
            bar.innerHTML = '<span style="color:var(--accent);font-weight:600;margin-right:8px">Context:</span>' +
                contextPath.slice(0, 5).map((item, i, arr) => {
                    const sep = i < arr.length - 1 ? '<span style="margin:0 4px;opacity:0.4">›</span>' : '';
                    return `<span title="${escapeHtml(item)}">${escapeHtml(trunc(item))}</span>${sep}`;
                }).join('');

            chatFeed.appendChild(createUserGroup(text));
            scrollToBottom();

            const typingGroup = createTypingGroup();
            chatFeed.appendChild(typingGroup);
            scrollToBottom();

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text, thread_id: threadId })
                });
                if (!response.ok) {
                    throw new Error(response.status === 422 ? 'Message too long or invalid.' : 'Server error. Please try again.');
                }
                const data = await response.json();
                if (chatFeed.contains(typingGroup)) chatFeed.removeChild(typingGroup);

                renderAiResponse(data);
                saveConversation(text, data);
                scrollToBottom();

            } catch (err) {
                if (chatFeed.contains(typingGroup)) chatFeed.removeChild(typingGroup);
                chatFeed.appendChild(createAiGroup(
                    `<span style="color:#EF4444;font-weight:500">Connection Error</span><br><span style="font-size:0.82rem;opacity:0.65">${escapeHtml(err.message)}</span>`
                ));
                scrollToBottom();
            }

            setThinking(false);
            inputField.focus();
        }

        // ── Push Notifications ────────────────────────────────
        let swRegistration = null;

        async function initServiceWorker() {
            if (!('serviceWorker' in navigator) || !('PushManager' in window)) return;
            try {
                // One-time migration: clean up the legacy /static/sw.js registration
                // (was shadowed by the pdf_output named volume on prod, never updated).
                const legacy = await navigator.serviceWorker.getRegistration('/static/sw.js');
                if (legacy) await legacy.unregister();
                swRegistration = await navigator.serviceWorker.register('/assets/sw.js');
                const sub = await swRegistration.pushManager.getSubscription();
                pushEnabled = !!sub;
            } catch (e) { console.log('SW registration failed:', e); }
        }

        async function enableNotifications() {
            if (!swRegistration) return;
            try {
                const permission = await Notification.requestPermission();
                if (permission !== 'granted') return;
                const keyResp = await fetch('/api/vapid-key');
                const keyData = await keyResp.json();
                if (!keyData.publicKey) return;
                const sub = await swRegistration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: urlBase64ToUint8Array(keyData.publicKey),
                });
                const subJson = sub.toJSON();
                await fetch('/api/push/subscribe', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ endpoint: subJson.endpoint, keys: subJson.keys, teacher_id: threadId }),
                });
                pushEnabled = true;
            } catch (e) { console.error('Push subscription failed:', e); }
        }

        function urlBase64ToUint8Array(base64String) {
            const padding = '='.repeat((4 - base64String.length % 4) % 4);
            const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
            const raw = window.atob(base64);
            const arr = new Uint8Array(raw.length);
            for (let i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
            return arr;
        }

        // ── Profile Sidebar ───────────────────────────────────
        const profileState = { registered: false, teacher: null, stats: null, codes: [], loaded: false };
        let currentTab = 'profile';
        let pushEnabled = false;

        function toggleSidebar() {
            const sidebar = document.getElementById('profile-sidebar');
            if (sidebar.classList.contains('open')) { closeSidebar(); return; }
            sidebar.classList.add('open');
            document.getElementById('sidebar-overlay').classList.add('active');
            if (!profileState.loaded) fetchProfile();
            else renderSidebar();
        }

        function closeSidebar() {
            document.getElementById('profile-sidebar').classList.remove('open');
            document.getElementById('sidebar-overlay').classList.remove('active');
        }

        function switchTab(tab) {
            currentTab = tab;
            document.querySelectorAll('.sidebar-tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
            renderSidebar();
        }

        async function fetchProfile() {
            try {
                const [profileResp, countriesResp] = await Promise.all([
                    fetch('/api/teacher/profile?thread_id=' + encodeURIComponent(threadId)),
                    fetch('/api/teacher/countries'),
                ]);
                const data = await profileResp.json();
                const countriesData = await countriesResp.json();
                window._countryGroups = countriesData.groups || [];
                profileState.loaded = true;
                profileState.registered = data.registered;
                if (data.registered) {
                    profileState.teacher = data.teacher;
                    profileState.stats   = data.stats;
                    profileState.codes   = data.codes || [];
                    document.getElementById('profile-btn').classList.add('registered');
                }
            } catch (e) { console.error('Error fetching profile:', e); profileState.loaded = true; }
            renderSidebar();
        }

        function renderSidebar() {
            const container = document.getElementById('sidebar-content');
            if (currentTab === 'profile') renderProfileTab(container);
            else renderSettingsTab(container);
        }

        function renderProfileTab(container) {
            if (!profileState.registered) {
                container.innerHTML = `
                    <div style="padding:2rem 0;text-align:center">
                        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="none" viewBox="0 0 24 24" stroke="var(--accent)" style="margin:0 auto 1rem;display:block"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
                        <p style="color:var(--sidebar-muted);font-size:0.85rem;margin-bottom:1.25rem">Set up your profile so we can tailor lessons to your country and track your homework codes.</p>
                        <div class="sidebar-input-row" style="flex-direction:column;gap:0.6rem">
                            <input class="sidebar-input" id="register-name" type="text" placeholder="Your name (e.g. Mrs. Okafor)" maxlength="100">
                            <select class="sidebar-input" id="register-country" style="width:100%">
                                <option value="">Where do you teach?</option>
                                ${(window._countryGroups || []).map(g => `
                                    <optgroup label="${escapeHtml(g.region)}">
                                        ${(g.countries || []).map(c => `<option value="${escapeHtml(c.name)}">${c.flag ? c.flag + ' ' : ''}${escapeHtml(c.name)}</option>`).join('')}
                                    </optgroup>`).join('')}
                            </select>
                            <button class="sidebar-btn" style="width:100%" onclick="registerTeacher()">Get Started</button>
                        </div>
                    </div>
                `;
                return;
            }

            const t = profileState.teacher;
            const s = profileState.stats || { total: 0, this_week: 0, this_month: 0 };
            const codes = profileState.codes || [];

            const classesHtml = (t.classes && t.classes.length)
                ? t.classes.map(c => `<span class="sidebar-badge">${escapeHtml(c)}<button class="remove-class" onclick="removeClass('${escapeHtml(c)}')">&times;</button></span>`).join('')
                : `<span style="color:var(--sidebar-muted);font-size:0.8rem">No classes added yet</span>`;

            const codesHtml = codes.length
                ? '<ul class="sidebar-code-list">' + codes.map(c =>
                    `<li><a href="/h/${escapeHtml(c.code)}" target="_blank">${escapeHtml(c.code)}</a><span class="sidebar-code-title">${escapeHtml(c.title)}</span></li>`
                  ).join('') + '</ul>'
                : `<span style="color:var(--sidebar-muted);font-size:0.8rem">Generate a lesson to create homework codes</span>`;

            container.innerHTML = `
                <div class="sidebar-section">
                    <div class="sidebar-section-title">Name</div>
                    <div class="sidebar-input-row">
                        <input class="sidebar-input" id="edit-name" type="text" value="${escapeHtml(t.name)}" maxlength="100">
                        <button class="sidebar-btn" onclick="updateName()">Save</button>
                    </div>
                </div>
                <div class="sidebar-section">
                    <div class="sidebar-section-title">Country</div>
                    <select class="sidebar-input" id="country-select" onchange="updateCountry()" style="width:100%">
                        <option value="">Select country</option>
                        ${(window._countryGroups || []).map(g => `
                            <optgroup label="${escapeHtml(g.region)}">
                                ${(g.countries || []).map(c => `<option value="${escapeHtml(c.name)}" ${c.name === (t.country || '') ? 'selected' : ''}>${c.flag ? c.flag + ' ' : ''}${escapeHtml(c.name)}</option>`).join('')}
                            </optgroup>`).join('')}
                    </select>
                </div>
                <div class="sidebar-stats">
                    <div class="sidebar-stat"><div class="num">${s.total}</div><div class="lbl">Total</div></div>
                    <div class="sidebar-stat"><div class="num">${s.this_week}</div><div class="lbl">This Week</div></div>
                    <div class="sidebar-stat"><div class="num">${s.this_month}</div><div class="lbl">This Month</div></div>
                </div>
                <div class="sidebar-section">
                    <div class="sidebar-section-title">Classes</div>
                    <div style="margin-bottom:0.5rem">${classesHtml}</div>
                    <div class="sidebar-input-row">
                        <input class="sidebar-input" id="add-class-input" type="text" placeholder="e.g. SS2 Biology">
                        <button class="sidebar-btn" onclick="addClass()">Add</button>
                    </div>
                </div>
                <div class="sidebar-section">
                    <div class="sidebar-section-title">Recent Homework</div>
                    ${codesHtml}
                </div>
                ${t.slug ? `<div style="text-align:center;margin-top:0.5rem"><a href="/t/${escapeHtml(t.slug)}" target="_blank" style="color:var(--sidebar-code-link);font-size:0.8rem">View profile</a> &middot; <a href="/t/${escapeHtml(t.slug)}/export" style="color:var(--sidebar-code-link);font-size:0.8rem">Export CSV</a></div>` : ''}
            `;
        }

        function renderSettingsTab(container) {
            const dark = isDarkMode();
            const push = pushEnabled;
            container.innerHTML = `
                <div class="sidebar-section">
                    <div class="sidebar-section-title">Appearance</div>
                    <div class="sidebar-toggle">
                        <span>Dark mode</span>
                        <div class="toggle-switch ${dark ? 'on' : ''}" id="dark-toggle" onclick="toggleDarkMode()"></div>
                    </div>
                </div>

                <div class="sidebar-section">
                    <div class="sidebar-section-title">Notifications</div>
                    <div class="sidebar-toggle">
                        <span>Push notifications</span>
                        <div class="toggle-switch ${push ? 'on' : ''}" id="push-toggle" onclick="togglePush()"></div>
                    </div>
                    <p style="font-size:0.7rem;color:var(--sidebar-muted);margin-top:4px">Get notified when students submit quizzes</p>
                </div>

                <div class="sidebar-section">
                    <div class="sidebar-section-title">Intro</div>
                    <button class="sidebar-btn" style="width:100%" onclick="resetIntro()">Reset intro</button>
                    <p style="font-size:0.7rem;color:var(--sidebar-muted);margin-top:6px">Show intro on next refresh.</p>
                </div>

                <div class="sidebar-section">
                    <div class="sidebar-section-title">Chat</div>
                    <button class="sidebar-btn sidebar-btn-danger" style="width:100%" onclick="clearChatHistory()">Clear chat history</button>
                    <p style="font-size:0.7rem;color:var(--sidebar-muted);margin-top:6px">Removes all messages from this session</p>
                </div>
            `;
        }

        function resetIntro() {
            localStorage.removeItem('classgen_intro_seen');
            showToast('Intro will show on next refresh.');
        }

        async function registerTeacher() {
            const nameInput = document.getElementById('register-name');
            const countryInput = document.getElementById('register-country');
            const name = nameInput ? nameInput.value.trim() : '';
            const country = countryInput ? countryInput.value : '';
            if (name.length < 2) { nameInput && nameInput.focus(); return; }
            if (!country) { countryInput && countryInput.focus(); return; }
            try {
                const resp = await fetch('/api/teacher/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ thread_id: threadId, name, country }),
                });
                if (!resp.ok) return;
                const data = await resp.json();
                profileState.registered = true;
                profileState.teacher = data.teacher;
                profileState.stats   = { total: 0, this_week: 0, this_month: 0 };
                profileState.codes   = [];
                document.getElementById('profile-btn').classList.add('registered');
                renderSidebar();
            } catch (e) { console.error('Register error:', e); }
        }

        async function updateName() {
            const nameInput = document.getElementById('edit-name');
            const name = nameInput ? nameInput.value.trim() : '';
            if (name.length < 2) return;
            try {
                const resp = await fetch('/api/teacher/profile', {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ thread_id: threadId, name }),
                });
                if (!resp.ok) return;
                const data = await resp.json();
                profileState.teacher = data.teacher;
                renderSidebar();
            } catch (e) { console.error('Update name error:', e); }
        }

        async function updateCountry() {
            const sel = document.getElementById('country-select');
            const country = sel ? sel.value : '';
            if (!country) return;
            try {
                const resp = await fetch('/api/teacher/country', {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ thread_id: threadId, country }),
                });
                if (!resp.ok) return;
                profileState.teacher.country = country;
            } catch (e) { console.error('Update country error:', e); }
        }

        async function addClass() {
            const input = document.getElementById('add-class-input');
            const className = input ? input.value.trim() : '';
            if (className.length < 3) { input && input.focus(); return; }
            try {
                const resp = await fetch('/api/teacher/classes', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ thread_id: threadId, class_name: className }),
                });
                if (!resp.ok) return;
                const data = await resp.json();
                profileState.teacher.classes = data.classes;
                renderSidebar();
            } catch (e) { console.error('Add class error:', e); }
        }

        async function removeClass(className) {
            try {
                const resp = await fetch('/api/teacher/classes/' + encodeURIComponent(className) + '?thread_id=' + encodeURIComponent(threadId), { method: 'DELETE' });
                if (!resp.ok) return;
                const data = await resp.json();
                profileState.teacher.classes = data.classes;
                renderSidebar();
            } catch (e) { console.error('Remove class error:', e); }
        }

        async function clearChatHistory() {
            if (!confirm('Clear all chat messages? This cannot be undone.')) return;
            try {
                await fetch('/api/teacher/history?thread_id=' + encodeURIComponent(threadId), { method: 'DELETE' });
                chatFeed.innerHTML = '';
                contextPath.length = 0;
                const bar = document.getElementById('breadcrumb-bar');
                bar.classList.remove('visible'); bar.innerHTML = '';
                chatFeed.appendChild(createAiGroup('Chat history cleared. What topic shall we work on?'));
                scrollToBottom();
            } catch (e) { console.error('Clear history error:', e); }
        }

        async function togglePush() {
            if (pushEnabled) return;
            await enableNotifications();
            if (swRegistration) {
                const sub = await swRegistration.pushManager.getSubscription();
                if (sub) {
                    pushEnabled = true;
                    const toggle = document.getElementById('push-toggle');
                    if (toggle) toggle.classList.add('on');
                }
            }
        }

        async function checkPushStatus() {
            if (!('serviceWorker' in navigator) || !('PushManager' in window)) return;
            try {
                const reg = await navigator.serviceWorker.getRegistration('/assets/sw.js');
                if (reg) { const sub = await reg.pushManager.getSubscription(); pushEnabled = !!sub; }
            } catch (e) {}
        }

        // ── Intro Onboarding ──────────────────────────────────

        const INTRO_CONTENT = {
            brand: 'ClassGen',
            tagline: 'Your Teaching assistant that gives you super powers ',
            subtitle: 'Ready-to-teach lesson packs for your classroom \u2014 in seconds',
            slides: [
                {
                    heading: 'Type a topic. Get a lesson pack.',
                    body: 'Send any topic and get a structured lesson: opener hook, core concept, classroom activity, exercise-book homework, and teacher notes.',
                    examples: [
                        '🇳🇬 · SS2, Nigeria, Biology, Photosynthesis, 40 mins',
                        '🇰🇪 · Form 3, Wave Motion, Physics, Kenya, 1 hour',
                        '🇷🇼 · History, Rwanda, Senior 4, Colonial Rule in East Africa, 45 mins',
                        '🇮🇳 · Class 10, India, Quadratic Equations, Maths, 1h 20 mins',
                    ],
                },
                {
                    heading: 'Everything your students need',
                    features: [
                        'Download & print lesson plans as PDF',
                        'Homework codes with auto-graded quizzes',
                        'Works on WhatsApp too \u2014 just send a message',
                    ],
                },
            ],
            cta: 'Accept & Start Teaching',
            skip: 'Skip',
            terms_url: '/terms',
            terms_text: 'By continuing you agree to our Terms & Privacy Policy',
        };

        let introSlide = 0;
        const LAST_SLIDE = 3;
        const ctaLabels = ['See How It Works', 'Next', 'Next', 'Accept & Start Teaching'];

        function initIntro() {
            if (localStorage.getItem('classgen_intro_seen')) return;
            const overlay = document.getElementById('intro-overlay');
            overlay.classList.remove('hidden');

            // Touch swipe support
            let touchStartX = 0;
            overlay.addEventListener('touchstart', e => { touchStartX = e.touches[0].clientX; }, { passive: true });
            overlay.addEventListener('touchend', e => {
                const dx = e.changedTouches[0].clientX - touchStartX;
                if (Math.abs(dx) > 50) {
                    if (dx < 0 && introSlide < LAST_SLIDE) goToIntroSlide(introSlide + 1);
                    else if (dx > 0 && introSlide > 0) goToIntroSlide(introSlide - 1);
                }
            }, { passive: true });

            // Dot clicks
            document.querySelectorAll('.intro-dot').forEach(dot => {
                dot.addEventListener('click', () => goToIntroSlide(parseInt(dot.dataset.dot)));
            });

            // CTA button
            document.getElementById('intro-cta').addEventListener('click', () => {
                if (introSlide < LAST_SLIDE) goToIntroSlide(introSlide + 1);
                else dismissIntro();
            });

            // Skip button
            document.getElementById('intro-skip').addEventListener('click', () => {
                goToIntroSlide(LAST_SLIDE); // Jump to accept slide
            });
        }

        function goToIntroSlide(n) {
            const slides = document.querySelectorAll('.intro-slide');
            const dots = document.querySelectorAll('.intro-dot');
            slides[introSlide].classList.remove('active');
            slides[introSlide].classList.add('prev');
            setTimeout(() => slides[introSlide].classList.remove('prev'), 400);
            introSlide = n;
            slides[introSlide].classList.add('active');
            dots.forEach((d, i) => d.classList.toggle('active', i === n));
            document.getElementById('intro-cta').textContent = ctaLabels[n];
            // Hide skip on last slide
            document.getElementById('intro-skip').style.display = n === LAST_SLIDE ? 'none' : '';
        }

        function dismissIntro() {
            localStorage.setItem('classgen_intro_seen', '1');
            const overlay = document.getElementById('intro-overlay');
            overlay.classList.add('hidden');
            setTimeout(() => overlay.remove(), 600);
            inputField.focus();
        }

        window.onload = () => {
            chatFeed.appendChild(createAiGroup(
                'Hey! Let\'s build a great lesson. What subject are we teaching today?'
            ));
            restoreConversation();
            initIntro();
            inputField.focus();
            initServiceWorker();
            fetchProfile();
            checkPushStatus();
        };
