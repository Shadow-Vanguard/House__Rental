document.getElementById("updateProfileForm").addEventListener("submit", function (event) {
    var password = document.getElementById("password").value;
    var confirmPassword = document.getElementById("confirm_password").value;

    // Clear previous error messages
    var errorMessages = document.querySelectorAll(".error-message");
    errorMessages.forEach(function (msg) {
        msg.remove();
    });

    // Password validation
    if (password !== confirmPassword) {
        event.preventDefault();
        var errorMessage = document.createElement("p");
        errorMessage.className = "error-message";
        errorMessage.textContent = "Passwords do not match!";
        document.querySelector(".form-group:last-child").appendChild(errorMessage);
    }
});
