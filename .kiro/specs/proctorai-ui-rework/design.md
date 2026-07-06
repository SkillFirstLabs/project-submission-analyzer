# Design Document: ProctorAI UI/UX Rework

## Overview

This design document outlines the technical approach for modernizing and polishing the ProctorAI user interface. The rework maintains the existing 4-step workflow architecture while enhancing visual design, improving user experience, and ensuring accessibility. All changes are CSS and JavaScript-based modifications to the existing static HTML/CSS/JS stack, with no backend or architectural changes required.

The design focuses on:
- Refining the dark theme design system with consistent spacing, typography, and color usage
- Enhancing animations and transitions for a polished, premium feel
- Improving form UX with better validation feedback and focus states
- Upgrading data visualizations with animated gauges, progress bars, and charts
- Enhancing the camera and proctoring interface with better visual feedback
- Ensuring WCAG 2.1 Level AA accessibility compliance
- Maintaining all existing functionality without breaking changes

## Architecture

### High-Level Structure

The ProctorAI application follows a single-page application (SPA) pattern with four distinct step containers:

```
┌─────────────────────────────────────────────────────────┐
│                    Fixed Navbar                         │
│  (Logo, Status, System Time)                           │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│                                                         │
│              Active Step Container                      │
│           (Upload / Consent / Viva / Report)           │
│                                                         │
│  Each step container has visibility toggled via        │
│  .hidden class, preserving state between transitions   │
│                                                         │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│              Toast Container (fixed)                    │
│           (Top-right positioned notifications)          │
└─────────────────────────────────────────────────────────┘
```

### Design System Architecture

The design system is built on CSS custom properties (CSS variables) defined in `:root`:

**Color Tokens:**
- `--bg`, `--bg-2`, `--bg-3`, `--bg-4`: Background layers (darkest to lightest)
- `--border`, `--border-2`: Border colors with varying opacity
- `--accent`, `--accent-2`: Primary purple colors (#6366f1, #818cf8)
- `--accent-glow`: Transparent purple for shadows and glows
- `--green`, `--amber`, `--rose`: Semantic status colors
- `--text-1`, `--text-2`, `--text-3`: Text hierarchy (brightest to most muted)

**Typography Tokens:**
- `--mono`: JetBrains Mono for code and numbers
- `--sans`: Space Grotesk / Inter for UI text
- Font weights: 300-700 across all families

**Spacing Tokens:**
- `--radius`, `--radius-lg`, `--radius-sm`: Border-radius values (12px, 18px, 8px)
- `--shadow`, `--shadow-lg`, `--shadow-accent`: Box-shadow presets

### Component Architecture

Each step follows a consistent component structure:

1. **Step Container** (`.step-container`): Root wrapper for each step, initially hidden except the first
2. **Navbar Component** (`.navbar`): Fixed header with branding and status
3. **Main Content Area**: Step-specific layout (grid, flex, or custom)
4. **Interactive Controls**: Buttons, forms, inputs styled with design system tokens
5. **Overlays/Modals**: Fullscreen overlays for transitions (e.g., verification success)

## Components and Interfaces

### 1. Upload Step Components

**Hero Section** (`.upload-hero`)
- **Purpose**: Engage users with project overview and feature highlights
- **Layout**: Flex column with 64px padding
- **Key Elements**:
  - Hero chip (`.hero-chip`): Badge-style label
  - Hero title (`.hero-title`): 3.6rem heading with gradient text
  - Feature pills (`.pill`): Horizontal flex list of capability badges
  - Terminal widget (`.terminal-widget`): Live log output simulation
- **Interactions**: Terminal text animates in via JavaScript with timed delays

**Form Card** (`.upload-form-card`)
- **Purpose**: Collect project details and file upload
- **Layout**: Flex column with 64px padding on dark background
- **Key Elements**:
  - Field groups (`.field-group`): Label + input/textarea pairs
  - Dropzone (`.dropzone`): File upload with drag-and-drop
  - Submit button (`.btn-primary`): Initiates analysis
- **Interactions**:
  - Focus states on inputs: purple border + box-shadow
  - Dropzone hover: border color change + background tint
  - File selected: Display filename and size in dropzone

**Interface:**
```typescript
interface UploadStepState {
  projectTitle: string;
  projectDescription: string;
  projectOutcomes: string;
  zipFile: File | null;
  isAnalyzing: boolean;
}

interface UploadStepActions {
  onFileSelect(file: File): void;
  onSubmit(data: UploadStepState): Promise<void>;
  updateTerminalLog(message: string): void;
}
```

### 2. Consent Step Components

**Camera Panel** (`.consent-camera-panel`)
- **Purpose**: Display live camera feed with face detection overlay
- **Layout**: Grid column (50% width) with 40px padding
- **Key Elements**:
  - Camera viewport (`.camera-viewport`): 16:9 video container
  - Video element (`#camera-feed`): MediaStream display
  - Canvas overlay (`#camera-overlay`): Face-api.js drawing surface
  - Corner brackets (`.cam-corner`): Animated UI chrome
  - Scan line (`.scan-line`): Vertical scanning animation
  - Status badge (`.cam-badge`): "ANALYZING BIOMETRICS" indicator
  - Manual capture button (`.btn-capture`): Fallback photo capture
  - Payload box (`.payload-box`): JSON signal preview
- **Interactions**:
  - Face detection draws yellow bounding boxes on canvas
  - Scan line animates top to bottom over 3 seconds (infinite loop)
  - Payload updates every 1 second with random simulated data

**Consent Info Panel** (`.consent-info-panel`)
- **Purpose**: Explain proctoring and obtain user consent
- **Layout**: Grid column (50% width) with 40px padding
- **Key Elements**:
  - Icon wrap (`.consent-icon-wrap`): Shield SVG icon
  - Monitoring list (`.monitoring-list`): 4 capability cards
  - Checkbox row (`.consent-checkbox-row`): Custom styled checkbox
  - Consent button (`.btn-primary.btn-wide`): Proceed to viva
- **Interactions**:
  - Checkbox enables/disables consent button
  - Button hover: background lightens, shadow enhances
  - On consent: show full-screen success overlay with animation

**Success Overlay** (`.verification-overlay`)
- **Purpose**: Provide visual transition after successful verification
- **Layout**: Fixed fullscreen overlay (z-index: 9999)
- **Key Elements**:
  - Success card (`.success-card`): Centered modal with scale animation
  - Checkmark icon: Large green checkmark SVG
  - Loading bar (`.loading-bar`): Animated progress bar
  - Success message: "Identity Verified" heading
- **Interactions**:
  - Overlay animates in: opacity 0→1, scale 0.9→1
  - Loading bar fills from 0% to 100% over 2 seconds
  - Auto-dismisses after animation complete, transitions to viva

**Interface:**
```typescript
interface ConsentStepState {
  cameraActive: boolean;
  faceDetected: boolean;
  consentGiven: boolean;
  capturedPhoto: string | null; // base64 data URI
  biometricPayload: BiometricData;
}

interface BiometricData {
  faceCount: number;
  gazeDirection: string;
  headPose: { yaw: number; pitch: number; roll: number };
  expressions: { neutral: number; focused: number };
  timestamp: number;
}

interface ConsentStepActions {
  initCamera(): Promise<void>;
  startFaceDetection(): void;
  capturePhoto(): void;
  onConsentGiven(): void;
}
```

### 3. Viva Step Components

**Viva Header** (`.viva-header`)
- **Purpose**: Display session status and progress
- **Layout**: Fixed sticky header with flexbox (space-between)
- **Key Elements**:
  - Live badge (`.live-badge`): Green pulsing dot + "LIVE SESSION"
  - Timer display (`.header-stat`): Elapsed time in mm:ss
  - Question counter (`.header-stat`): Current/total (e.g., "03 / 12")
  - Integrity indicator (`.header-stat`): Real-time score
- **Interactions**:
  - Timer updates every second
  - Question counter updates on navigation
  - Integrity score updates based on proctoring events

**Viva Sidebar** (`.viva-sidebar`)
- **Purpose**: Continuous monitoring display
- **Layout**: Fixed-width (280px) left column with sticky positioning
- **Key Elements**:
  - Camera viewport (`.sidebar-cam-viewport`): Scaled-down video feed with canvas overlay
  - Activity log (`.activity-log`): Scrollable list of proctoring events
  - Help button (`.btn-ghost`): Request assistance action
- **Interactions**:
  - Face detection continues with yellow bounding box
  - Activity log auto-scrolls to bottom on new entries
  - Log entries color-coded by severity (clean, low, medium, high)

**Viva Main Content** (`.viva-main`)
- **Purpose**: Display questions and collect answers
- **Layout**: Flex-1 main column with padding, scrollable
- **Key Elements**:
  - Progress bar (`.viva-progress`): Horizontal segmented progress indicator
  - Question card (`.question-card`): Individual question container
  - Question badge (`.q-num-badge`): Question number indicator
  - Code reference (`.code-ref`): Optional collapsible code block
  - Answer textarea (`.answer-textarea`): Multi-line input for responses
  - Navigation buttons: Previous/Next/Submit
- **Interactions**:
  - Progress bar fills segments based on answered questions
  - Code reference expands/collapses on click
  - Textarea auto-expands vertically as user types
  - Submit button becomes active when all questions answered

**Interface:**
```typescript
interface VivaStepState {
  questions: Question[];
  currentQuestionIndex: number;
  answers: Map<number, string>;
  elapsedTime: number;
  integrityScore: number;
  activityLog: ActivityLogEntry[];
}

interface Question {
  id: number;
  text: string;
  codeReference?: {
    filename: string;
    content: string;
  };
}

interface ActivityLogEntry {
  timestamp: number;
  type: 'face_lost' | 'tab_switch' | 'multiple_faces' | 'clean';
  severity: 'clean' | 'low' | 'medium' | 'high';
  message: string;
}

interface VivaStepActions {
  navigateToQuestion(index: number): void;
  saveAnswer(questionId: number, answer: string): void;
  submitViva(): Promise<void>;
  logActivity(entry: ActivityLogEntry): void;
}
```

### 4. Report Step Components

**Report Header** (`.report-header`)
- **Purpose**: Display branding and export action
- **Layout**: Flex row with space-between
- **Key Elements**:
  - Report title: "Evaluation Report"
  - Download button (`.btn-outline`): Export JSON data
- **Interactions**:
  - Download button triggers JSON export with filename

**Score Gauges Section** (`.score-gauges`)
- **Purpose**: Display alignment and integrity scores prominently
- **Layout**: Grid (2 columns) with gap
- **Key Elements**:
  - Alignment gauge (`.gauge-card`): Circular conic-gradient gauge
  - Integrity gauge (`.gauge-card`): Numeric display with risk badge
- **Interactions**:
  - Alignment gauge animates fill from 0% to score over 1.5 seconds
  - Gauge color changes based on score range
  - Counter increments from 0 to final value in 2% steps

**Skills Section** (`.skills-grid`)
- **Purpose**: Display detected skills with confidence levels
- **Layout**: Responsive grid (2-3 columns based on screen width)
- **Key Elements**:
  - Skill card (`.skill-card`): Container with name, percentage, progress bar, rationale
  - Progress bar (`.skill-progress-bar`): Horizontal gradient-filled bar
- **Interactions**:
  - Cards animate in with staggered delays (fadeIn)
  - Progress bars animate width from 0% to confidence value
  - Hover effects: border color change, shadow enhancement

**Outcomes Section** (`.outcomes-list`)
- **Purpose**: Display learning outcome assessments
- **Layout**: Vertical flex column with gap
- **Key Elements**:
  - Outcome card (`.outcome-card`): Container with status badge, evidence, gap analysis
  - Status badge (`.outcome-status`): Color-coded pill (met/partial/not_demonstrated)
- **Interactions**:
  - Badges color-coded: green (met), amber (partial), red (not_demonstrated)
  - Cards have subtle hover effects

**Proctoring Section** (`.proctoring-grid`)
- **Purpose**: Display monitoring data and captured photo
- **Layout**: Grid (2 columns) with gap
- **Key Elements**:
  - Identity photo card (`.identity-snapshot`): Captured verification photo
  - Integrity metrics card (`.integrity-metrics`): Score, risk level, event counts
  - Activity summary (`.activity-summary`): Log of flagged events
- **Interactions**:
  - Photo displays if captured, otherwise shows "No photo captured"
  - Metrics display with icon indicators

**Report Footer** (`.report-footer`)
- **Purpose**: Display technical metadata and copyright
- **Layout**: Flex column with centered text
- **Key Elements**:
  - Metadata row: Tokens, extraction time, files analyzed, model name
  - Disclaimer text: Copyright and privacy notice
- **Interactions**: Static display, no interactions

**Interface:**
```typescript
interface ReportStepState {
  alignmentScore: number;
  integrityScore: number;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  skills: Skill[];
  outcomes: Outcome[];
  capturedPhoto: string | null;
  metadata: ReportMetadata;
  activityLog: ActivityLogEntry[];
}

interface Skill {
  name: string;
  confidence: number; // 0-100
  rationale: string;
}

interface Outcome {
  name: string;
  status: 'met' | 'partial' | 'not_demonstrated';
  evidence: string;
  gap?: string;
}

interface ReportMetadata {
  tokensUsed: number;
  extractionTimeMs: number;
  filesAnalyzed: number;
  modelName: string;
}
```

### 5. Shared Components

**Toast Notification System**
- **Container** (`.toast-container`): Fixed top-right positioned wrapper
- **Toast** (`.toast`): Individual notification card
- **Variants**: `.toast-error`, `.toast-warning`, `.toast-success`, `.toast-info`
- **Animation**: Slide in from right, auto-dismiss after 4 seconds
- **Stacking**: Multiple toasts stack vertically with 12px gap

**Button System**
- **Primary** (`.btn-primary`): Purple fill, white text, accent shadow
- **Outline** (`.btn-outline`): Transparent fill, purple border, white text
- **Ghost** (`.btn-ghost`): Transparent fill, subtle hover state
- **Disabled State**: Opacity 0.4, cursor not-allowed, no hover effects

**Form Elements**
- **Field Group** (`.field-group`): Label + input wrapper
- **Input** (`.input`): Text/email inputs with focus states
- **Textarea** (`.textarea`): Multi-line input with resize capability
- **Checkbox**: Custom styled with checkmark animation
- **Focus State**: Purple border, 3px rgba(99,102,241,0.15) box-shadow

## Data Models

### Application State

The application maintains a global state object that persists across step transitions:

```typescript
interface AppState {
  currentStep: 'upload' | 'consent' | 'viva' | 'report';
  
  // Upload data
  projectTitle: string;
  projectDescription: string;
  projectOutcomes: string;
  zipFile: File | null;
  analysisResult: AnalysisResult | null;
  
  // Consent data
  cameraStream: MediaStream | null;
  faceDetectionActive: boolean;
  capturedPhoto: string | null;
  consentTimestamp: number | null;
  
  // Viva data
  questions: Question[];
  answers: Map<number, string>;
  vivaStartTime: number | null;
  currentQuestionIndex: number;
  integrityScore: number;
  activityLog: ActivityLogEntry[];
  
  // Report data
  evaluationReport: EvaluationReport | null;
}

interface AnalysisResult {
  questions: Question[];
  outcomes: Outcome[];
  extractedFiles: string[];
  tokenCount: number;
  extractionTime: number;
}

interface EvaluationReport {
  alignmentScore: number;
  integrityScore: number;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  skills: Skill[];
  outcomes: Outcome[];
  metadata: ReportMetadata;
  submissionTimestamp: number;
}
```

### Face Detection Data Model

Face-api.js returns detection results that we process for proctoring:

```typescript
interface FaceDetectionResult {
  detection: {
    box: { x: number; y: number; width: number; height: number };
    score: number;
  };
  landmarks: {
    positions: Array<{ x: number; y: number }>;
  };
  expressions: {
    neutral: number;
    happy: number;
    sad: number;
    angry: number;
    // ... other expressions
  };
}

interface ProcessedBiometricData {
  faceCount: number;
  primaryFaceBox: { x: number; y: number; width: number; height: number } | null;
  gazeDirection: 'center' | 'left' | 'right' | 'up' | 'down';
  expressions: { neutral: number; focused: number };
  timestamp: number;
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Before defining the correctness properties, I need to perform prework analysis on the acceptance criteria to determine which are testable as properties, examples, or edge cases.