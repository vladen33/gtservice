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
  const e = (ext || '').toLowerCase();

  const iconMap = {
    '.pdf':  'icon-pdf',
    '.docx': 'icon-docx',
    '.doc':  'icon-docx',
    '.xlsx': 'icon-xlsx',
    '.xls':  'icon-xlsx',
    '.pptx': 'icon-pptx',
    '.ppt':  'icon-pptx',
    '.txt':  'icon-txt',
    '.zip':  'icon-zip',
    '.rar':  'icon-zip',
    '.7z':   'icon-zip',
    '.png':  'icon-png',
    '.jpg':  'icon-jpg',
    '.jpeg': 'icon-jpg',
    '.csv':  'icon-csv',
  };

  const iconId = iconMap[e] || 'icon-default';

  return `<svg class="icon ${iconId}" viewBox="0 0 16 16" width="20" height="20">
    <use href="#${iconId}"></use>
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

