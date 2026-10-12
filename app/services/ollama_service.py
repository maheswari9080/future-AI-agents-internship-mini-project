import re
from typing import Dict, Any, Optional
import httpx
from sqlalchemy.orm import Session
from app.config import settings
from app.crud import get_dashboard_stats, get_students
from app.models import Student


async def check_ollama_status() -> Dict[str, Any]:
    """Check whether local Ollama service is reachable."""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/version")
            if response.status_code == 200:
                data = response.json()
                return {
                    "available": True,
                    "version": data.get("version", "unknown"),
                    "model": settings.OLLAMA_MODEL,
                    "base_url": settings.OLLAMA_BASE_URL,
                }
    except Exception:
        pass
    return {
        "available": False,
        "version": None,
        "model": settings.OLLAMA_MODEL,
        "base_url": settings.OLLAMA_BASE_URL,
    }


def compute_grounded_answer(db: Session, question: str) -> Optional[str]:
    """
    Deterministic rule-based answers computed strictly in Python/SQLAlchemy.
    Zero hallucination, 100% exact math.
    """
    q = question.lower().strip()
    stats = get_dashboard_stats(db)
    total = stats["total_students"]

    if total == 0:
        return "There are currently no student records in the database."

    # Question: How many students / student count?
    if re.search(r"\b(how many students|total students|student count|number of students|records exist)\b", q):
        return f"There are currently {total} student record(s) registered in the system."

    # Question: Which course has most students?
    if re.search(r"\b(most students|popular course|highest enrollment|top course)\b", q):
        dist = stats["course_distribution"]
        if not dist:
            return "No course enrollment data is available."
        top_course, top_count = list(dist.items())[0]
        return f"The course with the most students is '{top_course}' with {top_count} enrolled student(s)."

    # Question: Course summary / distribution?
    if re.search(r"\b(course distribution|summary by course|courses list|enrollment by course)\b", q):
        dist = stats["course_distribution"]
        lines = [f"- {course}: {cnt} student(s)" for course, cnt in dist.items()]
        return f"Current course distribution ({stats['total_courses']} courses):\n" + "\n".join(lines)

    # Question: Students born after year?
    born_after_match = re.search(r"born after (\d{4})", q)
    if born_after_match:
        year = int(born_after_match.group(1))
        from datetime import date
        cutoff = date(year, 12, 31)
        students = db.query(Student).filter(Student.date_of_birth > cutoff).all()
        if not students:
            return f"No students were born after {year}."
        names = [f"{s.name} ({s.course or 'No course'}, DOB: {s.date_of_birth})" for s in students]
        return f"Found {len(students)} student(s) born after {year}:\n" + "\n".join(f"- {n}" for n in names)

    # Question: Students enrolled in [course]?
    course_match = re.search(r"enrolled in (.+)", q)
    if course_match:
        target_course = course_match.group(1).strip().strip("?.,'\"")
        students = db.query(Student).filter(Student.course.ilike(f"%{target_course}%")).all()
        if not students:
            return f"No students are enrolled in course matching '{target_course}'."
        names = [f"{s.name} (Enrolled: {s.enrollment_date or 'N/A'})" for s in students]
        return f"Found {len(students)} student(s) in '{target_course}':\n" + "\n".join(f"- {n}" for n in names)

    return None


async def ask_ai_assistant(db: Session, question: str) -> Dict[str, Any]:
    """
    Processes user query:
    1. First checks for an exact deterministic calculation in Python.
    2. If Ollama is available, enriches response using local LLM with non-PII context.
    3. If Ollama is unavailable, returns accurate deterministic answer or helpful guidance.
    """
    stats = get_dashboard_stats(db)
    det_answer = compute_grounded_answer(db, question)

    # Check Ollama status
    ollama_status = await check_ollama_status()

    if not ollama_status["available"]:
        if det_answer:
            return {
                "answer": det_answer,
                "source": "deterministic (Ollama offline)",
                "context_summary": stats,
            }
        return {
            "answer": (
                f"Local Ollama service is currently unavailable at {settings.OLLAMA_BASE_URL}. "
                f"Currently there are {stats['total_students']} student(s) registered across "
                f"{stats['total_courses']} course(s). Start Ollama (`ollama run {settings.OLLAMA_MODEL}`) "
                "for natural-language queries."
            ),
            "source": "deterministic (Ollama offline)",
            "context_summary": stats,
        }

    # Prepare privacy-safe, non-PII summary context
    students_sample = (
        db.query(Student.name, Student.course, Student.date_of_birth, Student.enrollment_date)
        .limit(25)
        .all()
    )
    student_summaries = [
        f"Name: {s.name}, Course: {s.course or 'N/A'}, DOB: {s.date_of_birth}, Enrolled: {s.enrollment_date or 'N/A'}"
        for s in students_sample
    ]

    context_str = (
        f"Database Summary:\n"
        f"Total Students: {stats['total_students']}\n"
        f"Total Courses: {stats['total_courses']}\n"
        f"Course Distribution: {stats['course_distribution']}\n\n"
        f"Sample Records (Non-PII):\n" + "\n".join(student_summaries)
    )

    prompt = (
        "You are an academic database assistant for the EWB Student Record Management System. "
        "Answer the question based STRICTLY and ONLY on the following context. "
        "Do not invent facts or SQL. If the information is not in the context, say so concisely.\n\n"
        f"{context_str}\n\n"
        f"User Question: {question}\n\n"
        "Concise Answer:"
    )

    try:
        async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT_SECONDS) as client:
            resp = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            if resp.status_code == 200:
                answer = resp.json().get("response", "").strip()
                return {
                    "answer": answer or (det_answer or "No response generated."),
                    "source": "ollama",
                    "context_summary": stats,
                }
    except Exception:
        pass

    # Fallback if Ollama request times out or errors
    return {
        "answer": det_answer or f"Total students: {stats['total_students']}. Courses: {stats['total_courses']}.",
        "source": "deterministic (Ollama timed out)",
        "context_summary": stats,
    }
