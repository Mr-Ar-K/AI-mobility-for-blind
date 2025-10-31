document.addEventListener('DOMContentLoaded', async () => {
	const profileForm = document.getElementById('profile-form');
	const firstNameInput = document.getElementById('first-name');
	const emailInput = document.getElementById('email');
	const updateButton = document.getElementById('update-profile-button');
	const messageText = document.getElementById('message-text');

	// 1. Load current user data into the form
	try {
		const user = await getCurrentUser(); // from api.js
		firstNameInput.value = user.first_name;
		emailInput.value = user.email;
	} catch (error) {
		messageText.textContent = `Failed to load profile: ${error.message}`;
		messageText.className = 'error-text';
	}

	// 2. Add listener for the form submission
	profileForm.addEventListener('submit', async (e) => {
		e.preventDefault();

		// Show loading state
		updateButton.disabled = true;
		updateButton.textContent = 'Updating...';
		messageText.textContent = '';

		try {
			const newFirstName = firstNameInput.value;
			const newEmail = emailInput.value; // Your backend allows this, but it's disabled in HTML

			const updatedUser = await updateUser(newFirstName, newEmail); // from api.js

			// Success!
			messageText.textContent = 'Profile updated successfully!';
			messageText.style.color = 'green';
            
			// Also update the initials in the navbar
			const userInitialsSpan = document.getElementById('user-initials');
			if (userInitialsSpan) {
				userInitialsSpan.textContent = updatedUser.first_name.charAt(0).toUpperCase();
			}

		} catch (error) {
			messageText.textContent = `Update failed: ${error.message}`;
			messageText.className = 'error-text';
		} finally {
			// Always re-enable button
			updateButton.disabled = false;
			updateButton.textContent = 'Update Profile';
		}
	});
});
