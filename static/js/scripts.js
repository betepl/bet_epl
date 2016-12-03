function login() {
    var name = document.getElementById('login1').value;
    var pass = document.getElementById('password1').value;
    alert('Witaj ' + name);
}

function register() {
    var name = document.getElementById('login2').value;
    var mail = document.getElementById('email2').value;
    var pass = document.getElementById('password2').value;
    var repass = document.getElementById('repassword2').value;
    alert('Dziękujemy za rejestrację ' + name + '\nNa e-mail ' + mail + ' wysłany został link aktywacyjny.');
}

function change_pass() {
    var oldpass = document.getElementById('oldpassword').value;
    var newpass = document.getElementById('newpassword').value;
    var repass = document.getElementById('repassword').value;
    alert('Hasło zostało zmienione.');
}
