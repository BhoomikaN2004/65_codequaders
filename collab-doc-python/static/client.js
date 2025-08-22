// static/client.js
const socket = io();
let base_version = -1;
const editor = document.getElementById('editor');
const status = document.getElementById('status');
const authorField = document.getElementById('author');

function setStatus(s) { status.textContent = s }

socket.on('connect', () => {
  socket.emit('join', {room: 'main'});
  fetch('/api/current').then(r=>r.json()).then(data=>{
    base_version = data.version;
    editor.value = data.text;
    setStatus('v' + base_version);
  });
});

socket.on('joined', (data) => {
  base_version = data.version;
  editor.value = data.text;
  setStatus('joined v' + base_version);
});

// debounce edits so we don't spam the server
let typingTimer;
editor.addEventListener('input', () => {
  clearTimeout(typingTimer);
  typingTimer = setTimeout(() => {
    const text = editor.value;
    socket.emit('edit', {text: text, base_version: base_version});
  }, 350);
});

socket.on('update', (data) => {
  // replace content if the incoming version is newer
  if (data.version > base_version) {
    const cursor = editor.selectionStart;
    editor.value = data.text;
    try { editor.selectionStart = editor.selectionEnd = cursor } catch(e) {}
    base_version = data.version;
    setStatus('v' + base_version);
  }
});

socket.on('conflict', (data) => {
  // naive conflict resolution: overwrite local with server content
  editor.value = data.text;
  base_version = data.version;
  setStatus('conflict — synced to v' + base_version);
});

// Commit button
document.getElementById('commitBtn').addEventListener('click', () => {
  const msg = document.getElementById('commitMsg').value || 'manual commit';
  const author = authorField.value || 'anonymous';
  fetch('/api/commit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({message: msg, author: author})
  }).then(r=>r.json()).then(data => {
    if (data.version) {
      base_version = data.version;
      setStatus('committed v' + base_version);
    }
  });
});

// History button
document.getElementById('historyBtn').addEventListener('click', () => {
  const histDiv = document.getElementById('history');
  fetch('/api/commits').then(r=>r.json()).then(commits => {
    histDiv.style.display = 'block';
    histDiv.innerHTML = '';
    commits.forEach(c => {
      const btn = document.createElement('button');
      btn.textContent = `v${c.version} — ${c.author} — ${c.message} — ${new Date(c.timestamp*1000).toLocaleString()}`;
      btn.addEventListener('click', () => {
        fetch('/api/checkout/' + c.version, { method: 'POST' })
          .then(r=>r.json()).then(res => {
            if (res.version) setStatus('checked out v' + res.version);
          });
      });
      histDiv.appendChild(btn);
      histDiv.appendChild(document.createElement('br'));
    });
  });
});
