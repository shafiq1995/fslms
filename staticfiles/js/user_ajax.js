// static/admin_tools/js/user_ajax.js

document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("userTableContainer");
  const searchInput = document.getElementById("searchInput");
  const roleFilter = document.getElementById("roleFilter");
  const statusFilter = document.getElementById("statusFilter");

  // Helper to build query string
  function getFilters(page = 1) {
    const params = new URLSearchParams();
    if (searchInput.value.trim()) params.append("q", searchInput.value.trim());
    if (roleFilter.value) params.append("role", roleFilter.value);
    if (statusFilter.value) params.append("status", statusFilter.value);
    if (page) params.append("page", page);
    return params.toString();
  }

  // Load data via AJAX
  function loadUsers(page = 1) {
    fetch(`/admin-panel/users/ajax/?${getFilters(page)}`, {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    })
      .then((res) => res.text())
      .then((html) => {
        container.innerHTML = html;
        attachPagination();
        attachToggleButtons();
      })
      .catch((err) => console.error("Error:", err));
  }

  // Attach pagination button listeners
  function attachPagination() {
    document.querySelectorAll(".page-btn").forEach((link) => {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        const page = new URL(link.href).searchParams.get("page") || 1;
        loadUsers(page);
      });
    });
  }

  // Attach toggle buttons (reuse from user_toggle.js)
  function attachToggleButtons() {
    const event = new Event("DOMContentLoaded");
    document.dispatchEvent(event); // reinit user_toggle.js logic
  }

  // Trigger search on typing
  let typingTimer;
  searchInput.addEventListener("input", () => {
    clearTimeout(typingTimer);
    typingTimer = setTimeout(() => loadUsers(1), 400);
  });

  // Trigger filter changes
  [roleFilter, statusFilter].forEach((filter) =>
    filter.addEventListener("change", () => loadUsers(1))
  );

  // Initial load (if needed)
  attachPagination();
});
