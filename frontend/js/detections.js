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
			card.className = 'detection-item stat-card-modern'; // Use modern stat card style

				// Icon at top to match stat-card style
				const icon = document.createElement('div');
				icon.className = 'stat-icon-large';
				icon.setAttribute('aria-hidden', 'true');
				if (item.video_path) icon.textContent = '🎬';
				else if (item.image_path) icon.textContent = '🖼️';
				else icon.textContent = '🔎';
				card.appendChild(icon);

			// Title (Date)
				const title = document.createElement('h3');
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
				videoPlayer.preload = 'metadata'; // fast first preview
				const videoUrl = `${API_URL}/history/video/${item.id}`;
				console.log('Video URL:', videoUrl);
				// Use a <source> with explicit MIME type for better compatibility
				const source = document.createElement('source');
				source.src = videoUrl;
				source.type = 'video/mp4';
				videoPlayer.appendChild(source);
				
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
					
					// Show user-friendly error with theme-aware style
					const errorMsg = document.createElement('p');
					errorMsg.className = 'error-text';
					errorMsg.textContent = `⚠️ Could not load video (Error ${videoPlayer.error?.code || 'unknown'})`;
					videoContainer.appendChild(errorMsg);
					// Fallback: show download link so user can open in native player
					const dl = document.createElement('a');
					dl.href = videoUrl;
					dl.textContent = 'Download video';
					dl.style.display = 'inline-block';
					dl.style.marginTop = '8px';
					videoContainer.appendChild(dl);
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
			detectionsText.className = 'objects-found';
			detectionsText.textContent = `Objects found: ${objects}`;
			card.appendChild(detectionsText);

			// Audio Player
			if (item.audio_path) {
				const audioContainer = document.createElement('div');
				audioContainer.style.marginTop = '1rem';
				
				const audioLabel = document.createElement('p');
				audioLabel.style.fontWeight = 'bold';
				audioLabel.style.marginBottom = '0.5rem';
				audioLabel.textContent = '🔊 Audio Summary:';
				audioContainer.appendChild(audioLabel);

				const audioPlayer = document.createElement('audio');
				audioPlayer.controls = true;
				audioPlayer.style.width = '100%';
				audioPlayer.style.marginBottom = '0.5rem';
				// Backend serves audio at /history/audio/{id}
				audioPlayer.src = `${API_URL}/history/audio/${item.id}`;
				audioPlayer.playbackRate = 1.0; // Default to normal speed
				
				// Add loading/error handling
				audioPlayer.onerror = function(e) {
					console.error('Audio load error:', e);
					console.error('Failed to load audio:', audioPlayer.src);
					const errorMsg = document.createElement('p');
					errorMsg.className = 'error-text';
					errorMsg.textContent = '⚠️ Could not load audio file';
					audioContainer.appendChild(errorMsg);
				};
				
				audioContainer.appendChild(audioPlayer);
				
				// Playback speed controls
				const speedContainer = document.createElement('div');
				speedContainer.style.display = 'flex';
				speedContainer.style.gap = '0.5rem';
				speedContainer.style.alignItems = 'center';
				speedContainer.style.marginTop = '0.5rem';
				
				const speedLabel = document.createElement('span');
				speedLabel.textContent = 'Speed:';
				speedLabel.style.fontSize = '0.9rem';
				speedContainer.appendChild(speedLabel);
				
				const speeds = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0];
				speeds.forEach(speed => {
					const btn = document.createElement('button');
					btn.textContent = speed === 1.0 ? 'Normal' : `${speed}x`;
					btn.className = speed === 1.0 ? 'btn btn-primary btn-sm' : 'btn btn-secondary btn-sm';
					btn.style.padding = '0.25rem 0.75rem';
					btn.style.fontSize = '0.85rem';
					btn.onclick = () => {
						audioPlayer.playbackRate = speed;
						// Update button styles
						speedContainer.querySelectorAll('button').forEach(b => {
							b.className = 'btn btn-secondary btn-sm';
						});
						btn.className = 'btn btn-primary btn-sm';
						announce(`Playback speed set to ${speed === 1.0 ? 'normal' : speed + 'x'}`);
					};
					speedContainer.appendChild(btn);
				});
				
				audioContainer.appendChild(speedContainer);
				card.appendChild(audioContainer);
			}

			// Add the new card to the grid
			listContainer.appendChild(card);
		});

	} catch (error) {
		listContainer.innerHTML = `<p class="error-text">Failed to load history: ${error.message}</p>`;
	}
});
