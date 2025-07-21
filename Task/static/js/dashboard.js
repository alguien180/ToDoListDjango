/**
 * dashboard_dashboard.js
 * All interactive behaviour for the Dashboard page.
 *
 * Requires:
 *  - FullCalendar (already loaded before this file)
 *  - HTML structure from dashboard.html
 */

(function () {
  "use strict";

  // ---------- Utilities ----------
  function $(selector, root = document) {
    return root.querySelector(selector);
  }
  function $all(selector, root = document) {
    return Array.from(root.querySelectorAll(selector));
  }

  function submitFilterForm() {
    const form = $("#typeFilterForm");
    if (form) form.submit();
  }

  // ---------- Tag Selector Logic ----------
  function initTagSelector() {
    const selector = $("#tag-selector");
    const searchInput = $("#tagSearch");
    const clearBtn = $("#clearTags");
    const form = $("#typeFilterForm");
    if (!selector || !form) return;

    const hiddenTagsInput = form.querySelector('input[name="tags"]');

    function collectSelected() {
      const selected = $all(".tag-option.selected", selector).map(
        (el) => el.dataset.tag
      );
      hiddenTagsInput.value = selected.join(",");
    }

    selector.addEventListener("click", (e) => {
      const el = e.target.closest(".tag-option");
      if (!el) return;
      el.classList.toggle("selected");
      collectSelected();
      form.submit();
    });

    if (searchInput) {
      searchInput.addEventListener("input", () => {
        const q = searchInput.value.toLowerCase();
        $all(".tag-option", selector).forEach((opt) => {
          opt.style.display =
            !q || opt.dataset.tag.toLowerCase().includes(q) ? "" : "none";
        });
      });
    }

    if (clearBtn) {
      clearBtn.addEventListener("click", () => {
        $all(".tag-option.selected", selector).forEach((o) =>
          o.classList.remove("selected")
        );
        collectSelected();
        form.submit();
      });
    }
  }

  // ---------- Filter Type (radios & checkboxes) ----------
  function initFilterTypeForm() {
    const form = $("#typeFilterForm");
    if (!form) return;

    // Any input change triggers submit (except we already handle some manually above)
    $all("input", form).forEach((inp) => {
      inp.addEventListener("change", () => {
        // group colour handled separately
        if (inp.id === "groupColourToggle") return;
        submitFilterForm();
      });
    });

    // Group by colour toggle logic
    const groupToggle = $("#groupColourToggle");
    if (groupToggle) {
      groupToggle.addEventListener("change", () => {
        // If unchecked we add hidden input group_colour=off, else remove it
        let hidden = form.querySelector('input[name="group_colour"]');
        if (!groupToggle.checked) {
          if (!hidden) {
            hidden = document.createElement("input");
            hidden.type = "hidden";
            hidden.name = "group_colour";
            hidden.value = "off";
            form.appendChild(hidden);
          } else {
            hidden.value = "off";
          }
        } else {
          if (hidden) hidden.remove();
        }
        form.submit();
      });
    }
  }

  // ---------- Colour Style Switcher ----------
  function initColourStyleSelect() {
    const select = $("#colourStyleSelect");
    if (!select) return;

    function setActiveStyle(val) {
      // Enable/disable linked alternate styles by title attribute
      const links = document.querySelectorAll('link.alternate-style[title]');
      links.forEach((lnk) => {
        if (lnk.getAttribute("title") === val) {
          lnk.disabled = false;
        } else {
          lnk.disabled = true;
        }
      });
    }

    select.addEventListener("change", () => {
      setActiveStyle(select.value);
    });
  }

  // ---------- Calendar ----------
  function initCalendar() {
    const calEl = $("#calendar");
    if (!calEl || typeof FullCalendar === "undefined") return;

    let events = [];
    const dataEl = $("#eventData");
    if (dataEl) {
      try {
        events = JSON.parse(dataEl.textContent.trim() || "[]");
      } catch (e) {
        console.warn("Invalid event JSON", e);
      }
    }

    const calendar = new FullCalendar.Calendar(calEl, {
      initialView: "dayGridMonth",
      height: "auto",
      headerToolbar: {
        left: "prev,next today",
        center: "title",
        right: "dayGridMonth,timeGridWeek,timeGridDay,listWeek",
      },
      events: events,
      eventDisplay: "block",
      eventTimeFormat: { hour: "2-digit", minute: "2-digit", hour12: false },
    });

    calendar.render();
  }

  // ---------- Export buttons (stubs) ----------
  function initExportButtons() {
    const pdfBtn = $(".export_dashboard_pdf");
    const docBtn = $(".export_dashboard_doc");
    if (pdfBtn)
      pdfBtn.addEventListener("click", (e) => {
        e.preventDefault();
        alert("PDF export stub. Implement generation logic here.");
      });
    if (docBtn)
      docBtn.addEventListener("click", (e) => {
        e.preventDefault();
        alert("DOCX export stub. Implement generation logic here.");
      });
  }

  // ---------- Init ----------
  document.addEventListener("DOMContentLoaded", () => {
    initTagSelector();
    initFilterTypeForm();
    initColourStyleSelect();
    initCalendar();
    initExportButtons();
  });
})();
