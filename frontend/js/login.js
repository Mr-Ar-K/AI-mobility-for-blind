// Wait for the page's HTML to be fully loaded
document.addEventListener('DOMContentLoaded', () => {
	const loginForm = document.getElementById('login-form');
	const identifierInput = document.getElementById('identifier');
	const passwordInput = document.getElementById('password');
	const loginButton = document.getElementById('login-button');
	const errorMessage = document.getElementById('error-message');

	loginForm.addEventListener('submit', async (e) => {
		e.preventDefault(); // Stop the form from submitting the old way

		// Show a loading state
		loginButton.disabled = true;
		loginButton.textContent = 'Logging in...';
		errorMessage.textContent = ''; // Clear old errors

		try {
			const identifier = identifierInput.value; // username or email
			const password = passwordInput.value;

			// Call the login function from api.js (stores user in localStorage)
			await login(identifier, password);

			// Redirect to the home page
			window.location.href = 'home.html';

		} catch (error) {
			errorMessage.textContent = error.message;
		} finally {
			// Always re-enable the button
			loginButton.disabled = false;
			loginButton.textContent = 'Login';
		}
	});
});
