document.getElementById('loginForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const email = document.getElementById('email').value;
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    // Basic validation (this can be expanded)
    if (email === '' || username === '' || password === '') {
        alert('Please fill out all fields.');
    } else {
        // Perform login action (e.g., AJAX request, form submission)
        alert('Login successful!');
    }
});
