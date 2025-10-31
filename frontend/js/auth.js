/**
 * This is an IIFE (Immediately Invoked Function Expression).
 * It runs immediately when the script is loaded.
 * It checks if a token exists in local storage.
 * If not, it redirects the user to the login page.
 */
(function() {
	// Pages that do NOT require authentication
	const publicPages = ['/index.html', '/login.html', '/register.html'];
    
	const token = localStorage.getItem('token');
	const currentPage = window.location.pathname;

	if (!token && !publicPages.includes(currentPage)) {
		// User is not logged in and is trying to access a protected page
		console.log('No token found, redirecting to login.');
		window.location.href = 'login.html';
	} else if (token && (currentPage === '/login.html' || currentPage === '/register.html')) {
		// User is logged in but is trying to access login/register page
		console.log('Token found, redirecting to home.');
		window.location.href = 'home.html';
	}
})();
