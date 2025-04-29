
    document.querySelectorAll('.status-form').forEach(form => {
        form.addEventListener('change', function(event) {
            event.preventDefault();
            let url = this.action;
            let formData = new FormData(this);

            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Status updated to: ' + data.new_status);
                } else {
                    alert('Error: ' + data.error);
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });