# Requirements Document: ProctorAI UI/UX Rework

## Introduction

This specification defines the requirements for modernizing and polishing the ProctorAI user interface. ProctorAI is a FastAPI-based Project Submission AI Analyzer with live proctored viva sessions. The application guides students through a 4-step workflow: Upload → Consent → Viva Session → Report. The rework will enhance the visual design, improve user experience, maintain the premium dark aesthetic, and ensure accessibility while preserving all existing functionality.

## Glossary

- **ProctorAI**: The AI-powered project submission analyzer with live proctored viva sessions
- **Viva_Session**: A live interview component where AI-generated questions are asked to the student
- **Proctoring_System**: Real-time monitoring system that tracks face detection, gaze, tab switching, and other integrity signals
- **Upload_Step**: The first step where students upload project ZIP files and provide project details
- **Consent_Step**: The second step where identity verification and consent acknowledgment occurs
- **Viva_Step**: The third step where the live proctored interview takes place
- **Report_Step**: The fourth step where the final evaluation report with scoring is displayed
- **Face_API**: The face-api.js library used for client-side face detection and landmark tracking
- **Integrity_Score**: A numerical value representing the proctoring confidence and risk level
- **Alignment_Score**: A percentage indicating how well the submitted project meets expected outcomes
- **UI_Component**: A visual element or section of the interface
- **Transition**: An animated change between UI states or steps
- **Dark_Theme**: The primary color scheme using dark backgrounds (#0a0b0f) with purple accents (#6366f1)
- **Toast_Notification**: A temporary message that appears to provide feedback to the user

## Requirements

### Requirement 1: Modernize Visual Design System

**User Story:** As a student using ProctorAI, I want a modern and visually appealing interface, so that I feel confident and engaged throughout the evaluation process.

#### Acceptance Criteria

1. THE ProctorAI SHALL maintain the dark theme with purple accent color (#6366f1) as the primary visual identity
2. THE ProctorAI SHALL use consistent border-radius values (8px, 12px, 18px) across all UI components for visual harmony
3. THE ProctorAI SHALL apply subtle shadow effects (0 4px 24px rgba(0,0,0,0.4)) to elevated components for depth perception
4. THE ProctorAI SHALL use a refined color palette with proper contrast ratios for accessibility (WCAG AA minimum)
5. THE ProctorAI SHALL implement gradient accents on key interactive elements using linear-gradient(135deg, #6366f1, #818cf8)

### Requirement 2: Enhance Upload Step Interface

**User Story:** As a student, I want an intuitive and engaging file upload experience, so that I can easily submit my project for analysis.

#### Acceptance Criteria

1. WHEN a student visits the upload page, THE Upload_Step SHALL display a split-screen layout with hero content on the left and form on the right
2. WHEN a student drags a file over the drop zone, THE Upload_Step SHALL provide visual feedback with border color change and background highlight
3. WHEN a file is selected, THE Upload_Step SHALL display the filename, file size, and a success indicator
4. THE Upload_Step SHALL display real-time terminal-style logging during analysis with animated text rendering
5. THE Upload_Step SHALL show feature pills highlighting key capabilities (Secure Extraction, GPT-4o Analysis, Live Proctoring, Instant Report)

### Requirement 3: Improve Consent and Identity Verification UI

**User Story:** As a student, I want a clear and professional identity verification experience, so that I understand the proctoring process and feel secure about my privacy.

#### Acceptance Criteria

1. WHEN a student enters the consent step, THE Consent_Step SHALL display the camera viewport with animated corner brackets and a scanning line effect
2. WHEN face detection is active, THE Face_API SHALL overlay facial landmarks on the video feed in real-time
3. THE Consent_Step SHALL display a real-time JSON payload preview showing anonymized biometric signals with 1-second update intervals
4. THE Consent_Step SHALL present monitoring capabilities in card format with icons, names, and descriptions
5. WHEN identity is verified, THE ProctorAI SHALL display a full-screen modal overlay with success animation and loading bar before transitioning to viva

### Requirement 4: Enhance Viva Session Interface

**User Story:** As a student, I want a focused and distraction-free interview interface, so that I can concentrate on answering questions effectively.

#### Acceptance Criteria

1. WHEN the viva session starts, THE Viva_Step SHALL display a sticky header with session stats (elapsed time, question counter, integrity status)
2. THE Viva_Step SHALL position the camera feed and activity log in a left sidebar for continuous monitoring visibility
3. THE Viva_Step SHALL render each question in a card with a gradient accent bar, question number badge, and optional code reference block
4. THE Viva_Step SHALL provide a multi-line textarea for answers with focus states showing purple border and subtle shadow
5. THE Viva_Step SHALL display a horizontal progress bar showing completion status across all questions

### Requirement 5: Modernize Report Presentation

**User Story:** As a student, I want a comprehensive and visually appealing evaluation report, so that I can clearly understand my performance and areas for improvement.

#### Acceptance Criteria

1. WHEN the report is generated, THE Report_Step SHALL display alignment and integrity scores prominently using circular gauge visualizations
2. THE Report_Step SHALL render the alignment score gauge with animated conic-gradient from 0% to final value over 1.5 seconds
3. THE Report_Step SHALL organize skills in a responsive grid with animated progress bars and confidence percentages
4. THE Report_Step SHALL display outcomes in cards with color-coded status badges (met, partial, not_demonstrated)
5. THE Report_Step SHALL include the captured identity photo alongside proctoring metrics and activity log

### Requirement 6: Implement Smooth Transitions and Animations

**User Story:** As a student, I want smooth visual transitions between steps, so that the application feels polished and responsive.

#### Acceptance Criteria

1. WHEN transitioning between steps, THE ProctorAI SHALL apply a fadeIn animation (opacity and translateY) over 300ms
2. WHEN hovering over interactive elements, THE UI_Component SHALL respond with transform: translateY(-1px) and box-shadow enhancement within 200ms
3. WHEN a button is clicked, THE UI_Component SHALL apply transform: scale(0.97) feedback for 150ms
4. THE ProctorAI SHALL animate all data visualizations (progress bars, gauges, counters) with smooth easing functions
5. WHEN displaying the success overlay after verification, THE ProctorAI SHALL animate the modal scale and opacity simultaneously

### Requirement 7: Improve Form User Experience

**User Story:** As a student, I want clear form validation and helpful feedback, so that I can correctly complete all required fields without confusion.

#### Acceptance Criteria

1. WHEN a form field receives focus, THE UI_Component SHALL display a purple border with 3px rgba(99,102,241,0.15) box-shadow
2. WHEN a required field is empty on submission, THE ProctorAI SHALL use native browser validation with custom styling
3. THE ProctorAI SHALL mark required fields with a red asterisk (*) next to the label
4. WHEN typing in textarea fields, THE UI_Component SHALL provide adequate vertical resize capability
5. THE ProctorAI SHALL display placeholder text in a muted color (--text-3: #64748b) for all input fields

### Requirement 8: Enhance Data Visualization

**User Story:** As a student, I want clear and engaging data visualizations for my scores and metrics, so that I can quickly understand my performance.

#### Acceptance Criteria

1. WHEN displaying the alignment score, THE Report_Step SHALL use a conic-gradient circular gauge with percentage value centered
2. THE Report_Step SHALL color-code the gauge based on score ranges: green (≥80%), blue (50-79%), red (<50%)
3. WHEN rendering skill confidence levels, THE Report_Step SHALL display animated horizontal progress bars with gradient fills
4. THE Report_Step SHALL show the integrity score as a large numeric display with risk level badge (LOW, MEDIUM, HIGH)
5. THE Report_Step SHALL render the progress indicator in the viva step as segmented bars with smooth color transitions

### Requirement 9: Improve Proctoring Interface Feedback

**User Story:** As a student, I want clear visual feedback during proctoring, so that I know when the system detects potential issues.

#### Acceptance Criteria

1. WHEN face detection is active, THE Proctoring_System SHALL draw a yellow bounding box with 3px stroke around the detected face
2. WHEN the system detects no face for more than 2 seconds, THE ProctorAI SHALL log the event and display a toast notification
3. WHEN tab switching is detected, THE Proctoring_System SHALL log the event with timestamp in the activity sidebar
4. THE Viva_Step SHALL display activity log entries with time-based color coding (clean, low, medium, high severity)
5. WHEN multiple faces are detected, THE Proctoring_System SHALL immediately log a high-severity event with toast notification

### Requirement 10: Enhance Accessibility and Responsiveness

**User Story:** As a student using assistive technologies or different devices, I want an accessible and responsive interface, so that I can use ProctorAI effectively regardless of my situation.

#### Acceptance Criteria

1. THE ProctorAI SHALL ensure all interactive elements have sufficient color contrast ratios meeting WCAG 2.1 Level AA standards (minimum 4.5:1 for normal text)
2. THE ProctorAI SHALL support keyboard navigation for all interactive components with visible focus indicators
3. WHEN viewing on different screen sizes, THE UI_Component SHALL adjust layouts using CSS media queries and flexible grid systems
4. THE ProctorAI SHALL provide semantic HTML structure with proper heading hierarchy (h1, h2, h3) for screen readers
5. THE ProctorAI SHALL ensure all images and icons have appropriate aria-labels or alt text for screen reader users

### Requirement 11: Improve Toast Notification System

**User Story:** As a student, I want timely and non-intrusive notifications, so that I stay informed about system events without losing focus.

#### Acceptance Criteria

1. WHEN a system event occurs, THE Toast_Notification SHALL slide in from the top-right corner with 300ms animation
2. THE Toast_Notification SHALL display for 4 seconds before automatically dismissing with fade-out animation
3. THE ProctorAI SHALL style toast messages with color-coded backgrounds based on severity (error: red, warning: amber, success: green, info: blue)
4. THE Toast_Notification SHALL stack vertically when multiple notifications appear simultaneously
5. WHEN a toast is dismissed, THE ProctorAI SHALL animate remaining toasts to fill the gap smoothly

### Requirement 12: Enhance Button and Control Styling

**User Story:** As a student, I want clearly distinguishable and responsive buttons, so that I can confidently interact with the interface.

#### Acceptance Criteria

1. THE ProctorAI SHALL provide primary buttons with purple background, white text, and shadow effect (0 4px 20px rgba(99,102,241,0.3))
2. WHEN hovering over primary buttons, THE UI_Component SHALL lighten the background to #818cf8 and enhance shadow to 0 4px 28px
3. THE ProctorAI SHALL provide outline buttons with transparent background, 1px border, and hover effects
4. WHEN a button is disabled, THE UI_Component SHALL reduce opacity to 0.4 and show not-allowed cursor
5. THE ProctorAI SHALL provide ghost buttons for secondary actions with transparent background and subtle hover states

### Requirement 13: Improve Camera Viewport Design

**User Story:** As a student, I want a professional camera interface, so that the identity verification and monitoring feels trustworthy and secure.

#### Acceptance Criteria

1. WHEN the camera is active, THE Consent_Step SHALL display the video feed with 16:9 aspect ratio and rounded corners
2. THE Consent_Step SHALL overlay animated corner brackets in purple (#6366f1) at each corner of the viewport
3. WHEN scanning is active, THE UI_Component SHALL animate a horizontal scan line from top to bottom over 3 seconds repeatedly
4. THE Consent_Step SHALL display a status badge at the bottom center showing "ANALYZING BIOMETRICS" with pulsing green dot
5. WHEN the camera moves to the sidebar in viva, THE Viva_Step SHALL scale down the viewport while maintaining aspect ratio and overlays

### Requirement 14: Enhance Typography Hierarchy

**User Story:** As a student, I want clear and readable text throughout the application, so that I can easily consume information without eye strain.

#### Acceptance Criteria

1. THE ProctorAI SHALL use Space Grotesk font for headings and display text with font weights 400-700
2. THE ProctorAI SHALL use Inter font for body text and UI labels with font weights 300-600
3. THE ProctorAI SHALL use JetBrains Mono font for code snippets, terminal output, and numeric displays
4. THE ProctorAI SHALL apply font-smoothing (-webkit-font-smoothing: antialiased) for improved text rendering
5. THE ProctorAI SHALL implement a type scale with heading sizes from 0.68rem (labels) to 3.6rem (hero titles)

### Requirement 15: Improve Navigation and Status Indicators

**User Story:** As a student, I want clear navigation and status information, so that I always know where I am in the process and what the system is doing.

#### Acceptance Criteria

1. THE ProctorAI SHALL display a fixed top navigation bar with logo, application name, status badge, and system indicators
2. THE ProctorAI SHALL show a pulsing green dot with "System Online" or "Secure Channel" status in the navbar
3. WHEN in the viva session, THE Viva_Step SHALL display live session indicator with green pulsing dot and "LIVE SESSION" label
4. THE ProctorAI SHALL show elapsed time in mm:ss format updated every second during the viva session
5. THE ProctorAI SHALL display the current question number and total count in the header (e.g., "01 / 12")

### Requirement 16: Enhance Loading and Progress States

**User Story:** As a student, I want clear feedback during loading and processing, so that I know the system is working and not frozen.

#### Acceptance Criteria

1. WHEN analysis is running, THE Upload_Step SHALL display a spinning icon and "Analyzing..." text in the submit button
2. WHEN verification succeeds, THE Consent_Step SHALL show a loading bar that animates from 0% to 100% width over 2 seconds
3. THE ProctorAI SHALL display processing states with animated SVG spinners using CSS rotation animation
4. WHEN data is being loaded, THE UI_Component SHALL show skeleton loaders or subtle shimmer effects
5. THE ProctorAI SHALL disable interactive elements during processing and reduce opacity to indicate unavailability

### Requirement 17: Improve Code Reference Display

**User Story:** As a student, I want code snippets to be clearly formatted and readable, so that I can reference my code when answering questions.

#### Acceptance Criteria

1. WHEN a question includes code references, THE Viva_Step SHALL display a collapsible code block with dark background (#0d1117)
2. THE Viva_Step SHALL show the referenced filename in the code block header with monospace font
3. THE ProctorAI SHALL syntax-highlight code snippets with muted colors appropriate for dark theme
4. THE Viva_Step SHALL render code content in JetBrains Mono font at 0.78rem with 1.7 line-height
5. THE ProctorAI SHALL apply horizontal scrolling for code blocks that exceed container width

### Requirement 18: Enhance Skill and Outcome Cards

**User Story:** As a student, I want skill and outcome information presented in digestible cards, so that I can easily review my evaluation results.

#### Acceptance Criteria

1. WHEN displaying skills, THE Report_Step SHALL render each skill in a card with name, confidence percentage, progress bar, and rationale
2. THE Report_Step SHALL apply hover effects to skill cards (border color change and shadow enhancement)
3. WHEN showing outcomes, THE Report_Step SHALL display status badges with color coding (green: met, amber: partial, red: not_demonstrated)
4. THE Report_Step SHALL include evidence text and optional gap analysis for each outcome
5. THE ProctorAI SHALL animate skill cards with staggered fadeIn effects for visual interest

### Requirement 19: Improve Sidebar and Panel Layouts

**User Story:** As a student, I want well-organized sidebar content, so that I can monitor camera feed and activity without distraction.

#### Acceptance Criteria

1. WHEN in viva session, THE Viva_Step SHALL display a 280px fixed-width left sidebar with camera and activity log sections
2. THE Viva_Step SHALL make the activity log scrollable with custom thin scrollbar (5px width) styled to match theme
3. THE Viva_Step SHALL separate sidebar sections with small gaps and section labels in uppercase with letter-spacing
4. THE Viva_Step SHALL include a "Request Help" button at the bottom of the sidebar as a secondary action
5. THE Viva_Step SHALL apply sticky positioning to the header so it remains visible during scrolling

### Requirement 20: Enhance Report Footer Metadata

**User Story:** As a student, I want to see technical metadata about my evaluation, so that I understand the processing details and can verify the analysis depth.

#### Acceptance Criteria

1. WHEN viewing the report, THE Report_Step SHALL display a footer section with metadata including tokens used, extraction time, files analyzed, and model name
2. THE Report_Step SHALL format numeric metadata values with thousand separators (e.g., 12,450 tokens)
3. THE Report_Step SHALL display extraction time in milliseconds with "ms" unit suffix
4. THE ProctorAI SHALL include a copyright notice and disclaimer in small text below the metadata
5. THE Report_Step SHALL provide a "Download JSON" button in the navbar for exporting the full evaluation report

### Requirement 21: Improve Error Handling and Edge Cases

**User Story:** As a student, I want helpful error messages and graceful degradation, so that I can recover from issues and complete my evaluation.

#### Acceptance Criteria

1. WHEN file upload fails, THE ProctorAI SHALL display a toast notification with the specific error message
2. WHEN camera access is denied, THE Consent_Step SHALL show an error message explaining how to enable camera permissions
3. WHEN face detection models fail to load, THE ProctorAI SHALL retry loading after 500ms and log errors to console
4. WHEN no questions are generated, THE Viva_Step SHALL display a message: "No questions generated for this submission. You may end the session."
5. WHEN network requests fail, THE ProctorAI SHALL display user-friendly error messages rather than technical error strings

### Requirement 22: Enhance Micro-Interactions

**User Story:** As a student, I want subtle interactive feedback throughout the interface, so that the application feels responsive and polished.

#### Acceptance Criteria

1. WHEN hovering over interactive pills or badges, THE UI_Component SHALL change border color from --border to --border-2 within 200ms
2. WHEN clicking the manual capture button, THE UI_Component SHALL change background to green tint and display checkmark
3. WHEN the consent checkbox is checked, THE UI_Component SHALL animate the checkmark appearance with smooth transition
4. WHEN typing in answer textarea, THE UI_Component SHALL expand vertically as needed with smooth resize behavior
5. THE ProctorAI SHALL apply cursor: pointer to all clickable elements and cursor: not-allowed to disabled elements

### Requirement 23: Improve Monitoring List Design

**User Story:** As a student, I want clear information about what is being monitored, so that I understand the proctoring system and feel informed about my privacy.

#### Acceptance Criteria

1. WHEN viewing the consent page, THE Consent_Step SHALL display monitoring capabilities in a vertical list with cards
2. THE Consent_Step SHALL show an emoji icon, capability name, and description for each monitoring type
3. THE ProctorAI SHALL style monitor cards with dark background (--bg-2), border, and padding for visual separation
4. THE Consent_Step SHALL display monitoring types: Gaze & Face Detection, Tab Switch Detection, Fullscreen Monitoring, Paste & Screenshot Detection
5. THE Consent_Step SHALL explain that all processing happens locally with "no video leaves browser" messaging

### Requirement 24: Enhance Score Gauge Animations

**User Story:** As a student, I want satisfying score reveal animations, so that viewing my results feels rewarding and engaging.

#### Acceptance Criteria

1. WHEN the report loads, THE Report_Step SHALL animate the alignment score counter from 0 to final value in 2% increments every 20ms
2. THE Report_Step SHALL simultaneously animate the conic-gradient gauge fill matching the counter progress
3. WHEN the score is ≥80%, THE Report_Step SHALL use green color (#10b981) for gauge and add green glow shadow
4. WHEN the score is <50%, THE Report_Step SHALL use red color (#ef4444) for gauge and add red glow shadow
5. WHEN the score is 50-79%, THE Report_Step SHALL use blue color (#3b82f6) for gauge and add blue glow shadow

### Requirement 25: Improve Proctoring Photo Display

**User Story:** As a student, I want to see my verification photo in the final report, so that I can confirm my identity was properly captured.

#### Acceptance Criteria

1. WHEN a photo is captured, THE ProctorAI SHALL store it as a base64-encoded JPEG data URI in application state
2. WHEN displaying the report, THE Report_Step SHALL render the captured photo in an identity snapshot card with rounded corners
3. THE Report_Step SHALL overlay "No photo captured" text if no photo is available in the state
4. THE Report_Step SHALL display a "● CAPTURED" badge above the photo with green color indicator
5. THE Report_Step SHALL size the photo card to fit within the proctoring grid layout alongside integrity metrics
