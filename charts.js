document.addEventListener("DOMContentLoaded", function(){



// ================================
// FUEL COST LINE CHART
// ================================


const fuelCost = document.getElementById('fuelCostChart');


if(fuelCost){


new Chart(fuelCost,{

type:'line',

data:{


labels:[
'Jan',
'Feb',
'Mar',
'Apr',
'May',
'Jun'
],


datasets:[{

label:'Fuel Cost',

data:[
45000,
52000,
48000,
65000,
70000,
76000
],


borderWidth:3,

tension:0.4

}]


},


options:{


responsive:true,

maintainAspectRatio:false


}


});


}







// ================================
// VEHICLE COST BAR CHART
// ================================


const vehicleCost = document.getElementById('vehicleCostChart');


if(vehicleCost){


new Chart(vehicleCost,{


type:'bar',


data:{


labels:[

'Truck 01',
'Truck 02',
'Truck 03',
'Truck 04'

],


datasets:[{


label:'Operational Cost',

data:[

120000,
95000,
150000,
80000

]


}]


},


options:{


responsive:true,

maintainAspectRatio:false


}



});


}








// ================================
// TRIP ANALYSIS CHART
// ================================


const tripChart = document.getElementById('tripChart');


if(tripChart){


new Chart(tripChart,{


type:'line',


data:{


labels:[

'Mon',
'Tue',
'Wed',
'Thu',
'Fri',
'Sat'

],


datasets:[{


label:'Trips Completed',


data:[

20,
35,
30,
45,
55,
60

],


fill:true,


tension:0.4


}]


},


options:{


responsive:true,

maintainAspectRatio:false


}



});


}








// ================================
// FLEET UTILIZATION DOUGHNUT
// ================================


const fleetChart = document.getElementById('fleetChart');


if(fleetChart){



new Chart(fleetChart,{


type:'doughnut',


data:{


labels:[

'Active',
'Idle'

],


datasets:[{


data:[

84,
16

]


}]


},


options:{


responsive:true,

maintainAspectRatio:false,


plugins:{


legend:{


position:'bottom'


}


}



}



});


}









// ================================
// EXPENSE BREAKDOWN PIE
// ================================


const expenseChart = document.getElementById('expenseChart');


if(expenseChart){


new Chart(expenseChart,{


type:'doughnut',


data:{


labels:[

'Fuel',
'Maintenance',
'Insurance',
'Other'

],


datasets:[{


label:'Expenses',


data:[

42,
30,
18,
10

]


}]


},


options:{


responsive:true,

maintainAspectRatio:false,


plugins:{


legend:{


position:'bottom'


}


}


}



});


}








// ================================
// EXPENSE TREND CHART
// ================================


const expenseTrend = document.getElementById('expenseTrend');


if(expenseTrend){


new Chart(expenseTrend,{


type:'line',


data:{


labels:[

'Jan',
'Feb',
'Mar',
'Apr',
'May',
'Jun'

],


datasets:[{


label:'Monthly Expenses',


data:[

35000,
45000,
42000,
60000,
58000,
72000

],


tension:0.4,


borderWidth:3


}]


},


options:{


responsive:true,

maintainAspectRatio:false


}



});


}



});