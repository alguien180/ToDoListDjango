// static/Task/js/tags.js
export function initTagWidget(root) {
  const inputSel = root.getAttribute('data-tag-input');
  const hiddenSel = root.getAttribute('data-tag-hidden');
  const containerSel = root.getAttribute('data-tag-container');
  const maxTags = parseInt(root.getAttribute('data-tag-max') || '0', 10);

  const input = root.querySelector(inputSel) || document.querySelector(inputSel);
  const hidden = root.querySelector(hiddenSel) || document.querySelector(hiddenSel);
  const holder = root.querySelector(containerSel) || document.querySelector(containerSel);

  if (!input || !hidden || !holder) return;

  function parseTags() {
    return (hidden.value || '').split(',').map(t => t.trim()).filter(Boolean);
  }

  function emit(name, detail) {
    root.dispatchEvent(new CustomEvent(name, { detail }));
  }

  function setTags(tags) {
    hidden.value = tags.join(',');
    render();
    emit('tags:change', { tags });
  }

  function addTag(tag) {
    if (!tag) return;
    const tags = parseTags();
    if (maxTags && tags.length >= maxTags) return;
    const lower = tags.map(t => t.toLowerCase());
    if (!lower.includes(tag.toLowerCase())) {
      setTags([...tags, tag]);
    }
  }

  function removeTag(tag) {
    const tags = parseTags().filter(t => t.toLowerCase() !== tag.toLowerCase());
    setTags(tags);
  }

  function render() {
    holder.innerHTML = '';
    parseTags().forEach(tag => {
      const pill = document.createElement('span');
      pill.className = 'tag-pill';
      pill.textContent = tag;
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'tag-pill-remove';
      btn.textContent = '×';
      btn.setAttribute('aria-label', 'Remove tag ' + tag);
      btn.addEventListener('click', () => removeTag(tag));
      pill.appendChild(btn);
      holder.appendChild(pill);
    });
  }

  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      const v = input.value.trim().replace(/,$/, '');
      if (v) { addTag(v); input.value = ''; }
    } else if (e.key === 'Backspace' && !input.value) {
      const tags = parseTags();
      if (tags.length) removeTag(tags[tags.length - 1]);
    }
  });

  input.addEventListener('paste', e => {
    const text = (e.clipboardData.getData('text') || '').trim();
    if (text.includes(',')) {
      e.preventDefault();
      text.split(',')
          .map(t => t.trim())
          .filter(Boolean)
          .forEach(addTag);
      input.value = '';
    }
  });

  // Public API
  root._tagWidget = { addTag, removeTag, getTags: parseTags, setTags };

  render();
  return root._tagWidget;
}

export function initAllTagWidgets() {
  const widgets = [];
  document.querySelectorAll('[data-tag-root]').forEach(root => {
    const api = initTagWidget(root);
    if (api) widgets.push(api);
  });
  return widgets;
}
