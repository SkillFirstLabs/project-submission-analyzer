# ProctorAI - Complete Code Analysis

## Project Overview
ProctorAI is an AI-powered project submission analyzer with live proctored viva sessions built using FastAPI backend and vanilla JavaScript frontend.

## Architecture Analysis

### 1. Frontend Structure (Single Page Application)

**HTML Structure (`static/index.html`)**
- 4-step workflow: Upload → Consent → Viva → Report
- Each step is a `.step-container` div toggled with `.hidden` class
- Fixed navbar across all steps
- Toast notification container for alerts

**Key Components:**
```
Step 1 (Upload): 
  - Hero section with feature pills
  - Terminal widget for live feedback
  - Form with project details + ZIP upload
  - Dropzone with drag-and-drop

Step 2 (Consent):
  - Camera viewport with face detection overlay
  - Animated corner brackets + scan line
  - Real-time biometric payload preview
  - Monitoring capability list
  - Manual capture button
  - Consent checkbox + verification flow

Step 3 (Viva):
  - Sticky header with session stats
  - Left sidebar (280px) with camera + activity log
  - Main area with questions + answer textarea
  - Progress bar (segmented)
  - Navigation controls (prev/next/submit)
  - Speech recognition integration

Step 4 (Report):
  - Hero section with alignment/integrity scores
  - Animated circular gauge (conic-gradient)
  - Skills grid with confidence bars
  - Outcomes grid with status badges
  - Proctoring section (photo + metrics)
  - Footer with metadata
```

### 2. JavaScript Architecture (`static/app.js`)

**State Management:**
```javascript
const state = {
  submissionData: null,      // Analysis results from backend
  questions: [],             // Array of viva questions
  qIndex: 0,                 // Current question index
  finalReport: null,         // Complete evaluation report
  sessionId: null,           // Viva session identifier
  faceModelReady: false,     // Face-api.js initialization flag
  gazeOffSince: null,        // Timestamp for gaze tracking
  noFaceSince: null,         // Timestamp for face loss
  strikeCount: 0,            // Proctoring violation counter
  capturedPhoto: null,       // Base64 photo data URI
  streamActive: false,       // Camera stream status
  lastHeartbeat: null        // Last ping to prevent timeout
};
```

**Key Functions:**

1. **Face Detection System**
```javascript
async function loadFaceModel()
// Loads face-api.js models (TinyFaceDetector, FaceLandmark68Net)
// Sets state.faceModelReady = true

async function runFaceLoop(video)
// Main proctoring loop (runs every 700ms)
// Detects faces, draws bounding boxes
// Monitors: no face, multiple faces, off-center gaze
// Posts events to backend via postEvent()
// Includes heartbeat ping every 5s to prevent timeout
```

2. **MediaPipe Gesture Recognition**
```javascript
async function initGestureRecognizer()
// Initializes MediaPipe Gesture Recognizer
// Detects thumbs-up gesture for verification

async function scanGestureLoop(video)
// Scans for thumbs-up gesture
// Auto-captures photo and enables consent button
```

3. **Step Navigation**
```javascript
function show(id)
// Hides all step containers, shows target step
// Preserves state between transitions

function renderQuestion()
// Displays current question with:
//   - Question number badge
//   - Question text
//   - Optional code reference block
//   - Progress bar update
//   - Answer textarea pre-fill
```

4. **API Integration**
```javascript
// POST /analyze-submission
// - Uploads ZIP + project details
// - Returns analysis with questions

// POST /viva-session/start
// - Starts proctored session
// - Returns session_id

// POST /viva-session/event
// - Logs proctoring events (tab_switch, face_lost, etc.)
// - Calculates integrity score

// POST /viva-session/end
// - Submits answers
// - Returns complete evaluation report
```

5. **Speech Recognition**
```javascript
let recognition = new webkitSpeechRecognition();
recognition.continuous = true;
recognition.interimResults = true;
// Transcribes speech to answer textarea
// Toggle via mic button
```

6. **Proctoring Event System**
```javascript
async function postEvent(eventType, durationMs, confidence)
// Event types:
//   - heartbeat (every 5s to prevent timeout)
//   - id_verified (face detected in consent)
//   - face_not_detected (no face for 2s+)
//   - multiple_faces_detected
//   - gaze_off_screen (off-center for 1.5s+)
//   - tab_switched (visibility change)
//   - interview_started

function logEvent(msg, level)
// Adds entry to activity log
// Levels: info, success, warning, error
// Color-coded in sidebar
```

### 3. CSS Architecture (`static/style.css`)

**Design System:**
```css
:root {
  /* Color Palette */
  --bg: #0a0b0f (darkest)
  --bg-2: #111218
  --bg-3: #16181f
  --bg-4: #1c1e27 (lightest dark)
  
  --accent: #6366f1 (primary purple)
  --accent-2: #818cf8 (lighter purple)
  
  --green: #22c55e (success)
  --amber: #f59e0b (warning)
  --rose: #f43f5e (error)
  
  /* Typography */
  --sans: 'Space Grotesk', 'Inter'
  --mono: 'JetBrains Mono'
  
  /* Spacing */
  --radius: 12px
  --radius-lg: 18px
  --radius-sm: 8px
}
```

**Key Patterns:**
- Dark theme with purple accents
- Glassmorphism (backdrop-filter: blur)
- Subtle shadows for depth
- Smooth transitions (0.2s ease)
- Hover states: translateY(-1px) + enhanced shadow
- Focus states: purple border + box-shadow ring
- Animations: fadeIn, slideIn, pulse, scan, spin

### 4. Data Flow

```
1. Upload Flow:
   User fills form → File selected → analyze-btn clicked
   → FormData posted to /analyze-submission
   → Backend extracts ZIP, analyzes code with GPT-4o
   → Returns: {questions[], outcomes[], skills[], metadata}
   → Transitions to Consent step

2. Consent Flow:
   Camera initialized → Face-api.js loads models
   → Real-time face detection starts (runFaceLoop)
   → User checks consent checkbox
   → Manual capture or thumbs-up gesture
   → POST /viva-session/start with submission_id
   → Returns session_id
   → Success overlay → Transition to Viva

3. Viva Flow:
   Session started → Questions rendered
   → Proctoring active (face loop continues)
   → Events posted to /viva-session/event
   → User answers questions (text or speech)
   → Navigation: prev/next buttons
   → Final question: "Submit Session" button
   → POST /viva-session/end with answers[]
   → Returns complete evaluation report
   → Transition to Report

4. Report Flow:
   Data rendered from finalReport
   → Alignment gauge animates (0→score%)
   → Skills/outcomes populate grids
   → Photo displayed if captured
   → Download JSON button available
```

### 5. Security Features

**ZIP Security:**
- Backend validates ZIP structure
- Prevents Zip Slip attacks
- Sandboxed extraction

**Proctoring Privacy:**
- All face detection happens client-side
- No video/audio uploaded to server
- Only anonymized event signals sent
- Photo capture optional (base64 stored locally)

**Data Handling:**
- CORS configured for API access
- File size limits (25MB)
- Session-based integrity tracking

### 6. Key Integrations

**External Libraries:**
1. `face-api.js` (v0.22.2) - Face detection and landmarks
2. `MediaPipe Tasks Vision` (v0.10.3) - Gesture recognition
3. Google Fonts: Inter, Space Grotesk, JetBrains Mono

**Browser APIs:**
1. MediaDevices (getUserMedia) - Camera access
2. webkitSpeechRecognition - Voice input
3. Visibility API - Tab switch detection
4. Fullscreen API - Fullscreen monitoring (planned)
5. Clipboard API - Paste detection (planned)

### 7. Performance Considerations

**Optimization Points:**
- Face detection throttled to 700ms intervals (not every frame)
- Canvas overlay for face landmarks (no re-renders)
- Heartbeat pings every 5s (prevents 12s backend timeout)
- CSS transitions use transform (GPU-accelerated)
- Lazy loading of face-api models
- Debounced gaze/face-loss detection (prevents spam)

**Bundle Size:**
- face-api.js: ~1.5MB (CDN)
- MediaPipe: ~2MB (CDN)
- Custom CSS: ~40KB
- Custom JS: ~15KB

### 8. Browser Compatibility

**Required Features:**
- ES6+ (async/await, fetch, const/let)
- CSS Grid & Flexbox
- CSS Custom Properties (variables)
- getUserMedia (camera)
- webkitSpeechRecognition (Chrome/Edge)
- Canvas API
- Visibility API

**Tested On:**
- Chrome 90+ ✅
- Edge 90+ ✅
- Firefox 88+ ⚠️ (no speech recognition)
- Safari 14+ ⚠️ (limited speech support)

### 9. Potential Improvements

**UX Enhancements:**
1. ✅ Toast notifications (already implemented)
2. ✅ Smooth transitions (already implemented)
3. ✅ Loading states (already implemented)
4. Add keyboard shortcuts (Ctrl+Enter to submit answer)
5. Add question bookmarking/flagging
6. Add text formatting toolbar for answers
7. Add countdown timer for viva session

**Technical Enhancements:**
1. Migrate to TypeScript for type safety
2. Add WebSocket for real-time backend communication
3. Implement service worker for offline capability
4. Add error boundary for graceful error handling
5. Compress face-api models (reduce load time)
6. Add unit tests (Jest + Testing Library)
7. Add E2E tests (Playwright)

**Accessibility:**
1. Add aria-labels to all interactive elements
2. Improve keyboard navigation (focus trapping)
3. Add screen reader announcements for step changes
4. Ensure all colors meet WCAG AA contrast ratios
5. Add captions for video (if audio added)

### 10. Code Quality Metrics

**Strengths:**
- Clean separation of concerns (HTML/CSS/JS)
- Consistent naming conventions
- Comprehensive comments in complex functions
- Modular function design
- State management pattern

**Areas for Improvement:**
- No error boundaries (errors can crash app)
- Large monolithic JS file (needs splitting)
- Some magic numbers (700ms, 2000ms, etc.)
- Limited error messages (generic alerts)
- No loading retry logic

### 11. Backend Integration Points

**FastAPI Endpoints:**
```python
POST /analyze-submission
  - multipart/form-data
  - Fields: project_title, project_description, project_outcomes, zip_file
  - Returns: AnalysisResult

POST /viva-session/start
  - JSON: {submission_id, consent_acknowledged}
  - Returns: {session_id}

POST /viva-session/event
  - JSON: {session_id, event_type, timestamp, duration_ms, confidence}
  - Returns: {severity} (if flagged)

POST /viva-session/end
  - JSON: {session_id, answers[]}
  - Returns: EvaluationReport
```

## Conclusion

ProctorAI is a well-structured application with a clear 4-step workflow. The frontend uses vanilla JavaScript with modern browser APIs for proctoring, and the backend handles AI analysis via GPT-4o. The codebase is production-ready with good UX, but could benefit from TypeScript migration, better error handling, and comprehensive testing.

**Overall Rating: 8/10**
- UI/UX: 9/10 (polished, modern, intuitive)
- Code Quality: 7/10 (clean but needs modularization)
- Performance: 8/10 (optimized but can improve)
- Security: 8/10 (client-side privacy, needs more backend validation)
- Accessibility: 6/10 (basic compliance, needs ARIA improvements)
