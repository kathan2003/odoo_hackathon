// ======================================================
// TransitOps Fuel Management
// fuel.js
// ======================================================

document.addEventListener("DOMContentLoaded", function () {

    initializeFuelSearch();
    initializeDeleteButtons();
    initializeFormValidation();
    animateCards();

});

// ======================================================
// Search Fuel Logs
// ======================================================

function initializeFuelSearch() {

    const search = document.getElementById("fuelSearch");

    if (!search) return;

    search.addEventListener("keyup", function () {

        let value = this.value.toLowerCase();

        let rows = document.querySelectorAll("#fuelTable tbody tr");

        rows.forEach(row => {

            if (row.textContent.toLowerCase().includes(value)) {

                row.style.display = "";

            }

            else {

                row.style.display = "none";

            }

        });

    });

}

// ======================================================
// Delete Confirmation
// ======================================================

function initializeDeleteButtons() {

    let buttons = document.querySelectorAll(".btn-danger");

    buttons.forEach(button => {

        button.addEventListener("click", function (event) {

            event.preventDefault();

            let confirmDelete = confirm(
                "Are you sure you want to delete this fuel log?"
            );

            if (confirmDelete) {

                alert("Delete functionality will be connected with Flask backend.");

            }

        });

    });

}

// ======================================================
// Form Validation
// ======================================================

function initializeFormValidation() {

    const form = document.querySelector("form");

    if (!form) return;

    form.addEventListener("submit", function (e) {

        let fuel = document.querySelector("[name='fuel_liters']");

        let cost = document.querySelector("[name='fuel_cost']");

        let odometer = document.querySelector("[name='odometer']");

        if (

            Number(fuel.value) <= 0 ||

            Number(cost.value) <= 0 ||

            Number(odometer.value) <= 0

        ) {

            e.preventDefault();

            alert("Please enter valid values.");

        }

    });

}

// ======================================================
// Card Animation
// ======================================================

function animateCards() {

    let cards = document.querySelectorAll(".dashboard-card");

    cards.forEach((card, index) => {

        card.style.opacity = "0";

        card.style.transform = "translateY(20px)";

        setTimeout(() => {

            card.style.transition = ".5s";

            card.style.opacity = "1";

            card.style.transform = "translateY(0px)";

        }, index * 150);

    });

}

// ======================================================
// Auto Calculate Fuel Price Per Liter
// ======================================================

const fuelInput = document.querySelector("[name='fuel_liters']");

const costInput = document.querySelector("[name='fuel_cost']");

if (fuelInput && costInput) {

    costInput.addEventListener("keyup", calculatePrice);

    fuelInput.addEventListener("keyup", calculatePrice);

}

function calculatePrice() {

    let fuel = parseFloat(fuelInput.value);

    let cost = parseFloat(costInput.value);

    if (!isNaN(fuel) && fuel > 0 && !isNaN(cost)) {

        let price = (cost / fuel).toFixed(2);

        console.log("Fuel Price/Liter : ₹" + price);

    }

}

// ======================================================
// Highlight Current Row
// ======================================================

const rows = document.querySelectorAll("#fuelTable tbody tr");

rows.forEach(row => {

    row.addEventListener("mouseenter", function () {

        this.style.backgroundColor = "#eef6ff";

    });

    row.addEventListener("mouseleave", function () {

        this.style.backgroundColor = "";

    });

});