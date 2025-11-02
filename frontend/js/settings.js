document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('profile-form') || document.getElementById('settings-form');
  const langSel = document.getElementById('language-select');
  const audioSel = document.getElementById('audio-speed-select');
  const showTipsEl = document.getElementById('show-voice-tips');
  const compactTipsEl = document.getElementById('compact-voice-tips');
  const themeSel = document.getElementById('theme-select');
  const tonesEl = document.getElementById('enable-tones');
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
    // Enforce compact tips globally: hide/disable banner option and force compact
    if (showTipsEl) {
      // Hide the banner option as it's no longer used
      const row = showTipsEl.closest('.form-group') || showTipsEl.parentElement;
      if (row) row.style.display = 'none';
      showTipsEl.checked = false;
      showTipsEl.disabled = true;
    }
    if (compactTipsEl) {
      compactTipsEl.checked = true;
      compactTipsEl.disabled = true; // enforced
    }
    if (themeSel) themeSel.value = s.theme || 'light';
    if (tonesEl) tonesEl.checked = (s.enableTones !== false); // default true

    // Apply theme immediately
    if (s.theme) {
      document.documentElement.setAttribute('data-theme', s.theme);
    }
  } catch (_) {}

  if (!form) return;
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const language = langSel ? langSel.value : 'en';
    const audioRate = audioSel ? parseFloat(audioSel.value) : 1.3;
    // Enforce settings: banner disabled, compact enabled
    const showVoiceTips = false;
    const compactVoiceTips = true;
    const theme = themeSel ? themeSel.value : 'light';
    const enableTones = tonesEl ? !!tonesEl.checked : true;
    try {
      if (typeof setAppSettings === 'function') {
        setAppSettings({ language, audioRate, showVoiceTips, compactVoiceTips, theme, enableTones });
      } else {
        const current = JSON.parse(localStorage.getItem('app_settings')||'{}');
        const merged = { ...current, language, audioRate, showVoiceTips, compactVoiceTips, theme, enableTones };
        localStorage.setItem('app_settings', JSON.stringify(merged));
      }
    } catch (_) {}
    // Apply theme live
    document.documentElement.setAttribute('data-theme', theme);
    showMessage('Settings saved.');
    
    // Announce theme change for screen readers
    try {
      let liveRegion = document.getElementById('theme-announce-live');
      if (!liveRegion) {
        liveRegion = document.createElement('div');
        liveRegion.id = 'theme-announce-live';
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('aria-atomic', 'true');
        liveRegion.style.cssText = 'position:absolute;left:-10000px;width:1px;height:1px;overflow:hidden;';
        document.body.appendChild(liveRegion);
      }
      const themeLabel = themeSel ? themeSel.options[themeSel.selectedIndex].text : theme;
      liveRegion.textContent = `Theme changed to ${themeLabel}`;
    } catch(_) {}
  });
});
