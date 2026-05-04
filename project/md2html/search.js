function highlightCurrentPage() {
  const path = location.pathname.split('/').pop();
  const links = document.querySelectorAll('#nav a');
  links.forEach(a => {
    if (a.getAttribute('href').endsWith(path)) {
      a.classList.add('current-page');
    }
  });
}

function setupSearch() {
  const box = document.getElementById('searchBox');
  box.addEventListener('input', () => {
    const q = box.value.toLowerCase();
    const links = document.querySelectorAll('#nav a');
    links.forEach(a => {
      const text = a.textContent.toLowerCase();
      a.style.display = text.includes(q) ? '' : 'none';
    });
  });
}
