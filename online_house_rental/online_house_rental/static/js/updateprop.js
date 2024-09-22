document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("update-property-form");

    form.addEventListener("submit", (event) => {
        event.preventDefault(); // Prevent the default form submission

        // You can add validation or additional actions here if needed

        // Simulate a successful submission (you can remove this when integrating with your backend)
        document.getElementById("message").innerText = "Property updated successfully!";
        form.reset(); // Clear the form fields after submission
    });
});
