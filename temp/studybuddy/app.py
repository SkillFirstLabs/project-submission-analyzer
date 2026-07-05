from flask import Flask, render_template, request, jsonify
import json

app = Flask(__name__)

# Load data from JSON
with open('data.json', 'r') as f:
    subject_data = json.load(f)

@app.route('/')
def index():
    selected_subject = request.args.get('subject', 'Python')  # Default is Python
    content = subject_data.get(selected_subject, {})
    subjects = subject_data.keys()
    return render_template('index.html', subjects=subjects, content=content, selected_subject=selected_subject)

if __name__ == '__main__':
    app.run(debug=True)
