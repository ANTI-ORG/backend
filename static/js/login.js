function submitForm(event) {
    event.preventDefault(); // Предотвращаем стандартную отправку формы

    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/auth/admin/token', true);
    xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');

    var form = event.target;
    var formData = new FormData(form);
    var data = {
        username: formData.get('username'),
        password: formData.get('password'),
        seed: formData.get('seed'),
    };

    xhr.onreadystatechange = function() {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
                var response = JSON.parse(xhr.responseText);
                document.cookie = `access_token=${response.access_token}; HttpOnly`;
                window.location.href = '/admin'; // Перенаправляем на /admin после успешного входа
            } else {
                alert('Login failed: ' + xhr.responseText);
            }
        }
    };

    xhr.send(JSON.stringify(data));
}

// Добавляем обработчик события для формы после загрузки скрипта
document.addEventListener('DOMContentLoaded', function() {
    var form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', submitForm);
    }
});
