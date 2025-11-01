document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('settings-form');
  const langSel = document.getElementById('language-select');
  const audioSel = document.getElementById('audio-speed-select');
  const showTipsEl = document.getElementById('show-voice-tips');
  const compactTipsEl = document.getElementById('compact-voice-tips');
  const msg = document.getElementById('message-text');

  function showMessage(text, ok=true) {
    if (!msg) return;
    msg.textContent = text;
    msg.style.color = ok ? '#2e7d32' : '#c62828';
  }

  // Load existing settings
  try {
    const s = (typeof getAppSettings === 'function') ? getAppSettings() : (JSON.parse(localStorage.getItem('app_settings')||'{}'));
    if (s.language && langSel) langSel.value = s.language;
    if (s.audioRate && audioSel) audioSel.value = String(s.audioRate);
    if (showTipsEl) showTipsEl.checked = (s.showVoiceTips !== false); // default true
    if (compactTipsEl) compactTipsEl.checked = (s.compactVoiceTips === true); // default false
  } catch (_) {}

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const language = langSel ? langSel.value : 'en';
    const audioRate = audioSel ? parseFloat(audioSel.value) : 1.3;
    const showVoiceTips = showTipsEl ? !!showTipsEl.checked : true;
    const compactVoiceTips = compactTipsEl ? !!compactTipsEl.checked : false;
    try {
      if (typeof setAppSettings === 'function') {
        setAppSettings({ language, audioRate, showVoiceTips, compactVoiceTips });
      } else {
        const current = JSON.parse(localStorage.getItem('app_settings')||'{}');
        const merged = { ...current, language, audioRate, showVoiceTips, compactVoiceTips };
        localStorage.setItem('app_settings', JSON.stringify(merged));
      }
    } catch (_) {}
    showMessage('Settings saved.');
  });
});
