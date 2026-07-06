import re

with open('static/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# We need to remove lines 636-647 and one extra </div>.
# But it's safer to just replace the whole corrupted block.
target_block = """<div class="flex-1 flex flex-col gap-3">
<span class="font-headline-sm text-[10px] text-on-surface-variant uppercase tracking-widest">ACTIVITY LOG</span>
<div id="event-log-container" class="flex-1 bg-surface-container-low rounded-xl p-4 overflow-y-auto space-y-3 border border-outline-variant/30"></div>
<div class="flex gap-3 text-on-surface-variant">
<span class="font-code-md text-body-sm text-primary opacity-70">08:41</span>
<span class="font-body-sm text-on-surface">AI analyzing response...</span>
</div>
<div class="flex gap-3 text-on-surface-variant">
<span class="font-code-md text-body-sm text-primary opacity-70">08:42</span>
<span class="font-body-sm text-on-surface">Question 4 generated</span>
</div>
<div class="flex gap-3 text-on-surface-variant">
<span class="font-code-md text-body-sm text-primary opacity-70">08:42</span>
<span class="font-body-sm text-emerald-600 font-semibold">Identity verified</span>
</div>
</div>
</div>"""

replacement_block = """<div class="flex-1 flex flex-col gap-3">
<span class="font-headline-sm text-[10px] text-on-surface-variant uppercase tracking-widest">ACTIVITY LOG</span>
<div id="event-log-container" class="flex-1 bg-surface-container-low rounded-xl p-4 overflow-y-auto space-y-3 border border-outline-variant/30"></div>
</div>"""

if target_block in content:
    content = content.replace(target_block, replacement_block)
    print("Fixed corrupted HTML block!")
else:
    print("Target block not found precisely. Using regex...")
    pattern = re.compile(r'<div id="event-log-container"[^>]*></div>.*?Identity verified</span>\n</div>\n</div>\n</div>', re.DOTALL)
    if pattern.search(content):
        content = pattern.sub('<div id="event-log-container" class="flex-1 bg-surface-container-low rounded-xl p-4 overflow-y-auto space-y-3 border border-outline-variant/30"></div>\n</div>', content)
        print("Fixed corrupted HTML block with regex!")
    else:
        print("Could not find the block to fix.")

with open('static/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
