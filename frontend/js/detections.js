document.addEventListener('DOMContentLoaded', async () => {
	const listContainer = document.getElementById('detections-list');
	listContainer.innerHTML = '<p>Loading detection history...</p>';

	try {
		const history = await getHistory(); // from api.js

		if (!history || history.length === 0) {
			listContainer.innerHTML = '<p>You have no saved detections.</p>';
			return;
		}

		// Clear loading message
		listContainer.innerHTML = '';

		// Loop through history and create a card for each item
		history.forEach(item => {
			const card = document.createElement('div');
			card.className = 'detection-item card-link'; // Reuse our card style

			// Title (Date)
			const title = document.createElement('h2');
			const itemDate = new Date(item.timestamp);
			title.textContent = `Detection from ${itemDate.toLocaleString()}`;
			card.appendChild(title);

			// Detections Text
			const objects = (item.results && item.results.length) ? item.results.join(', ') : 'No objects detected';
			const detectionsText = document.createElement('p');
			detectionsText.textContent = `Objects found: ${objects}`;
			card.appendChild(detectionsText);

			// Audio Player
			const audioPlayer = document.createElement('audio');
			audioPlayer.controls = true;
			// Backend serves audio at /history/audio/{id}
			audioPlayer.src = `${API_URL}/history/audio/${item.id}`;
			card.appendChild(audioPlayer);

			// Add the new card to the grid
			listContainer.appendChild(card);
		});

	} catch (error) {
		listContainer.innerHTML = `<p class="error-text">Failed to load history: ${error.message}</p>`;
	}
});
