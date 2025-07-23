document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('eventModal');

  function openModal() {
    modal.removeAttribute('hidden');
  }
  function closeModal() {
    modal.setAttribute('hidden', 'hidden');
  }

  modal.addEventListener('click', e => {
    const act = e.target.dataset.action;
    if (!act) return;
    if (act === 'close') closeModal();
    // handle other actions (done / delete / edit / done-all) here
  });

  // Example: expose globally if other code calls these
  window.TaskModal = { open: openModal, close: closeModal };
});
document.addEventListener('DOMContentLoaded', () => {
    const btn  = document.getElementById('toggle-task-form');
    const wrap = document.getElementById('task-form-wrapper');
    btn?.addEventListener('click', () => wrap.classList.toggle('hidden'));
});

// calendar
document.addEventListener('DOMContentLoaded', () => {
  const calEl = document.getElementById('calendar');
  if (!calEl) return;

  const events = JSON.parse(document.getElementById('eventData').textContent);

  const calendar = new FullCalendar.Calendar(calEl, {
    initialView: 'timeGridWeek',
    events: events
  });

  calendar.render();
});
