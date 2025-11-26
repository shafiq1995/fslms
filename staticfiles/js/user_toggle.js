// static/admin_tools/js/user_toggle.js

document.addEventListener("DOMContentLoaded", function () {
  const toastEl = document.getElementById("userToast");
  const toastBody = document.getElementById("toastMsg");
  const toast = new bootstrap.Toast(toastEl);

  const buttons = document.querySelectorAll(".toggle-status-btn");

  buttons.forEach((btn) => {
    btn.addEventListener("click", function () {
      const userId = this.dataset.id;
      const isActive = this.dataset.active === "true";
      const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

      fetch(`/admin-panel/users/${userId}/toggle-status/`, {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken,
          "X-Requested-With": "XMLHttpRequest",
        },
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.success) {
            // Update status badge
            const statusBadge = document.getElementById(`status-${userId}`);
            statusBadge.innerText = data.new_status;
            statusBadge.className =
              "badge " + (data.is_active ? "bg-success" : "bg-secondary");

            // Update button text + style
            btn.innerText = data.is_active ? "Deactivate" : "Activate";
            btn.className =
              "btn btn-sm " + (data.is_active ? "btn-warning" : "btn-success");
            btn.dataset.active = data.is_active ? "true" : "false";

            // Show toast
            toastEl.classList.remove("text-bg-danger");
            toastEl.classList.add("text-bg-success");
          } else {
            toastEl.classList.remove("text-bg-success");
            toastEl.classList.add("text-bg-danger");
          }
          toastBody.innerText = data.message;
          toast.show();
        })
        .catch((err) => {
          console.error("Error:", err);
          toastEl.classList.remove("text-bg-success");
          toastEl.classList.add("text-bg-danger");
          toastBody.innerText = "An error occurred while updating status.";
          toast.show();
        });
    });
  });
});
