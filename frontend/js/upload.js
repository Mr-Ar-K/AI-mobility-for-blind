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
	const startDemoBtn = document.getElementById('start-demo');
	const demoWrap = document.getElementById('live-demo-video-wrapper');
	// Live Detection (Static Demo)
	if (startDemoBtn && demoWrap) {
		startDemoBtn.addEventListener('click', () => {
			// If we had a sample video URL, we would set it here; keep static placeholder.
			try { if (window.playTone) window.playTone('ping'); } catch(_) {}
			const hint = document.createElement('div');
			hint.style.color = '#ccc';
			hint.style.fontSize = '0.9rem';
			hint.style.padding = '12px';
			hint.textContent = 'This is a static demo placeholder for live detection. Real-time processing can be integrated with a streaming endpoint.';
			demoWrap.innerHTML = '';
			demoWrap.appendChild(hint);
		});
	}

	// Voice announcement function for accessibility
	function announceProgress(message) {
		if ('speechSynthesis' in window) {
			const utterance = new SpeechSynthesisUtterance(message);
			utterance.rate = 1.2;
			utterance.volume = 0.8;
			window.speechSynthesis.speak(utterance);
		}
	}

	// Announce page load for blind users
	announceProgress('Welcome to the upload page! To get started, please select a video file using the file input. Once selected, you can say upload video, and I will process it for you. This usually takes a few minutes depending on the video length.');

	uploadForm.addEventListener('submit', async (e) => {
		e.preventDefault();

		const file = videoInput.files[0];
		if (!file) {
			resultsContainer.innerHTML = '<p class="error-text">Please select a video file first.</p>';
			announceProgress('Oops! I do not see any video file selected. Please use the file input to choose a video, then try again.');
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

				// Announce status changes with conversational feedback
				if (prog.status && prog.status !== lastStatus) {
					if (prog.status === 'uploaded') announceProgress('Great! Your video has been uploaded successfully. Now analyzing the video to detect objects.');
					if (prog.status === 'processing') announceProgress('I am now detecting objects in your video. This may take a few minutes. Please be patient.');
					if (prog.status === 'completed') announceProgress('Excellent! Processing is complete. Your results are ready.');
					try { if (window.playTone) window.playTone('ping'); } catch(_) {}
					lastStatus = prog.status;
				}
				
				// Announce milestone percentages
				if (pct >= 25 && pct < 50 && !window._announced25) {
					announceProgress('Progress: 25 percent complete. Still working on it.');
					window._announced25 = true;
				} else if (pct >= 50 && pct < 75 && !window._announced50) {
					announceProgress('Progress: 50 percent complete. Halfway there!');
					window._announced50 = true;
				} else if (pct >= 75 && pct < 100 && !window._announced75) {
					announceProgress('Progress: 75 percent complete. Almost done!');
					window._announced75 = true;
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
			announceProgress(`Fantastic! Processing completed in ${totalTime} seconds. Your detection video and audio summary are now available below. You can say play video to watch it, or say play audio to hear the summary. You can also say go to detections to view all your saved results.`);
			try { if (window.playTone) window.playTone('success'); } catch(_) {}
			setTimeout(() => { progressSection.style.display = 'none'; }, 5000);
			// Reset announcement flags for next upload
			window._announced25 = false;
			window._announced50 = false;
			window._announced75 = false;

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
			announceProgress(`I am sorry, but something went wrong. The error message is: ${error.message}. Please try again, or contact support if the problem persists.`);
		} finally {
			// Always re-enable the button
			uploadButton.disabled = false;
			uploadButton.textContent = 'Upload and Process Video';
		}
	});
});
