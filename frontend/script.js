document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('analyze-form');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = submitBtn.querySelector('.btn-text');
    const resultsSection = document.getElementById('results-section');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // UI State: Loading
        submitBtn.disabled = true;
        btnText.textContent = 'Analyzing...';
        
        resultsSection.innerHTML = `
            <div class="card loading-card">
                <div class="spinner"></div>
                <h3>Analyzing Submission</h3>
                <p>Reading code files, running static scanner rules, and mapping skill outcomes. Please wait...</p>
            </div>
        `;

        const formData = new FormData(form);

        try {
            // Determine backend URL: if running from file:// or a different port (e.g. Live Server),
            // target the backend port (default 8000). Otherwise, use a relative path.
            let backendUrl = '/api/v1/analyze-submission';
            if (window.location.protocol === 'file:' || (window.location.port && window.location.port !== '8000')) {
                backendUrl = 'http://localhost:8000/api/v1/analyze-submission';
            }

            // Send request to backend
            const response = await fetch(backendUrl, {
                method: 'POST',
                body: formData,
            });

            // Read body as text first to avoid crashing if it's empty or not JSON
            const responseText = await response.text();
            let data = null;
            try {
                if (responseText) {
                    data = JSON.parse(responseText);
                }
            } catch (e) {
                console.error("Failed to parse response JSON:", e);
            }

            if (!response.ok) {
                let errorMsg = 'An error occurred during analysis.';
                if (data && data.error && data.error.message) {
                    errorMsg = data.error.message;
                } else {
                    errorMsg = responseText || `HTTP Error ${response.status}: ${response.statusText}`;
                }
                throw new Error(errorMsg);
            }

            if (!data) {
                throw new Error('Received an empty or invalid response from the server.');
            }

            renderResults(data);

        } catch (error) {
            resultsSection.innerHTML = `
                <div class="card error-card">
                    <div class="error-title">Analysis Failed</div>
                    <div class="error-message">${error.message}</div>
                </div>`;
        } finally {
            // UI State: Reset
            submitBtn.disabled = false;
            btnText.textContent = 'Analyze Project';
        }
    });

    function renderResults(data) {
        let html = `
            <div class="analysis-header">
                <h2>Analysis Results: ${data.project_title}</h2>
                <div class="analysis-meta">Processed in ${data.metadata.processing_time_ms}ms | Files Analyzed: ${data.metadata.files_analyzed}</div>
            </div>
        `;

        // 1. Summary Card
        if (data.evaluation_report && data.evaluation_report.summary) {
            const summary = data.evaluation_report.summary;
            
            const strengthsLi = summary.strengths && summary.strengths.length > 0
                ? summary.strengths.map(s => `<li>${s}</li>`).join('')
                : '<li>No specific strengths highlighted.</li>';
                
            const gapsLi = summary.gaps && summary.gaps.length > 0
                ? summary.gaps.map(g => `<li>${g}</li>`).join('')
                : '<li>No gaps identified.</li>';
            
            let statusClass = 'status-neutral';
            if (summary.overall_alignment === 'strong') statusClass = 'status-strong';
            else if (summary.overall_alignment === 'partial') statusClass = 'status-partial';
            else if (summary.overall_alignment === 'weak') statusClass = 'status-weak';

            html += `
                <div class="section-card">
                    <div class="score-card-hero">
                        <div class="score-hero-info">
                            <span class="score-hero-label">Alignment Score</span>
                            <span class="score-hero-val">${Math.round(summary.alignment_score * 100)}%</span>
                        </div>
                        <span class="score-status-badge ${statusClass}">
                            ${summary.overall_alignment.toUpperCase()}
                        </span>
                    </div>
                    <div class="hero-progress-container">
                        <div class="hero-progress-fill ${statusClass}" style="width: ${Math.round(summary.alignment_score * 100)}%;"></div>
                    </div>
                    
                    <p class="summary-narrative">${summary.narrative}</p>
                    
                    <div class="summary-callouts">
                        <div class="callout-card strength-callout">
                            <div class="callout-header">Key Strengths</div>
                            <ul class="callout-list strengths-list">${strengthsLi}</ul>
                        </div>
                        <div class="callout-card gap-callout">
                            <div class="callout-header">Gaps Detected</div>
                            <ul class="callout-list gaps-list">${gapsLi}</ul>
                        </div>
                    </div>
                </div>
            `;
        }

        // 2. Outcome Alignment Sheet
        if (data.evaluation_report && data.evaluation_report.outcome_evaluation && data.evaluation_report.outcome_evaluation.length > 0) {
            const outcomesHtml = data.evaluation_report.outcome_evaluation.map(outcome => {
                const statusLabel = outcome.status.replace('_', ' ');
                
                let gapHtml = '';
                if (outcome.gap) {
                    gapHtml = `
                        <div class="outcome-row-detail gap-detail">
                            <span class="detail-label">Gap:</span>
                            <span class="detail-text">${outcome.gap}</span>
                        </div>
                    `;
                }
                
                return `
                    <div class="outcome-row-item">
                        <div class="outcome-row-header">
                            <span class="outcome-row-title">${outcome.stated_outcome}</span>
                            <span class="status-indicator-inline">
                                <span class="status-dot ${outcome.status}"></span>
                                <span class="status-label-text">${statusLabel}</span>
                            </span>
                        </div>
                        <div class="outcome-row-body">
                            <div class="outcome-row-detail">
                                <span class="detail-label">Evidence:</span>
                                <span class="detail-text">${outcome.evidence}</span>
                            </div>
                            ${gapHtml}
                        </div>
                    </div>
                `;
            }).join('');

            html += `
                <div class="section-card">
                    <h3 class="section-title">Outcome Alignment Sheet</h3>
                    <div class="outcomes-table-view">${outcomesHtml}</div>
                </div>
            `;
        }

        // 3. Demonstrated Skills
        if (data.suggested_skills && data.suggested_skills.length > 0) {
            const skillsHtml = data.suggested_skills.map(skill => `
                <div class="skill-card-v2">
                    <div class="skill-info-row">
                        <span class="skill-name-v2">${skill.skill_name}</span>
                        <span class="skill-percent-v2">${Math.round(skill.confidence * 100)}% Match</span>
                    </div>
                    <div class="skill-bar-container">
                        <div class="skill-bar-fill" style="width: ${Math.round(skill.confidence * 100)}%;"></div>
                    </div>
                    <div class="skill-rationale-v2">${skill.rationale}</div>
                </div>
            `).join('');

            html += `
                <div class="section-card">
                    <h3 class="section-title">Demonstrated Skills</h3>
                    <div class="skills-grid-v2">${skillsHtml}</div>
                </div>
            `;
        }

        // 4. Suggested Viva Questions
        if (data.viva_questions && data.viva_questions.length > 0) {
            const questionsHtml = data.viva_questions.map((q, index) => `
                <details class="question-accordion" ${index === 0 ? 'open' : ''}>
                    <summary class="question-summary">
                        <span class="q-title-wrapper">
                            <span class="q-index">Q${index + 1}</span>
                            <span class="q-title-text">${q.question}</span>
                        </span>
                        <span class="q-icon-toggle"></span>
                    </summary>
                    <div class="question-content">
                        <div class="q-meta-tag">${q.skill_name} | ${q.question_type.toUpperCase()}</div>
                        <div class="q-hint-box">
                            <strong>Expected Answer Hint:</strong>
                            <p>${q.expected_answer_hint}</p>
                        </div>
                    </div>
                </details>
            `).join('');

            html += `
                <div class="section-card">
                    <h3 class="section-title">Suggested Viva Questions</h3>
                    <div class="questions-accordion-container">${questionsHtml}</div>
                </div>
            `;
        }

        resultsSection.innerHTML = html;
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
});
