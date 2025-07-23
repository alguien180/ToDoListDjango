(function() {
  const hidden = document.getElementById('tags_hidden');
  if (!hidden) return;

  function parse() {
    return (hidden.value || '').split(',').map(t => t.trim()).filter(Boolean);
  }
  function set(list) {
    hidden.value = list.join(',');
  }
  function submit() {
    document.getElementById('tags-form').submit();
  }

  // Toggle tags
  document.getElementById('tag_toggle_holder')?.addEventListener('click', e => {
    if (!e.target.classList.contains('tag-toggle-pill')) return;
    const token = e.target.getAttribute('data-tag-value');
    let list = parse();
    const low = list.map(t => t.toLowerCase());
    if (low.includes(token.toLowerCase())) {
      list = list.filter(t => t.toLowerCase() !== token.toLowerCase());
      e.target.classList.remove('is-active');
      e.target.setAttribute('aria-pressed', 'false');
    } else {
      list.push(token);
      e.target.classList.add('is-active');
      e.target.setAttribute('aria-pressed', 'true');
    }
    set(list);
    submit();
  });

  // Remove via active pills row
  document.querySelector('.active-tag-pills')?.addEventListener('click', e => {
    if (!e.target.classList.contains('tag-pill-remove')) return;
    const pill = e.target.closest('[data-active-tag]');
    if (!pill) return;
    const token = pill.getAttribute('data-active-tag');
    let list = parse().filter(t => t.toLowerCase() !== token.toLowerCase());
    set(list);
    submit();
  });

  // Clear all
  document.getElementById('clear-tags-btn')?.addEventListener('click', () => {
    if (!parse().length) return;
    set([]);
    submit();
  });
})();
