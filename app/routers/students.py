from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import crud
from app.schemas import (
    StudentCreate,
    StudentUpdate,
    StudentPatch,
    StudentResponse,
    StudentListResponse,
    DashboardStats,
)

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("/stats", response_model=DashboardStats)
def get_student_statistics(db: Session = Depends(get_db)):
    """Calculate and return live dashboard metrics from current database records."""
    return crud.get_dashboard_stats(db)


@router.get("/courses", response_model=List[str])
def get_available_courses(db: Session = Depends(get_db)):
    """Retrieve distinct course names for filter dropdowns."""
    return crud.get_distinct_courses_list(db)


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(
    student_in: StudentCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new student record.
    Enforces required name, valid past DOB, and at least one contact method (email or phone).
    """
    if student_in.email:
        existing = crud.get_student_by_email(db, student_in.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Student with email '{student_in.email}' already exists.",
            )

    return crud.create_student(db, student_in)


@router.get("", response_model=StudentListResponse)
def list_students(
    search: Optional[str] = Query(None, description="Case-insensitive name search"),
    course: Optional[str] = Query(None, description="Filter by exact course name"),
    enrolled_after: Optional[date] = Query(None, description="Enrolled on or after date"),
    enrolled_before: Optional[date] = Query(None, description="Enrolled on or before date"),
    born_after: Optional[date] = Query(None, description="Born on or after date"),
    born_before: Optional[date] = Query(None, description="Born on or before date"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(10, ge=1, le=100, description="Items per page (max 100)"),
    sort_by: str = Query("id", pattern="^(id|name|enrollment_date|date_of_birth)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    """
    List student records with search, filtering, pagination, and stable sorting.
    """
    skip = (page - 1) * limit
    items, total = crud.get_students(
        db,
        search=search,
        course=course,
        enrolled_after=enrolled_after,
        enrolled_before=enrolled_before,
        born_after=born_after,
        born_before=born_before,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    pages = (total + limit - 1) // limit if total > 0 else 1

    return StudentListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.get("/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db)):
    """Retrieve an individual student by primary key ID."""
    student = crud.get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found.",
        )
    return student


@router.put("/{student_id}", response_model=StudentResponse)
def update_student_full(
    student_id: int,
    student_in: StudentUpdate,
    db: Session = Depends(get_db)
):
    """
    Completely replace an existing student record (PUT).
    All fields are validated.
    """
    student = crud.get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found.",
        )

    if student_in.email:
        duplicate = crud.get_student_by_email(db, student_in.email, exclude_id=student_id)
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{student_in.email}' is already in use by another student.",
            )

    return crud.update_student_put(db, student, student_in)


@router.patch("/{student_id}", response_model=StudentResponse)
def patch_student_partial(
    student_id: int,
    patch_in: StudentPatch,
    db: Session = Depends(get_db)
):
    """
    Partially update supplied fields of an existing student record (PATCH).
    Guarantees that at least one contact method remains.
    """
    student = crud.get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found.",
        )

    if patch_in.email:
        duplicate = crud.get_student_by_email(db, patch_in.email, exclude_id=student_id)
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{patch_in.email}' is already in use by another student.",
            )

    try:
        return crud.patch_student(db, student, patch_in)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: int, db: Session = Depends(get_db)):
    """Delete a student record by ID. Returns 204 No Content."""
    student = crud.get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found.",
        )
    crud.delete_student(db, student)
    return None
