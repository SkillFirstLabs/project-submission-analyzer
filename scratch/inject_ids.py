import re

def main():
    with open("static/index.html", "r", encoding="utf-8") as f:
        content = f.read()

    # Step 1: Upload Form
    content = content.replace('placeholder="e.g., Scalable E-commerce Backend" type="text"/>', 'placeholder="e.g., Scalable E-commerce Backend" type="text" name="project_title" required/>')
    content = content.replace('placeholder="Provide a brief overview of the project\'s purpose..." rows="3"></textarea>', 'placeholder="Provide a brief overview of the project\'s purpose..." rows="3" name="project_description"></textarea>')
    content = content.replace('placeholder="Define the key metrics and functional outcomes expected from this submission..." rows="5"></textarea>', 'placeholder="Define the key metrics and functional outcomes expected from this submission..." rows="5" name="project_outcomes"></textarea>')
    content = content.replace('accept=".zip" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer" type="file"/>', 'accept=".zip" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer" type="file" name="zip_file" required/>')
    
    # Start Analysis button
    content = re.sub(r'(<button class="[^"]*Start Analysis[^>]*>)', r'\1', content, flags=re.IGNORECASE)
    content = content.replace('Start Analysis\n                    </button>', 'Start Analysis\n                    </button>').replace('<button class="flex items-center px-8 py-2.5 bg-primary text-on-primary font-label-lg rounded-lg hover:opacity-90 transition-all shadow-lg active:scale-95">', '<button id="analyze-btn" class="flex items-center px-8 py-2.5 bg-primary text-on-primary font-label-lg rounded-lg hover:opacity-90 transition-all shadow-lg active:scale-95" type="button">')

    # Step 2: Consent
    # Replace placeholder image with video and canvas
    camera_container_html = """
    <div class="absolute inset-0 w-full h-full bg-cover bg-center bg-black flex items-center justify-center relative overflow-hidden">
        <video id="camera-feed" autoplay muted playsinline class="absolute inset-0 w-full h-full object-cover"></video>
        <canvas id="camera-overlay" class="absolute inset-0 w-full h-full z-10 pointer-events-none"></canvas>
    </div>
    """
    content = re.sub(r'<div class="absolute inset-0 w-full h-full bg-cover bg-center"[^>]*>.*?</div>', camera_container_html, content, count=1, flags=re.DOTALL)
    
    # Change "I Consent & Start Viva" button to have id="consent-btn"
    content = content.replace('id="start-btn"', 'id="consent-btn"')

    # Step 3: Viva Session
    # Question display area
    content = re.sub(r'<span class="font-headline-sm text-label-md text-primary tracking-\[0\.2em\] uppercase">QUESTION 04</span>', '<span id="q-counter-display" class="font-headline-sm text-label-md text-primary tracking-[0.2em] uppercase">QUESTION 01</span>', content)
    content = re.sub(r'<h1 class="font-headline-md text-headline-md text-on-background leading-tight">.*?</h1>', '<h1 id="question-text" class="font-headline-md text-headline-md text-on-background leading-tight">Loading question...</h1>', content, flags=re.DOTALL)
    
    # Code block area
    content = re.sub(r'<div class="bg-\[#1E293B\] rounded-xl p-6 relative group">.*?</div>', '<div id="code-ref-block" class="bg-[#1E293B] rounded-xl p-6 relative group hidden"><div id="code-ref-filename" class="absolute top-4 right-4 text-slate-500 font-code-md text-[10px]"></div><pre id="code-ref-content" class="font-code-md text-code-md text-slate-300 leading-relaxed"></pre></div>', content, flags=re.DOTALL)

    # Answer textarea
    content = content.replace('<textarea class="w-full min-h-[160px] bg-surface-container-low border-outline-variant border rounded-xl p-6 font-body-md focus:ring-2 focus:ring-primary focus:border-transparent transition-all placeholder:text-outline-variant" placeholder="Start speaking or type your answer here..."></textarea>', '<textarea id="answer-input" class="w-full min-h-[160px] bg-surface-container-low border-outline-variant border rounded-xl p-6 font-body-md focus:ring-2 focus:ring-primary focus:border-transparent transition-all placeholder:text-outline-variant" placeholder="Start speaking or type your answer here..."></textarea>')

    # Previous / Next / End Buttons
    content = content.replace('PREVIOUS\n                    </button>', 'PREVIOUS\n                    </button>').replace('<button class="flex items-center gap-2 text-on-surface-variant hover:text-on-surface transition-colors font-headline-sm text-label-md uppercase tracking-wider group">', '<button id="prev-q-btn" class="flex items-center gap-2 text-on-surface-variant hover:text-on-surface transition-colors font-headline-sm text-label-md uppercase tracking-wider group" type="button">')
    content = content.replace('SKIP QUESTION\n                        </button>', 'SKIP QUESTION\n                        </button>').replace('<button class="px-8 py-4 bg-surface border border-outline-variant text-on-surface font-headline-sm text-label-md uppercase tracking-wider rounded-lg hover:bg-surface-container-high transition-all shadow-sm">', '<button id="skip-q-btn" class="px-8 py-4 bg-surface border border-outline-variant text-on-surface font-headline-sm text-label-md uppercase tracking-wider rounded-lg hover:bg-surface-container-high transition-all shadow-sm" type="button">')
    content = content.replace('SUBMIT ANSWER', 'SUBMIT ANSWER').replace('<button class="px-10 py-4 bg-primary text-on-primary font-headline-sm text-label-md uppercase tracking-wider rounded-lg hover:bg-primary-container transition-all shadow-lg hover:shadow-primary/20 flex items-center gap-3">', '<button id="next-q-btn" class="px-10 py-4 bg-primary text-on-primary font-headline-sm text-label-md uppercase tracking-wider rounded-lg hover:bg-primary-container transition-all shadow-lg hover:shadow-primary/20 flex items-center gap-3" type="button">')
    
    # Event Log container in Sidebar
    content = re.sub(r'<div class="flex-1 bg-surface-container-low rounded-xl p-4 overflow-y-auto space-y-3 border border-outline-variant/30">.*?</div>', '<div id="event-log-container" class="flex-1 bg-surface-container-low rounded-xl p-4 overflow-y-auto space-y-3 border border-outline-variant/30"></div>', content, count=1, flags=re.DOTALL)
    
    # Small Camera preview in Viva sidebar
    content = re.sub(r'<img alt="University student during proctored session"[^>]*>', '<div id="viva-sidebar-camera"></div>', content, count=1)

    # Step 4: Report
    content = content.replace('<h1 class="font-headline-xl text-headline-xl text-on-background">Distributed Systems: Auth Middleware Project</h1>', '<h1 id="report-title" class="font-headline-xl text-headline-xl text-on-background">Loading...</h1>')
    content = content.replace('<span class="absolute font-headline-md text-headline-md text-on-surface">86%</span>', '<span id="report-alignment-score" class="absolute font-headline-md text-headline-md text-on-surface">--%</span>')
    content = content.replace('<p class="text-on-surface-variant font-body-lg mt-2 max-w-2xl">A comprehensive technical assessment of the submitted ZIP archive and proctored viva session.</p>', '<p id="report-narrative" class="text-on-surface-variant font-body-lg mt-2 max-w-2xl">A comprehensive technical assessment...</p>')
    
    content = re.sub(r'<div class="grid grid-cols-1 md:grid-cols-2 gap-grid-gutter">.*?</div>\s*</section>', '<div id="report-skills-container" class="grid grid-cols-1 md:grid-cols-2 gap-grid-gutter"></div></section>', content, count=1, flags=re.DOTALL)
    content = re.sub(r'<div class="grid grid-cols-1 lg:grid-cols-3 gap-grid-gutter">.*?</div>\s*</section>', '<div id="report-outcomes-container" class="grid grid-cols-1 lg:grid-cols-3 gap-grid-gutter"></div></section>', content, count=1, flags=re.DOTALL)
    
    content = content.replace('<p class="text-headline-xl font-headline-xl">0.86</p>', '<p id="report-integrity-score" class="text-headline-xl font-headline-xl">--</p>')
    content = content.replace('<div class="px-3 py-1 bg-emerald-100 text-emerald-700 font-bold rounded-lg text-sm">Low Risk</div>', '<div id="report-risk-level" class="px-3 py-1 bg-emerald-100 text-emerald-700 font-bold rounded-lg text-sm">--</div>')
    
    content = re.sub(r'<div class="scrolling-log overflow-y-auto space-y-3 font-code-md text-code-md max-h-\[300px\]">.*?</div>', '<div id="report-event-log" class="scrolling-log overflow-y-auto space-y-3 font-code-md text-code-md max-h-[300px]"></div>', content, count=1, flags=re.DOTALL)

    # End Viva button
    # Add an End Session button below the question area
    end_btn = '<div class="mt-8 pt-6 border-t border-outline-variant flex justify-end"><button id="end-viva-btn" class="px-8 py-3 bg-rose-600 text-white rounded-lg font-bold uppercase hover:bg-rose-700 transition" type="button">End Session & Generate Report</button></div>'
    content = content.replace('</div>\n</section>\n</main>', f'{end_btn}\n</div>\n</section>\n</main>')

    # Remove all the hardcoded scripts from templates
    content = re.sub(r'<script>.*?</script>', '', content, flags=re.DOTALL)

    with open("static/index.html", "w", encoding="utf-8") as f:
        f.write(content)
    print("IDs injected successfully.")

if __name__ == "__main__":
    main()
