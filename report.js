// ======================================================
// TransitOps Reports Dashboard
// reports.js
// ======================================================

document.addEventListener("DOMContentLoaded", function () {

    initializeCharts();
    initializeSearch();
    animateCards();

});

// ======================================================
// Search Report Table
// ======================================================

function initializeSearch() {

    const searchInput = document.getElementById("searchVehicle");

    if (!searchInput) return;

    searchInput.addEventListener("keyup", function () {

        let value = this.value.toLowerCase();

        let rows = document.querySelectorAll("#reportTable tbody tr");

        rows.forEach(row => {

            row.style.display =
                row.textContent.toLowerCase().includes(value)
                ? ""
                : "none";

        });

    });

}

// ======================================================
// Dashboard Card Animation
// ======================================================

function animateCards() {

    let cards = document.querySelectorAll(".dashboard-card");

    cards.forEach((card, index) => {

        card.style.opacity = "0";

        card.style.transform = "translateY(25px)";

        setTimeout(() => {

            card.style.transition = "0.5s";

            card.style.opacity = "1";

            card.style.transform = "translateY(0)";

        }, index * 150);

    });

}

// ======================================================
// Charts
// ======================================================

function initializeCharts() {

    createFuelChart();

    createExpenseChart();

    createUtilizationChart();

    createROIChart();

    createFuelTrendChart();

}

// ======================================================
// Fuel Cost Chart
// ======================================================

function createFuelChart() {

    let ctx = document.getElementById("fuelCostChart");

    if (!ctx) return;

    new Chart(ctx, {

        type: "bar",

        data: {

            labels: ["V1","V2","V3","V4","V5"],

            datasets: [{

                label: "Fuel Cost",

                data: [12000,15000,9000,18000,13000]

            }]

        },

        options: {

            responsive: true,

            maintainAspectRatio: false

        }

    });

}

// ======================================================
// Expense Breakdown
// ======================================================

function createExpenseChart() {

    let ctx = document.getElementById("expenseChart");

    if (!ctx) return;

    new Chart(ctx, {

        type: "pie",

        data: {

            labels: [

                "Fuel",

                "Maintenance",

                "Insurance",

                "Repair"

            ],

            datasets: [{

                data: [

                    45,

                    25,

                    15,

                    15

                ]

            }]

        },

        options: {

            responsive: true

        }

    });

}

// ======================================================
// Fleet Utilization
// ======================================================

function createUtilizationChart() {

    let ctx = document.getElementById("utilizationChart");

    if (!ctx) return;

    new Chart(ctx, {

        type: "doughnut",

        data: {

            labels: [

                "Available",

                "On Trip",

                "Maintenance"

            ],

            datasets: [{

                data: [

                    14,

                    8,

                    3

                ]

            }]

        },

        options: {

            responsive: true

        }

    });

}

// ======================================================
// ROI Chart
// ======================================================

function createROIChart() {

    let ctx = document.getElementById("roiChart");

    if (!ctx) return;

    new Chart(ctx, {

        type: "line",

        data: {

            labels: [

                "V1",

                "V2",

                "V3",

                "V4",

                "V5"

            ],

            datasets: [{

                label: "ROI %",

                data: [

                    25,

                    32,

                    18,

                    40,

                    28

                ],

                fill: false,

                tension: .4

            }]

        },

        options: {

            responsive: true

        }

    });

}

// ======================================================
// Fuel Trend
// ======================================================

function createFuelTrendChart() {

    let ctx = document.getElementById("fuelTrendChart");

    if (!ctx) return;

    new Chart(ctx, {

        type: "line",

        data: {

            labels: [

                "Jan","Feb","Mar","Apr","May","Jun",

                "Jul","Aug","Sep","Oct","Nov","Dec"

            ],

            datasets: [{

                label: "Fuel Cost",

                data: [

                    12000,

                    15000,

                    14000,

                    17000,

                    19000,

                    21000,

                    18000,

                    17500,

                    19500,

                    22000,

                    21000,

                    23000

                ],

                fill: true,

                tension: .4

            }]

        },

        options: {

            responsive: true,

            maintainAspectRatio: false

        }

    });

}