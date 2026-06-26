import os
import tempfile
import json
from flask import Blueprint, request, jsonify

from app.services.zip_service import extract_zip_safe
from app.services.file_scanner import scan_project
from app.services.parser_service import parse_file
from app.services.language_detector import detect_languages
from app.services.framework_detector import detect_frameworks
from app.services.chunk_service import chunk_files
from app.services.vector_store import build_vector_store
from app.services.retrieval_service import retrieve_context
from app.services.skill_service import detect_skills
from app.services.interview_service import generate_interview_questions
from app.services.summary_service import generate_summary
from app.services.report_service import build_report
from app.services.cleanup_service import cleanup_project
from app.utils.validators import validate_zip_file, validate_file_size
from app.utils.constants import RETRIEVAL_QUERIES

analyze_bp = Blueprint("analyze", __name__)

@analyze_bp.route("/analyze-submission", methods=["POST"])
def analyze_submission():
    if "zip_file" not in request.files:
        return jsonify({"detail": "Missing uploaded file. Use key 'zip_file'."}), 400
        
    uploaded_file = request.files["zip_file"]
    if not uploaded_file.filename:
        return jsonify({"detail": "Empty filename."}), 400
        
    project_title = request.form.get("project_title")
    
    questions_per_skill_str = request.form.get("questions_per_skill", "5")
    try:
        questions_per_skill = int(questions_per_skill_str)
    except ValueError:
        questions_per_skill = 5
            
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    try:
        uploaded_file.save(temp_zip.name)
        temp_zip.close()
        
        try:
            validate_file_size(temp_zip.name)
            validate_zip_file(temp_zip.name)
        except ValueError as val_err:
            return jsonify({"detail": str(val_err)}), 400
            
        temp_dir = extract_zip_safe(temp_zip.name)
        
        files = scan_project(temp_dir)
        if not files:
            return jsonify({"detail": "No readable source files found in ZIP."}), 422
            
        parsed_structures = [parse_file(f["content"], f["filename"]) for f in files]
        
        languages = detect_languages(files)
        
        frameworks = detect_frameworks(files, parsed_structures)
        
        chunks = chunk_files(files)
        if not chunks:
            return jsonify({"detail": "Could not create any chunks from files."}), 422
            
        vector_store = build_vector_store(chunks)
        
        context = retrieve_context(vector_store, RETRIEVAL_QUERIES, top_k=2)
        
        lang_names = [l["language"] for l in languages]
        fw_names = [f["framework"] for f in frameworks]
        suggested_skills = detect_skills(context, detected_languages=lang_names, detected_frameworks=fw_names)
        print(f"Suggested skills: {suggested_skills}", flush=True)
        print(f"Context length: {len(context)} characters", flush=True)
        
        interview_data = generate_interview_questions(suggested_skills, context, questions_per_skill)
        
        summary_data = generate_summary(project_title, context)
        
        metadata = {
            "total_files": len(files),
            "total_chunks": len(chunks),
            "files_analyzed": len(files)
        }
        
        report = build_report(
            suggested_skills,
            languages,
            frameworks,
            interview_data,
            summary_data,
            metadata
        )
        
        return jsonify(report), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"detail": f"Analysis failed: {str(e)}"}), 500
        
    finally:
        if 'temp_dir' in locals():
            cleanup_project(temp_dir, temp_zip.name)
        else:
            cleanup_project(None, temp_zip.name)
