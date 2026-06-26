let pieChart = null;
let barChart = null;

/* -------------------------------
   PIE CHART
--------------------------------*/

function loadPieChart(skills) {
    if (!Array.isArray(skills)) return;

    // Group skills by category to represent the distribution
    const categoryGroups = {};
    skills.forEach(skill => {
        const cat = skill.category || "General";
        const confidence = typeof skill.confidence === 'number' ? skill.confidence : 0;
        if (!categoryGroups[cat]) {
            categoryGroups[cat] = 0;
        }
        categoryGroups[cat] += Math.round(confidence * 100);
    });

    const labels = Object.keys(categoryGroups);
    const values = Object.values(categoryGroups);

    if (pieChart) {
        pieChart.destroy();
        pieChart = null;
    }

    const canvas = document.getElementById("pieChart");
    if (!canvas) return;

    // Ensure container has a clean height for non-aspect-ratio rendering
    const parentDiv = canvas.parentElement;
    if (parentDiv) {
        parentDiv.style.height = "280px";
        parentDiv.style.position = "relative";
    }

    const ctx = canvas.getContext("2d");

    pieChart = new Chart(ctx, {
        type: "pie",
        data: {
            labels: labels,
            datasets: [
                {
                    data: values,
                    backgroundColor: [
                        "#6366f1", // Indigo
                        "#10b981", // Emerald
                        "#f59e0b", // Amber
                        "#ef4444", // Red
                        "#8b5cf6", // Purple
                        "#06b6d4", // Cyan
                        "#ec4899"  // Pink
                    ],
                    borderWidth: 2,
                    borderColor: "#0f172a" // Slate-900 border
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        color: "#94a3b8", // Slate-400 text
                        font: {
                            family: "'Outfit', sans-serif",
                            size: 11
                        },
                        padding: 15
                    }
                }
            }
        }
    });
}

/* -------------------------------
   BAR CHART
--------------------------------*/

function loadBarChart(skills) {
    if (!Array.isArray(skills)) return;

    const labels = skills.map(skill => skill.skill_name || "Unknown Skill");

    const values = skills.map(skill =>
        Math.round((typeof skill.confidence === 'number' ? skill.confidence : 0) * 100)
    );

    if (barChart) {
        barChart.destroy();
        barChart = null;
    }

    const canvas = document.getElementById("barChart");
    if (!canvas) return;

    // Dynamically calculate and set container height to prevent bars and labels from overlapping
    const parentDiv = canvas.parentElement;
    if (parentDiv) {
        const itemHeight = 35; // Pixels per skill
        const calculatedHeight = Math.max(300, skills.length * itemHeight);
        parentDiv.style.height = `${calculatedHeight}px`;
        parentDiv.style.position = "relative";
    }

    const ctx = canvas.getContext("2d");

    barChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Confidence %",
                    data: values,
                    backgroundColor: "#6366f1", // Indigo-500
                    borderRadius: 6,
                    barThickness: 16
                }
            ]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        color: "rgba(255, 255, 255, 0.05)" // Subtle gridlines
                    },
                    ticks: {
                        color: "#94a3b8", // Slate-400
                        font: {
                            family: "'Outfit', sans-serif"
                        }
                    }
                },
                y: {
                    grid: {
                        display: false // No horizontal grids
                    },
                    ticks: {
                        color: "#e2e8f0", // Slate-200
                        font: {
                            family: "'Outfit', sans-serif",
                            weight: "500"
                        }
                    }
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