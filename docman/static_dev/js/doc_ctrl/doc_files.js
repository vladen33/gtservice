// JavaScript для отображения выбранных в форме файлов

const filesInput = document.getElementById('files-input');
const chosenList = document.getElementById('chosen-files-list');
const emptyMsg = document.getElementById('chosen-files-empty');
const fileTemplate = document.getElementById('chosen-file-template').content;

// Хранилище выбранных файлов
let selectedFiles = [];

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' Б';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' КБ';
  return (bytes / (1024 * 1024)).toFixed(1) + ' МБ';
}

function getIconSVG(ext) {
  if (ext === '.pdf') {
    return `<svg viewBox="0 0 16 16" width="20" height="20" fill="#dc2626">
      <path d="M2 1.5A1.5 1.5 0 013.5 0h6.379a1.5 1.5 0 01.603.127 1.5 1.5 0 01.494.331l2.566 2.567a1.5 1.5 0 01.341.497A1.5 1.5 0 0114 4.621V14.5a1.5 1.5 0 01-1.5 1.5h-9A1.5 1.5 0 012 14.5v-13zM3.5 1a.5.5 0 00-.5.5v13a.5.5 0 00.5.5h9a.5.5 0 00.5-.5V6H9.5A1.5 1.5 0 018 4.5V1H3.5zM9 4.5a.5.5 0 00.5.5h3.379L9 1.621V4.5z"/>
      <text x="3.5" y="13" font-size="5" font-weight="bold" fill="#dc2626">PDF</text>
    </svg>`;
  }
  // DOCX
  return `<svg viewBox="0 0 16 16" width="20" height="20" fill="#2563eb">
    <path d="M2 1.5A1.5 1.5 0 013.5 0h6.379a1.5 1.5 0 01.603.127 1.5 1.5 0 01.494.331l2.566 2.567a1.5 1.5 0 01.341.497A1.5 1.5 0 0114 4.621V14.5a1.5 1.5 0 01-1.5 1.5h-9A1.5 1.5 0 012 14.5v-13zM3.5 1a.5.5 0 00-.5.5v13a.5.5 0 00.5.5h9a.5.5 0 00.5-.5V6H9.5A1.5 1.5 0 018 4.5V1H3.5zM9 4.5a.5.5 0 00.5.5h3.379L9 1.621V4.5z"/>
    <text x="2.5" y="13" font-size="4.5" font-weight="bold" fill="#2563eb">DOCX</text>
  </svg>`;
}

function renderFileList() {
  // Очищаем всё, кроме сообщения-заглушки
  const items = chosenList.querySelectorAll('.chosen-file-item');
  items.forEach(item => item.remove());

  if (selectedFiles.length === 0) {
    emptyMsg.style.display = 'block';
    return;
  }

  emptyMsg.style.display = 'none';

  selectedFiles.forEach((file, index) => {
    const clone = fileTemplate.cloneNode(true);
    const ext = '.' + (file.name.split('.').pop() || '').toLowerCase();
    const item = clone.querySelector('.chosen-file-item');
    item.dataset.index = index;
    clone.querySelector('.chosen-file-icon').innerHTML = getIconSVG(ext);
    clone.querySelector('.chosen-file-name').textContent = file.name;
    clone.querySelector('.chosen-file-size').textContent = formatSize(file.size);
    chosenList.appendChild(clone.firstElementChild);
  });
}

// Добавление файлов при выборе
filesInput.addEventListener('change', (e) => {
  const newFiles = Array.from(e.target.files);
  selectedFiles = selectedFiles.concat(newFiles);
  renderFileList();
});

// Удаление файла из списка (крестик)
chosenList.addEventListener('click', (e) => {
  if (!e.target.classList.contains('chosen-file-remove')) return;

  const item = e.target.closest('.chosen-file-item');
  const index = parseInt(item.dataset.index, 10);
  selectedFiles.splice(index, 1);
  renderFileList();

  // Обновляем input: создаём новый DataTransfer без удалённого файла
  const dt = new DataTransfer();
  selectedFiles.forEach(f => dt.items.add(f));
  filesInput.files = dt.files;
});


// Удаление файла с сервера
document.querySelectorAll('.btn-delete').forEach(btn => {
  btn.addEventListener('click', () => {
    const name = btn.dataset.name;
    const doc_pk = btn.dataset.doc_pk;
    const file_pk = btn.dataset.file_pk;
    if (confirm(`Удалить файл «${name}»?`)) {
      deleteFile(doc_pk, file_pk);
    }
  });
});

function deleteFile(doc_pk, file_pk) {
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  const csrftoken = getCookie('csrftoken');
  // Проверь, что этот URL точно совпадает с path в urls.py
  const url = `/${doc_pk}/files/${file_pk}/delete/`;
  console.log('Путь для УДАЛЕНИЯ файла = ', url);
  console.log('csrftoken = ', csrftoken);

  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken,
    },
    body: JSON.stringify({}),
  })
    .then(response => {
      if (!response.ok) {
        // Сначала читаем ответ как текст, чтобы увидеть HTML (ошибку Django)
        return response.text().then(text => {
          console.error('HTTP error:', response.status);
          console.error('Ответ сервера (HTML):', text);
          throw new Error(`HTTP ${response.status}`);
        });
      }
      return response.json();
    })
    .then(data => {
      // Успех
      const row = document.querySelector(`[data-file-id="${file_pk}"]`); // обрати внимание: file_pk, а не pk
      if (row) {
        row.style.opacity = '0';
        setTimeout(() => row.remove(), 300);
      }
      alert('Файл удалён');
    })
    .catch(error => {
      console.error('Ошибка удаления:', error);
      alert('Не удалось удалить файл. Проверь консоль (F12).');
    });
}

