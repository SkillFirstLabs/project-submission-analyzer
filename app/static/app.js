import {
    FaceDetector,
    FilesetResolver
} from "/static/mediapipe/vision_bundle.mjs";
const submissionForm =
    document.getElementById("submissionForm");

const loadingSection =
    document.getElementById("loadingSection");

const resultSection =
    document.getElementById("resultSection");

const projectInfo =
    document.getElementById("projectInfo");

const skillsResult =
    document.getElementById("skillsResult");

const questionsResult =
    document.getElementById("questionsResult");

const outcomesResult =
    document.getElementById("outcomesResult");

const summaryResult =
    document.getElementById("summaryResult");


let vivaQuestions = [];
let currentQuestionIndex = 0;
let vivaAnswers = [];
// Final assessment stored results
let latestAnalysisData = null;
let latestVivaEvaluation = null;
let latestProctoringReport = null;


submissionForm.addEventListener(
    "submit",
    async function (event) {

        event.preventDefault();

        const projectTitle =
            document.getElementById("projectTitle").value;

        const projectDescription =
            document.getElementById("projectDescription").value;

        const projectOutcomes =
            document.getElementById("projectOutcomes").value;

        const questionsPerSkill =
            document.getElementById("questionsPerSkill").value;

        const zipFile =
            document.getElementById("zipFile").files[0];


        if (!zipFile) {
            alert("Please select a ZIP file.");
            return;
        }


        const formData = new FormData();

        formData.append(
            "project_title",
            projectTitle
        );

        formData.append(
            "project_description",
            projectDescription
        );

        formData.append(
            "project_outcomes",
            projectOutcomes
        );

        formData.append(
            "questions_per_skill",
            questionsPerSkill
        );

        formData.append(
            "zip_file",
            zipFile
        );


        loadingSection.classList.remove("hidden");
        resultSection.classList.add("hidden");


        try {

            const response = await fetch(
                "/analyze-submission",
                {
                    method: "POST",
                    body: formData
                }
            );

            const data = await response.json();

            extractVivaQuestions(data);

            if (!response.ok) {
                throw new Error(
                    data.detail || "Project analysis failed"
                );
            }

            // reset previous session/final results when analyzing a new project
            latestAnalysisData = null;
            latestVivaEvaluation = null;
            latestProctoringReport = null;
            if (finalAssessmentSection) finalAssessmentSection.classList.add("hidden");
            if (vivaEvaluationSection) vivaEvaluationSection.style.display = "none";
            if (proctoringResultSection) proctoringResultSection.classList.add("hidden");

            latestAnalysisData = data;
            displayAnalysisResults(data);

            resultSection.classList.remove("hidden");

            resultSection.scrollIntoView({
                behavior: "smooth"
            });

        }
        catch (error) {

            alert(
                "Analysis Error: " + error.message
            );

        }
        finally {

            loadingSection.classList.add("hidden");

        }
    }
);


function displayAnalysisResults(data) {

    displayProjectInformation(data);

    displaySkills(data.suggested_skills);

    displayQuestions(
        data.evaluation_report.skills
    );

    displayOutcomes(
        data.evaluation_report.summary
            .outcome_evaluation
    );

    displaySummary(
        data.evaluation_report.summary
    );
}


function displayProjectInformation(data) {

    projectInfo.innerHTML = `
        <p>
            <strong>Project:</strong>
            ${escapeHtml(data.project_title)}
        </p>

        <p>
            <strong>Description:</strong>
            ${escapeHtml(
                data.project_description ||
                "No description provided"
            )}
        </p>

        <p>
            <strong>ZIP File:</strong>
            ${escapeHtml(data.zip_filename)}
        </p>

        <p>
            <strong>Files Analyzed:</strong>
            ${data.zip_analysis.files_analyzed}
        </p>
    `;
}


function displaySkills(skills) {

    skillsResult.innerHTML = "";

    if (!skills || skills.length === 0) {

        skillsResult.innerHTML =
            "<p>No skills were detected.</p>";

        return;
    }


    skills.forEach(function (skill) {

        const confidencePercentage =
            Math.round(skill.confidence * 100);

        const skillCard =
            document.createElement("div");

        skillCard.className = "skill-card";

        skillCard.innerHTML = `
            <div class="skill-header">

                <strong>
                    ${escapeHtml(skill.skill_name)}
                </strong>

                <span class="confidence-badge">
                    ${confidencePercentage}%
                </span>

            </div>

            <div class="progress-bar">

                <div
                    class="progress-fill"
                    style="width:
                    ${confidencePercentage}%"
                >
                </div>

            </div>

            <p>
                ${escapeHtml(skill.rationale)}
            </p>
        `;

        skillsResult.appendChild(skillCard);
    });
}


function displayQuestions(skills) {

    questionsResult.innerHTML = "";

    if (!skills || skills.length === 0) {

        questionsResult.innerHTML =
            "<p>No viva questions generated.</p>";

        return;
    }


    skills.forEach(function (skill) {

        const questionGroup =
            document.createElement("div");

        questionGroup.className =
            "question-group";

        const heading =
            document.createElement("h4");

        heading.textContent =
            skill.skill_name;

        questionGroup.appendChild(heading);


        skill.questions.forEach(
            function (question, index) {

                const questionCard =
                    document.createElement("div");

                questionCard.className =
                    "question-card";

                questionCard.innerHTML = `
                    <span class="question-type">
                        ${escapeHtml(question.type)}
                    </span>

                    <p>
                        <strong>
                            Question ${index + 1}:
                        </strong>

                        ${escapeHtml(question.question)}
                    </p>

                    ${
                        question.evidence_file
                        ?
                        `
                        <small>
                            Evidence:
                            ${escapeHtml(
                                question.evidence_file
                            )}
                        </small>
                        `
                        :
                        ""
                    }
                `;

                questionGroup.appendChild(
                    questionCard
                );
            }
        );

        questionsResult.appendChild(
            questionGroup
        );
    });
}


function displayOutcomes(outcomes) {

    outcomesResult.innerHTML = "";

    if (!outcomes || outcomes.length === 0) {

        outcomesResult.innerHTML =
            "<p>No outcomes were evaluated.</p>";

        return;
    }


    outcomes.forEach(function (outcome) {

        const outcomeCard =
            document.createElement("div");

        outcomeCard.className =
            "outcome-card";

        const evidenceText =
            outcome.evidence.length > 0
            ?
            outcome.evidence.join(", ")
            :
            "No evidence found";


        outcomeCard.innerHTML = `
            <div class="outcome-header">

                <strong>
                    ${escapeHtml(outcome.outcome)}
                </strong>

                <span
                    class="status-badge
                    status-${escapeHtml(outcome.status)}"
                >
                    ${escapeHtml(outcome.status)}
                </span>

            </div>

            <p>
                <strong>Evidence:</strong>
                ${escapeHtml(evidenceText)}
            </p>

            ${
                outcome.gap
                ?
                `
                <p>
                    <strong>Gap:</strong>
                    ${escapeHtml(outcome.gap)}
                </p>
                `
                :
                ""
            }
        `;

        outcomesResult.appendChild(
            outcomeCard
        );
    });
}


function displaySummary(summary) {

    const scorePercentage =
        Math.round(
            summary.alignment_score * 100
        );


    const strengthsHtml =
        summary.strengths.length > 0
        ?
        summary.strengths
            .map(
                strength =>
                `<li>${escapeHtml(strength)}</li>`
            )
            .join("")
        :
        "<li>No strengths identified.</li>";


    const gapsHtml =
        summary.gaps.length > 0
        ?
        summary.gaps
            .map(
                gap =>
                `<li>${escapeHtml(gap)}</li>`
            )
            .join("")
        :
        "<li>No major gaps identified.</li>";


    summaryResult.innerHTML = `

        <div class="score-container">

            <div class="score-circle">
                ${scorePercentage}%
            </div>

            <div>

                <h4>
                    Overall Alignment:
                    ${escapeHtml(
                        summary.overall_alignment
                    )}
                </h4>

                <p>
                    ${escapeHtml(summary.narrative)}
                </p>

            </div>

        </div>


        <div class="summary-columns">

            <div>

                <h4>Strengths</h4>

                <ul>
                    ${strengthsHtml}
                </ul>

            </div>


            <div>

                <h4>Gaps</h4>

                <ul>
                    ${gapsHtml}
                </ul>

            </div>

        </div>
    `;
}


function escapeHtml(value) {

    const element =
        document.createElement("div");

    element.textContent =
        String(value ?? "");

    return element.innerHTML;
}

// --------------------------------------------------
// VIVA SESSION
// --------------------------------------------------

const startVivaButton =
    document.getElementById("startVivaButton");

const endVivaButton =
    document.getElementById("endVivaButton");

const sessionStatus =
    document.getElementById("sessionStatus");

const sessionIdDisplay =
    document.getElementById("sessionIdDisplay");

const vivaWarning =
    document.getElementById("vivaWarning");

const proctoringResultSection =
    document.getElementById("proctoringResultSection");

const proctoringResult =
    document.getElementById("proctoringResult");

// Viva evaluation UI elements
const vivaEvaluationSection =
    document.getElementById("vivaEvaluationSection");

const vivaScoreCircle =
    document.getElementById("vivaScoreCircle");

const vivaPerformanceLevel =
    document.getElementById("vivaPerformanceLevel");

const vivaTotalQuestions =
    document.getElementById("vivaTotalQuestions");

const evaluatedAnswersContainer =
    document.getElementById("evaluatedAnswersContainer");

// Final assessment element references
const finalAssessmentSection =
    document.getElementById("finalAssessmentSection");

const finalProjectScore =
    document.getElementById("finalProjectScore");

const finalVivaScore =
    document.getElementById("finalVivaScore");

const finalIntegrityScore =
    document.getElementById("finalIntegrityScore");

const finalOverallScore =
    document.getElementById("finalOverallScore");

const finalPerformanceLevel =
    document.getElementById("finalPerformanceLevel");

const finalRiskLevel =
    document.getElementById("finalRiskLevel");

const finalRecommendation =
    document.getElementById("finalRecommendation");

const finalStrengths =
    document.getElementById("finalStrengths");

const finalGaps =
    document.getElementById("finalGaps");


let activeSessionId = null;

let vivaActive = false;

let cameraStream = null;

let faceDetector = null;
let faceDetectionInterval = null;
let faceDetectionRunning = false;
let lastVideoTime = -1;
let lastNoFaceEventTime = 0;
let lastMultipleFaceEventTime = 0;

const FACE_EVENT_COOLDOWN = 10000;


const cameraSection =
    document.getElementById("cameraSection");

const cameraVideo =
    document.getElementById("cameraVideo");

const cameraStatus =
    document.getElementById("cameraStatus");

const questionProgress =
    document.getElementById("questionProgress");

const questionType =
    document.getElementById("questionType");

const currentQuestion =
    document.getElementById("currentQuestion");

const questionSkill =
    document.getElementById("questionSkill");

const vivaAnswer =
    document.getElementById("vivaAnswer");

const nextQuestionButton =
    document.getElementById("nextQuestionButton");


// --------------------------------------------------
// START VIVA
// --------------------------------------------------

startVivaButton.addEventListener(
    "click",
    async function () {

        try {

            // ---------------------------------------
            // CHECK PROJECT ANALYSIS
            // ---------------------------------------

            if (!latestAnalysisData) {

                throw new Error(
                    "Please analyze the project before starting the viva."
                );

            }


            // ---------------------------------------
            // START VIVA SESSION
            // ---------------------------------------

            const response = await fetch(
                "/viva-session/start",
                {
                    method: "POST"
                }
            );


            const data = await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Unable to start viva"
                );

            }


            // ---------------------------------------
            // SAVE SESSION ID
            // ---------------------------------------

            activeSessionId =
                data.session_id;


            console.log(
                "Viva Session Created:",
                activeSessionId
            );


            // ---------------------------------------
            // STORE PROJECT ANALYSIS
            // ---------------------------------------

            const analysisResponse = await fetch(
                "/viva-session/project-analysis",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        session_id:
                            activeSessionId,

                        project_analysis:
                            latestAnalysisData

                    })
                }
            );


            const analysisData =
                await analysisResponse.json();


            if (!analysisResponse.ok) {

                throw new Error(
                    analysisData.detail ||
                    "Unable to store project analysis"
                );

            }


            console.log(
                "Project Analysis Stored:",
                analysisData
            );


            // ---------------------------------------
            // ACTIVATE VIVA
            // ---------------------------------------

            vivaActive = true;


            sessionStatus.textContent =
                "Viva session is active.";


            sessionIdDisplay.textContent =
                activeSessionId;


            // ---------------------------------------
            // RESET QUESTIONS AND ANSWERS
            // ---------------------------------------

            currentQuestionIndex = 0;

            vivaAnswers = [];


            displayCurrentQuestion();


            // ---------------------------------------
            // UPDATE BUTTONS
            // ---------------------------------------

            startVivaButton.disabled = true;

            endVivaButton.disabled = false;


            // ---------------------------------------
            // HIDE OLD PROCTORING REPORT
            // ---------------------------------------

            proctoringResultSection
                .classList.add("hidden");


            // ---------------------------------------
            // DISPLAY MESSAGE
            // ---------------------------------------

            showVivaWarning(
                "Viva started. Browser activity is now being monitored."
            );


            // ---------------------------------------
            // START CAMERA
            // ---------------------------------------

            const cameraStarted =
                await startCamera();


            if (!cameraStarted) {

                await sendProctoringEvent(
                    "face_not_detected",
                    0,
                    1.0
                );

            }


            // ---------------------------------------
            // ENTER FULLSCREEN
            // ---------------------------------------

            await enterFullscreen();

        }

        catch (error) {

            console.error(
                "Start Viva Error:",
                error
            );


            alert(
                "Start Viva Error: " +
                error.message
            );

        }

    }
);


// --------------------------------------------------
// END VIVA
// --------------------------------------------------

endVivaButton.addEventListener(
    "click",
    async function () {

        if (!activeSessionId) {
            return;
        }


        try {

            // Stop event monitoring before
            // intentionally leaving fullscreen.
            vivaActive = false;


            stopCamera();


            const response = await fetch(
                "/viva-session/end",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        session_id:
                            activeSessionId
                    })
                }
            );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Unable to end viva"
                );

            }


            displayProctoringReport(
                data.proctoring_report
            );
            // Generate final assessment combining analysis, viva, and proctoring
            try {
                await generateFinalAssessment();
            }
            catch (e) {
                console.error("Final assessment generation failed:", e);
            }


            sessionStatus.textContent =
                "Viva session completed.";


            startVivaButton.disabled = false;

            endVivaButton.disabled = true;


            proctoringResultSection
                .classList.remove("hidden");


            proctoringResultSection
                .scrollIntoView({
                    behavior: "smooth"
                });


            if (document.fullscreenElement) {

                await document.exitFullscreen();

            }


            activeSessionId = null;

        }
        catch (error) {

            // Restore monitoring because
            // ending the session failed.
            vivaActive = true;

            alert(
                "End Viva Error: " +
                error.message
            );

        }
    }
);


// --------------------------------------------------
// SEND PROCTORING EVENT
// --------------------------------------------------

async function sendProctoringEvent(
    eventType,
    durationMs = null,
    confidence = null
) {

    if (!vivaActive || !activeSessionId) {
        return;
    }


    try {

        const response = await fetch(
            "/viva-session/event",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

                    session_id:
                        activeSessionId,

                    event_type:
                        eventType,

                    duration_ms:
                        durationMs,

                    confidence:
                        confidence

                })
            }
        );


        if (!response.ok) {

            const data =
                await response.json();

            console.error(
                "Proctoring event error:",
                data
            );

        }

    }
    catch (error) {

        console.error(
            "Unable to send proctoring event:",
            error
        );

    }
}


// --------------------------------------------------
// TAB SWITCH DETECTION
// --------------------------------------------------

document.addEventListener(
    "visibilitychange",
    function () {

        if (
            vivaActive &&
            document.hidden
        ) {

            sendProctoringEvent(
                "tab_switched",
                0,
                1.0
            );


            showVivaWarning(
                "Warning: Tab switching detected."
            );

        }
    }
);


// --------------------------------------------------
// FULLSCREEN EXIT DETECTION
// --------------------------------------------------

document.addEventListener(
    "fullscreenchange",
    function () {

        if (
            vivaActive &&
            !document.fullscreenElement
        ) {

            sendProctoringEvent(
                "fullscreen_exited",
                0,
                1.0
            );


            showVivaWarning(
                "Warning: Fullscreen mode was exited."
            );

        }
    }
);


// --------------------------------------------------
// PASTE ATTEMPT DETECTION
// --------------------------------------------------

document.addEventListener(
    "paste",
    function () {

        if (vivaActive) {

            sendProctoringEvent(
                "paste_attempted",
                0,
                1.0
            );


            showVivaWarning(
                "Warning: Paste attempt detected."
            );

        }
    }
);


// --------------------------------------------------
// ENTER FULLSCREEN
// --------------------------------------------------

async function enterFullscreen() {

    try {

        if (!document.fullscreenElement) {

            await document.documentElement
                .requestFullscreen();

        }

    }
    catch (error) {

        console.log(
            "Fullscreen permission was not granted."
        );

    }
}


// --------------------------------------------------
// DISPLAY WARNING
// --------------------------------------------------

function showVivaWarning(message) {

    vivaWarning.textContent = message;

    vivaWarning.classList.remove("hidden");


    setTimeout(
        function () {

            vivaWarning.classList.add(
                "hidden"
            );

        },
        4000
    );
}


// --------------------------------------------------
// DISPLAY PROCTORING REPORT
// --------------------------------------------------

async function startCamera() {

    try {

        cameraStream =
            await navigator.mediaDevices.getUserMedia({

                video: {
                    width: {
                        ideal: 640
                    },

                    height: {
                        ideal: 480
                    },

                    facingMode: "user"
                },

                audio: false

            });


        cameraVideo.srcObject =
            cameraStream;


        cameraSection.classList.remove(
            "hidden"
        );


        cameraStatus.textContent =
            "Camera active";


        await cameraVideo.play();


        await startFaceMonitoring();


        return true;

    }
    catch (error) {

        console.error(
            "Camera error:",
            error
        );


        cameraSection.classList.remove(
            "hidden"
        );


        cameraStatus.textContent =
            "Camera permission denied or unavailable";


        showVivaWarning(
            "Camera could not be started."
        );


        return false;

    }

}


// --------------------------------------------------
// STOP CAMERA
// --------------------------------------------------

function stopCamera() {

    stopFaceMonitoring();

    if (faceDetector) {
        faceDetector.close();
        faceDetector = null;
    }

    lastNoFaceEventTime = 0;
    lastMultipleFaceEventTime = 0;

    if (cameraStream) {

        cameraStream
            .getTracks()
            .forEach(
                function (track) {

                    track.stop();

                }
            );


        cameraStream = null;

    }


    cameraVideo.srcObject = null;


    cameraStatus.textContent =
        "Camera inactive";


    cameraSection.classList.add(
        "hidden"
    );

}


// --------------------------------------------------
// DISPLAY PROCTORING REPORT
// --------------------------------------------------

function displayProctoringReport(report) {
    latestProctoringReport = report;

    const score =
        Math.round(
            report.integrity_score * 100
        );


    const flags =
        Object.entries(
            report.flag_summary
        );


    const flagHtml =
        flags.length > 0
        ?
        flags.map(
            function ([eventType, count]) {

                return `
                    <li>
                        ${escapeHtml(eventType)}
                        :
                        ${count}
                    </li>
                `;

            }
        ).join("")
        :
        "<li>No proctoring flags detected.</li>";


    proctoringResult.innerHTML = `

        <div class="score-container">

            <div class="score-circle">
                ${score}%
            </div>


            <div>

                <h3>
                    Integrity Score
                </h3>

                <p>
                    <strong>Risk Level:</strong>

                    ${escapeHtml(
                        report.risk_level
                    )}
                </p>

                <p>
                    <strong>ID Check:</strong>

                    ${escapeHtml(
                        report.id_check
                    )}
                </p>

            </div>

        </div>


        <div class="result-box">

            <h3>
                Flag Summary
            </h3>

            <ul>
                ${flagHtml}
            </ul>

        </div>
    `;
}


// --------------------------------------------------
// INITIALIZE MEDIAPIPE FACE DETECTOR
// --------------------------------------------------

async function initializeFaceDetector() {

    try {

        cameraStatus.textContent =
            "Loading AI face detector...";


        const vision =
            await FilesetResolver.forVisionTasks(
                "/static/mediapipe/wasm"
            );


        faceDetector =
            await FaceDetector.createFromOptions(

                vision,

                {

                    baseOptions: {

                        modelAssetPath:

                            "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite",

                        delegate: "GPU"

                    },


                    runningMode: "VIDEO",


                    minDetectionConfidence: 0.5

                }

            );


        cameraStatus.textContent =
            "AI face detector ready";


        return true;

    }
    catch (error) {

        console.error(
            "MediaPipe initialization error:",
            error
        );


        cameraStatus.textContent =
            "Face detector initialization failed";


        return false;

    }

}


// --------------------------------------------------
// START FACE MONITORING
// --------------------------------------------------

async function startFaceMonitoring() {

    const detectorReady =
        await initializeFaceDetector();


    if (!detectorReady) {

        showVivaWarning(
            "Face detection could not be started."
        );

        return;

    }


    stopFaceMonitoring();


    faceDetectionRunning = true;


    faceDetectionInterval =
        setInterval(

            detectFaces,

            1000

        );

}


// --------------------------------------------------
// DETECT FACES
// --------------------------------------------------

async function detectFaces() {

    if (
        !vivaActive ||
        !faceDetector ||
        !faceDetectionRunning ||
        cameraVideo.readyState < 2
    ) {

        return;

    }


    try {

        if (
            cameraVideo.currentTime ===
            lastVideoTime
        ) {

            return;

        }


        lastVideoTime =
            cameraVideo.currentTime;


        const currentTimestamp =
            performance.now();


        const result =
            faceDetector.detectForVideo(

                cameraVideo,

                currentTimestamp

            );


        const faces =
            result.detections || [];


        const faceCount =
            faces.length;


        if (faceCount === 1) {

            cameraStatus.textContent =
                "1 face detected";

        }


        else if (faceCount === 0) {

            cameraStatus.textContent =
                "Warning: No face detected";


            const currentTime =
                Date.now();


            if (

                currentTime -
                lastNoFaceEventTime

                >=

                FACE_EVENT_COOLDOWN

            ) {


                await sendProctoringEvent(

                    "face_not_detected",

                    0,

                    1.0

                );


                lastNoFaceEventTime =
                    currentTime;


                showVivaWarning(

                    "Warning: No face detected."

                );

            }

        }


        else {

            cameraStatus.textContent =
                `${faceCount} faces detected`;


            const currentTime =
                Date.now();


            if (

                currentTime -
                lastMultipleFaceEventTime

                >=

                FACE_EVENT_COOLDOWN

            ) {


                await sendProctoringEvent(

                    "multiple_faces_detected",

                    0,

                    1.0

                );


                lastMultipleFaceEventTime =
                    currentTime;


                showVivaWarning(

                    "Warning: Multiple faces detected."

                );

            }

        }

    }
    catch (error) {

        console.error(

            "MediaPipe face detection error:",

            error

        );

    }

}


// --------------------------------------------------
// STOP FACE MONITORING
// --------------------------------------------------

function stopFaceMonitoring() {

    faceDetectionRunning = false;


    if (faceDetectionInterval) {

        clearInterval(
            faceDetectionInterval
        );


        faceDetectionInterval = null;

    }


    lastVideoTime = -1;

}


// --------------------------------------------------
// VIVA QUESTION HELPERS
// --------------------------------------------------

function extractVivaQuestions(analysisData) {
    vivaQuestions = [];
    const skills =
        analysisData?.evaluation_report?.skills || [];
    skills.forEach((skill) => {
        const skillName =
            skill.skill_name || "General";
        const questions =
            skill.questions || [];
        questions.forEach((question) => {
            vivaQuestions.push({
                skillName: skillName,
                type:
                    question.type || "general",
                question:
                    question.question || "Question unavailable",
                evidenceFile:
                    question.evidence_file || null
            });
        });
    });
    console.log(
        "Extracted Viva Questions:",
        vivaQuestions
    );
}


function displayCurrentQuestion() {
    if (vivaQuestions.length === 0) {
        questionProgress.textContent =
            "No viva questions available";
        questionType.textContent =
            "No Question";
        currentQuestion.textContent =
            "Analyze a project before starting the viva.";
        questionSkill.textContent = "";
        vivaAnswer.disabled = true;
        nextQuestionButton.disabled = true;
        return;
    }
    if (
        currentQuestionIndex >=
        vivaQuestions.length
    ) {
        completeVivaQuestions();
        return;
    }
    const question =
        vivaQuestions[currentQuestionIndex];
    questionProgress.textContent =
        `Question ${currentQuestionIndex + 1} of ${vivaQuestions.length}`;
    questionType.textContent =
        question.type;
    currentQuestion.textContent =
        question.question;
    questionSkill.textContent =
        `Skill: ${question.skillName}`;
    vivaAnswer.value = "";
    vivaAnswer.disabled = false;
    nextQuestionButton.disabled = false;
    if (
        currentQuestionIndex ===
        vivaQuestions.length - 1
    ) {
        nextQuestionButton.textContent =
            "Submit Final Answer";
    }
    else {
        nextQuestionButton.textContent =
            "Submit Answer & Next";
    }
}


function submitCurrentAnswer() {
    if (!vivaActive) {
        showVivaWarning(
            "Start the viva before answering questions."
        );
        return;
    }
    const answer =
        vivaAnswer.value.trim();
    if (!answer) {
        showVivaWarning(
            "Please enter an answer before continuing."
        );
        return;
    }
    const question =
        vivaQuestions[currentQuestionIndex];
    vivaAnswers.push({
        questionNumber:
            currentQuestionIndex + 1,
        skillName:
            question.skillName,
        type:
            question.type,
        question:
            question.question,
        answer:
            answer,
        evidenceFile:
            question.evidenceFile
    });
    console.log(
        "Answer Submitted:",
        vivaAnswers[vivaAnswers.length - 1]
    );
    currentQuestionIndex++;
    displayCurrentQuestion();
}


function completeVivaQuestions() {
    questionProgress.textContent =
        "All questions completed";
    questionType.textContent =
        "Evaluating...";
    currentQuestion.textContent =
        "Your viva answers are being evaluated.";
    questionSkill.textContent = "";
    vivaAnswer.value = "";
    vivaAnswer.disabled = true;
    nextQuestionButton.disabled = true;
    console.log(
        "Final Viva Answers:",
        vivaAnswers
    );
    (async function () {
        const evaluationData =
            await evaluateVivaAnswers();
        if (evaluationData) {
            displayVivaEvaluation(
                evaluationData
            );
            questionType.textContent =
                "Completed";
            currentQuestion.textContent =
                "Viva evaluation completed. Click End Viva to finish the session.";
        }
        else {
            questionType.textContent =
                "Evaluation Failed";
            currentQuestion.textContent =
                "Answers were completed, but evaluation failed.";
        }
    })();
}


nextQuestionButton.addEventListener(
    "click",
    submitCurrentAnswer
);


// --------------------------------------------------
// VIVA EVALUATION: Request + Display
// --------------------------------------------------

async function evaluateVivaAnswers() {
    if (!activeSessionId) {
        showVivaWarning("No active viva session found.");
        return null;
    }
    if (vivaAnswers.length === 0) {
        showVivaWarning("No viva answers available for evaluation.");
        return null;
    }
    try {
        const response = await fetch(
            "/viva-session/evaluate",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    session_id: activeSessionId,
                    answers: vivaAnswers
                })
            }
        );
        const data = await response.json();
        if (!response.ok) {
            console.error("Viva evaluation failed:", data);
            showVivaWarning("Viva evaluation failed.");
            return null;
        }
        console.log("Viva Evaluation Result:", data);
        return data;
    }
    catch (error) {
        console.error(
            "Viva evaluation request error:",
            error
        );
        showVivaWarning(
            "Unable to evaluate viva answers."
        );
        return null;
    }
}


function displayVivaEvaluation(data) {
    if (!data || !data.evaluation) {
        return;
    }
    const evaluation = data.evaluation;
    latestVivaEvaluation = evaluation;
    if (vivaEvaluationSection) {
        vivaEvaluationSection.style.display = "block";
    }
    if (vivaScoreCircle) {
        vivaScoreCircle.textContent = `${evaluation.average_score}%`;
    }
    if (vivaPerformanceLevel) {
        vivaPerformanceLevel.textContent = evaluation.performance_level;
    }
    if (vivaTotalQuestions) {
        vivaTotalQuestions.textContent = evaluation.total_questions;
    }
    if (evaluatedAnswersContainer) {
        evaluatedAnswersContainer.innerHTML = "";
        evaluation.evaluated_answers.forEach((item) => {
            const card = document.createElement("div");
            card.className = "evaluated-answer-card";
            const title = document.createElement("h3");
            title.textContent = `Question ${item.question_number}`;
            const question = document.createElement("p");
            const questionLabel = document.createElement("strong");
            questionLabel.textContent = "Question: ";
            question.appendChild(questionLabel);
            question.appendChild(document.createTextNode(item.question));
            const answer = document.createElement("p");
            const answerLabel = document.createElement("strong");
            answerLabel.textContent = "Your Answer: ";
            answer.appendChild(answerLabel);
            answer.appendChild(document.createTextNode(item.candidate_answer));
            const score = document.createElement("p");
            score.className = "answer-score";
            score.textContent = `Score: ${item.score}%`;
            const feedback = document.createElement("p");
            feedback.className = "answer-feedback";
            feedback.textContent = `Feedback: ${item.feedback}`;
            card.appendChild(title);
            card.appendChild(question);
            card.appendChild(answer);
            card.appendChild(score);
            card.appendChild(feedback);
            evaluatedAnswersContainer.appendChild(card);
        });
        vivaEvaluationSection?.scrollIntoView({ behavior: "smooth" });
    }
}


// --------------------------------------------------
// FINAL ASSESSMENT GENERATOR
// --------------------------------------------------

async function generateFinalAssessment() {
    if (!activeSessionId) {
        console.error(
            "No active session ID available."
        );
        return;
    }
    try {
        const response = await fetch(
            "/final-assessment",
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify({
                    session_id:
                        activeSessionId
                })
            }
        );
        const data =
            await response.json();
        if (!response.ok) {
            throw new Error(
                data.detail ||
                "Final assessment generation failed"
            );
        }
        console.log(
            "Final Assessment Result:",
            data
        );
        displayFinalAssessment(
            data.final_assessment
        );
    }
    catch (error) {
        console.error(
            "Final assessment error:",
            error
        );
        showVivaWarning(
            "Unable to generate final assessment."
        );
    }
}


function displayFinalAssessment(assessment) {
    finalProjectScore.textContent =
        `${Math.round(
            assessment.project_score
        )}%`;
    finalVivaScore.textContent =
        `${Math.round(
            assessment.viva_score
        )}%`;
    finalIntegrityScore.textContent =
        `${Math.round(
            assessment.integrity_score
        )}%`;
    finalOverallScore.textContent =
        `${Math.round(
            assessment.overall_score
        )}%`;
    finalPerformanceLevel.textContent =
        assessment.performance_level;
    finalRiskLevel.textContent =
        assessment.risk_level;
    finalRecommendation.textContent =
        assessment.recommendation;
    // -------------------------------
    // DISPLAY STRENGTHS
    // -------------------------------
    finalStrengths.innerHTML = "";
    const strengths =
        assessment.strengths || [];
    if (strengths.length === 0) {
        const item =
            document.createElement("li");
        item.textContent =
            "No specific strengths identified.";
        finalStrengths.appendChild(
            item
        );
    }
    else {
        strengths.forEach(
            function (strength) {
                const item =
                    document.createElement("li");
                item.textContent =
                    strength;
                finalStrengths.appendChild(
                    item
                );
            }
        );
    }
    // -------------------------------
    // DISPLAY GAPS
    // -------------------------------
    finalGaps.innerHTML = "";
    const gaps =
        assessment.gaps || [];
    if (gaps.length === 0) {
        const item =
            document.createElement("li");
        item.textContent =
            "No major gaps identified.";
        finalGaps.appendChild(
            item
        );
    }
    else {
        gaps.forEach(
            function (gap) {
                const item =
                    document.createElement("li");
                item.textContent =
                    gap;
                finalGaps.appendChild(
                    item
                );
            }
        );
    }
    finalAssessmentSection
        .classList.remove("hidden");
    finalAssessmentSection
        .scrollIntoView({
            behavior: "smooth"
        });
}