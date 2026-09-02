function previewImage(event) {
    var file = event.target.files[0];
    if (file) {
        var reader = new FileReader();
        reader.onload = function (e) {
            document.getElementById('imagePreview').src = e.target.result;
            document.getElementById('previewContainer').style.display = 'block';
        }
        reader.readAsDataURL(file);
    }
}

function clearImage() {
    document.getElementById('imageInput').value = '';
    document.getElementById('previewContainer').style.display = 'none';
    document.getElementById('imagePreview').src = '';
}

document.addEventListener('DOMContentLoaded', function () {
    var uploadArea = document.getElementById('uploadArea');

    if (uploadArea) {
        uploadArea.addEventListener('dragover', function (e) {
            e.preventDefault();
            this.style.borderColor = '#00b894';
            this.style.backgroundColor = 'rgba(0, 184, 148, 0.05)';
        });

        uploadArea.addEventListener('dragleave', function (e) {
            e.preventDefault();
            this.style.borderColor = 'rgba(255,255,255,0.2)';
            this.style.backgroundColor = 'rgba(255, 255, 255, 0.03)';
        });

        uploadArea.addEventListener('drop', function (e) {
            e.preventDefault();
            this.style.borderColor = 'rgba(255,255,255,0.2)';
            this.style.backgroundColor = 'rgba(255, 255, 255, 0.03)';

            var files = e.dataTransfer.files;
            if (files.length > 0) {
                var fileInput = document.getElementById('imageInput');
                fileInput.files = files;
                fileInput.dispatchEvent(new Event('change'));
            }
        });
    }
});

setTimeout(function () {
    var alerts = document.querySelectorAll('.alert');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(function () {
                if (alert.parentNode) {
                    alert.style.display = 'none';
                }
            }, 500);
        }, 5000);
    });
}, 1000);

function checkModelStatus() {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        fetch('/status')
            .then(function (response) {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(function (data) {
                var badge = document.querySelector('.badge');
                var btn = document.getElementById('colorizeBtn');

                if (data.model_loaded) {
                    if (badge) {
                        badge.className = 'badge badge-success';
                        badge.innerHTML = '<span class="icon"></span> Model Ready';
                    }
                    if (btn) {
                        btn.disabled = false;
                        btn.innerHTML = '<span class="icon"></span> Colorize Image';
                    }
                } else {
                    if (badge) {
                        badge.className = 'badge badge-danger';
                        badge.innerHTML = '<span class="icon"></span> No Model';
                    }
                    if (btn) {
                        btn.disabled = true;
                        btn.innerHTML = '<span class="icon"></span> No Model';
                    }
                }
            })
            .catch(function (error) {
                console.log('Status check not available');
            });
    }
}

if (document.querySelector('.badge')) {
    setTimeout(checkModelStatus, 1000);
    setInterval(checkModelStatus, 30000);
}