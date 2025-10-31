// Wait for the page's HTML to be fully loaded
document.addEventListener('DOMContentLoaded', () => {
	const loginForm = document.getElementById('login-form');
	const emailInput = document.getElementById('email');
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
			const email = emailInput.value;
			const password = passwordInput.value;

			// Call the login function from api.js (stores user in localStorage)
			await login(email, password);

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
