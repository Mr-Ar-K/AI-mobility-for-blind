document.addEventListener('DOMContentLoaded', async () => {
	const profileForm = document.getElementById('profile-form');
	const usernameInput = document.getElementById('username');
	const emailInput = document.getElementById('email');
	const updateButton = document.getElementById('update-profile-button');
	const messageText = document.getElementById('message-text');

	// Announce page purpose for accessibility
	if ('speechSynthesis' in window) {
		const utterance = new SpeechSynthesisUtterance('Welcome to your profile and settings! Here you can update your username, change the audio language for summaries, adjust audio playback speed, and manage voice tips. Say what is my settings to hear your current configuration, or say username is, followed by your new name to update it. When you are done, say save all changes to keep your updates.');
		utterance.rate = 1.2;
		window.speechSynthesis.speak(utterance);
	}

	// 1. Load current user data into the form
	try {
		const user = await getCurrentUser(); // from api.js
		if (usernameInput) usernameInput.value = user.username;
		if (emailInput) emailInput.value = user.email;
	} catch (error) {
		messageText.textContent = `Failed to load profile: ${error.message}`;
		messageText.className = 'error-text';
		if ('speechSynthesis' in window) {
			window.speechSynthesis.speak(new SpeechSynthesisUtterance(`I am sorry, I could not load your profile. The error is: ${error.message}. Please try refreshing the page.`));
		}
	}

	// 2. Add listener for the form submission (handles both profile + settings)
	profileForm.addEventListener('submit', async (e) => {
		e.preventDefault();

		// Show loading state
		updateButton.disabled = true;
		updateButton.textContent = 'Saving...';
		messageText.textContent = '';

		if ('speechSynthesis' in window) {
			window.speechSynthesis.speak(new SpeechSynthesisUtterance('Saving your changes.'));
		}

		try {
			const newUsername = usernameInput ? usernameInput.value : '';
			const newEmail = emailInput ? emailInput.value : '';

			// Update profile
			const updatedUser = await updateUser(newUsername, newEmail); // from api.js

			// Save settings (handled by settings.js, trigger its form submit programmatically or inline here)
			const settingsForm = document.getElementById('settings-form');
			if (settingsForm) {
				// Manually save settings
				const langSelect = document.getElementById('language-select');
				const audioSelect = document.getElementById('audio-speed-select');
				const showTipsEl = document.getElementById('show-voice-tips');
				const compactTipsEl = document.getElementById('compact-voice-tips');
				const language = langSelect ? langSelect.value : 'en';
				const audioRate = audioSelect ? parseFloat(audioSelect.value) : 1.3;
				const showVoiceTips = showTipsEl ? !!showTipsEl.checked : true;
				const compactVoiceTips = compactTipsEl ? !!compactTipsEl.checked : false;
				if (typeof setAppSettings === 'function') {
					setAppSettings({ language, audioRate, showVoiceTips, compactVoiceTips });
				}
			}

			// Success!
			messageText.textContent = 'Profile and settings updated successfully!';
			messageText.style.color = 'green';

			if ('speechSynthesis' in window) {
				window.speechSynthesis.speak(new SpeechSynthesisUtterance('Perfect! Your profile and settings have been saved successfully. All your changes are now active. Is there anything else you would like to update?'));
			}
            
			// Also update the initials in the navbar
			const userInitialsSpan = document.getElementById('user-initials');
			if (userInitialsSpan) {
				userInitialsSpan.textContent = (updatedUser.username || '').charAt(0).toUpperCase();
			}

		} catch (error) {
			messageText.textContent = `Update failed: ${error.message}`;
			messageText.className = 'error-text';
			if ('speechSynthesis' in window) {
				window.speechSynthesis.speak(new SpeechSynthesisUtterance(`I am sorry, but the update failed. The error is: ${error.message}. Please check your information and try again.`));
			}
		} finally {
			// Always re-enable button
			updateButton.disabled = false;
			updateButton.textContent = 'Save All Changes';
		}
	});
});
