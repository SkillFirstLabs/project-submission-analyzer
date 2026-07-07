def evaluate_single_answer(answer_text: str):
    cleaned_answer = answer_text.strip()
    word_count = len(cleaned_answer.split())
    if word_count == 0:
        score = 0
        feedback = "No answer was provided."
    elif word_count < 5:
        score = 25
        feedback = "The answer is too short and needs more explanation."
    elif word_count < 15:
        score = 50
        feedback = "The answer shows basic understanding but needs more detail."
    elif word_count < 30:
        score = 75
        feedback = "The answer demonstrates good understanding."
    else:
        score = 100
        feedback = "The answer is detailed and demonstrates strong understanding."
    return {
        "score": score,
        "feedback": feedback,
        "word_count": word_count
    }


def evaluate_viva_answers(answers):
    evaluated_answers = []
    total_score = 0
    for answer in answers:
        result = evaluate_single_answer(
            answer.answer
        )
        evaluated_answer = {
            "question_number":
                answer.questionNumber,
            "skill_name":
                answer.skillName,
            "question_type":
                answer.type,
            "question":
                answer.question,
            "candidate_answer":
                answer.answer,
            "evidence_file":
                answer.evidenceFile,
            "score":
                result["score"],
            "feedback":
                result["feedback"],
            "word_count":
                result["word_count"]
        }
        evaluated_answers.append(
            evaluated_answer
        )
        total_score += result["score"]
    if evaluated_answers:
        average_score = round(
            total_score /
            len(evaluated_answers),
            2
        )
    else:
        average_score = 0
    if average_score >= 80:
        performance_level = "excellent"
    elif average_score >= 60:
        performance_level = "good"
    elif average_score >= 40:
        performance_level = "average"
    else:
        performance_level = "needs_improvement"
    return {
        "total_questions":
            len(evaluated_answers),
        "average_score":
            average_score,
        "performance_level":
            performance_level,
        "evaluated_answers":
            evaluated_answers
    }
