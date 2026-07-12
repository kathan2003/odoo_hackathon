// ==========================================
// TransitOps - Trip Management JavaScript
// ==========================================

// ------------------------------
// Initialize
// ------------------------------

document.addEventListener("DOMContentLoaded", function () {

    setupSearch();
    setupFilter();

});

// ------------------------------
// Live Search
// ------------------------------

function setupSearch() {

    const input = document.getElementById("searchInput");

    if (!input) return;

    input.addEventListener("keyup", function () {

        const value = input.value.toLowerCase();

        const rows = document.querySelectorAll("#tripTable tbody tr");

        rows.forEach(function (row) {

            const text = row.innerText.toLowerCase();

            row.style.display = text.includes(value) ? "" : "none";

        });

    });

}

// ------------------------------
// Status Filter
// ------------------------------

function setupFilter() {

    const filter = document.getElementById("statusFilter");

    if (!filter) return;

    filter.addEventListener("change", function () {

        const selected = filter.value.toLowerCase();

        const rows = document.querySelectorAll("#tripTable tbody tr");

        rows.forEach(function (row) {

            const badge = row.querySelector(".badge");

            if (!badge) return;

            const status = badge.innerText.toLowerCase();

            if (selected === "" || status === selected) {

                row.style.display = "";

            } else {

                row.style.display = "none";

            }

        });

    });

}

// ------------------------------
// Dispatch Trip
// ------------------------------

function dispatchTrip(id) {

    const confirmAction = confirm(
        "Are you sure you want to dispatch Trip " + id + "?"
    );

    if (!confirmAction) return;

    window.location.href = "/trip/dispatch/" + id;

}

// ------------------------------
// Complete Trip
// ------------------------------

function completeTrip(id) {

    const confirmAction = confirm(
        "Mark Trip " + id + " as completed?"
    );

    if (!confirmAction) return;

    window.location.href = "/trip/complete/" + id;

}

// ------------------------------
// Cancel Trip
// ------------------------------

function cancelTrip(id) {

    const confirmAction = confirm(
        "Cancel Trip " + id + "?"
    );

    if (!confirmAction) return;

    window.location.href = "/trip/cancel/" + id;

}

// ------------------------------
// View Trip Details
// ------------------------------

function viewTrip(id) {

    window.location.href = "/trip/details/" + id;

}

// ------------------------------
// Refresh Page
// ------------------------------

function refreshTrips() {

    window.location.reload();

}