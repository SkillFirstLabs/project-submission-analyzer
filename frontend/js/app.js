const uploadSection = document.getElementById("uploadSection");
const loadingSection = document.getElementById("loadingSection");
const dashboard = document.getElementById("dashboard");

const zipFile = document.getElementById("zipFile");
const filename = document.getElementById("filename");
const analyzeBtn = document.getElementById("analyzeBtn");

// Show selected filename
zipFile.addEventListener("change", () => {

    if (zipFile.files.length === 0) return;

    filename.innerHTML = `
        <span class="text-green-600">
            ✅ ${zipFile.files[0].name}
        </span>
    `;
});

// Analyze Button
analyzeBtn.addEventListener("click", async () => {

    if (zipFile.files.length === 0) {
        alert("Please select a ZIP file.");
        return;
    }

    const file = zipFile.files[0];

    if (!file.name.toLowerCase().endsWith(".zip")) {
        alert("Only ZIP files are allowed.");
        return;
    }

    uploadSection.classList.add("hidden");
    loadingSection.classList.remove("hidden");

    const formData = new FormData();
    formData.append("zip_file", file);

    try {

        const response = await fetch(
            "http://127.0.0.1:5000/analyze-submission",
            {
                method: "POST",
                body: formData
            }
        );

        const result = await response.json();

        loadingSection.classList.add("hidden");
        dashboard.classList.remove("hidden");

        populateDashboard(result);

    }
    catch (err) {

        console.error(err);

        alert("Analysis failed.");

        loadingSection.classList.add("hidden");
        uploadSection.classList.remove("hidden");

    }

});
function populateDashboard(data) {

    // Overall Score
    document.getElementById("score").innerText =
        Math.round(data.overall_score) + "%";

    // Statistics
    document.getElementById("files").innerText =
        data.metadata.files_analyzed;

    document.getElementById("skillsCount").innerText =
        data.suggested_skills.length;

    document.getElementById("questions").innerText =
        data.evaluation_report.skills.length * 2;

    //---------------------------
    // Interview Questions
    //---------------------------

    const questionContainer =
        document.getElementById("questionsContainer");

    questionContainer.innerHTML = "";

    data.evaluation_report.skills.forEach(skill => {

        let html = `
        <div class="border rounded-xl p-5 mb-5">

            <h3 class="text-xl font-bold text-blue-700">

                ${skill.skill_name}

            </h3>

            <ul class="list-disc ml-6 mt-4">
        `;

        skill.questions.forEach(q => {

            html += `
                <li class="mb-3">

                    ${q.question_text}

                </li>
            `;

        });

        html += "</ul></div>";

        questionContainer.innerHTML += html;

    });

    //---------------------------
    // Strengths
    //---------------------------

    const strengths =
        document.getElementById("strengths");

    strengths.innerHTML = "";

    data.evaluation_report.strengths.forEach(item => {

        strengths.innerHTML +=

        `<li class="mb-3">${item}</li>`;

    });

    //---------------------------
    // Gaps
    //---------------------------

    const gaps =
        document.getElementById("gaps");

    gaps.innerHTML = "";

    data.evaluation_report.gaps.forEach(item => {

        gaps.innerHTML +=

        `<li class="mb-3">${item}</li>`;

    });

    //---------------------------
    // Summary
    //---------------------------

    document.getElementById("summary").innerText =
        data.evaluation_report.summary.narrative;

    //---------------------------
    // Charts
    //---------------------------

    loadPieChart(data.suggested_skills);

    loadBarChart(data.suggested_skills);

}