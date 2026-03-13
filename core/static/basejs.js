 const navLinks = document.querySelectorAll('.NavLoggedIn .nav-link');

 navLinks.forEach(link => {
   link.addEventListener('click', (e) => {
     e.preventDefault();
     navLinks.forEach(l => l.classList.remove('active'));
     link.classList.add('active');
     window.location.href = link.href;
   });
  });

  