document.querySelectorAll('.settings-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.settings-btn, .settings-section').forEach(el => {
            el.classList.remove('active');
        });
        btn.classList.add('active');
        const sectionId = btn.getAttribute('data-section');
        document.getElementById(sectionId).classList.add('active');
    });
});


setTimeout(function() {
    const messages = document.getElementById("messages");
    if (messages) {
        messages.style.display = 'none';
    }
}, 5000);