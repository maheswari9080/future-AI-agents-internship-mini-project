from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator, ConfigDict


class StudentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Full name of student")
    date_of_birth: date = Field(..., description="Date of birth (must be in the past)")
    email: Optional[EmailStr] = Field(None, description="Valid email address")
    phone: Optional[str] = Field(None, max_length=50, description="Contact phone number")
    course: Optional[str] = Field(None, max_length=100, description="Enrolled course name")
    address: Optional[str] = Field(None, description="Residential or postal address")
    enrollment_date: Optional[date] = Field(None, description="Date of enrollment")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Student name cannot be empty or only whitespace")
        return trimmed

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: date) -> date:
        if v >= date.today():
            raise ValueError("Date of birth must be a past date")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            return trimmed if trimmed else None
        return None

    @field_validator("course", "address")
    @classmethod
    def validate_string_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            return trimmed if trimmed else None
        return None

    @model_validator(mode="after")
    def validate_contact_methods(self) -> "StudentBase":
        has_email = bool(self.email and str(self.email).strip())
        has_phone = bool(self.phone and self.phone.strip())
        if not has_email and not has_phone:
            raise ValueError("At least one contact method (email or phone) is required")
        return self


class StudentCreate(StudentBase):
    pass


class StudentUpdate(StudentBase):
    pass


class StudentPatch(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    course: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    enrollment_date: Optional[date] = None

    @field_validator("name")
    @classmethod
    def validate_patch_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Student name cannot be empty or only whitespace")
            return trimmed
        return None

    @field_validator("date_of_birth")
    @classmethod
    def validate_patch_dob(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v >= date.today():
            raise ValueError("Date of birth must be a past date")
        return v

    @field_validator("phone")
    @classmethod
    def validate_patch_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            return trimmed if trimmed else None
        return None

    @field_validator("course", "address")
    @classmethod
    def validate_patch_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            return trimmed if trimmed else None
        return None


class StudentResponse(BaseModel):
    id: int
    name: str
    date_of_birth: date
    email: Optional[str] = None
    phone: Optional[str] = None
    course: Optional[str] = None
    address: Optional[str] = None
    enrollment_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudentListResponse(BaseModel):
    items: List[StudentResponse]
    total: int
    page: int
    limit: int
    pages: int


class DashboardStats(BaseModel):
    total_students: int
    total_courses: int
    recent_enrollments_count: int
    course_distribution: Dict[str, int]


class AIQuestionRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500, description="Natural language inquiry about students")

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        trimmed = v.strip()
        if len(trimmed) < 3:
            raise ValueError("Question must be at least 3 characters long")
        return trimmed


class AIResponse(BaseModel):
    answer: str
    source: str = Field("deterministic", description="'ollama' or 'deterministic'")
    context_summary: Optional[Dict[str, Any]] = None
