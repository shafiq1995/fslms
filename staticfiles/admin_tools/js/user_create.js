d// static/admin_tools/js/user_create.js

document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("createUserForm");
  const toastEl = document.getElementById("userToast");
  const toastBody = document.getElementById("toastMsg");
  const toast = new bootstrap.Toast(toastEl);
  const modal = document.getElementById("createUserModal");
  const userTableContainer = document.getElementById("userTableContainer");

  if (!form) return;

  form.addEventListener("submit", function (e) {
    e.preventDefault();

    const formData = new FormData(form);
    const csrfToken = form.querySelector("[name=csrfmiddlewaretoken]").value;

    fetch("/admin-panel/users/ajax/create/", {
      method: "POST",
      headers: { "X-CSRFToken": csrfToken, "X-Requested-With": "XMLHttpRequest" },
      body: formData,
    })
      .then((res) => res.json())
      .then((data) => {
        toastBody.innerText = data.message;
        toastEl.classList.toggle("text-bg-danger", !data.success);
        toastEl.classList.toggle("text-bg-success", data.success);
        toast.show();

        if (data.success) {
          // Close modal and reset form
          const bsModal = bootstrap.Modal.getInstance(modal);
          bsModal.hide();
          form.reset();

          // Reload the table (first page)
          fetch("/admin-panel/users/ajax/?page=1", {
            headers: { "X-Requested-With": "XMLHttpRequest" },
          })
            .then((res) => res.text())
            .then((html) => {
              userTableContainer.innerHTML = html;
              document.dispatchEvent(new Event("DOMContentLoaded")); // rebind toggle buttons
            });
        }
      })
      .catch((err) => {
        console.error("Error:", err);
        toastBody.innerText = "An error occurred.";
        toastEl.classList.add("text-bg-danger");
        toast.show();
      });
  });
});
