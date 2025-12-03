/**
 * Personal AI Assistant - Main Module
 * Dashboard functionality for managing events, tasks, and Mac sync
 */

const AssistantMain = (() => {
  // State
  let dashboardData = null;
  let parsedData = null;

  // ===== Initialization =====
  async function init() {
    console.log('[Assistant] Initializing...');

    // Set today's date
    const today = new Date();
    const options = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' };
    document.getElementById('today-date').textContent = today.toLocaleDateString('ko-KR', options);

    // Load dashboard data
    await loadDashboard();
  }

  // ===== Dashboard Loading =====
  async function loadDashboard() {
    try {
      const response = await fetch('/assistant/api/dashboard');
      const data = await response.json();

      if (data.success) {
        dashboardData = data;
        renderDashboard(data);
      } else {
        console.error('[Assistant] Dashboard load error:', data.error);
        showError('Failed to load dashboard');
      }
    } catch (error) {
      console.error('[Assistant] Dashboard fetch error:', error);
      showError('Network error');
    }
  }

  // ===== Rendering =====
  function renderDashboard(data) {
    // Today's Events
    renderEvents('today-events', data.today_events);

    // Week Events
    renderEvents('week-events', data.week_events);

    // Pending Tasks
    renderTasks('pending-tasks', data.pending_tasks);

    // Pending Sync
    renderPendingSync('pending-sync', data.pending_sync);
  }

  function renderEvents(containerId, events) {
    const container = document.getElementById(containerId);

    if (!events || events.length === 0) {
      container.innerHTML = '<div class="empty">No events</div>';
      return;
    }

    container.innerHTML = events.map(event => {
      const startTime = event.start_time ? formatTime(event.start_time) : '';
      const category = event.category ? `<span class="item-category">${event.category}</span>` : '';
      const syncBadge = getSyncBadge(event.sync_status);

      return `
        <div class="item">
          <div class="item-time">${startTime}</div>
          <div class="item-content">
            <div class="item-title">${escapeHtml(event.title)}</div>
            <div class="item-meta">${category} ${syncBadge}</div>
          </div>
        </div>
      `;
    }).join('');
  }

  function renderTasks(containerId, tasks) {
    const container = document.getElementById(containerId);

    if (!tasks || tasks.length === 0) {
      container.innerHTML = '<div class="empty">No pending tasks</div>';
      return;
    }

    container.innerHTML = tasks.map(task => {
      const dueDate = task.due_date ? formatDate(task.due_date) : 'No due date';
      const priorityClass = `priority-${task.priority || 'medium'}`;
      const category = task.category ? `<span class="item-category">${task.category}</span>` : '';
      const syncBadge = getSyncBadge(task.sync_status);

      return `
        <div class="item">
          <div class="item-content">
            <div class="item-title">
              <span class="${priorityClass}">●</span>
              ${escapeHtml(task.title)}
            </div>
            <div class="item-meta">
              <span>${dueDate}</span>
              ${category} ${syncBadge}
            </div>
          </div>
          <button class="btn btn-small btn-secondary" onclick="AssistantMain.completeTask(${task.id})">
            ✓
          </button>
        </div>
      `;
    }).join('');
  }

  function renderPendingSync(containerId, syncInfo) {
    const container = document.getElementById(containerId);

    if (!syncInfo || syncInfo.total === 0) {
      container.innerHTML = '<div class="empty">All synced!</div>';
      document.getElementById('btn-sync').disabled = true;
      return;
    }

    document.getElementById('btn-sync').disabled = false;
    container.innerHTML = `
      <div class="item">
        <div class="item-content">
          <div class="item-title">${syncInfo.events} events, ${syncInfo.tasks} tasks</div>
          <div class="item-meta">Waiting to sync to Mac Calendar/Reminders</div>
        </div>
      </div>
    `;
  }

  // ===== Input Analyzer =====
  async function analyzeInput() {
    const inputBox = document.getElementById('input-box');
    const text = inputBox.value.trim();

    if (!text) {
      alert('Please enter some text to analyze');
      return;
    }

    const btn = document.getElementById('btn-analyze');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span class="loading"></span> Analyzing...';
    btn.disabled = true;

    try {
      const response = await fetch('/assistant/api/parse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });

      const data = await response.json();

      if (data.success) {
        parsedData = data.parsed;
        showParsedResult(data.parsed);
      } else {
        alert('Analysis failed: ' + data.error);
      }
    } catch (error) {
      console.error('[Assistant] Parse error:', error);
      alert('Network error');
    } finally {
      btn.innerHTML = originalText;
      btn.disabled = false;
    }
  }

  function showParsedResult(parsed) {
    const resultDiv = document.getElementById('parsed-result');
    const eventsDiv = document.getElementById('parsed-events');
    const tasksDiv = document.getElementById('parsed-tasks');

    // Render parsed events
    if (parsed.events && parsed.events.length > 0) {
      eventsDiv.innerHTML = `
        <h5>Events (${parsed.events.length})</h5>
        ${parsed.events.map((e, i) => `
          <div class="parsed-item">
            <div>
              <strong>${escapeHtml(e.title)}</strong>
              <span class="item-meta">${e.date} ${e.time || ''}</span>
            </div>
            <span class="item-category">${e.category || ''}</span>
          </div>
        `).join('')}
      `;
    } else {
      eventsDiv.innerHTML = '';
    }

    // Render parsed tasks
    if (parsed.tasks && parsed.tasks.length > 0) {
      tasksDiv.innerHTML = `
        <h5 style="margin-top: 1rem;">Tasks (${parsed.tasks.length})</h5>
        ${parsed.tasks.map((t, i) => `
          <div class="parsed-item">
            <div>
              <strong>${escapeHtml(t.title)}</strong>
              <span class="item-meta">${t.due_date || 'No due date'}</span>
            </div>
            <span class="priority-${t.priority || 'medium'}">${t.priority || 'medium'}</span>
          </div>
        `).join('')}
      `;
    } else {
      tasksDiv.innerHTML = '';
    }

    resultDiv.classList.add('show');
  }

  async function saveParsedData() {
    if (!parsedData) {
      alert('No parsed data to save');
      return;
    }

    try {
      let savedEvents = 0;
      let savedTasks = 0;

      // Save events
      for (const event of (parsedData.events || [])) {
        const response = await fetch('/assistant/api/events', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: event.title,
            start_time: `${event.date}T${event.time || '00:00'}:00`,
            end_time: event.end_time ? `${event.date}T${event.end_time}:00` : null,
            category: event.category
          })
        });
        if ((await response.json()).success) savedEvents++;
      }

      // Save tasks
      for (const task of (parsedData.tasks || [])) {
        const response = await fetch('/assistant/api/tasks', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: task.title,
            due_date: task.due_date,
            priority: task.priority,
            category: task.category
          })
        });
        if ((await response.json()).success) savedTasks++;
      }

      alert(`Saved ${savedEvents} events and ${savedTasks} tasks`);

      // Clear and reload
      document.getElementById('input-box').value = '';
      document.getElementById('parsed-result').classList.remove('show');
      parsedData = null;
      await loadDashboard();

    } catch (error) {
      console.error('[Assistant] Save error:', error);
      alert('Failed to save data');
    }
  }

  // ===== Task Actions =====
  async function completeTask(taskId) {
    try {
      const response = await fetch(`/assistant/api/tasks/${taskId}/complete`, {
        method: 'POST'
      });

      const data = await response.json();
      if (data.success) {
        await loadDashboard();
      } else {
        alert('Failed to complete task: ' + data.error);
      }
    } catch (error) {
      console.error('[Assistant] Complete task error:', error);
      alert('Network error');
    }
  }

  function addTask() {
    const title = prompt('Enter task title:');
    if (!title) return;

    const dueDate = prompt('Enter due date (YYYY-MM-DD) or leave empty:');

    fetch('/assistant/api/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title,
        due_date: dueDate || null,
        priority: 'medium'
      })
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        loadDashboard();
      } else {
        alert('Failed to add task: ' + data.error);
      }
    })
    .catch(err => {
      console.error('[Assistant] Add task error:', err);
      alert('Network error');
    });
  }

  // ===== Mac Sync =====
  async function syncToMac() {
    const btn = document.getElementById('btn-sync');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span class="loading"></span> Syncing...';
    btn.disabled = true;

    try {
      // Get pending items
      const response = await fetch('/assistant/api/sync/to-mac');
      const data = await response.json();

      if (data.success) {
        // Show sync data (for manual copy to Mac Shortcuts)
        const syncData = {
          events: data.events,
          tasks: data.tasks
        };

        console.log('[Assistant] Sync data for Mac:', syncData);

        // Copy to clipboard
        await navigator.clipboard.writeText(JSON.stringify(syncData, null, 2));
        alert(`Sync data copied to clipboard!\n\nEvents: ${data.events.length}\nTasks: ${data.tasks.length}\n\nPaste this in Mac Shortcuts to sync.`);
      } else {
        alert('Sync failed: ' + data.error);
      }
    } catch (error) {
      console.error('[Assistant] Sync error:', error);
      alert('Network error');
    } finally {
      btn.innerHTML = originalText;
      btn.disabled = false;
    }
  }

  // ===== Section Navigation =====
  function showSection(section) {
    console.log('[Assistant] Show section:', section);
    // TODO: Implement section navigation
    alert('Section navigation coming soon: ' + section);
  }

  // ===== Utility Functions =====
  function formatTime(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
  }

  function formatDate(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
  }

  function getSyncBadge(status) {
    if (status === 'synced') {
      return '<span class="sync-badge sync-synced">✓ Synced</span>';
    } else if (status === 'pending_to_mac') {
      return '<span class="sync-badge sync-pending">⏳ Pending</span>';
    }
    return '';
  }

  function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function showError(message) {
    console.error('[Assistant] Error:', message);
    // Show error in all containers
    ['today-events', 'week-events', 'pending-tasks', 'pending-sync'].forEach(id => {
      const container = document.getElementById(id);
      if (container) {
        container.innerHTML = `<div class="empty" style="color: #f44336;">Error: ${message}</div>`;
      }
    });
  }

  // ===== Initialize on DOM Ready =====
  document.addEventListener('DOMContentLoaded', init);

  // ===== Public API =====
  return {
    loadDashboard,
    analyzeInput,
    saveParsedData,
    completeTask,
    addTask,
    syncToMac,
    showSection
  };
})();
