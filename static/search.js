document.getElementById("search-form").addEventListener('submit', async function (event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    // Collect the selected radius value
    const selectedRadius = document.querySelector('#radius-buttons input[name="radius"]:checked');;
    if (selectedRadius) {
        formData.append('radius', selectedRadius.value);

        // Clear the error message
        document.getElementById('error-message').innerText = '';

        // Remove the previous map if it exists
        const mapContainer = document.getElementById('map');
        if (mapContainer) {
            mapContainer.remove();
        }

        // Remove the previous results list
        const resultsContainer = document.getElementById('results-container');
        resultsContainer.innerHTML = '';

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();

            if (data.error) {
                document.getElementById('error-message').innerText = data.error;
            } else if (data.results) {
                const resultsContainer = document.getElementById('results-container');

                // Create the Leaflet map
                const newMapContainer = document.createElement('div');
                newMapContainer.id = 'map';
                newMapContainer.style.width = '100%';
                newMapContainer.style.height = '500px';
                resultsContainer.appendChild(newMapContainer);

                // Initialize the map
                const map = L.map('map').setView([51.61794, -0.017785], 14); // Set initial map view

                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                }).addTo(map);

                // Add markers to the map
                data.results.forEach(result => {
                    const marker = L.marker([result.geocodes.main.latitude, result.geocodes.main.longitude]).addTo(map);
                    marker.bindPopup(`<b>${result.name}</b><br>${result.location.formatted_address}`);
                });

            }
        } catch (error) {
            document.getElementById('error-message').innerText = 'An error occurred during the search.';
        }
    } else {
        // Display error message if no radius is selected
        document.getElementById('error-message').innerText = 'Please select a radius.';
    }
});
