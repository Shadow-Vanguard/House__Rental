document.getElementById('forgotPasswordForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const email = document.getElementById('email').value;

    // Simulating sending reset link (you would normally handle this with Django backend)
    alert(`A password reset link has been sent to ${email}`);

    // Redirect to a confirmation page or show a success message
    window.location.href = "{% url 'index' %}"; // Redirect to home after sending
});
