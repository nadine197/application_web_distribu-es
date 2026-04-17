"""
Course recommendation engine.
Uses a rule-based scoring algorithm:
  - Level match score     (40 pts)
  - Not already completed (30 pts)
  - Quiz performance      (20 pts)
  - Course popularity     (10 pts)
"""

import logging
from typing import List, Dict, Any

from models import CourseRecommendation

logger = logging.getLogger(__name__)

# CEFR level ordering
LEVEL_ORDER = {"A1": 0, "A2": 1, "B1": 2, "B2": 3, "C1": 4, "C2": 5}

# Level → expected difficulty label mapping
LEVEL_DIFFICULTY = {
    "A1": ["beginner", "a1"],
    "A2": ["beginner", "elementary", "a1", "a2"],
    "B1": ["elementary", "intermediate", "a2", "b1"],
    "B2": ["intermediate", "upper-intermediate", "b1", "b2"],
    "C1": ["upper-intermediate", "advanced", "b2", "c1"],
    "C2": ["advanced", "proficiency", "c1", "c2"],
}


class CourseRecommender:

    def recommend(
        self,
        student_level: str,
        all_courses: List[Dict[str, Any]],
        quiz_results: List[Dict[str, Any]],
        limit: int = 5,
    ) -> List[CourseRecommendation]:

        if not all_courses:
            logger.warning("No courses available to recommend")
            return []

        # Build set of already-completed course IDs from quiz results
        completed_ids = {
            str(r.get("courseId") or r.get("course_id", ""))
            for r in quiz_results
            if r.get("passed") or r.get("score", 0) >= 70
        }

        level_idx = LEVEL_ORDER.get(student_level.upper(), 0)
        allowed_difficulties = LEVEL_DIFFICULTY.get(student_level.upper(), ["beginner"])

        scored = []
        for course in all_courses:
            score = 0.0
            course_id  = course.get("id") or course.get("courseId", 0)
            title      = course.get("title") or course.get("name", "Unknown Course")
            difficulty = (course.get("difficulty") or course.get("level") or "beginner").lower()
            duration   = course.get("duration") or course.get("durationHours")

            # ── 1. Level match (40 pts) ───────────────────────────────────────
            if difficulty in allowed_difficulties:
                score += 40
            else:
                # Penalize courses that are too easy or too hard
                course_level_idx = self._difficulty_to_idx(difficulty)
                distance = abs(level_idx - course_level_idx)
                score += max(0, 40 - distance * 10)

            # ── 2. Not completed (30 pts) ─────────────────────────────────────
            if str(course_id) not in completed_ids:
                score += 30

            # ── 3. Quiz performance bonus (20 pts) ────────────────────────────
            # If student scored > 80% in related quizzes, boost next-level courses
            if quiz_results:
                avg_score = sum(r.get("score", 0) for r in quiz_results) / len(quiz_results)
                if avg_score >= 80 and self._is_next_level(difficulty, level_idx):
                    score += 20
                elif avg_score >= 60:
                    score += 10

            # ── 4. Popularity (10 pts) ────────────────────────────────────────
            enroll_count = course.get("enrollmentCount") or course.get("students") or 0
            if enroll_count > 100:
                score += 10
            elif enroll_count > 50:
                score += 5

            reason = self._build_reason(student_level, difficulty, str(course_id) in completed_ids)

            scored.append(CourseRecommendation(
                course_id=int(course_id) if str(course_id).isdigit() else 0,
                title=title,
                score=round(score, 1),
                reason=reason,
                difficulty=difficulty.capitalize(),
                duration_hours=int(duration) if duration else None,
            ))

        # Sort by score descending, return top N
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:limit]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "algorithm": "rule-based scoring",
            "factors": [
                "Level match (40 pts)",
                "Not completed (30 pts)",
                "Quiz performance (20 pts)",
                "Popularity (10 pts)",
            ],
            "supported_levels": list(LEVEL_ORDER.keys()),
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _difficulty_to_idx(self, difficulty: str) -> int:
        mapping = {
            "beginner": 0, "a1": 0,
            "elementary": 1, "a2": 1,
            "intermediate": 2, "b1": 2,
            "upper-intermediate": 3, "b2": 3,
            "advanced": 4, "c1": 4,
            "proficiency": 5, "c2": 5,
        }
        return mapping.get(difficulty.lower(), 2)

    def _is_next_level(self, difficulty: str, current_idx: int) -> bool:
        """Return True if the course is one level above the student."""
        return self._difficulty_to_idx(difficulty) == current_idx + 1

    def _build_reason(self, student_level: str, difficulty: str, already_done: bool) -> str:
        if already_done:
            return f"Review course — reinforce your {student_level} knowledge"
        diff_idx = self._difficulty_to_idx(difficulty)
        level_idx = LEVEL_ORDER.get(student_level.upper(), 0)
        if diff_idx == level_idx:
            return f"Perfect match for your {student_level} level"
        elif diff_idx == level_idx + 1:
            return f"Challenge yourself — step up from {student_level}"
        elif diff_idx < level_idx:
            return f"Consolidate your foundations before advancing"
        else:
            return f"Recommended for your learning journey"
