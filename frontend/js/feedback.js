// Feedback page specific logic
document.addEventListener('DOMContentLoaded', () => {
	// Voice announcement function
	function announce(message) {
		if ('speechSynthesis' in window) {
			const utterance = new SpeechSynthesisUtterance(message);
			utterance.rate = 1.2;
			utterance.volume = 0.8;
			window.speechSynthesis.speak(utterance);
		}
	}

	// Announce page load
	announce('Welcome to the feedback page! I would love to hear your thoughts. You can say feedback is, followed by your message. For example, say feedback is, the app is very helpful. Then say submit feedback to send it to us. Your feedback helps us improve!');

	const form = document.getElementById('feedback-form');
	const feedbackText = document.getElementById('feedback-text');
	const messageDiv = document.getElementById('message-text');

	if (form) {
		form.addEventListener('submit', async (e) => {
			e.preventDefault();

			const feedback = feedbackText.value.trim();
			if (!feedback) {
				messageDiv.textContent = 'Please enter your feedback.';
				messageDiv.className = 'error-text';
				announce('I notice the feedback field is empty. Please say feedback is, followed by your message, or type it in the text area.');
				return;
			}

			try {
				announce('Thank you! I am submitting your feedback now. Please wait a moment.');
				messageDiv.textContent = 'Submitting...';
				messageDiv.className = 'info-text';

				// Here you would typically send the feedback to the backend
				// For now, simulate success
				await new Promise(resolve => setTimeout(resolve, 1000));

				messageDiv.textContent = 'Thank you for your feedback!';
				messageDiv.className = 'success-text';
				announce('Wonderful! Your feedback has been submitted successfully. We really appreciate you taking the time to share your thoughts with us. Your input helps us improve the application for everyone. Would you like to go back home? Just say go to home.');
				
				// Clear form
				feedbackText.value = '';

			} catch (error) {
				console.error('Error submitting feedback:', error);
				messageDiv.textContent = 'Failed to submit feedback. Please try again.';
				messageDiv.className = 'error-text';
				announce(`I am sorry, but I could not submit your feedback. The error is: ${error.message}. Please try again in a moment.`);
			}
		});
	}
});
