document.getElementById('searchForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const location = document.getElementById('location').value;
    const priceRange = document.getElementById('price-range').value;
    const propertyType = document.getElementById('property-type').value;

    // Simulate a property search result
    const properties = [
        { id: 1, name: 'Luxury Villa', location: 'New York', price: '$1500', type: 'villa' },
        { id: 2, name: 'Cozy Apartment', location: 'San Francisco', price: '$1200', type: 'apartment' },
        { id: 3, name: 'Spacious House', location: 'Los Angeles', price: '$1000', type: 'house' }
    ];

    const filteredProperties = properties.filter(property => {
        return property.location.includes(location) && 
               property.price.includes(priceRange) &&
               property.type === propertyType;
    });

    const propertiesContainer = document.getElementById('properties');
    propertiesContainer.innerHTML = '';

    if (filteredProperties.length > 0) {
        filteredProperties.forEach(property => {
            const propertyDiv = document.createElement('div');
            propertyDiv.innerHTML = `
                <h3>${property.name}</h3>
                <p>Location: ${property.location}</p>
                <p>Price: ${property.price}</p>
                <p>Type: ${property.type}</p>
            `;
            propertiesContainer.appendChild(propertyDiv);
        });
    } else {
        propertiesContainer.innerHTML = '<p>No properties found.</p>';
    }
});
