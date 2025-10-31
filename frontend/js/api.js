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
 * Gets the stored user object from local storage.
 * @returns {object | null} The stored user or null.
 */
function getUser() {
	try { return JSON.parse(localStorage.getItem('user')); } catch { return null; }
}

/**
 * Handles user logout by clearing the token and redirecting to the login page.
 */
function handleLogout() {
	localStorage.removeItem('token');
	localStorage.removeItem('user');
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
	// Create new Headers object or use existing one
	const headers = new Headers(options.headers || {});

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
 * Logs in the user (backend: /users/login returns user object).
 * @param {string} emailOrUsername - Email or username (we map to username for backend).
 * @param {string} password - The user's password.
 * @returns {Promise<object>} The user object.
 */
async function login(emailOrUsername, password) {
	const payload = {
		username: emailOrUsername,
		password: password,
	};
	const response = await fetchWithFallback('/users/login', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(payload),
	});

	if (!response.ok) {
		const errorData = await response.json().catch(() => ({}));
		throw new Error(errorData.detail || 'Login failed. Please check credentials.');
	}
    
	const user = await response.json();
	// Persist user for subsequent calls
	localStorage.setItem('user', JSON.stringify(user));
	return user;
}

/**
 * Registers a new user.
 * @param {string} firstName - The user's first name (mapped to username).
 * @param {string} email - The user's email.
 * @param {string} password - The user's password.
 * @returns {Promise<object>} The new user object.
 */
async function register(firstName, email, password) {
	// Backend expects username, email, password at /users/signup
	return fetchWithFallback('/users/signup', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({
			username: firstName,
			email: email,
			password: password,
		}),
	}).then(r => r.json());
}

/**
 * Fetches the current user (from local storage or backend by id).
 * @returns {Promise<object>} The user object.
 */
async function getCurrentUser() {
	const user = getUser();
	if (!user) throw new Error('Not logged in');
	// Optionally refresh from backend
	const res = await fetchWithFallback(`/users/${user.id}`, { method: 'GET' });
	if (res.ok) {
		const fresh = await res.json();
		localStorage.setItem('user', JSON.stringify(fresh));
		return fresh;
	}
	return user;
}

/**
 * Updates the current user's profile.
 * @param {string} firstName - New first name (mapped to username).
 * @param {string} email - New email.
 * @returns {Promise<object>} Updated user.
 */
async function updateUser(firstName, email) {
	const user = getUser();
	if (!user) throw new Error('Not logged in');
	const res = await fetchWithFallback(`/users/${user.id}`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ username: firstName, email })
	});
	if (!res.ok) throw new Error((await res.json().catch(()=>({}))).detail || 'Update failed');
	const updated = await res.json();
	localStorage.setItem('user', JSON.stringify(updated));
	return updated;
}

/**
 * Uploads a video file for detection for current user.
 * @param {File} file - The video file to upload.
 * @returns {Promise<object>} The detection results including audio_url.
 */
async function uploadVideo(file) {
	const formData = new FormData();
	formData.append('file', file); // 'file' must match the name in your FastAPI endpoint
	const user = getUser();
	if (!user) throw new Error('Not logged in');
	const res = await fetchWithFallback(`/detect/${user.id}/with-audio`, {
		method: 'POST',
		body: formData,
	});
	if (!res.ok) throw new Error((await res.json().catch(()=>({}))).detail || 'Upload failed');
	return res.json();
}

/**
 * Fetches the current user's detection history.
 * @returns {Promise<Array<object>>} A list of detection history items.
 */
async function getHistory() {
	const user = getUser();
	if (!user) throw new Error('Not logged in');
	const res = await fetchWithFallback(`/history/${user.id}`, { method: 'GET' });
	if (!res.ok) throw new Error((await res.json().catch(()=>({}))).detail || 'Failed to fetch history');
	return res.json();
}
