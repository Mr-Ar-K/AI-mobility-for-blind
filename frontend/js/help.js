// Accessibility Help - Keyboard Shortcuts Guide
(function() {
	// Create help button
	const helpBtn = document.createElement('button');
	helpBtn.id = 'keyboard-help-btn';
	helpBtn.textContent = '?';
	helpBtn.title = 'Keyboard shortcuts help (Alt+?)';
	helpBtn.setAttribute('aria-label', 'Show keyboard shortcuts help');
	helpBtn.style.cssText = `
		position: fixed;
		bottom: 20px;
		right: 20px;
		z-index: 9999;
		width: 50px;
		height: 50px;
		border-radius: 50%;
		background: #2196F3;
		color: white;
		border: none;
		font-size: 24px;
		font-weight: bold;
		cursor: pointer;
		box-shadow: 0 4px 12px rgba(0,0,0,0.3);
		transition: transform 0.2s, background 0.2s;
	`;
	helpBtn.addEventListener('mouseenter', () => {
		helpBtn.style.transform = 'scale(1.1)';
		helpBtn.style.background = '#1976D2';
	});
	helpBtn.addEventListener('mouseleave', () => {
		helpBtn.style.transform = 'scale(1)';
		helpBtn.style.background = '#2196F3';
	});

	// Create help modal
	const modal = document.createElement('div');
	modal.id = 'keyboard-help-modal';
	modal.setAttribute('role', 'dialog');
	modal.setAttribute('aria-labelledby', 'help-title');
	modal.setAttribute('aria-modal', 'true');
	modal.style.cssText = `
		display: none;
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: rgba(0,0,0,0.7);
		z-index: 10000;
		justify-content: center;
		align-items: center;
	`;

	const modalContent = document.createElement('div');
	modalContent.style.cssText = `
		background: white;
		padding: 30px;
		border-radius: 12px;
		max-width: 600px;
		max-height: 80vh;
		overflow-y: auto;
		box-shadow: 0 8px 24px rgba(0,0,0,0.4);
	`;

	modalContent.innerHTML = `
		<h2 id="help-title" style="margin-top: 0; color: #2196F3;">Accessibility Features & Keyboard Shortcuts</h2>
		
		<section style="margin-bottom: 20px;">
			<h3 style="color: #333; margin-bottom: 10px;">🎤 Voice Commands</h3>
			<p style="color: #666; margin-bottom: 10px;">Click anywhere on the page to activate voice commands. Say:</p>
			<ul style="color: #666; line-height: 1.8;">
				<li><strong>"Go to upload"</strong> - Navigate to upload page</li>
				<li><strong>"Go to detections"</strong> - View detection history</li>
				<li><strong>"Go to profile"</strong> - Open profile & settings</li>
				<li><strong>"Play audio"</strong> - Play audio summary</li>
				<li><strong>"Pause audio"</strong> - Pause audio playback</li>
				<li><strong>"Upload video"</strong> - Submit selected video</li>
				<li><strong>"Logout"</strong> - Sign out of your account</li>
			</ul>
		</section>

		<section style="margin-bottom: 20px;">
			<h3 style="color: #333; margin-bottom: 10px;">⌨️ Keyboard Shortcuts</h3>
			<p style="color: #666; margin-bottom: 10px;">Use Alt + key to navigate quickly:</p>
			<ul style="color: #666; line-height: 1.8;">
				<li><strong>Alt + H</strong> - Go to Home</li>
				<li><strong>Alt + U</strong> - Go to Upload</li>
				<li><strong>Alt + D</strong> - Go to Detections</li>
				<li><strong>Alt + P</strong> - Go to Profile & Settings</li>
				<li><strong>Alt + A</strong> - Go to About</li>
				<li><strong>Alt + F</strong> - Go to Feedback</li>
				<li><strong>Alt + L</strong> - Logout</li>
				<li><strong>Alt + ?</strong> - Show this help (any page)</li>
			</ul>
		</section>

		<section style="margin-bottom: 20px;">
			<h3 style="color: #333; margin-bottom: 10px;">🌐 Language Support</h3>
			<p style="color: #666;">Audio summaries available in English, Telugu, and Hindi. Change language in Profile & Settings.</p>
		</section>

		<section>
			<h3 style="color: #333; margin-bottom: 10px;">♿ Screen Reader Support</h3>
			<p style="color: #666;">All pages include ARIA labels and live regions for optimal screen reader experience.</p>
		</section>

		<button id="close-help-btn" style="
			margin-top: 20px;
			padding: 12px 24px;
			background: #2196F3;
			color: white;
			border: none;
			border-radius: 6px;
			font-size: 16px;
			cursor: pointer;
			width: 100%;
		" aria-label="Close help dialog">Close</button>
	`;

	modal.appendChild(modalContent);

	// Add to document
	document.body.appendChild(helpBtn);
	document.body.appendChild(modal);

	// Show modal
	function showModal() {
		modal.style.display = 'flex';
		document.getElementById('close-help-btn').focus();
		if ('speechSynthesis' in window) {
			const utterance = new SpeechSynthesisUtterance('Accessibility help opened. Press Escape or say close to dismiss.');
			utterance.rate = 1.2;
			window.speechSynthesis.speak(utterance);
		}
	}

	// Hide modal
	function hideModal() {
		modal.style.display = 'none';
		helpBtn.focus();
	}

	// Event listeners
	helpBtn.addEventListener('click', showModal);
	document.getElementById('close-help-btn').addEventListener('click', hideModal);
	
	// Close on background click
	modal.addEventListener('click', (e) => {
		if (e.target === modal) hideModal();
	});

	// Keyboard shortcuts
	document.addEventListener('keydown', (e) => {
		// Alt + ? to show help
		if (e.altKey && e.key === '?') {
			e.preventDefault();
			showModal();
		}
		// Escape to close modal
		if (e.key === 'Escape' && modal.style.display === 'flex') {
			hideModal();
		}
	});

})();
