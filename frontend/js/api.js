// Backend base URLs with automatic fallback.
// Primary: DevTunnels (HTTPS). Fallbacks: localhost variants.
const API_BASES = [
	"https://cjcf4dl2-8000.inc1.devtunnels.ms",
	"http://127.0.0.1:8000",
	"http://0.0.0.0:8000" // note: many browsers cannot reach 0.0.0.0; kept per request
];

// Current base URL used by the API client; updated on successful call.
let API_URL = API_BASES[0];

/**
 * Resolve the first reachable API base by attempting the provided request.
 * Falls back through API_BASES on network errors. On success, updates API_URL.
 * @param {RequestInfo} path - endpoint path like '/users/me'
 * @param {RequestInit} options - fetch options
 * @returns {Promise<Response>} response
 */
async function fetchWithFallback(path, options) {
	let lastError = null;
	// try current API_URL first, then others
	const tried = new Set();
	const candidates = [API_URL, ...API_BASES.filter(b => b !== API_URL)];

	for (const base of candidates) {
		tried.add(base);
		try {
			const res = await fetch(`${base}${path}`, options);
			// If we get any HTTP response, consider the base reachable
			API_URL = base;
			return res;
		} catch (e) {
			lastError = e;
			// network error -> try next base
			continue;
		}
	}
	// If all failed due to network errors
	if (lastError) throw lastError;
	throw new Error('All API bases failed');
}

/**
 * Gets the authentication token from browser's local storage.
 * @returns {string | null} The stored token, or null if not found.
 */
function getToken() {
	return localStorage.getItem('token');
}

/**
 * Handles user logout by clearing the token and redirecting to the login page.
 */
function handleLogout() {
	localStorage.removeItem('token');
	window.location.href = 'login.html';
}

/**
 * A general-purpose function for making authenticated API calls.
 * It automatically adds the 'Authorization' header.
 * @param {string} endpoint - The API endpoint (e.g., '/users/me').
 * @param {object} options - The standard 'fetch' options object.
 * @returns {Promise<any>} - The JSON response from the server.
 */
async function fetchWithAuth(endpoint, options = {}) {
	const token = getToken();

	// Create new Headers object or use existing one
	const headers = new Headers(options.headers || {});
    
	// Add the Authorization header
	if (token) {
		headers.append('Authorization', `Bearer ${token}`);
	}

	// Don't set Content-Type for FormData; browser does it automatically
	// with the correct boundary.
	if (!(options.body instanceof FormData)) {
		if (!headers.has('Content-Type')) {
			headers.append('Content-Type', 'application/json');
		}
	}
    
	options.headers = headers;

	try {
		const response = await fetchWithFallback(endpoint, options);

		// If the token is bad (e.g., expired), log the user out.
		if (response.status === 401) {
			console.error('Authentication failed. Logging out.');
			handleLogout();
			throw new Error('Unauthorized');
		}

		if (!response.ok) {
			// Try to get error details from the server's JSON response
			const errorData = await response.json().catch(() => ({}));
			const errorMessage = errorData.detail || `HTTP error! status: ${response.status}`;
			throw new Error(errorMessage);
		}
        
		// Handle responses that might not have a JSON body (like a 204 No Content)
		if (response.status === 204) {
			return null;
		}

	return response.json();

	} catch (error) {
		console.error('API call failed:', error.message);
		throw error; // Re-throw the error to be caught by the calling function
	}
}

/**
 * Logs in the user.
 * @param {string} email - The user's email.
 * @param {string} password - The user's password.
 * @returns {Promise<object>} The response data, including the access_token.
 */
async function login(email, password) {
	// Your FastAPI /token endpoint expects "x-www-form-urlencoded" data
	const formData = new URLSearchParams();
	formData.append('username', email);
	formData.append('password', password);

	const response = await fetch(`${API_URL}/token`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/x-www-form-urlencoded',
		},
		body: formData,
	});

	if (!response.ok) {
		const errorData = await response.json().catch(() => ({}));
		throw new Error(errorData.detail || 'Login failed. Please check credentials.');
	}
    
	return response.json();
}

/**
 * Registers a new user.
 * @param {string} firstName - The user's first name.
 * @param {string} email - The user's email.
 * @param {string} password - The user's password.
 * @returns {Promise<object>} The new user object.
 */
async function register(firstName, email, password) {
	// Your /users/ endpoint expects JSON
	return fetchWithAuth('/users/', {
		method: 'POST',
		body: JSON.stringify({
			first_name: firstName,
			email: email,
			password: password,
		}),
	});
}

/**
 * Fetches the currently logged-in user's details.
 * @returns {Promise<object>} The user object.
 */
async function getCurrentUser() {
	return fetchWithAuth('/users/me', {
		method: 'GET',
	});
}

/**
 * Updates the currently logged-in user's profile.
 * @param {string} firstName - The new first name.
 * @param {string} email - The new email.
 * @returns {Promise<object>} The updated user object.
 */
async function updateUser(firstName, email) {
	return fetchWithAuth('/users/me', {
		method: 'PUT',
		body: JSON.stringify({
			first_name: firstName,
			email: email,
		}),
	});
}

/**
 * Uploads a video file for detection.
 * @param {File} file - The video file to upload.
 * @returns {Promise<object>} The detection results.
 */
async function uploadVideo(file) {
	const formData = new FormData();
	formData.append('file', file); // 'file' must match the name in your FastAPI endpoint

	// fetchWithAuth will handle the token and headers
	return fetchWithAuth('/detection/', {
		method: 'POST',
		body: formData,
		// Do NOT set Content-Type header here
	});
}

/**
 * Fetches the user's detection history.
 * @returns {Promise<Array<object>>} A list of detection history items.
 */
async function getHistory() {
	return fetchWithAuth('/history/', {
		method: 'GET',
	});
}
