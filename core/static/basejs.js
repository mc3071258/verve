// CSRF token for AJAX requests 
function getCookie(name) {
    let value = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return value ? value.pop() : '';
}

// Active nav link highlighting
const navLinks = document.querySelectorAll('.NavLoggedIn .nav-link');
navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        navLinks.forEach(l => l.classList.remove('active'));
        link.classList.add('active');
        window.location.href = link.href;
    });
});

// AJAX vote toggle
document.querySelectorAll('.vote-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const url = this.dataset.url;
        const button = this;

        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(response => response.json())
        .then(data => {
            button.querySelector('.vote-count').textContent = data.vote_count;
            if (data.voted) {
                button.classList.add('voted');
            } else {
                button.classList.remove('voted');
            }
        });
    });
});

// AJAX follow toggle
document.querySelectorAll('.follow-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const button = this;
        const url = button.dataset.url;

        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(response => response.json())
        .then(data => {
            button.dataset.url = data.next_url;
            button.dataset.following = data.following ? 'true' : 'false';
            button.textContent = data.following ? 'Unfollow' : 'Follow';

            button.classList.remove('btn-primary', 'btn-outline-danger');
            if (data.following) {
                button.classList.add('btn-outline-danger');
            } else {
                button.classList.add('btn-primary');
            }

            const followerCount = document.getElementById('follower-count');
            if (followerCount) {
                followerCount.textContent = data.follower_count;
            }
        });
    });
});