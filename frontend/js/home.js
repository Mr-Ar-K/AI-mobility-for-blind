// This function runs on every page that includes it
document.addEventListener('DOMContentLoaded', async () => {
    
	// --- 1. Navbar Logic (Runs on all pages) ---
	const logoutButton = document.getElementById('logout-button');
	const userInitialsSpan = document.getElementById('user-initials');
	const userNameSpan = document.getElementById('user-name'); // This only exists on home.html

	if (logoutButton) {
		logoutButton.addEventListener('click', () => {
			handleLogout(); // This function is from api.js
		});
	}

	let firstName = 'User';
	try {
		// Fetch user data to populate navbar
	const user = await getCurrentUser(); // returns backend user
        
	firstName = user.username || 'User';
		const initials = firstName.charAt(0).toUpperCase();

		if (userInitialsSpan) {
			userInitialsSpan.textContent = initials;
		}
        
		// Only home.html has the #user-name span
		if (userNameSpan) {
			userNameSpan.textContent = firstName + '!';
		}

	} catch (error) {
		console.error('Failed to get user info:', error);
		// auth.js will handle the redirect if the token is invalid
	}

	// Mark active nav link on all pages
	try {
		const cur = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
		document.querySelectorAll('.nav-link').forEach(a => {
			const isActive = (a.getAttribute('href') || '').toLowerCase().endsWith(cur);
			if (isActive) { a.classList.add('active'); a.setAttribute('aria-current','page'); }
			else { a.classList.remove('active'); a.removeAttribute('aria-current'); }
		});
	} catch(_) {}

	// --- 2. Home Page Specific Logic ---
	const isHome = (location.pathname.split('/').pop() || '').toLowerCase() === 'home.html';
	if (isHome && 'speechSynthesis' in window) {
		const utterance = new SpeechSynthesisUtterance(`Welcome home, ${firstName}! You can say go to upload to process a new video, or say go to detections to review your history. You can also say go to profile to change your settings.`);
		utterance.rate = 1.2;
		utterance.volume = 0.8;
		window.speechSynthesis.speak(utterance);
	}
});
