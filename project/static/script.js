document.getElementById('loginForm').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent default form submission

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const isAdmin = document.getElementById('isAdmin').checked;
    const errorMessage = document.getElementById('errorMessage');

    // Basic client-side validation (replace with actual authentication)
    if (username === '' || password === '') {
        errorMessage.textContent = 'Please enter both username and password.';
        return;
    }

    // Simulate login for demonstration
    if (isAdmin) {
        if (username === 'admin' && password === 'adminpass') {
            errorMessage.textContent = '';
            alert('Admin login successful!');
            // Redirect to admin dashboard or perform admin actions
        } else {
            errorMessage.textContent = 'Invalid admin credentials.';
        }
    } else {
        if (username === 'user' && password === 'userpass') {
            errorMessage.textContent = '';
            alert('User login successful!');
            // Redirect to user dashboard or perform user actions
        } else {
            errorMessage.textContent = 'Invalid user credentials.';
        }
    }
});