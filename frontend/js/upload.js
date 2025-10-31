document.addEventListener('DOMContentLoaded', () => {
	const uploadForm = document.getElementById('upload-form');
	const videoInput = document.getElementById('video-input');
	const uploadButton = document.getElementById('upload-button');
	const resultsContainer = document.getElementById('results-container');

	uploadForm.addEventListener('submit', async (e) => {
		e.preventDefault();

		const file = videoInput.files[0];
		if (!file) {
			resultsContainer.innerHTML = '<p class="error-text">Please select a video file first.</p>';
			return;
		}

		// Show loading state
		uploadButton.disabled = true;
		uploadButton.textContent = 'Processing Video...';
		resultsContainer.innerHTML = '<p>Uploading and analyzing your video. This may take a moment...</p>';

		try {
			// Call the uploadVideo function from api.js
			const data = await uploadVideo(file);

			// --- Success! Build the results HTML ---
			resultsContainer.innerHTML = ''; // Clear loading message

			// 1. Add the Detections List
			const detectionsTitle = document.createElement('h3');
			detectionsTitle.textContent = 'Detections Found:';
			resultsContainer.appendChild(detectionsTitle);
            
			const detectionList = document.createElement('ul');
			if (Object.keys(data.detections).length === 0) {
				detectionList.innerHTML = '<li>No objects detected.</li>';
			} else {
				for (const [object, count] of Object.entries(data.detections)) {
					const item = document.createElement('li');
					item.textContent = `${object}: ${count}`;
					detectionList.appendChild(item);
				}
			}
			resultsContainer.appendChild(detectionList);
            
			// 2. Add the Audio Player
			const audioTitle = document.createElement('h3');
			audioTitle.textContent = 'Audio Summary:';
			audioTitle.style.marginTop = '1.5rem';
			resultsContainer.appendChild(audioTitle);

			const audioPlayer = document.createElement('audio');
			audioPlayer.controls = true;
			// Prepend API_URL because the backend returns a relative path
			audioPlayer.src = `${API_URL}${data.audio_url}`; 
			resultsContainer.appendChild(audioPlayer);

		} catch (error) {
			resultsContainer.innerHTML = `<p class="error-text">An error occurred: ${error.message}</p>`;
		} finally {
			// Always re-enable the button
			uploadButton.disabled = false;
			uploadButton.textContent = 'Upload and Process Video';
		}
	});
});
