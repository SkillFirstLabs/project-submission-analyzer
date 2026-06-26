const API_BASE_URL = "http://127.0.0.1:5000";

// DOM Elements
const uploadSection = document.getElementById("uploadSection");
const loadingSection = document.getElementById("loadingSection");
const dashboard = document.getElementById("dashboard");

const zipFile = document.getElementById("zipFile");
const filename = document.getElementById("filename");
const analyzeBtn = document.getElementById("analyzeBtn");
const newAnalysisBtn = document.getElementById("newAnalysisBtn");
const dropZone = document.getElementById("dropZone");

const errorAlert = document.getElementById("errorAlert");
const errorText = document.getElementById("errorText");

// Helper: Show custom error alert
function showError(message) {
    if (errorAlert && errorText) {
        errorText.innerText = message;
        errorAlert.classList.remove("hidden");
        // Scroll to top of section so user sees the error
        uploadSection.scrollIntoView({ behavior: "smooth" });
    } else {
        alert(message);
    }
}

// Helper: Hide custom error alert
function hideError() {
    if (errorAlert) {
        errorAlert.classList.add("hidden");
        errorText.innerText = "";
    }
}

// Update file display and perform client-side file validations
function handleFileSelect(file) {
    hideError();
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".zip")) {
        showError("Invalid file type. Only ZIP archives (.zip) are allowed.");
        zipFile.value = "";
        filename.innerHTML = "No File Selected";
        return;
    }

    // Limit check: 10MB limit on the frontend for early warning
    const MAX_SIZE = 10 * 1024 * 1024;
    if (file.size > MAX_SIZE) {
        showError("File size exceeds 10MB limit. Please upload a smaller project archive.");
        zipFile.value = "";
        filename.innerHTML = "No File Selected";
        return;
    }

    filename.innerHTML = `
        <span class="text-green-600 font-semibold flex items-center justify-center gap-1">
            ✅ ${file.name} (${(file.size / (1024 * 1024)).toFixed(2)} MB)
        </span>
    `;
}

// Show selected filename on manual file choice
zipFile.addEventListener("change", () => {
    if (zipFile.files.length > 0) {
        handleFileSelect(zipFile.files[0]);
    }
});

// Drag and Drop Event Listeners
if (dropZone) {
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add("border-blue-600", "bg-blue-50/50");
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove("border-blue-600", "bg-blue-50/50");
        }, false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files && files.length > 0) {
            zipFile.files = files;
            handleFileSelect(files[0]);
        }
    });
}

// Reset / New Analysis Functionality
function resetApplication() {
    hideError();
    
    // Reset Form Inputs
    zipFile.value = "";
    filename.innerHTML = "No File Selected";
    document.getElementById("questionsPerSkill").value = "2";

    // Clear dashboard components
    document.getElementById("languagesContainer").innerHTML = "";
    document.getElementById("frameworksContainer").innerHTML = "";

    // Switch screens
    dashboard.classList.add("hidden");
    loadingSection.classList.add("hidden");
    uploadSection.classList.remove("hidden");
}

newAnalysisBtn.addEventListener("click", resetApplication);

// Analyze Button Click Action
analyzeBtn.addEventListener("click", async () => {
    hideError();

    // 1. Validate Inputs BEFORE changing UI state
    if (zipFile.files.length === 0) {
        showError("Please select or drop a ZIP file containing the project source code.");
        return;
    }

    const file = zipFile.files[0];
    if (!file.name.toLowerCase().endsWith(".zip")) {
        showError("Only ZIP files are allowed.");
        return;
    }

    const qPerSkillStr = document.getElementById("questionsPerSkill").value.trim();
    const qPerSkill = parseInt(qPerSkillStr, 10);
    if (isNaN(qPerSkill) || qPerSkill < 1 || qPerSkill > 10) {
        showError("Questions Per Skill must be a number between 1 and 10.");
        return;
    }

    // Derive title from filename
    const title = file.name.replace(/\.zip$/i, "").replace(/[-_]/g, " ").replace(/\b\w/g, c => c.toUpperCase());

    // 2. Switch UI state to Loading
    uploadSection.classList.add("hidden");
    loadingSection.classList.remove("hidden");

    // 3. Construct form data
    const formData = new FormData();
    formData.append("project_title", title);
    formData.append("questions_per_skill", qPerSkill);
    formData.append("zip_file", file);

    // 5. Send API Request with robust error checks
    try {
        const response = await fetch(`${API_BASE_URL}/analyze-submission`, {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            // Read detail error message from API if available
            let errorMessage = `Server error (Status: ${response.status})`;
            try {
                const errData = await response.json();
                if (errData && errData.detail) {
                    errorMessage = errData.detail;
                }
            } catch (e) {
                // Response wasn't JSON, fallback to default error
            }
            throw new Error(errorMessage);
        }

        const result = await response.json();

        // 6. Transition to Dashboard and populate
        loadingSection.classList.add("hidden");
        dashboard.classList.remove("hidden");
        populateDashboard(result);

    } catch (err) {
        console.error("Analysis Failed:", err);
        
        let displayError = err.message;
        if (err.message.includes("Failed to fetch")) {
            displayError = `Cannot connect to the backend server. Please verify that the Flask server is running at ${API_BASE_URL}.`;
        }

        showError(displayError);

        loadingSection.classList.add("hidden");
        uploadSection.classList.remove("hidden");
    }
});

// Populate Dashboard dynamically
function populateDashboard(data) {
    if (!data) return;

    // Overall Score (with fallback)
    const scoreVal = typeof data.overall_score === 'number' ? data.overall_score : 0;
    const scoreEl = document.getElementById("score");
    scoreEl.innerText = Math.round(scoreVal) + "%";
    
    // Score colors depending on value
    if (scoreVal >= 80) {
        scoreEl.className = "text-5xl font-bold text-green-600";
    } else if (scoreVal >= 50) {
        scoreEl.className = "text-5xl font-bold text-yellow-500";
    } else {
        scoreEl.className = "text-5xl font-bold text-red-500";
    }

    // Statistics (safeguarded)
    const totalFiles = (data.metadata && typeof data.metadata.files_analyzed === 'number') 
        ? data.metadata.files_analyzed 
        : (data.metadata && typeof data.metadata.total_files === 'number') 
            ? data.metadata.total_files 
            : 0;
    document.getElementById("files").innerText = totalFiles;

    const skillsList = Array.isArray(data.suggested_skills) ? data.suggested_skills : [];
    document.getElementById("skillsCount").innerText = skillsList.length;

    // Handle nested evaluation report elements safely
    const evalReport = data.evaluation_report || {};
    const reportSkillsList = Array.isArray(evalReport.skills) ? evalReport.skills : [];

    // Calculate exact number of questions
    let totalQuestions = 0;
    reportSkillsList.forEach(s => {
        if (s.questions && Array.isArray(s.questions)) {
            totalQuestions += s.questions.length;
        }
    });
    document.getElementById("questions").innerText = totalQuestions;

    //---------------------------
    // Interview Questions
    //---------------------------
    const questionContainer = document.getElementById("questionsContainer");
    questionContainer.innerHTML = "";

    if (reportSkillsList.length === 0) {
        questionContainer.innerHTML = `<p class="text-gray-500 italic">No interview questions generated.</p>`;
    } else {
        reportSkillsList.forEach(skill => {
            const skillQuestions = Array.isArray(skill.questions) ? skill.questions : [];
            let html = `
            <div class="border rounded-xl p-5 mb-5 bg-white shadow-sm">
                <h3 class="text-xl font-bold text-blue-700">
                    ${skill.skill_name || "Unknown Skill"}
                </h3>
                <ul class="list-disc ml-6 mt-4 space-y-2">
            `;

            if (skillQuestions.length === 0) {
                html += `<li class="text-gray-500 italic">No questions for this skill.</li>`;
            } else {
                skillQuestions.forEach(q => {
                    html += `
                        <li class="text-gray-700">
                            <strong>Question:</strong> ${q.question_text || "N/A"}<br>
                            <span class="text-sm text-gray-500 italic block mt-1">Expected Concept: ${q.expected_answer || "N/A"}</span>
                        </li>
                    `;
                });
            }

            html += "</ul></div>";
            questionContainer.innerHTML += html;
        });
    }

    //---------------------------
    // Strengths
    //---------------------------
    const strengths = document.getElementById("strengths");
    strengths.innerHTML = "";
    const strengthsList = Array.isArray(evalReport.strengths) ? evalReport.strengths : [];
    if (strengthsList.length === 0) {
        strengths.innerHTML = `<li class="text-gray-500 italic">No strengths identified.</li>`;
    } else {
        strengthsList.forEach(item => {
            strengths.innerHTML += `<li class="mb-3 text-gray-700">${item}</li>`;
        });
    }

    //---------------------------
    // Gaps
    //---------------------------
    const gaps = document.getElementById("gaps");
    gaps.innerHTML = "";
    const gapsList = Array.isArray(evalReport.gaps) ? evalReport.gaps : [];
    if (gapsList.length === 0) {
        gaps.innerHTML = `<li class="text-gray-500 italic">No gaps identified.</li>`;
    } else {
        gapsList.forEach(item => {
            gaps.innerHTML += `<li class="mb-3 text-gray-700">${item}</li>`;
        });
    }

    //---------------------------
    // Summary
    //---------------------------
    const narrative = (evalReport.summary && typeof evalReport.summary.narrative === 'string') 
        ? evalReport.summary.narrative 
        : "No summary evaluation details provided.";
    document.getElementById("summary").innerText = narrative;

    //---------------------------
    // Languages Used
    //---------------------------
    const languagesContainer = document.getElementById("languagesContainer");
    if (languagesContainer) {
        languagesContainer.innerHTML = "";
        const langList = Array.isArray(data.language_analysis) ? data.language_analysis : [];
        if (langList.length === 0) {
            languagesContainer.innerHTML = `<p class="text-gray-500 italic">No languages detected.</p>`;
        } else {
            langList.forEach(lang => {
                const percentage = typeof lang.percentage === 'number' ? lang.percentage : 0;
                const loc = typeof lang.loc === 'number' ? lang.loc : 0;
                const langName = lang.language || "Unknown";
                
                languagesContainer.innerHTML += `
                    <div class="mb-4">
                        <div class="flex justify-between items-center mb-1">
                            <span class="font-semibold text-gray-700">${langName}</span>
                            <span class="text-sm text-gray-500">${percentage}% (${loc} LOC)</span>
                        </div>
                        <div class="w-full bg-gray-200 rounded-full h-2.5">
                            <div class="bg-blue-600 h-2.5 rounded-full" style="width: ${percentage}%"></div>
                        </div>
                    </div>
                `;
            });
        }
    }

    //---------------------------
    // Frameworks & Libraries Detected
    //---------------------------
    const frameworksContainer = document.getElementById("frameworksContainer");
    if (frameworksContainer) {
        frameworksContainer.innerHTML = "";
        const fwList = Array.isArray(data.framework_analysis) ? data.framework_analysis : [];
        if (fwList.length === 0) {
            frameworksContainer.innerHTML = `<p class="text-gray-500 italic">No frameworks or libraries detected.</p>`;
        } else {
            fwList.forEach(fw => {
                const fwName = fw.framework || "Unknown";
                const confidence = typeof fw.confidence === 'number' ? Math.round(fw.confidence * 100) : 0;
                
                frameworksContainer.innerHTML += `
                    <div class="flex items-center justify-between p-3 bg-white border border-gray-100 rounded-xl shadow-sm">
                        <div>
                            <span class="font-semibold text-gray-800">${fwName}</span>
                            <p class="text-xs text-gray-400 mt-0.5">Confidence: ${confidence}%</p>
                        </div>
                        <span class="px-2.5 py-1 text-xs font-semibold bg-green-50 text-green-700 rounded-full border border-green-200">
                            Detected
                        </span>
                    </div>
                `;
            });
        }
    }

    //---------------------------
    // Charts (Only load if skills are present)
    //---------------------------
    if (skillsList.length > 0) {
        loadPieChart(skillsList);
        loadBarChart(skillsList);
    } else {
        // Clear or show empty charts placeholders if needed
        console.log("No suggested skills detected. Chart rendering skipped.");
    }
}