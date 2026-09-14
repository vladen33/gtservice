
document.addEventListener('DOMContentLoaded', () => {
  const toggleBtn = document.getElementById('filter-toggle-btn');
  const filterPanel = document.querySelector('.filter-panel');
  const arrow = toggleBtn.querySelector('.toggle-arrow');
  const text = toggleBtn.querySelector('.toggle-text');

  // Если есть GET-параметры — сразу открываем
  const hasFilters = new URLSearchParams(window.location.search).toString().length > 0;
  if (hasFilters) {
    filterPanel.classList.add('open');
    arrow.textContent = '▼';
    text.textContent = 'Скрыть фильтры';
  } else {
    // По умолчанию закрыт
    filterPanel.classList.remove('open');
    arrow.textContent = '▶';
    text.textContent = 'Фильтры';
  }

  toggleBtn.addEventListener('click', () => {
    const isOpen = filterPanel.classList.contains('open');

    if (isOpen) {
      // Закрываем
      filterPanel.classList.remove('open');
      arrow.textContent = '▶';
      text.textContent = 'Фильтры';
    } else {
      // Открываем
      filterPanel.classList.add('open');
      arrow.textContent = '▼';
      text.textContent = 'Фильтры';
    }
  });
});