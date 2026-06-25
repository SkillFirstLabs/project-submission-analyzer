let pieChart = null;
let barChart = null;

/* -------------------------------
   PIE CHART
--------------------------------*/

function loadPieChart(skills) {

    const labels = skills.map(skill => skill.skill_name);

    const values = skills.map(skill =>
        Math.round(skill.confidence * 100)
    );

    if (pieChart) {
        pieChart.destroy();
    }

    const ctx = document
        .getElementById("pieChart")
        .getContext("2d");

    pieChart = new Chart(ctx, {

        type: "pie",

        data: {

            labels: labels,

            datasets: [

                {

                    data: values,

                    backgroundColor: [

                        "#2563eb",
                        "#16a34a",
                        "#f59e0b",
                        "#ef4444",
                        "#8b5cf6",
                        "#06b6d4",
                        "#ec4899"

                    ],

                    borderWidth: 2,
                    borderColor: "#fff"

                }

            ]

        },

        options: {

            responsive: true,

            plugins: {

                legend: {

                    position: "bottom"

                }

            }

        }

    });

}


/* -------------------------------
   BAR CHART
--------------------------------*/

function loadBarChart(skills) {

    const labels = skills.map(skill => skill.skill_name);

    const values = skills.map(skill =>
        Math.round(skill.confidence * 100)
    );

    if (barChart) {
        barChart.destroy();
    }

    const ctx = document
        .getElementById("barChart")
        .getContext("2d");

    barChart = new Chart(ctx, {

        type: "bar",

        data: {

            labels: labels,

            datasets: [

                {

                    label: "Confidence %",

                    data: values,

                    backgroundColor: "#2563eb",

                    borderRadius: 8

                }

            ]

        },

        options: {

            indexAxis: "y",

            responsive: true,

            scales: {

                x: {

                    beginAtZero: true,

                    max: 100

                }

            },

            plugins: {

                legend: {

                    display: false

                }

            }

        }

    });

}