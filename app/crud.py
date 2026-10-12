from datetime import date, timedelta
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc
from app.models import Student
from app.schemas import StudentCreate, StudentUpdate, StudentPatch


def get_student_by_id(db: Session, student_id: int) -> Optional[Student]:
    """Retrieve a single student by primary key ID."""
    return db.query(Student).filter(Student.id == student_id).first()


def get_student_by_email(db: Session, email: str, exclude_id: Optional[int] = None) -> Optional[Student]:
    """Retrieve a student by email address, optionally excluding a student ID for updates."""
    if not email:
        return None
    query = db.query(Student).filter(func.lower(Student.email) == email.lower().strip())
    if exclude_id is not None:
        query = query.filter(Student.id != exclude_id)
    return query.first()


def get_students(
    db: Session,
    search: Optional[str] = None,
    course: Optional[str] = None,
    enrolled_after: Optional[date] = None,
    enrolled_before: Optional[date] = None,
    born_after: Optional[date] = None,
    born_before: Optional[date] = None,
    skip: int = 0,
    limit: int = 10,
    sort_by: str = "id",
    sort_order: str = "desc"
) -> Tuple[List[Student], int]:
    """
    Query students with case-insensitive search, filters, pagination, and stable sorting.
    Returns (items, total_count).
    """
    query = db.query(Student)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(Student.name.ilike(term))

    if course and course.strip():
        query = query.filter(func.lower(Student.course) == course.strip().lower())

    if enrolled_after:
        query = query.filter(Student.enrollment_date >= enrolled_after)

    if enrolled_before:
        query = query.filter(Student.enrollment_date <= enrolled_before)

    if born_after:
        query = query.filter(Student.date_of_birth >= born_after)

    if born_before:
        query = query.filter(Student.date_of_birth <= born_before)

    total = query.count()

    # Stable sorting
    order_col = Student.id
    if sort_by == "name":
        order_col = Student.name
    elif sort_by == "enrollment_date":
        order_col = Student.enrollment_date
    elif sort_by == "date_of_birth":
        order_col = Student.date_of_birth

    if sort_order.lower() == "asc":
        query = query.order_by(order_col.asc(), Student.id.asc())
    else:
        query = query.order_by(order_col.desc(), Student.id.desc())

    # Clamp limit
    clamped_limit = max(1, min(limit, 100))
    clamped_skip = max(0, skip)

    items = query.offset(clamped_skip).limit(clamped_limit).all()
    return items, total


def create_student(db: Session, student_in: StudentCreate) -> Student:
    """Create a new student record and commit to database."""
    student_data = student_in.model_dump()
    db_student = Student(**student_data)
    try:
        db.add(db_student)
        db.commit()
        db.refresh(db_student)
        return db_student
    except Exception:
        db.rollback()
        raise


def update_student_put(db: Session, student: Student, student_in: StudentUpdate) -> Student:
    """Completely replace the editable fields of an existing student."""
    update_data = student_in.model_dump()
    for field, value in update_data.items():
        setattr(student, field, value)

    try:
        db.commit()
        db.refresh(student)
        return student
    except Exception:
        db.rollback()
        raise


def patch_student(db: Session, student: Student, patch_in: StudentPatch) -> Student:
    """
    Partially update supplied fields.
    Validates that the resulting state preserves at least one contact method.
    """
    update_data = patch_in.model_dump(exclude_unset=True)

    future_email = update_data.get("email", student.email)
    future_phone = update_data.get("phone", student.phone)

    has_email = bool(future_email and str(future_email).strip())
    has_phone = bool(future_phone and str(future_phone).strip())

    if not has_email and not has_phone:
        raise ValueError("Cannot remove both email and phone; at least one contact method must remain.")

    for field, value in update_data.items():
        setattr(student, field, value)

    try:
        db.commit()
        db.refresh(student)
        return student
    except Exception:
        db.rollback()
        raise


def delete_student(db: Session, student: Student) -> None:
    """Delete a student record from the database."""
    try:
        db.delete(student)
        db.commit()
    except Exception:
        db.rollback()
        raise


def get_dashboard_stats(db: Session) -> Dict[str, Any]:
    """
    Calculate live database statistics from stored records:
    - Total registered students
    - Number of distinct courses
    - Recently enrolled students (past 30 days)
    - Distribution of students by course
    """
    total_students = db.query(func.count(Student.id)).scalar() or 0

    # Distinct courses count (excluding null/empty)
    distinct_courses = (
        db.query(func.count(func.distinct(Student.course)))
        .filter(Student.course.isnot(None), Student.course != "")
        .scalar()
        or 0
    )

    # Recent enrollments (past 30 days)
    thirty_days_ago = date.today() - timedelta(days=30)
    recent_enrollments = (
        db.query(func.count(Student.id))
        .filter(Student.enrollment_date >= thirty_days_ago)
        .scalar()
        or 0
    )

    # Course distribution
    distribution_rows = (
        db.query(Student.course, func.count(Student.id))
        .filter(Student.course.isnot(None), Student.course != "")
        .group_by(Student.course)
        .order_by(desc(func.count(Student.id)))
        .all()
    )

    course_distribution = {course: count for course, count in distribution_rows}

    # Include unassigned count if any
    unassigned = (
        db.query(func.count(Student.id))
        .filter(or_(Student.course.is_(None), Student.course == ""))
        .scalar()
        or 0
    )
    if unassigned > 0:
        course_distribution["Unassigned"] = unassigned

    return {
        "total_students": total_students,
        "total_courses": distinct_courses,
        "recent_enrollments_count": recent_enrollments,
        "course_distribution": course_distribution,
    }


def get_distinct_courses_list(db: Session) -> List[str]:
    """Retrieve list of distinct non-empty course names."""
    rows = (
        db.query(Student.course)
        .filter(Student.course.isnot(None), Student.course != "")
        .distinct()
        .order_by(Student.course)
        .all()
    )
    return [r[0] for r in rows if r[0]]
