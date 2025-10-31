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
