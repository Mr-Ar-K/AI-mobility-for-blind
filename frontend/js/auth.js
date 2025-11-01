/**
 * This is an IIFE (Immediately Invoked Function Expression).
 * It runs immediately when the script is loaded.
 * It checks if a token exists in local storage.
 * If not, it redirects the user to the login page.
 */
(function() {
	// Pages that do NOT require authentication
	const publicPages = ['/index.html', '/login.html', '/register.html'];
	const currentPage = window.location.pathname;

	const hasToken = !!localStorage.getItem('token');
	const hasUser = !!localStorage.getItem('user');
	const isPublic = publicPages.includes(currentPage);

	if (!(hasToken || hasUser) && !isPublic) {
		console.log('No session found, redirecting to login.');
		window.location.href = 'login.html';
	} else if ((hasToken || hasUser) && (currentPage === '/login.html' || currentPage === '/register.html')) {
		console.log('Session found, redirecting to home.');
		window.location.href = 'home.html';
	}
})();

// Global keyboard shortcuts for accessibility
document.addEventListener('keydown', (e) => {
	// Only trigger shortcuts with Alt key (to avoid conflicts with browser/form shortcuts)
	if (!e.altKey) return;

	const key = e.key.toLowerCase();
	
	// Alt+H - Home
	if (key === 'h') {
		e.preventDefault();
		window.location.href = 'home.html';
		return;
	}
	
	// Alt+U - Upload
	if (key === 'u') {
		e.preventDefault();
		window.location.href = 'upload.html';
		return;
	}
	
	// Alt+D - Detections
	if (key === 'd') {
		e.preventDefault();
		window.location.href = 'detections.html';
		return;
	}
	
	// Alt+P - Profile
	if (key === 'p') {
		e.preventDefault();
		window.location.href = 'profile.html';
		return;
	}
	
	// Alt+A - About
	if (key === 'a') {
		e.preventDefault();
		window.location.href = 'about.html';
		return;
	}
	
	// Alt+F - Feedback
	if (key === 'f') {
		e.preventDefault();
		window.location.href = 'feedback.html';
		return;
	}
	
	// Alt+L - Logout
	if (key === 'l') {
		e.preventDefault();
		if (typeof handleLogout === 'function') {
			handleLogout();
		}
		return;
	}
});
