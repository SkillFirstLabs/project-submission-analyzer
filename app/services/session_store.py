import json
from typing import Dict, Any, Optional

from app.database import SessionLocal
from app.database_models import AssessmentSession


# --------------------------------------------------
# HELPER: CONVERT DATABASE ROW TO DICTIONARY
# --------------------------------------------------

def _session_to_dict(
    session: AssessmentSession
) -> Dict[str, Any]:

    return {
        "project_analysis": (
            json.loads(session.project_analysis)
            if session.project_analysis
            else None
        ),

        "viva_evaluation": (
            json.loads(session.viva_evaluation)
            if session.viva_evaluation
            else None
        ),

        "proctoring_report": (
            json.loads(session.proctoring_report)
            if session.proctoring_report
            else None
        ),

        "final_assessment": (
            json.loads(session.final_assessment)
            if session.final_assessment
            else None
        )
    }


# --------------------------------------------------
# CREATE SESSION
# --------------------------------------------------

def create_session(
    session_id: str
) -> Dict[str, Any]:

    db = SessionLocal()

    try:

        existing_session = (
            db.query(AssessmentSession)
            .filter(
                AssessmentSession.session_id
                == session_id
            )
            .first()
        )

        if existing_session:

            return _session_to_dict(
                existing_session
            )


        new_session = AssessmentSession(

            session_id=session_id,

            project_analysis=None,

            viva_evaluation=None,

            proctoring_report=None,

            final_assessment=None
        )


        db.add(new_session)

        db.commit()

        db.refresh(new_session)


        return _session_to_dict(
            new_session
        )


    finally:

        db.close()


# --------------------------------------------------
# CHECK SESSION
# --------------------------------------------------

def session_exists(
    session_id: str
) -> bool:

    db = SessionLocal()

    try:

        session = (
            db.query(AssessmentSession)
            .filter(
                AssessmentSession.session_id
                == session_id
            )
            .first()
        )

        return session is not None


    finally:

        db.close()


# --------------------------------------------------
# GET SESSION
# --------------------------------------------------

def get_session(
    session_id: str
) -> Optional[Dict[str, Any]]:

    db = SessionLocal()

    try:

        session = (
            db.query(AssessmentSession)
            .filter(
                AssessmentSession.session_id
                == session_id
            )
            .first()
        )


        if session is None:

            return None


        return _session_to_dict(
            session
        )


    finally:

        db.close()


# --------------------------------------------------
# STORE PROJECT ANALYSIS
# --------------------------------------------------

def store_project_analysis(
    session_id: str,
    project_analysis: Dict[str, Any]
):

    db = SessionLocal()

    try:

        session = (
            db.query(AssessmentSession)
            .filter(
                AssessmentSession.session_id
                == session_id
            )
            .first()
        )


        if session is None:

            session = AssessmentSession(
                session_id=session_id
            )

            db.add(session)


        session.project_analysis = json.dumps(
            project_analysis
        )


        db.commit()


    finally:

        db.close()


# --------------------------------------------------
# STORE VIVA EVALUATION
# --------------------------------------------------

def store_viva_evaluation(
    session_id: str,
    viva_evaluation: Dict[str, Any]
):

    db = SessionLocal()

    try:

        session = (
            db.query(AssessmentSession)
            .filter(
                AssessmentSession.session_id
                == session_id
            )
            .first()
        )


        if session is None:

            session = AssessmentSession(
                session_id=session_id
            )

            db.add(session)


        session.viva_evaluation = json.dumps(
            viva_evaluation
        )


        db.commit()


    finally:

        db.close()


# --------------------------------------------------
# STORE PROCTORING REPORT
# --------------------------------------------------

def store_proctoring_report(
    session_id: str,
    proctoring_report: Dict[str, Any]
):

    db = SessionLocal()

    try:

        session = (
            db.query(AssessmentSession)
            .filter(
                AssessmentSession.session_id
                == session_id
            )
            .first()
        )


        if session is None:

            session = AssessmentSession(
                session_id=session_id
            )

            db.add(session)


        session.proctoring_report = json.dumps(
            proctoring_report
        )


        db.commit()


    finally:

        db.close()


# --------------------------------------------------
# STORE FINAL ASSESSMENT
# --------------------------------------------------

def store_final_assessment(
    session_id: str,
    final_assessment: Dict[str, Any]
):

    db = SessionLocal()

    try:

        session = (
            db.query(AssessmentSession)
            .filter(
                AssessmentSession.session_id
                == session_id
            )
            .first()
        )


        if session is None:

            session = AssessmentSession(
                session_id=session_id
            )

            db.add(session)


        session.final_assessment = json.dumps(
            final_assessment
        )


        db.commit()


    finally:

        db.close()


# --------------------------------------------------
# DELETE SESSION
# --------------------------------------------------

def delete_session(
    session_id: str
) -> bool:

    db = SessionLocal()

    try:

        session = (
            db.query(AssessmentSession)
            .filter(
                AssessmentSession.session_id
                == session_id
            )
            .first()
        )


        if session is None:

            return False


        db.delete(session)

        db.commit()


        return True


    finally:

        db.close()