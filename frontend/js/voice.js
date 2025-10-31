// Voice command controller using Web Speech API
// Provides navigation and page actions via voice.

(function() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const synth = window.speechSynthesis;

  function speak(text) {
    try {
      if (!synth) return;
      const utter = new SpeechSynthesisUtterance(text);
      utter.rate = 1;
      utter.pitch = 1;
      utter.lang = 'en-US';
      synth.cancel();
      synth.speak(utter);
    } catch (_) {}
  }

  if (!SpeechRecognition) {
    console.warn('SpeechRecognition not supported in this browser');
    // Optional: tell the user via TTS if available
    speak('Voice control is not supported in this browser.');
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = 'en-US';
  recognition.continuous = true;
  recognition.interimResults = false;

  // Utilities
  const go = (page) => { window.location.href = page; };
  const on = (sel) => document.querySelector(sel);
  const onAll = (sel) => Array.from(document.querySelectorAll(sel));

  function handleCommonCommands(cmd) {
    // Navigation
    if (/go (to )?home|open home/.test(cmd)) { speak('Opening home'); go('home.html'); return true; }
    if (/go (to )?upload|open upload/.test(cmd)) { speak('Opening upload'); go('upload.html'); return true; }
    if (/go (to )?detection|open detection|go (to )?detections|open detections/.test(cmd)) { speak('Opening detections'); go('detections.html'); return true; }
    if (/go (to )?about|open about/.test(cmd)) { speak('Opening about'); go('about.html'); return true; }
    if (/go (to )?profile|open profile/.test(cmd)) { speak('Opening profile'); go('profile.html'); return true; }
    if (/go (to )?settings|open settings/.test(cmd)) { speak('Opening settings'); go('settings.html'); return true; }
    if (/go (to )?feedback|open feedback/.test(cmd)) { speak('Opening feedback'); go('feedback.html'); return true; }
    if (/go (to )?login|open login/.test(cmd)) { speak('Opening login'); go('login.html'); return true; }
    if (/go (to )?register|open register|sign up|create account/.test(cmd)) { speak('Opening register'); go('register.html'); return true; }
    
    // Logout
    if (/logout|log out|sign out/.test(cmd)) { try { handleLogout(); } catch(_) {} speak('Logging out'); return true; }
    
    // Playback controls (generic)
    if (/play audio|play (the )?summary/.test(cmd)) {
      const a = on('audio'); if (a) { a.play(); speak('Playing'); } else { speak('No audio found'); }
      return true;
    }
    if (/pause audio|pause/.test(cmd)) {
      const a = on('audio'); if (a) { a.pause(); speak('Paused'); } else { speak('No audio found'); }
      return true;
    }
    // Play nth audio: "play first|second|third audio" or "play audio number 2"
    const nthMap = { first:1, second:2, third:3, fourth:4, fifth:5 };
    const nthMatch = cmd.match(/play (the )?(\w+) audio|play audio number (\d+)/);
    if (nthMatch) {
      let idx = null;
      if (nthMatch[2] && nthMap[nthMatch[2]]) idx = nthMap[nthMatch[2]] - 1;
      if (nthMatch[3]) idx = parseInt(nthMatch[3], 10) - 1;
      const audios = onAll('audio');
      if (idx != null && audios[idx]) { audios[idx].play(); speak('Playing'); return true; }
      speak('Audio not found'); return true;
    }
    return false;
  }

  function handleIndexCommands(cmd) {
    // Landing page: allow login/register by voice
    if (/login/.test(cmd)) { speak('Opening login'); go('login.html'); return true; }
    if (/register|sign up|create account/.test(cmd)) { speak('Opening register'); go('register.html'); return true; }
    return false;
  }

  function handleLoginCommands(cmd) {
    const emailEl = on('#email');
    const passEl = on('#password');
    const form = on('#login-form');
    if (/email (is|at) (.+)/.test(cmd) && emailEl) {
      const m = cmd.match(/email (is|at) (.+)/);
      emailEl.value = (m && m[2]) ? m[2].replace(/\s+at\s+/g,'@').replace(/\s+dot\s+/g,'.').replace(/\s/g,'') : emailEl.value;
      speak('Email set'); return true;
    }
    if (/password (is|equals) (.+)/.test(cmd) && passEl) {
      const m = cmd.match(/password (is|equals) (.+)/);
      passEl.value = m && m[2] ? m[2] : passEl.value;
      speak('Password set'); return true;
    }
    if (/(log in|login|sign in|submit)/.test(cmd) && form) { form.dispatchEvent(new Event('submit', {cancelable:true, bubbles:true})); speak('Logging in'); return true; }
    return false;
  }

  function handleRegisterCommands(cmd) {
    const firstEl = on('#first-name');
    const emailEl = on('#email');
    const passEl = on('#password');
    const form = on('#register-form');
    if (/first name (is|equals) (.+)/.test(cmd) && firstEl) { firstEl.value = cmd.match(/first name (is|equals) (.+)/)[2]; speak('First name set'); return true; }
    if (/email (is|at) (.+)/.test(cmd) && emailEl) {
      const m = cmd.match(/email (is|at) (.+)/);
      emailEl.value = (m && m[2]) ? m[2].replace(/\s+at\s+/g,'@').replace(/\s+dot\s+/g,'.').replace(/\s/g,'') : emailEl.value;
      speak('Email set'); return true;
    }
    if (/password (is|equals) (.+)/.test(cmd) && passEl) { passEl.value = cmd.match(/password (is|equals) (.+)/)[2]; speak('Password set'); return true; }
    if (/(create account|register|sign up|submit)/.test(cmd) && form) { form.dispatchEvent(new Event('submit', {cancelable:true, bubbles:true})); speak('Creating account'); return true; }
    return false;
  }

  function handleHomeCommands(cmd) {
    // Cards are just navigation, covered by common commands.
    return false;
  }

  function handleUploadCommands(cmd) {
    const form = on('#upload-form');
    const fileEl = on('#video-input');
    if (/(upload|process) (video|file)|submit/.test(cmd)) {
      if (fileEl && fileEl.files && fileEl.files.length > 0) {
        form && form.dispatchEvent(new Event('submit', {cancelable:true, bubbles:true}));
        speak('Uploading and processing your video');
      } else {
        speak('Please select a video file first. For security reasons, the browser does not allow voice selection of files.');
      }
      return true;
    }
    return false;
  }

  function handleDetectionsCommands(cmd) {
    // Covered by common audio commands
    return false;
  }

  function handleProfileCommands(cmd) {
    const firstEl = on('#first-name');
    const form = on('#profile-form');
    if (/first name (is|equals) (.+)/.test(cmd) && firstEl) { firstEl.value = cmd.match(/first name (is|equals) (.+)/)[2]; speak('First name set'); return true; }
    if (/(update profile|save profile|submit)/.test(cmd) && form) { form.dispatchEvent(new Event('submit', {cancelable:true, bubbles:true})); speak('Updating profile'); return true; }
    return false;
  }

  function handleFeedbackCommands(cmd) {
    const textEl = on('#feedback-form #feedback-text');
    const form = on('#feedback-form');
    if (/feedback (is|equals) (.+)/.test(cmd) && textEl) { textEl.value = cmd.match(/feedback (is|equals) (.+)/)[2]; speak('Feedback set'); return true; }
    if (/(submit feedback|send feedback|submit)/.test(cmd) && form) { form.dispatchEvent(new Event('submit', {cancelable:true, bubbles:true})); speak('Submitting feedback'); return true; }
    return false;
  }

  function handleSettingsCommands(cmd) {
    // Example: "set language english"
    const select = on('#language-select');
    if (/set language (.+)/.test(cmd) && select) {
      const lang = cmd.match(/set language (.+)/)[1].trim();
      for (const opt of select.options) {
        if (opt.text.toLowerCase() === lang || opt.value.toLowerCase() === lang) {
          select.value = opt.value; speak('Language set to ' + opt.text); return true;
        }
      }
      speak('Language not found'); return true;
    }
    const form = on('#settings-form');
    if (/(save settings|submit)/.test(cmd) && form) { form.dispatchEvent(new Event('submit', {cancelable:true, bubbles:true})); speak('Saving settings'); return true; }
    return false;
  }

  function routeCommand(cmd) {
    cmd = cmd.toLowerCase().trim();
    if (!cmd) return;
    if (handleCommonCommands(cmd)) return;

    const path = window.location.pathname;
    if (path.endsWith('/index.html') || path.endsWith('/') ) { if (handleIndexCommands(cmd)) return; }
    if (path.endsWith('/login.html')) { if (handleLoginCommands(cmd)) return; }
    if (path.endsWith('/register.html')) { if (handleRegisterCommands(cmd)) return; }
    if (path.endsWith('/home.html')) { if (handleHomeCommands(cmd)) return; }
    if (path.endsWith('/upload.html')) { if (handleUploadCommands(cmd)) return; }
    if (path.endsWith('/detections.html')) { if (handleDetectionsCommands(cmd)) return; }
    if (path.endsWith('/profile.html')) { if (handleProfileCommands(cmd)) return; }
    if (path.endsWith('/feedback.html')) { if (handleFeedbackCommands(cmd)) return; }
    if (path.endsWith('/settings.html')) { if (handleSettingsCommands(cmd)) return; }
  }

  recognition.onresult = (e) => {
    const result = e.results[e.results.length - 1];
    if (result.isFinal) {
      const transcript = result[0].transcript;
      routeCommand(transcript);
    }
  };
  recognition.onend = () => { try { recognition.start(); } catch(_) {} };

  // Start listening after DOM content is ready to ensure forms exist.
  document.addEventListener('DOMContentLoaded', () => {
    try { recognition.start(); speak('Voice control activated.'); } catch(_) {}
  });
})();
