document.addEventListener('DOMContentLoaded', () => {
	const uploadForm = document.getElementById('upload-form');
	const videoInput = document.getElementById('video-input');
	const uploadButton = document.getElementById('upload-button');
	const resultsContainer = document.getElementById('results-container');
	const progressSection = document.getElementById('progress-section');
	const progressBar = document.getElementById('progress-bar');
	const progressPercent = document.getElementById('progress-percent');
	const progressStatus = document.getElementById('progress-status');
	const progressMessage = document.getElementById('progress-message');
	const progressTime = document.getElementById('progress-time');

	// Voice announcement function for accessibility
	function announceProgress(message) {
		if ('speechSynthesis' in window) {
			const utterance = new SpeechSynthesisUtterance(message);
			utterance.rate = 1.2;
			utterance.volume = 0.8;
			window.speechSynthesis.speak(utterance);
		}
	}

	uploadForm.addEventListener('submit', async (e) => {
		e.preventDefault();

		const file = videoInput.files[0];
		if (!file) {
			resultsContainer.innerHTML = '<p class="error-text">Please select a video file first.</p>';
			return;
		}

		// Show loading state and progress bar
		uploadButton.disabled = true;
		uploadButton.textContent = 'Processing Video...';
		resultsContainer.innerHTML = '';
		progressSection.style.display = 'block';
		progressBar.style.width = '0%';
		progressPercent.textContent = '0%';
		progressStatus.textContent = 'Uploading video...';
		progressMessage.textContent = 'Please wait while we process your video';
		progressTime.textContent = '';
		
		// Voice announcement
		announceProgress('Video upload started. Please wait.');
		
		const startTime = Date.now();

		try {
			// Start detection using task_id
			const startRes = await startDetection(file);
			const taskId = startRes.task_id;
			if (!taskId) throw new Error('No task id returned from server');

			let lastStatus = '';
			let poll = true;
			while (poll) {
				await new Promise(r => setTimeout(r, 600));
				const prog = await getProgress(taskId);
				// Update UI
				const pct = Math.max(0, Math.min(100, Math.floor(prog.progress || 0)));
				progressBar.style.width = pct + '%';
				progressPercent.textContent = pct + '%';
				progressStatus.textContent = (prog.status || 'processing').toUpperCase();
				progressMessage.textContent = prog.message || '';
				const elapsed = Math.floor((Date.now() - startTime) / 1000);
				progressTime.textContent = `${elapsed}s elapsed`;

				// Announce status changes
				if (prog.status && prog.status !== lastStatus) {
					if (prog.status === 'uploaded') announceProgress('Video uploaded');
					if (prog.status === 'processing') announceProgress('Detecting objects');
					if (prog.status === 'completed') announceProgress('Processing complete');
					lastStatus = prog.status;
				}

				if (prog.status === 'completed' || prog.status === 'failed') {
					poll = false;
				}
			}

			// Completed: fetch latest history and render media + results
			const hist = await getHistory();
			const latest = (hist && hist.length) ? hist[0] : null;
			const totalTime = Math.floor((Date.now() - startTime) / 1000);
			progressBar.style.width = '100%';
			progressPercent.textContent = '100%';
			progressStatus.textContent = 'PROCESSING COMPLETE!';
			progressTime.textContent = `Completed in ${totalTime}s`;
			progressMessage.textContent = 'Video processed successfully';
			announceProgress(`Processing complete in ${totalTime} seconds. Results are ready.`);
			setTimeout(() => { progressSection.style.display = 'none'; }, 5000);

			resultsContainer.innerHTML = '';
			// Results list (from latest history)
			const detectionsTitle = document.createElement('h3');
			detectionsTitle.textContent = 'Detections Found:';
			resultsContainer.appendChild(detectionsTitle);
			const detectionList = document.createElement('ul');
			const items = (latest && latest.results && Array.isArray(latest.results)) ? latest.results : [];
			if (!items.length) {
				detectionList.innerHTML = '<li>No objects detected.</li>';
			} else {
				for (const t of items) {
					const li = document.createElement('li');
					li.textContent = t;
					detectionList.appendChild(li);
				}
			}
			resultsContainer.appendChild(detectionList);

			// Video (playable)
			if (latest && latest.id && latest.video_path) {
				const videoTitle = document.createElement('h3');
				videoTitle.textContent = 'Detection Video:';
				videoTitle.style.marginTop = '1.5rem';
				resultsContainer.appendChild(videoTitle);
				const video = document.createElement('video');
				video.controls = true;
				video.playsInline = true;
				video.style.width = '100%';
				video.style.maxWidth = '720px';
				video.style.backgroundColor = '#000';
				video.src = `${API_URL}/history/video/${latest.id}`;
				resultsContainer.appendChild(video);
			}

			// Audio (faster playback or from settings)
			if (latest && latest.id && latest.audio_path) {
				const audioTitle = document.createElement('h3');
				audioTitle.textContent = 'Audio Summary:';
				audioTitle.style.marginTop = '1.5rem';
				resultsContainer.appendChild(audioTitle);
				const audio = document.createElement('audio');
				audio.controls = true;
				audio.src = `${API_URL}/history/audio/${latest.id}`;
				audio.playbackRate = (typeof getAudioRate === 'function') ? getAudioRate() : 1.3;
				resultsContainer.appendChild(audio);
			}

		} catch (error) {
			// Hide progress and show error
			progressSection.style.display = 'none';
			resultsContainer.innerHTML = `<p class="error-text">An error occurred: ${error.message}</p>`;
		} finally {
			// Always re-enable the button
			uploadButton.disabled = false;
			uploadButton.textContent = 'Upload and Process Video';
		}
	});
});
