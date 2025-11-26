// static/payments/js/payments_admin.js
document.addEventListener("DOMContentLoaded", function () {
  const modal = new bootstrap.Modal(document.getElementById("actionModal"));
  const form = document.getElementById("actionForm");
  const noteInput = document.getElementById("note");
  const paymentIdInput = document.getElementById("paymentId");
  const actionTypeInput = document.getElementById("actionType");

  const toastEl = document.getElementById("alertToast");
  const toast = new bootstrap.Toast(toastEl);
  const toastMsg = document.getElementById("toastMessage");

  // Open modal on button click
  document.querySelectorAll(".open-action-modal").forEach((btn) => {
    btn.addEventListener("click", () => {
      paymentIdInput.value = btn.dataset.id;
      actionTypeInput.value = btn.dataset.action;
      noteInput.value = "";
      modal.show();
    });
  });

  // Submit modal form via AJAX
  form.addEventListener("submit", function (e) {
    e.preventDefault();

    const paymentId = paymentIdInput.value;
    const actionType = actionTypeInput.value;
    const note = noteInput.value.trim();
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    let url = "";
    if (actionType === "approve") url = `/payments/admin/ajax/approve/${paymentId}/`;
    else if (actionType === "reject") url = `/payments/admin/ajax/reject/${paymentId}/`;
    else if (actionType === "refund") url = `/payments/admin/ajax/refund/${paymentId}/`;

    fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken,
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({ note }),
    })
      .then((res) => res.json())
      .then((data) => {
        modal.hide();
        toastMsg.innerText = data.message;
        if (data.success) {
          toastEl.classList.remove("text-bg-danger");
          toastEl.classList.add("text-bg-success");
          // Update the status badge on table row dynamically
          const row = document.querySelector(`[data-id='${paymentId}']`).closest("tr");
          const statusCell = row.querySelector("td:nth-child(7)");
          statusCell.innerHTML = `<span class="badge bg-success">${data.new_status}</span>`;
          // Disable buttons
          row.querySelectorAll(".open-action-modal").forEach((b) => (b.disabled = true));
        } else {
          toastEl.classList.remove("text-bg-success");
          toastEl.classList.add("text-bg-danger");
        }
        toast.show();
      })
      .catch((err) => {
        console.error(err);
        toastMsg.innerText = "Error performing action.";
        toastEl.classList.add("text-bg-danger");
        toast.show();
      });
  });
});
