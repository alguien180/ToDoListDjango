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
