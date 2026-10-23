/**
 * Expense Tracker ET - Client Script
 */

document.addEventListener("DOMContentLoaded", function () {
  // 1. Mobile Sidebar Toggle
  const sidebar = document.getElementById("sidebar");
  const sidebarBackdrop = document.getElementById("sidebar-backdrop");
  const toggleBtn = document.getElementById("sidebarToggle");

  if (toggleBtn && sidebar && sidebarBackdrop) {
    toggleBtn.addEventListener("click", function () {
      sidebar.classList.toggle("show");
      sidebarBackdrop.classList.toggle("show");
    });

    sidebarBackdrop.addEventListener("click", function () {
      sidebar.classList.remove("show");
      sidebarBackdrop.classList.remove("show");
    });
  }

  // 2. Auto-dismiss alerts after 5 seconds
  const autoAlerts = document.querySelectorAll(".alert.alert-dismissible");
  autoAlerts.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = bootstrap.Alert.getInstance(alert) || new bootstrap.Alert(alert);
      if (bsAlert) {
        bsAlert.close();
      }
    }, 6000);
  });

  // 3. Confirm Delete Dialog Helper
  document.querySelectorAll("[data-confirm-delete]").forEach(function (element) {
    element.addEventListener("click", function (e) {
      const message = this.getAttribute("data-confirm-delete") || "Are you sure you want to delete this record?";
      if (!confirm(message)) {
        e.preventDefault();
        return false;
      }
    });
  });

  // 4. Dynamic category filtering based on transaction type selection
  const typeSelect = document.getElementById("type");
  const categorySelect = document.getElementById("category_id");

  if (typeSelect && categorySelect) {
    typeSelect.addEventListener("change", function () {
      const selectedType = this.value;
      // If categories have data-type attribute, filter options
      const options = categorySelect.querySelectorAll("option");
      let firstVisibleSelected = false;
      
      options.forEach(function (opt) {
        const catType = opt.getAttribute("data-type");
        if (!catType || catType === "both" || catType === selectedType) {
          opt.style.display = "";
          if (!firstVisibleSelected) {
            opt.selected = true;
            firstVisibleSelected = true;
          }
        } else {
          opt.style.display = "none";
          if (opt.selected) {
            opt.selected = false;
          }
        }
      });
    });
  }
});

/**
 * Safe Chart.js Initialization Helper
 * Falls back gracefully if Chart.js is offline or unavailable.
 */
function initSafeChart(canvasId, fallbackId, configBuilder) {
  const canvas = document.getElementById(canvasId);
  const fallback = document.getElementById(fallbackId);

  if (!canvas) return null;

  if (typeof Chart === "undefined") {
    if (fallback) fallback.style.display = "block";
    canvas.style.display = "none";
    return null;
  }

  try {
    const config = configBuilder();
    if (!config) return null;
    return new Chart(canvas, config);
  } catch (err) {
    console.warn("Chart rendering failed:", err);
    if (fallback) fallback.style.display = "block";
    canvas.style.display = "none";
    return null;
  }
}
