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

	try {
		// Fetch user data to populate navbar
	const user = await getCurrentUser(); // returns backend user
        
	const firstName = user.username || 'User';
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

	// --- 2. Home Page Specific Logic ---
	// This code only runs if it finds the ".home-grid"
	if (document.querySelector('.home-grid')) {
		document.getElementById('upload-card').addEventListener('click', () => {
			window.location.href = 'upload.html';
		});
		document.getElementById('detections-card').addEventListener('click', () => {
			window.location.href = 'detections.html';
		});
		document.getElementById('about-card').addEventListener('click', () => {
			window.location.href = 'about.html';
		});
		document.getElementById('feedback-card').addEventListener('click', () => {
			window.location.href = 'feedback.html';
		});
	}
});
