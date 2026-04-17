"""Pydantic models for the Recommendation Service."""

from typing import List, Optional
from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    student_email: Optional[str] = Field(None, description="Student email")
    student_id: Optional[str] = Field(None, description="Student UUID")
    english_level: Optional[str] = Field(None, description="English level: A1, A2, B1, B2, C1, C2")
    limit: int = Field(5, ge=1, le=20, description="Max number of recommendations")


class CourseRecommendation(BaseModel):
    course_id: int
    title: str
    score: float = Field(description="Relevance score 0-100")
    reason: str = Field(description="Why this course is recommended")
    difficulty: str
    duration_hours: Optional[int] = None


class RecommendationResponse(BaseModel):
    student_email: Optional[str]
    english_level: str
    recommendations: List[CourseRecommendation]
    total: int
