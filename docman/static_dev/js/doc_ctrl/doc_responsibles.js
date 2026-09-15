// JavaScript для добавления/удаления строк без перезагрузки

const respBody = document.getElementById('responsibles-body');
const respRowTemplate = document.getElementById('responsible-row-template').content;
const addRespBtn = document.getElementById('add-responsible-btn');

function addRow() {
  const clone = respRowTemplate.cloneNode(true);
  const deadline = clone.querySelector('input[name="responsibles_deadline[]"]');
  deadline.value = '';
  respBody.appendChild(clone.firstElementChild);
}

addRespBtn.addEventListener('click', addRow);

respBody.addEventListener('click', (e) => {
  if (e.target.classList.contains('remove-row-btn')) {
    const row = e.target.closest('.responsible-row');
    if (respBody.children.length > 0) {
      row.remove();
    }
  }
});

function addDateToHidden(visible_field, hidden_field) {
    hidden_field.value = visible_field.value;
}


// Опционально: валидация перед отправкой
document.getElementById('doc-form').addEventListener('submit', (e) => {
  // Можно добавить свою валидацию, если нужно
});

function toggleDeadline(cb) {
  const row = cb.closest('.responsible-row');
  const dateInput = row.querySelector('.deadline-date-field');
  const dateHiddenInput = row.querySelector('.deadline-hidden-field');
  if (!dateInput) return;
  if (cb.checked) {
    dateInput.disabled = true;
    dateInput.value = '';
    dateHiddenInput.value = '';
  } else {
    dateInput.disabled = false;
    dateInput.value = new Date().toISOString().split('T')[0];
    dateHiddenInput.value = dateInput.value;
  }
}
