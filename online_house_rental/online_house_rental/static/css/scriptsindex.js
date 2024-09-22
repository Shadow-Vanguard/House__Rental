document.addEventListener("DOMContentLoaded", () => {
    // Smooth scroll for navigation links
    const navLinks = document.querySelectorAll('nav ul li a');
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);

            window.scrollTo({
                top: targetSection.offsetTop - 50,
                behavior: 'smooth'
            });
        });
    });

    // Property details hover effect
    const propertyCards = document.querySelectorAll('.property-card');

    propertyCards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'scale(1.05)';
            card.style.transition = 'transform 0.3s ease';
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = 'scale(1)';
            card.style.transition = 'transform 0.3s ease';
        });
    });

    // Dynamic loading of properties (example)
    const propertiesGrid = document.querySelector('.properties-grid');
    const properties = [
        {
            img: 'property1.jpg',
            title: 'Modern Apartment',
            desc: '2 Bed, 2 Bath'
        },
        {
            img: 'property2.jpg',
            title: 'Cozy Cottage',
            desc: '3 Bed, 2 Bath'
        },
        {
            img: 'property3.jpg',
            title: 'Luxury Villa',
            desc: '4 Bed, 3 Bath'
        }
    ];

    properties.forEach(property => {
        const propertyCard = document.createElement('div');
        propertyCard.className = 'property-card';
        propertyCard.innerHTML = `
            <img src="${property.img}" alt="${property.title}">
            <h3>${property.title}</h3>
            <p>${property.desc}</p>
            <a href="#" class="btn">View Details</a>
        `;
        propertiesGrid.appendChild(propertyCard);
    });
});
