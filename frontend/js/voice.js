// Voice command controller using Web Speech API
// Provides navigation and page actions via voice.

(function() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const synth = window.speechSynthesis;

  // Apply theme from settings on every page early
  try {
    const s = JSON.parse(localStorage.getItem('app_settings')||'{}');
    if (s && s.theme) {
      document.documentElement.setAttribute('data-theme', s.theme);
    }
  } catch(_) {}

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

  // Non-verbal tones using Web Audio API
  function playTone(kind = 'ping') {
    try {
      const settings = JSON.parse(localStorage.getItem('app_settings')||'{}');
      if (settings && settings.enableTones === false) return; // disabled
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.connect(g); g.connect(ctx.destination);
      const now = ctx.currentTime;
      let freq = 880; let dur = 0.08;
      if (kind === 'success') { freq = 1047; dur = 0.12; }
      if (kind === 'confirm') { freq = 988; dur = 0.1; }
      if (kind === 'ping') { freq = 880; dur = 0.08; }
      o.type = 'sine'; o.frequency.setValueAtTime(freq, now);
      g.gain.setValueAtTime(0.0001, now);
      g.gain.exponentialRampToValueAtTime(0.08, now + 0.01);
      g.gain.exponentialRampToValueAtTime(0.0001, now + dur);
      o.start(now); o.stop(now + dur + 0.02);
    } catch(_) {}
  }
  window.playTone = playTone;

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
      bottom: 30px;
      z-index: 9998;
      background: rgba(0,0,0,0.7);
      color: #fff;
      padding: 8px 10px;
      border-radius: 10px;
      max-width: 300px;
      font-size: 11px;
      line-height: 1.4;
      box-shadow: 0 4px 15px rgba(0,0,0,0.2);
      opacity: 0.6;
      transition: opacity 0.3s ease;
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
    setTimeout(() => { try { wrap.style.display = 'none'; } catch(_) {} }, 12000);
  }
  function getAppSettingsLocal() {
    try {
      if (typeof window.getAppSettings === 'function') return window.getAppSettings();
      return JSON.parse(localStorage.getItem('app_settings') || '{}') || {};
    } catch(_) { return {}; }
  }

  function createCompactTips() {
    // Remove existing
    const existing = on('#voice-tips-icon');
    if (existing) existing.remove();

    const icon = document.createElement('button');
    icon.id = 'voice-tips-icon';
    icon.setAttribute('aria-label', 'Show voice tips');
    icon.style.cssText = `
      position: fixed;
      left: 20px;
      bottom: 30px;
      z-index: 9998;
      width: 36px; height: 36px;
      border-radius: 50%;
      border: none;
      background: rgba(0,0,0,0.7);
      color: #fff;
      cursor: pointer;
      box-shadow: 0 4px 15px rgba(0,0,0,0.2);
      display: flex; align-items: center; justify-content: center;
    `;
    icon.textContent = '❔';

    const pop = document.createElement('div');
    pop.id = 'voice-tips-popover';
    pop.style.cssText = `
      position: fixed;
      left: 66px;
      bottom: 30px;
      z-index: 9998;
      background: rgba(0,0,0,0.85);
      color: #fff;
      padding: 8px 10px;
      border-radius: 8px;
      max-width: 320px;
      font-size: 12px;
      line-height: 1.4;
      box-shadow: 0 4px 15px rgba(0,0,0,0.2);
      display: none;
    `;
    const title = document.createElement('div');
    title.textContent = 'Voice tips';
    title.style.cssText = 'font-weight:700; margin-bottom:6px;';
    const list = document.createElement('ul');
    list.style.cssText = 'margin:0; padding-left:18px;';
    const tips = tipsForPath(window.location.pathname);
    tips.slice(0,5).forEach(t => { const li = document.createElement('li'); li.textContent = t; list.appendChild(li); });
    pop.appendChild(title); pop.appendChild(list);

    let visible = false;
    function togglePopover() {
      visible = !visible;
      pop.style.display = visible ? 'block' : 'none';
    }
    icon.addEventListener('click', togglePopover);
    document.addEventListener('click', (e) => {
      if (visible && e.target !== icon && !pop.contains(e.target)) {
        visible = false; pop.style.display = 'none';
      }
    });

    document.body.appendChild(icon);
    document.body.appendChild(pop);
  }

  function initTipsUI() {
    const s = getAppSettingsLocal();
    const show = (s.showVoiceTips !== false); // default true
    const compact = (s.compactVoiceTips === true); // default false
    if (compact) {
      // Compact mode: show icon; only expand on click
      createCompactTips();
      // If show=true, we keep just the icon (still compact)
    } else if (show) {
      // Full banner
      createTipsBanner();
    }
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
    // Help command
    if (/help|what can i say|what commands/.test(cmd)) {
      const tips = tipsForPath(window.location.pathname);
      speak('Here are some commands you can use. ' + tips.slice(0, 3).join('. ') + '. Say help again for more options.');
      return true;
    }
    
    // Navigation with conversational responses
    if (/go (to )?home|open home/.test(cmd)) { speak('Taking you to the home page where you can access all features.'); go('home.html'); return true; }
    if (/go (to )?upload|open upload/.test(cmd)) { speak('Opening upload page. You can select and process a video file there.'); go('upload.html'); return true; }
    if (/go (to )?detection|open detection|go (to )?detections|open detections/.test(cmd)) { speak('Opening your detections history. You can review all your processed videos there.'); go('detections.html'); return true; }
    if (/go (to )?about|open about/.test(cmd)) { speak('Opening about page. Learn how this application works.'); go('about.html'); return true; }
    if (/go (to )?profile|open profile/.test(cmd)) { speak('Opening your profile and settings page. You can update your information and preferences there.'); go('profile.html'); return true; }
    if (/go (to )?settings|open settings/.test(cmd)) { speak('Opening settings. Settings are now in your profile page.'); go('profile.html'); return true; }
    if (/go (to )?feedback|open feedback/.test(cmd)) { speak('Opening feedback page. We would love to hear your thoughts.'); go('feedback.html'); return true; }
    if (/go (to )?login|open login/.test(cmd)) { speak('Opening login page'); go('login.html'); return true; }
    if (/go (to )?register|open register|sign up|create account/.test(cmd)) { speak('Opening registration page. Create a new account to get started.'); go('register.html'); return true; }
    
    // Logout with confirmation
    if (/logout|log out|sign out/.test(cmd)) { 
      speak('Logging you out. Have a great day!'); 
      setTimeout(() => { try { handleLogout(); } catch(_) {} }, 1000);
      return true; 
    }
    
    // Playback controls (generic) - with conversational feedback
    if (/play audio|play (the )?summary/.test(cmd)) {
      const a = on('audio'); 
      if (a) { 
        a.play(); 
        speak('Playing audio summary. Say pause audio to stop, or say faster or slower to adjust speed.'); 
      } else { 
        speak('Sorry, I could not find any audio on this page. Please process a video first to generate audio.'); 
      }
      return true;
    }
    if (/pause audio|stop audio|pause/.test(cmd)) {
      const a = on('audio'); 
      if (a) { 
        a.pause(); 
        speak('Audio paused. Say play audio to resume.'); 
      } else { 
        speak('No audio is currently playing.'); 
      }
      return true;
    }
    if (/(increase|faster|speed up) audio( speed)?/.test(cmd)) {
      const audios = onAll('audio');
      if (audios.length) { 
        audios.forEach(a => a.playbackRate = Math.min(2.0, (a.playbackRate || 1) + 0.2)); 
        const newRate = audios[0].playbackRate.toFixed(1);
        speak(`Audio speed increased to ${newRate} times. Say slower to decrease, or reset speed for normal.`); 
      }
      else { speak('No audio found on this page.'); }
      return true;
    }
    if (/(decrease|slower|slow down) audio( speed)?/.test(cmd)) {
      const audios = onAll('audio');
      if (audios.length) { 
        audios.forEach(a => a.playbackRate = Math.max(0.5, (a.playbackRate || 1) - 0.2)); 
        const newRate = audios[0].playbackRate.toFixed(1);
        speak(`Audio speed decreased to ${newRate} times. Say faster to increase.`); 
      }
      else { speak('No audio found on this page.'); }
      return true;
    }
    if (/reset audio speed|normal speed/.test(cmd)) {
      const audios = onAll('audio');
      if (audios.length) { 
        audios.forEach(a => a.playbackRate = 1.0); 
        speak('Audio speed reset to normal. Say faster or slower to adjust.'); 
      }
      else { speak('No audio found on this page.'); }
      return true;
    }
    if (/mute audio/.test(cmd)) { 
      const a = on('audio'); 
      if (a) { 
        a.muted = true; 
        speak('Audio muted. Say unmute audio to hear it again.'); 
      } else { 
        speak('No audio found.'); 
      } 
      return true; 
    }
    if (/unmute audio/.test(cmd)) { 
      const a = on('audio'); 
      if (a) { 
        a.muted = false; 
        speak('Audio unmuted. You should hear it now.'); 
      } else { 
        speak('No audio found.'); 
      } 
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
    const idEl = on('#identifier');
    const passEl = on('#password');
    const form = on('#login-form');
    if (/email (is|at) (.+)/.test(cmd) && idEl) {
      const m = cmd.match(/email (is|at) (.+)/);
      idEl.value = (m && m[2]) ? m[2].replace(/\s+at\s+/g,'@').replace(/\s+dot\s+/g,'.').replace(/\s/g,'') : idEl.value;
      speak('Email set. Now say: password is, followed by your password. Or say login to proceed.'); 
      return true;
    }
    if (/username (is|equals) (.+)/.test(cmd) && idEl) { 
      idEl.value = cmd.match(/username (is|equals) (.+)/)[2]; 
      speak('Username set. Now say: password is, followed by your password.'); 
      return true; 
    }
    if (/password (is|equals) (.+)/.test(cmd) && passEl) {
      const m = cmd.match(/password (is|equals) (.+)/);
      passEl.value = m && m[2] ? m[2] : passEl.value;
      speak('Password set. Say login to sign in, or say email is to change your email.'); 
      return true;
    }
    if (/(log in|login|sign in|submit)/.test(cmd) && form) { 
      form.dispatchEvent(new Event('submit', {cancelable:true, bubbles:true})); 
      speak('Logging you in. Please wait.'); 
      return true; 
    }
    return false;
  }

  function handleRegisterCommands(cmd) {
    const usernameEl = on('#username');
    const emailEl = on('#email');
    const passEl = on('#password');
    const form = on('#register-form');
    if (/username (is|equals) (.+)/.test(cmd) && usernameEl) { 
      usernameEl.value = cmd.match(/username (is|equals) (.+)/)[2]; 
      speak('Username set. Now say: email is, followed by your email address.'); 
      return true; 
    }
    if (/email (is|at) (.+)/.test(cmd) && emailEl) {
      const m = cmd.match(/email (is|at) (.+)/);
      emailEl.value = (m && m[2]) ? m[2].replace(/\s+at\s+/g,'@').replace(/\s+dot\s+/g,'.').replace(/\s/g,'') : emailEl.value;
      speak('Email set. Now say: password is, followed by your desired password.'); 
      return true;
    }
    if (/password (is|equals) (.+)/.test(cmd) && passEl) { 
      passEl.value = cmd.match(/password (is|equals) (.+)/)[2]; 
      speak('Password set. Say register or create account to complete your registration.'); 
      return true; 
    }
    if (/(create account|register|sign up|submit)/.test(cmd) && form) { 
      form.dispatchEvent(new Event('submit', {cancelable:true, bubbles:true})); 
      speak('Creating your account. Please wait a moment.'); 
      return true; 
    }
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
        const fileName = fileEl.files[0].name;
        form && form.dispatchEvent(new Event('submit', {cancelable:true, bubbles:true}));
        speak(`Uploading and processing ${fileName}. This may take a few minutes. I will keep you updated on the progress.`);
      } else {
        speak('I do not see any video file selected yet. Please use the file input to select a video, then say upload video again. For security reasons, I cannot select files using voice commands.');
      }
      return true;
    }
    if (/what (file|video)|which (file|video)|selected/.test(cmd)) {
      if (fileEl && fileEl.files && fileEl.files.length > 0) {
        const fileName = fileEl.files[0].name;
        speak(`You have selected ${fileName}. Say upload video to process it.`);
      } else {
        speak('No video file is currently selected. Please choose a file first.');
      }
      return true;
    }
    return false;
  }

  function handleDetectionsCommands(cmd) {
    // Count videos and audios
    if (/how many|count|list/.test(cmd)) {
      const videos = onAll('video');
      const audios = onAll('audio');
      speak(`You have ${videos.length} detection ${videos.length === 1 ? 'video' : 'videos'} and ${audios.length} audio ${audios.length === 1 ? 'summary' : 'summaries'}. Say play first video or play first audio to review them.`);
      return true;
    }
    
    // Video controls with conversational feedback
    if (/play video|play (the )?first video/.test(cmd)) {
      const v = on('video'); 
      if (v) { 
        v.play(); 
        speak('Playing your detection video. Say pause video to stop, or play audio to hear the summary.'); 
      } else { 
        speak('Sorry, I could not find any videos. You might not have any detections yet. Say go to upload to process a new video.'); 
      }
      return true;
    }
    if (/pause video|stop video/.test(cmd)) {
      const v = on('video'); 
      if (v) { 
        v.pause(); 
        speak('Video paused. Say play video to resume.'); 
      } else { 
        speak('No video is currently playing.'); 
      }
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
      if (idx != null && videos[idx]) { 
        videos[idx].play(); 
        const position = videoMatch[2] || `number ${videoMatch[3]}`;
        speak(`Playing ${position} video. Say pause video to stop.`); 
        return true; 
      }
      speak(`Sorry, I could not find that video. You have ${videos.length} ${videos.length === 1 ? 'video' : 'videos'} available.`); 
      return true;
    }
    // Covered by common audio commands
    return false;
  }

  function handleProfileCommands(cmd) {
    const usernameEl = on('#username');
    const form = on('#profile-form');
    const langSelect = on('#language-select');
    const speedSelect = on('#audio-speed-select');
    
    if (/username (is|equals) (.+)/.test(cmd) && usernameEl) { 
      const newName = cmd.match(/username (is|equals) (.+)/)[2];
      usernameEl.value = newName; 
      speak(`Username changed to ${newName}. Say save profile to keep this change, or continue editing your settings.`); 
      return true; 
    }
    if (/(update profile|save (profile|settings)|save all|submit)/.test(cmd) && form) { 
      form.dispatchEvent(new Event('submit', {cancelable:true, bubbles:true})); 
      speak('Saving your profile and settings. Please wait.'); 
      return true; 
    }
    if (/what (is )?my (settings|language|speed)/.test(cmd)) {
      const lang = langSelect ? langSelect.options[langSelect.selectedIndex].text : 'unknown';
      const speed = speedSelect ? speedSelect.value : 'unknown';
      speak(`Your current audio language is ${lang}, and audio speed is ${speed} times normal. Say save settings to keep changes, or say change language to update.`);
      return true;
    }
    return false;
  }

  function handleFeedbackCommands(cmd) {
    const textEl = on('#feedback-form #feedback-text');
    const form = on('#feedback-form');
    if (/feedback (is|equals) (.+)/.test(cmd) && textEl) { 
      const feedbackText = cmd.match(/feedback (is|equals) (.+)/)[2];
      textEl.value = feedbackText; 
      speak('Got it. Your feedback has been entered. Say submit feedback to send it to us, or continue speaking to add more.'); 
      return true; 
    }
    if (/(submit feedback|send feedback|submit)/.test(cmd) && form) { 
      form.dispatchEvent(new Event('submit', {cancelable:true, bubbles:true})); 
      speak('Thank you for your feedback! Submitting it now. Your input helps us improve.'); 
      return true; 
    }
    if (/clear feedback|delete feedback|start over/.test(cmd) && textEl) {
      textEl.value = '';
      speak('Feedback cleared. You can start over. Say feedback is, followed by your message.');
      return true;
    }
    return false;
  }

  function handleSettingsCommands(cmd) {
    // Example: "set language english"
    const select = on('#language-select');
    if (/set language (.+)/.test(cmd) && select) {
      const lang = cmd.match(/set language (.+)/)[1].trim();
      for (const opt of select.options) {
        if (opt.text.toLowerCase() === lang || opt.value.toLowerCase() === lang) {
          select.value = opt.value; 
          speak(`Language changed to ${opt.text}. This will affect your audio summaries. Say save settings to apply this change.`); 
          return true;
        }
      }
      speak('Sorry, I could not find that language. Available languages are English, Telugu, and Hindi. Please try again.'); 
      return true;
    }
    // Example: "set audio speed 1.3" or "set audio speed to 1.5"
    const audioSelect = on('#audio-speed-select');
    const m = cmd.match(/set audio speed(?: to)?\s+([0-9.]+)/);
    if (m && audioSelect) {
      const rate = m[1];
      for (const opt of audioSelect.options) {
        if (opt.value === rate) { 
          audioSelect.value = rate; 
          speak(`Audio speed set to ${rate} times normal. Say save settings to keep this change, or try a different speed.`); 
          return true; 
        }
      }
      speak(`Sorry, ${rate} is not available. Available speeds are 0.8, 1.0, 1.3, 1.5, 1.8, and 2.0. Please choose one of these.`); 
      return true;
    }
    const form = on('#settings-form') || on('#profile-form');
    if (/(save settings|save all|submit)/.test(cmd) && form) { 
      form.dispatchEvent(new Event('submit', {cancelable:true, bubbles:true})); 
      speak('Saving all your settings. Your preferences will be applied immediately.'); 
      return true; 
    }
    return false;
  }

  function routeCommand(cmd) {
    cmd = cmd.toLowerCase().trim();
    if (!cmd) return false;
    if (handleCommonCommands(cmd)) return true;

    const path = window.location.pathname;
    if (path.endsWith('/index.html') || path.endsWith('/') ) { if (handleIndexCommands(cmd)) return true; }
    if (path.endsWith('/login.html')) { if (handleLoginCommands(cmd)) return true; }
    if (path.endsWith('/register.html')) { if (handleRegisterCommands(cmd)) return true; }
    if (path.endsWith('/home.html')) { if (handleHomeCommands(cmd)) return true; }
    if (path.endsWith('/upload.html')) { if (handleUploadCommands(cmd)) return true; }
    if (path.endsWith('/detections.html')) { if (handleDetectionsCommands(cmd)) return true; }
    if (path.endsWith('/profile.html')) { if (handleProfileCommands(cmd)) return true; }
    if (path.endsWith('/feedback.html')) { if (handleFeedbackCommands(cmd)) return true; }
    if (path.endsWith('/settings.html')) { if (handleSettingsCommands(cmd)) return true; }
    
    return false; // Command not handled
  }

  let isListening = false;
  let recognitionActive = false;

  recognition.onresult = (e) => {
    const result = e.results[e.results.length - 1];
    if (result.isFinal) {
      const transcript = result[0].transcript.toLowerCase().trim();
      console.log('Voice command detected:', transcript);
      showHeard(transcript);
      
      // Filter out non-command phrases (voice tips content, general speech)
      if (isLikelyCommand(transcript)) {
        const handled = routeCommand(transcript);
        if (!handled) {
          speak('I did not understand that command. Could you please repeat? Or say help to hear what I can do for you.');
        }
      } else {
        console.log('Ignored non-command speech:', transcript);
        // Occasionally prompt the user if they seem to be talking but not giving commands
        if (Math.random() < 0.3) {
          speak('I am listening. Say help if you need to know what I can do.');
        }
      }
      
      try { resetInactivityTimer(); } catch(_) {}
    }
  };

  // Check if transcript looks like a command (starts with known keywords)
  function isLikelyCommand(text) {
    const commandKeywords = [
      'go', 'open', 'login', 'logout', 'register', 'sign',
      'play', 'pause', 'upload', 'submit', 'save', 'update',
      'email', 'username', 'password', 'feedback', 'language',
      'audio', 'speed', 'mute', 'unmute', 'faster', 'slower', 'reset',
      'first', 'second', 'third', 'fourth', 'fifth', 'video', 'detection'
    ];
    return commandKeywords.some(kw => text.includes(kw));
  }
  
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

  // Inactivity timeout: auto-stop listening after a period without final results
  let inactivityTimer = null;
  function resetInactivityTimer() {
    clearTimeout(inactivityTimer);
    inactivityTimer = setTimeout(() => {
      if (recognitionActive) {
        stopListening();
        speak('Voice control timed out. Click anywhere to reactivate.');
      }
    }, 90000);
  }

  function startListening() {
    if (!recognitionActive) {
      recognitionActive = true;
      try { 
        recognition.start(); 
        speak('Hello! I am listening. What would you like to do? Say help to hear available commands.');
        console.log('Voice recognition started');
      } catch(e) {
        console.error('Failed to start recognition:', e);
      }
      try { resetInactivityTimer(); } catch(_) {}
    }
  }

  function stopListening() {
    recognitionActive = false;
    try { 
      recognition.stop(); 
      speak('Voice control turned off. Click anywhere to talk to me again.');
      console.log('Voice recognition stopped');
    } catch(_) {}
    try { clearTimeout(inactivityTimer); } catch(_) {}
  }

  // Activate voice commands when user clicks anywhere on the page
  document.addEventListener('DOMContentLoaded', () => {
  // Inject global background overlay (marquee + brand mark)
  try {
    if (!document.querySelector('.bg-overlay')) {
      const overlay = document.createElement('div');
      overlay.className = 'bg-overlay';
      // Brand mark
      const mark = document.createElement('div');
      mark.className = 'bg-brand-mark';
      mark.textContent = 'AI Mobility Assist';
      overlay.appendChild(mark);
      // Running texts from config
      const messages = (window.APP_CONFIG && window.APP_CONFIG.marqueeMessages) ? window.APP_CONFIG.marqueeMessages : [
        'Voice-first',
        'Multi-language',
        'Accessibility-first',
      ];
      const makeMarquee = (pos) => {
        const row = document.createElement('div');
        row.className = 'bg-marquee ' + pos;
        const track = document.createElement('div');
        track.className = 'track';
        const track2 = document.createElement('div');
        track2.className = 'track';
        const fill = (t) => {
          for (let i = 0; i < 3; i++) {
            for (const m of messages) {
              const span = document.createElement('span');
              span.className = 'item';
              span.textContent = `• ${m}`;
              t.appendChild(span);
            }
          }
        };
        fill(track); fill(track2);
        row.appendChild(track); row.appendChild(track2);
        return row;
      };
      overlay.appendChild(makeMarquee('top'));
      overlay.appendChild(makeMarquee('bottom'));
      document.body.appendChild(overlay);
    }
  } catch(_) {}

  // Build contextual tips per settings
  initTipsUI();

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
        try { playTone('ping'); } catch(_) {}
        // Speak one short tip on activation
        const tips = tipsForPath(window.location.pathname);
        if (tips && tips.length) speak(tips[0]);
      } else {
        stopListening();
        voiceButton.innerHTML = '🎤 Click to Activate Voice Commands';
        voiceButton.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        try { playTone('confirm'); } catch(_) {}
      }
    };
    
    document.body.appendChild(voiceButton);
    
    // Also activate on any click on the page
    document.body.addEventListener('click', (e) => {
      if (e.target.id !== 'voice-activation-button' && !recognitionActive) {
        startListening();
        voiceButton.innerHTML = '🎤 Voice Active (Click to Stop)';
        voiceButton.style.background = 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)';
        try { playTone('ping'); } catch(_) {}
        const tips = tipsForPath(window.location.pathname);
        if (tips && tips.length) speak(tips[0]);
      }
    }, { once: false });
  });
})();
