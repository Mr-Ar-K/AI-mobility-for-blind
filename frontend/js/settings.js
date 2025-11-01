document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('settings-form');
  const langSel = document.getElementById('language-select');
  const audioSel = document.getElementById('audio-speed-select');
  const msg = document.getElementById('message-text');

  function showMessage(text, ok=true) {
    if (!msg) return;
    msg.textContent = text;
    msg.style.color = ok ? '#2e7d32' : '#c62828';
  }

  // Load existing settings
  try {
    const s = (typeof getAppSettings === 'function') ? getAppSettings() : {};
    if (s.language && langSel) langSel.value = s.language;
    if (s.audioRate && audioSel) audioSel.value = String(s.audioRate);
  } catch (_) {}

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const language = langSel ? langSel.value : 'en';
    const audioRate = audioSel ? parseFloat(audioSel.value) : 1.3;
    if (typeof setAppSettings === 'function') {
      setAppSettings({ language, audioRate });
    }
    showMessage('Settings saved.');
  });
});
