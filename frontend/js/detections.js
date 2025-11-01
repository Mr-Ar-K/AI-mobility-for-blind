document.addEventListener('DOMContentLoaded', async () => {
	const listContainer = document.getElementById('detections-list');
	listContainer.innerHTML = '<p>Loading detection history...</p>';

	// Voice announcement function
	function announce(message) {
		if ('speechSynthesis' in window) {
			const utterance = new SpeechSynthesisUtterance(message);
			utterance.rate = 1.2;
			utterance.volume = 0.8;
			window.speechSynthesis.speak(utterance);
		}
	}

	try {
		const history = await getHistory(); // from api.js

		if (!history || history.length === 0) {
			listContainer.innerHTML = '<p>You have no saved detections.</p>';
			announce('Welcome to your detections history! You do not have any saved detections yet. Would you like to upload a video? Just say go to upload, and I will take you there to process your first video.');
			return;
		}

		// Clear loading message
		listContainer.innerHTML = '';
		
		// Announce page load with count
		announce(`Welcome to your detections history! You have ${history.length} saved ${history.length === 1 ? 'detection' : 'detections'}. You can say play first video to watch the detection video, or say play first audio to hear the summary. You can also say how many to get a count, or say go to upload to process a new video.`);

		// Debug: log what we received
		console.log('Detection history:', history);

		// Loop through history and create a card for each item
		history.forEach(item => {
			console.log('Processing item:', item);
			const card = document.createElement('div');
			card.className = 'detection-item card-link'; // Reuse our card style

			// Title (Date)
			const title = document.createElement('h2');
			const itemDate = new Date(item.timestamp);
			title.textContent = `Detection from ${itemDate.toLocaleString()}`;
			card.appendChild(title);

			// Video Player (if video exists)
			if (item.video_path) {
				console.log('Adding video player for:', item.video_path);
				
				const videoContainer = document.createElement('div');
				videoContainer.style.marginBottom = '1rem';
				
				const videoLabel = document.createElement('p');
				videoLabel.style.fontWeight = 'bold';
				videoLabel.style.marginBottom = '0.5rem';
				videoLabel.textContent = '🎬 Detection Video:';
				videoContainer.appendChild(videoLabel);
				
				const videoPlayer = document.createElement('video');
				videoPlayer.controls = true;
				videoPlayer.style.width = '100%';
				videoPlayer.style.maxWidth = '640px';
				videoPlayer.style.borderRadius = '8px';
				videoPlayer.style.backgroundColor = '#000';
				const videoUrl = `${API_URL}/history/video/${item.id}`;
				console.log('Video URL:', videoUrl);
				// Backend serves video at /history/video/{id}
				videoPlayer.src = videoUrl;
				videoPlayer.preload = 'metadata';
				
				// Add loading/error feedback
				videoPlayer.onloadstart = function() {
					console.log('Video loading started:', videoUrl);
				};
				videoPlayer.onloadedmetadata = function() {
					console.log('Video metadata loaded successfully');
				};
				videoPlayer.onerror = function(e) {
					console.error('Video load error:', e);
					console.error('Failed to load:', videoUrl);
					console.error('Error code:', videoPlayer.error?.code);
					console.error('Error message:', videoPlayer.error?.message);
					
					// Show user-friendly error
					const errorMsg = document.createElement('p');
					errorMsg.style.color = 'red';
					errorMsg.textContent = `⚠️ Could not load video (Error ${videoPlayer.error?.code || 'unknown'})`;
					videoContainer.appendChild(errorMsg);
				};
				
				videoContainer.appendChild(videoPlayer);
				card.appendChild(videoContainer);
			} else {
				console.log('No video_path for this item');
			}

			// Image Player (if image exists and no video)
			if (item.image_path && !item.video_path) {
				const imagePlayer = document.createElement('img');
				imagePlayer.style.width = '100%';
				imagePlayer.style.maxWidth = '640px';
				imagePlayer.style.marginBottom = '1rem';
				imagePlayer.style.borderRadius = '8px';
				imagePlayer.alt = 'Detection image';
				// Backend serves image at /history/image/{id}
				imagePlayer.src = `${API_URL}/history/image/${item.id}`;
				card.appendChild(imagePlayer);
			}

			// Detections Text
			const objects = (item.results && item.results.length) ? item.results.join(', ') : 'No objects detected';
			const detectionsText = document.createElement('p');
			detectionsText.textContent = `Objects found: ${objects}`;
			card.appendChild(detectionsText);

			// Audio Player
			if (item.audio_path) {
				const audioLabel = document.createElement('p');
				audioLabel.style.fontWeight = 'bold';
				audioLabel.style.marginTop = '0.5rem';
				audioLabel.textContent = 'Audio Summary:';
				card.appendChild(audioLabel);

				const audioPlayer = document.createElement('audio');
				audioPlayer.controls = true;
				audioPlayer.style.width = '100%';
				// Backend serves audio at /history/audio/{id}
				audioPlayer.src = `${API_URL}/history/audio/${item.id}`;
				audioPlayer.playbackRate = (typeof getAudioRate === 'function') ? getAudioRate() : 1.3;
				card.appendChild(audioPlayer);
			}

			// Add the new card to the grid
			listContainer.appendChild(card);
		});

	} catch (error) {
		listContainer.innerHTML = `<p class="error-text">Failed to load history: ${error.message}</p>`;
	}
});
