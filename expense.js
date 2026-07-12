// ======================================================
// TransitOps Expense Management
// expense.js
// ======================================================

document.addEventListener("DOMContentLoaded", function () {

    initializeExpenseSearch();

    initializeDeleteButtons();

    initializeFormValidation();

    initializeCardAnimation();

    initializeExpenseStatistics();

});

// ======================================================
// Search Expense Table
// ======================================================

function initializeExpenseSearch() {

    const searchBox = document.getElementById("expenseSearch");

    if (!searchBox) return;

    searchBox.addEventListener("keyup", function () {

        let value = this.value.toLowerCase();

        let rows = document.querySelectorAll("#expenseTable tbody tr");

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

    const buttons = document.querySelectorAll(".btn-danger");

    buttons.forEach(button => {

        button.addEventListener("click", function (e) {

            e.preventDefault();

            let result = confirm(

                "Are you sure you want to delete this expense?"

            );

            if(result){

                alert(

                    "Delete API will be connected with Flask."

                );

            }

        });

    });

}

// ======================================================
// Form Validation
// ======================================================

function initializeFormValidation() {

    const form = document.querySelector("form");

    if(!form) return;

    form.addEventListener("submit", function(e){

        let amount = document.querySelector("[name='amount']");

        if(Number(amount.value) <= 0){

            e.preventDefault();

            alert("Amount should be greater than zero.");

            amount.focus();

        }

    });

}

// ======================================================
// Dashboard Card Animation
// ======================================================

function initializeCardAnimation(){

    const cards = document.querySelectorAll(".dashboard-card");

    cards.forEach((card,index)=>{

        card.style.opacity="0";

        card.style.transform="translateY(25px)";

        setTimeout(()=>{

            card.style.transition=".5s";

            card.style.opacity="1";

            card.style.transform="translateY(0px)";

        },index*150);

    });

}

// ======================================================
// Calculate Total Expenses
// ======================================================

function initializeExpenseStatistics(){

    let total = 0;

    let rows = document.querySelectorAll("#expenseTable tbody tr");

    rows.forEach(row=>{

        let amountCell = row.cells[3];

        if(amountCell){

            let value = amountCell.innerText
                .replace("₹","")
                .replace(",","");

            total += Number(value);

        }

    });

    console.log("Total Expense : ₹"+total);

}

// ======================================================
// Highlight Row
// ======================================================

document.querySelectorAll("#expenseTable tbody tr").forEach(row=>{

    row.addEventListener("mouseenter",function(){

        this.style.background="#eef6ff";

    });

    row.addEventListener("mouseleave",function(){

        this.style.background="";

    });

});

// ======================================================
// Auto Format Amount Field
// ======================================================

const amountInput=document.querySelector("[name='amount']");

if(amountInput){

    amountInput.addEventListener("blur",function(){

        if(this.value){

            this.value=parseFloat(this.value).toFixed(2);

        }

    });

}

// ======================================================
// Expense Category Colors
// ======================================================

document.querySelectorAll("#expenseTable tbody tr").forEach(row=>{

    let category=row.cells[2];

    if(!category) return;

    switch(category.innerText.trim()){

        case "Fuel":

            category.style.color="#2563eb";

            category.style.fontWeight="600";

            break;

        case "Maintenance":

            category.style.color="#dc2626";

            category.style.fontWeight="600";

            break;

        case "Insurance":

            category.style.color="#16a34a";

            category.style.fontWeight="600";

            break;

        case "Repair":

            category.style.color="#ea580c";

            category.style.fontWeight="600";

            break;

        default:

            category.style.color="#475569";

    }

});

// ======================================================
// Simple Notification
// ======================================================

function showNotification(message){

    const toast=document.createElement("div");

    toast.className="alert alert-success position-fixed";

    toast.style.top="20px";

    toast.style.right="20px";

    toast.style.zIndex="9999";

    toast.innerHTML=message;

    document.body.appendChild(toast);

    setTimeout(()=>{

        toast.remove();

    },3000);

}