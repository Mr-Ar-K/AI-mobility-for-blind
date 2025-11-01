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

// Keyboard shortcuts removed per requirement: navigation via voice and UI only.

// Accessible mobile navbar toggle
document.addEventListener('DOMContentLoaded', () => {
	const toggle = document.querySelector('.navbar-toggle');
	const navLinks = document.getElementById('primary-navigation');
	if (!toggle || !navLinks) return;

	// Create backdrop overlay for mobile menu
	let backdrop = document.querySelector('.nav-backdrop');
	if (!backdrop) {
		backdrop = document.createElement('div');
		backdrop.className = 'nav-backdrop';
		document.body.appendChild(backdrop);
	}

	const closeMenu = () => {
		navLinks.classList.remove('is-open');
		toggle.setAttribute('aria-expanded', 'false');
			backdrop.classList.remove('is-visible');
	};

	const openMenu = () => {
		navLinks.classList.add('is-open');
		toggle.setAttribute('aria-expanded', 'true');
			backdrop.classList.add('is-visible');
		// Move focus to first link for accessibility
		const firstLink = navLinks.querySelector('.nav-link');
		if (firstLink) firstLink.focus({ preventScroll: true });
	};

	const toggleMenu = () => {
		const isOpen = navLinks.classList.contains('is-open');
		if (isOpen) closeMenu(); else openMenu();
	};

	toggle.addEventListener('click', (e) => {
		e.stopPropagation();
		toggleMenu();
	});

	// Close when clicking a link inside the menu
	navLinks.addEventListener('click', (e) => {
		const target = e.target;
		if (target && target.classList && target.classList.contains('nav-link')) {
			closeMenu();
		}
	});

	// Close on outside click
	document.addEventListener('click', (e) => {
		const isClickInside = navLinks.contains(e.target) || toggle.contains(e.target);
		if (!isClickInside) closeMenu();
	});

		// Close when clicking backdrop
		backdrop.addEventListener('click', closeMenu);

	// Close on Escape
	document.addEventListener('keydown', (e) => {
		if (e.key === 'Escape') closeMenu();
	});

	// Close when resizing to desktop
	let lastWidth = window.innerWidth;
	window.addEventListener('resize', () => {
		const now = window.innerWidth;
		if (lastWidth < 768 && now >= 768) {
			closeMenu();
		}
		lastWidth = now;
	});
});
