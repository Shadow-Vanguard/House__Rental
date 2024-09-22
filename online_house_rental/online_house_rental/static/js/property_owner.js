// Simple script to manage owner actions or add interactivity
document.addEventListener('DOMContentLoaded', function () {
    // Example: Highlighting the current section
    const navLinks = document.querySelectorAll('nav ul li a');
    navLinks.forEach(link => {
        link.addEventListener('click', function () {
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
        });
    });
});
