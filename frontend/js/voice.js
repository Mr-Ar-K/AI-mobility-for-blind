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

  // Build contextual voice tips per page
  function tipsForPath(path) {
    const common = [
      'Say: go to home | upload | detections',
      'Say: play audio / pause audio',
      'Say: logout',
    ];
    if (path.endsWith('/index.html') || path.endsWith('/')) {
      return [
        'Say: login',
        'Say: register',
        ...common,
      ];
    }
    if (path.endsWith('/login.html')) {
      return [
        'Say: username is <your name>',
        'Say: email is name at example dot com',
        'Say: password is <your password>',
        'Say: login',
        ...common,
      ];
    }
    if (path.endsWith('/register.html')) {
      return [
        'Say: username is <your name>',
        'Say: email is name at example dot com',
        'Say: password is <your password>',
        'Say: register',
        ...common,
      ];
    }
    if (path.endsWith('/home.html')) {
      return [
        'Say: go to upload',
        'Say: go to detections',
        ...common,
      ];
    }
    if (path.endsWith('/upload.html')) {
      return [
        'Say: upload video',
        'Progress is announced while processing',
        ...common,
      ];
    }
    if (path.endsWith('/detections.html')) {
      return [
        'Say: play video | pause video',
        'Say: play first/second video',
        'Say: play audio | pause audio',
        ...common,
      ];
    }
    if (path.endsWith('/profile.html')) {
      return [
        'Say: username is <new name>',
        'Say: update profile',
        ...common,
      ];
    }
    if (path.endsWith('/settings.html')) {
      return [
        'Say: set language English',
        'Say: set audio speed 1.3',
        'Say: save settings',
        ...common,
      ];
    }
    if (path.endsWith('/feedback.html')) {
      return [
        'Say: feedback is <your message>',
        'Say: submit feedback',
        ...common,
      ];
    }
    return common;
  }

  // UI helpers for tips and last-heard overlay
  function createTipsBanner() {
    const existing = on('#voice-tips');
    if (existing) existing.remove();
    const tips = tipsForPath(window.location.pathname);
    const wrap = document.createElement('div');
    wrap.id = 'voice-tips';
    wrap.setAttribute('aria-live', 'polite');
    wrap.style.cssText = `
      position: fixed;
      left: 20px;
      bottom: 90px;
      z-index: 9998;
      background: rgba(0,0,0,0.75);
      color: #fff;
      padding: 10px 12px;
      border-radius: 10px;
      max-width: 320px;
      font-size: 12px;
      line-height: 1.4;
      box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    `;
    const title = document.createElement('div');
    title.textContent = 'Voice tips:';
    title.style.cssText = 'font-weight: 700; margin-bottom: 6px;';
    const list = document.createElement('ul');
    list.style.cssText = 'margin: 0; padding-left: 18px;';
    tips.slice(0,5).forEach(t => {
      const li = document.createElement('li');
      li.textContent = t;
      list.appendChild(li);
    });
    wrap.appendChild(title);
    wrap.appendChild(list);
    document.body.appendChild(wrap);
  }

  function showHeard(text) {
    let box = on('#voice-heard');
    if (!box) {
      box = document.createElement('div');
      box.id = 'voice-heard';
      box.style.cssText = `
        position: fixed;
        right: 20px;
        bottom: 90px;
        z-index: 9998;
        background: rgba(255,255,255,0.95);
        color: #111;
        padding: 8px 10px;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        font-size: 12px;
        max-width: 50vw;
      `;
      document.body.appendChild(box);
    }
    box.textContent = `Heard: "${text}"`;
    clearTimeout(showHeard._t);
    showHeard._t = setTimeout(() => { try { box.remove(); } catch(_) {} }, 4000);
  }

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
    if (/(increase|faster) audio speed/.test(cmd)) {
      const audios = onAll('audio');
      if (audios.length) { audios.forEach(a => a.playbackRate = Math.min(2.0, (a.playbackRate || 1) + 0.2)); speak('Faster'); }
      else { speak('No audio found'); }
      return true;
    }
    if (/(decrease|slower) audio speed/.test(cmd)) {
      const audios = onAll('audio');
      if (audios.length) { audios.forEach(a => a.playbackRate = Math.max(0.5, (a.playbackRate || 1) - 0.2)); speak('Slower'); }
      else { speak('No audio found'); }
      return true;
    }
    if (/reset audio speed/.test(cmd)) {
      const audios = onAll('audio');
      if (audios.length) { audios.forEach(a => a.playbackRate = 1.0); speak('Normal speed'); }
      else { speak('No audio found'); }
      return true;
    }
    if (/mute audio/.test(cmd)) { const a = on('audio'); if (a) { a.muted = true; speak('Muted'); } else { speak('No audio found'); } return true; }
    if (/unmute audio/.test(cmd)) { const a = on('audio'); if (a) { a.muted = false; speak('Unmuted'); } else { speak('No audio found'); } return true; }
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
    const idEl = on('#identifier');
    const passEl = on('#password');
    const form = on('#login-form');
    if (/email (is|at) (.+)/.test(cmd) && idEl) {
      const m = cmd.match(/email (is|at) (.+)/);
      idEl.value = (m && m[2]) ? m[2].replace(/\s+at\s+/g,'@').replace(/\s+dot\s+/g,'.').replace(/\s/g,'') : idEl.value;
      speak('Email set'); return true;
    }
    if (/username (is|equals) (.+)/.test(cmd) && idEl) { idEl.value = cmd.match(/username (is|equals) (.+)/)[2]; speak('Username set'); return true; }
    if (/password (is|equals) (.+)/.test(cmd) && passEl) {
      const m = cmd.match(/password (is|equals) (.+)/);
      passEl.value = m && m[2] ? m[2] : passEl.value;
      speak('Password set'); return true;
    }
    if (/(log in|login|sign in|submit)/.test(cmd) && form) { form.dispatchEvent(new Event('submit', {cancelable:true, bubbles:true})); speak('Logging in'); return true; }
    return false;
  }

  function handleRegisterCommands(cmd) {
    const usernameEl = on('#username');
    const emailEl = on('#email');
    const passEl = on('#password');
    const form = on('#register-form');
    if (/username (is|equals) (.+)/.test(cmd) && usernameEl) { usernameEl.value = cmd.match(/username (is|equals) (.+)/)[2]; speak('Username set'); return true; }
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
    // Video controls
    if (/play video|play (the )?first video/.test(cmd)) {
      const v = on('video'); if (v) { v.play(); speak('Playing video'); } else { speak('No video found'); }
      return true;
    }
    if (/pause video/.test(cmd)) {
      const v = on('video'); if (v) { v.pause(); speak('Paused'); } else { speak('No video found'); }
      return true;
    }
    // Play nth video: "play second video" or "play video number 2"
    const nthMap = { first:1, second:2, third:3, fourth:4, fifth:5 };
    const videoMatch = cmd.match(/play (the )?(\w+) video|play video number (\d+)/);
    if (videoMatch) {
      let idx = null;
      if (videoMatch[2] && nthMap[videoMatch[2]]) idx = nthMap[videoMatch[2]] - 1;
      if (videoMatch[3]) idx = parseInt(videoMatch[3], 10) - 1;
      const videos = onAll('video');
      if (idx != null && videos[idx]) { videos[idx].play(); speak('Playing video'); return true; }
      speak('Video not found'); return true;
    }
    // Covered by common audio commands
    return false;
  }

  function handleProfileCommands(cmd) {
    const usernameEl = on('#username');
    const form = on('#profile-form');
    if (/username (is|equals) (.+)/.test(cmd) && usernameEl) { usernameEl.value = cmd.match(/username (is|equals) (.+)/)[2]; speak('Username set'); return true; }
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
    // Example: "set audio speed 1.3" or "set audio speed to 1.5"
    const audioSelect = on('#audio-speed-select');
    const m = cmd.match(/set audio speed(?: to)?\s+([0-9.]+)/);
    if (m && audioSelect) {
      const rate = m[1];
      for (const opt of audioSelect.options) {
        if (opt.value === rate) { audioSelect.value = rate; speak('Audio speed set to ' + rate + ' x'); return true; }
      }
      speak('Requested audio speed not available'); return true;
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

  let isListening = false;
  let recognitionActive = false;

  recognition.onresult = (e) => {
    const result = e.results[e.results.length - 1];
    if (result.isFinal) {
      const transcript = result[0].transcript.toLowerCase();
      console.log('Voice command detected:', transcript);
      showHeard(transcript);
      routeCommand(transcript);
    }
  };
  
  recognition.onerror = (e) => {
    console.error('Speech recognition error:', e.error);
    if (e.error === 'no-speech') {
      // Silently restart if no speech detected
      if (recognitionActive) {
        try { recognition.start(); } catch(_) {}
      }
    }
  };
  
  recognition.onend = () => { 
    if (recognitionActive) {
      try { recognition.start(); } catch(_) {} 
    }
  };

  function startListening() {
    if (!recognitionActive) {
      recognitionActive = true;
      try { 
        recognition.start(); 
        speak('Voice control activated. You can now speak commands.');
        console.log('Voice recognition started');
      } catch(e) {
        console.error('Failed to start recognition:', e);
      }
    }
  }

  function stopListening() {
    recognitionActive = false;
    try { 
      recognition.stop(); 
      speak('Voice control deactivated.');
      console.log('Voice recognition stopped');
    } catch(_) {}
  }

  // Activate voice commands when user clicks anywhere on the page
  document.addEventListener('DOMContentLoaded', () => {
    // Build contextual tips on load
    createTipsBanner();

    // Create a visible button for voice activation
    const voiceButton = document.createElement('button');
    voiceButton.id = 'voice-activation-button';
    voiceButton.innerHTML = '🎤 Click to Activate Voice Commands';
    voiceButton.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      z-index: 9999;
      padding: 12px 20px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border: none;
      border-radius: 25px;
      font-size: 14px;
      font-weight: bold;
      cursor: pointer;
      box-shadow: 0 4px 15px rgba(0,0,0,0.2);
      transition: all 0.3s ease;
    `;
    
    voiceButton.onmouseover = () => {
      voiceButton.style.transform = 'scale(1.05)';
      voiceButton.style.boxShadow = '0 6px 20px rgba(0,0,0,0.3)';
    };
    
    voiceButton.onmouseout = () => {
      voiceButton.style.transform = 'scale(1)';
      voiceButton.style.boxShadow = '0 4px 15px rgba(0,0,0,0.2)';
    };
    
    voiceButton.onclick = () => {
      if (!recognitionActive) {
        startListening();
        voiceButton.innerHTML = '🎤 Voice Active (Click to Stop)';
        voiceButton.style.background = 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)';
        // Speak one short tip on activation
        const tips = tipsForPath(window.location.pathname);
        if (tips && tips.length) speak(tips[0]);
      } else {
        stopListening();
        voiceButton.innerHTML = '🎤 Click to Activate Voice Commands';
        voiceButton.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
      }
    };
    
    document.body.appendChild(voiceButton);
    
    // Also activate on any click on the page
    document.body.addEventListener('click', (e) => {
      if (e.target.id !== 'voice-activation-button' && !recognitionActive) {
        startListening();
        voiceButton.innerHTML = '🎤 Voice Active (Click to Stop)';
        voiceButton.style.background = 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)';
        const tips = tipsForPath(window.location.pathname);
        if (tips && tips.length) speak(tips[0]);
      }
    }, { once: false });
  });
})();
