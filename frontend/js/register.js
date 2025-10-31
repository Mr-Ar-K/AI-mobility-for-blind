document.addEventListener('DOMContentLoaded', () => {
	const registerForm = document.getElementById('register-form');
	const firstNameInput = document.getElementById('first-name');
	const emailInput = document.getElementById('email');
	const passwordInput = document.getElementById('password');
	const registerButton = document.getElementById('register-button');
	const errorMessage = document.getElementById('error-message');

	registerForm.addEventListener('submit', async (e) => {
		e.preventDefault();

		// Show loading state
		registerButton.disabled = true;
		registerButton.textContent = 'Creating Account...';
		errorMessage.textContent = '';

		try {
			const firstName = firstNameInput.value;
			const email = emailInput.value;
			const password = passwordInput.value;

			// Call the register function from api.js
			await register(firstName, email, password);

			// On success, tell the user and redirect to login
			errorMessage.textContent = 'Account created successfully! Redirecting to login...';
			errorMessage.style.color = 'green'; // Use success color

			setTimeout(() => {
				window.location.href = 'login.html';
			}, 2000);

		} catch (error) {
			errorMessage.textContent = error.message;
			// Re-enable button on failure
			registerButton.disabled = false;
			registerButton.textContent = 'Create Account';
		}
	});
});
