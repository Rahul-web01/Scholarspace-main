function toggleMenu() {
    const menu = document.getElementById('mobileMenu');
    menu.classList.toggle('show');
}
      // Back to Top Button
      const backToTop = document.querySelector('.back-to-top');
      window.addEventListener('scroll', () => {
        if (window.scrollY > 500) {
          backToTop.style.opacity = '1';
        } else {
          backToTop.style.opacity = '0';
        }
      });

      // stars ko interactive banane ke liye
document.querySelectorAll('.stars').forEach(starContainer => {
    const stars = starContainer.querySelectorAll('span');
    stars.forEach((star, index) => {
        star.addEventListener('click', () => {
            stars.forEach((s, i) => {
                s.style.color = i <= index ? '#ff9800' : '#ffd700';
            });
        });
    });
});