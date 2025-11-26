// static/admin_tools/js/user_edit.js

document.addEventListener("DOMContentLoaded", function () {
  const toastEl = document.getElementById("userToast");
  const toastBody = document.getElementById("toastMsg");
  const toast = new bootstrap.Toast(toastEl);
  const editModal = new bootstrap.Modal(document.getElementById("editUserModal"));
  const editForm = document.getElementById("editUserForm");
  const userTableContainer = document.getElementById("userTableContainer");

  // When "Edit" button is clicked
  document.addEventListener("click", function (e) {
    if (e.target.closest(".edit-user-btn")) {
      const btn = e.target.closest(".edit-user-btn");
      const userId = btn.dataset.id;
      const username = btn.dataset.username;
      const email = btn.dataset.email;
      const role = btn.dataset.role;
      const isActive = btn.dataset.active === "true";

      // Fill modal form
      document.getElementById("editUserId").value = userId;
      document.getElementById("editUsername").value = username;
      document.getElementById("editEmail").value = email;
      document.getElementById("editRole").value = role;
      document.getElementById("editIsActive").checked = isActive;

      editModal.show();
    }
  });

  // Submit form via AJAX
  if (editForm) {
    editForm.addEventListener("submit", function (e) {
      e.preventDefault();

      const formData = new FormData(editForm);
      const csrfToken = editForm.querySelector("[name=csrfmiddlewaretoken]").value;

      fetch("/admin-panel/users/ajax/edit/", {
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
            // Close modal
            editModal.hide();

            // Reload table to reflect changes
            fetch("/admin-panel/users/ajax/?page=1", {
              headers: { "X-Requested-With": "XMLHttpRequest" },
            })
              .then((res) => res.text())
              .then((html) => {
                userTableContainer.innerHTML = html;
                document.dispatchEvent(new Event("DOMContentLoaded"));
              });
          }
        })
        .catch((err) => {
          console.error("Error:", err);
          toastBody.innerText = "An error occurred while updating.";
          toastEl.classList.add("text-bg-danger");
          toast.show();
        });
    });
  }
});
