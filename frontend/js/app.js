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
        const titleDisplay = document.getElementById("projectTitleDisplay");
        if (titleDisplay) {
            titleDisplay.innerText = title;
        }
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
        scoreEl.className = "text-4xl md:text-5xl font-extrabold text-emerald-400 mt-3";
    } else if (scoreVal >= 50) {
        scoreEl.className = "text-4xl md:text-5xl font-extrabold text-amber-400 mt-3";
    } else {
        scoreEl.className = "text-4xl md:text-5xl font-extrabold text-rose-400 mt-3";
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
        questionContainer.innerHTML = `<p class="text-slate-500 italic text-sm">No interview questions generated.</p>`;
    } else {
        let qIndex = 0;
        reportSkillsList.forEach((skill, skillIdx) => {
            const skillQuestions = Array.isArray(skill.questions) ? skill.questions : [];
            let html = `
            <div class="bg-slate-900/35 border border-slate-800/80 rounded-2xl p-6 mb-6">
                <div class="flex items-center gap-2.5 mb-5">
                    <div class="w-3 h-3 rounded-full bg-indigo-500 shadow-lg shadow-indigo-500/50"></div>
                    <h3 class="text-lg font-bold text-white">
                        ${skill.skill_name || "Unknown Skill"}
                    </h3>
                </div>
                <div class="space-y-4">
            `;

            if (skillQuestions.length === 0) {
                html += `<p class="text-slate-500 italic text-xs">No questions generated for this skill.</p>`;
            } else {
                skillQuestions.forEach(q => {
                    const qId = `q_reveal_${skillIdx}_${qIndex++}`;
                    const difficulty = q.difficulty || "Medium";
                    let diffBadgeColor = "bg-amber-950/40 text-amber-400 border-amber-900/40";
                    if (difficulty.toLowerCase() === 'easy') {
                        diffBadgeColor = "bg-emerald-950/40 text-emerald-400 border-emerald-900/40";
                    } else if (difficulty.toLowerCase() === 'hard') {
                        diffBadgeColor = "bg-rose-950/40 text-rose-400 border-rose-900/40";
                    }
                    
                    html += `
                    <div class="bg-slate-900/60 border border-slate-850/60 rounded-xl p-4 transition-all duration-200 hover:border-slate-800">
                        <div class="flex flex-wrap items-center gap-2 mb-3">
                            <span class="px-2.5 py-0.5 text-[10px] font-bold rounded border ${diffBadgeColor}">
                                ${difficulty}
                            </span>
                            ${q.topic ? `
                            <span class="px-2.5 py-0.5 text-[10px] font-bold rounded bg-indigo-950/40 text-indigo-400 border border-indigo-900/30">
                                ${q.topic}
                            </span>
                            ` : ''}
                        </div>
                        <p class="text-slate-200 text-sm font-medium leading-relaxed">
                            ${q.question_text || q.question || "N/A"}
                        </p>
                        
                        <div class="mt-4 pt-3 border-t border-slate-800/40">
                            <button onclick="toggleAnswer('${qId}')" class="text-xs text-indigo-400 hover:text-indigo-300 font-bold flex items-center gap-1.5 focus:outline-none transition">
                                <span id="icon_${qId}">➕</span> <span id="btn_text_${qId}">Reveal Expected Concept</span>
                            </button>
                            <div id="${qId}" class="hidden mt-3 bg-slate-950/40 border border-slate-900 rounded-lg p-3 text-xs text-slate-400 leading-relaxed font-mono">
                                <strong class="text-indigo-300 block mb-1 font-sans font-semibold">Expected Answer Hint:</strong>
                                ${q.expected_answer || "N/A"}
                            </div>
                        </div>
                    </div>
                    `;
                });
            }

            html += "</div></div>";
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
        strengths.innerHTML = `<li class="text-slate-500 italic text-sm">No strengths identified.</li>`;
    } else {
        strengthsList.forEach(item => {
            strengths.innerHTML += `
                <li class="flex items-start gap-3 text-sm text-slate-300">
                    <span class="text-emerald-400 mt-0.5 flex-shrink-0 font-bold">✓</span>
                    <span>${item}</span>
                </li>
            `;
        });
    }

    //---------------------------
    // Gaps
    //---------------------------
    const gaps = document.getElementById("gaps");
    gaps.innerHTML = "";
    const gapsList = Array.isArray(evalReport.gaps) ? evalReport.gaps : [];
    if (gapsList.length === 0) {
        gaps.innerHTML = `<li class="text-slate-500 italic text-sm">No gaps identified.</li>`;
    } else {
        gapsList.forEach(item => {
            gaps.innerHTML += `
                <li class="flex items-start gap-3 text-sm text-slate-300">
                    <span class="text-rose-400 mt-0.5 flex-shrink-0 font-bold">⚠</span>
                    <span>${item}</span>
                </li>
            `;
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
            languagesContainer.innerHTML = `<p class="text-slate-500 italic text-sm">No languages detected.</p>`;
        } else {
            const gradientMap = {
                'python': 'from-blue-500 to-yellow-500',
                'javascript': 'from-yellow-400 to-amber-500',
                'typescript': 'from-blue-600 to-sky-400',
                'rust': 'from-orange-600 to-amber-600',
                'go': 'from-cyan-500 to-blue-400',
                'java': 'from-orange-500 to-red-500',
                'c++': 'from-blue-600 to-indigo-600',
                'c': 'from-slate-400 to-slate-600',
                'html': 'from-orange-500 to-red-400',
                'css': 'from-indigo-400 to-blue-500',
            };

            langList.forEach(lang => {
                const percentage = typeof lang.percentage === 'number' ? lang.percentage : 0;
                const loc = typeof lang.loc === 'number' ? lang.loc : 0;
                const langName = lang.language || "Unknown";
                
                const langLower = langName.toLowerCase();
                const barGradient = gradientMap[langLower] || 'from-indigo-500 to-purple-500';

                languagesContainer.innerHTML += `
                    <div class="mb-5 animate-fade-in">
                        <div class="flex justify-between items-center mb-2">
                            <span class="font-bold text-slate-200 text-sm flex items-center gap-1.5">
                                ${langName}
                            </span>
                            <span class="text-xs text-slate-400 font-mono">${percentage}% (${loc.toLocaleString()} LOC)</span>
                        </div>
                        <div class="w-full bg-slate-900 border border-slate-800/80 rounded-full h-2.5 overflow-hidden">
                            <div class="bg-gradient-to-r ${barGradient} h-2.5 rounded-full" style="width: ${percentage}%"></div>
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
            frameworksContainer.innerHTML = `<p class="text-slate-500 italic text-sm col-span-2">No framework or module identifiers detected.</p>`;
        } else {
            fwList.forEach(fw => {
                const fwName = fw.framework || "Unknown";
                const confidence = typeof fw.confidence === 'number' ? Math.round(fw.confidence * 100) : 0;
                
                frameworksContainer.innerHTML += `
                    <div class="flex items-center justify-between p-4 bg-slate-900/50 border border-slate-850 rounded-xl transition duration-300 hover:border-slate-800 animate-fade-in">
                        <div>
                            <span class="font-bold text-slate-200 text-sm block">${fwName}</span>
                            <span class="text-[10px] text-slate-500 font-mono mt-0.5 block">Confidence: ${confidence}%</span>
                        </div>
                        <span class="px-2.5 py-0.5 text-[10px] font-bold bg-emerald-950/40 text-emerald-400 rounded-full border border-emerald-900/30">
                            Active
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
        console.log("No suggested skills detected. Chart rendering skipped.");
    }
}

// Global reveal toggle for questions
window.toggleAnswer = function(id) {
    const el = document.getElementById(id);
    const icon = document.getElementById(`icon_${id}`);
    const btnText = document.getElementById(`btn_text_${id}`);
    if (el.classList.contains("hidden")) {
        el.classList.remove("hidden");
        icon.innerText = "➖";
        btnText.innerText = "Hide Expected Concept";
    } else {
        el.classList.add("hidden");
        icon.innerText = "➕";
        btnText.innerText = "Reveal Expected Concept";
    }
};