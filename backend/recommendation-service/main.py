"""
EnglishForU — Recommendation Service (Python / FastAPI)
Recommande des cours selon le niveau, les quiz complétés et le profil de l'étudiant.
S'enregistre sur Eureka pour être découvert par le Gateway.
"""

import os
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware

from eureka import EurekaClient
from recommender import CourseRecommender
from models import RecommendationRequest, RecommendationResponse
from auth import verify_jwt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
SERVICE_PORT   = int(os.getenv("SERVER_PORT", 8091))
SERVICE_HOST   = os.getenv("SERVICE_HOST", "recommendation-service")
EUREKA_URL     = os.getenv("EUREKA_URL", "http://localhost:8761/eureka")
COURSE_SVC_URL = os.getenv("COURSE_SERVICE_URL", "http://localhost:8084")
USER_SVC_URL   = os.getenv("USER_SERVICE_URL",   "http://localhost:8081")
QUIZ_SVC_URL   = os.getenv("QUIZ_SERVICE_URL",   "http://localhost:8056")


# ── Eureka registration ───────────────────────────────────────────────────────
eureka_client = EurekaClient(
    app_name="recommendation-service",
    instance_host=SERVICE_HOST,
    instance_port=SERVICE_PORT,
    eureka_url=EUREKA_URL,
)

recommender = CourseRecommender()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Register on Eureka at startup, deregister at shutdown."""
    await eureka_client.register()
    logger.info("✅ Registered on Eureka as 'recommendation-service'")
    yield
    await eureka_client.deregister()
    logger.info("👋 Deregistered from Eureka")


# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Recommendation Service",
    description="Course recommendation engine for EnglishForU",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:80", "http://localhost"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


# ── Health check (required by Eureka) ────────────────────────────────────────
@app.get("/actuator/health")
async def health():
    return {"status": "UP"}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/api/recommendations", response_model=RecommendationResponse)
async def get_recommendations(
    request: RecommendationRequest,
    authorization: str = Header(None),
):
    """
    Returns personalized course recommendations for a student.
    Calls Course service and Quiz service to gather context.
    JWT is forwarded to downstream services.
    """
    # Validate JWT
    user_ctx = verify_jwt(authorization)
    if user_ctx is None:
        raise HTTPException(status_code=401, detail="Invalid or missing JWT token")

    headers = {"Authorization": authorization} if authorization else {}

    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Fetch all available courses from Course service
        try:
            courses_resp = await client.get(f"{COURSE_SVC_URL}/api/courses", headers=headers)
            courses_resp.raise_for_status()
            all_courses = courses_resp.json()
        except Exception as e:
            logger.warning(f"Could not reach Course service: {e}")
            all_courses = []

        # 2. Fetch student quiz results from Quiz service
        quiz_results = []
        if request.student_email:
            try:
                quiz_resp = await client.get(
                    f"{QUIZ_SVC_URL}/api/quiz-attempts/overview",
                    params={"studentId": request.student_id} if request.student_id else {},
                    headers=headers,
                )
                if quiz_resp.status_code == 200:
                    quiz_results = quiz_resp.json()
            except Exception as e:
                logger.warning(f"Could not reach Quiz service: {e}")

        # 3. Fetch student profile from User service
        student_profile = {}
        if request.student_email:
            try:
                user_resp = await client.get(
                    f"{USER_SVC_URL}/api/users/public/by-email",
                    params={"email": request.student_email},
                    headers=headers,
                )
                if user_resp.status_code == 200:
                    student_profile = user_resp.json()
            except Exception as e:
                logger.warning(f"Could not reach User service: {e}")

    # 4. Run recommendation algorithm
    recommendations = recommender.recommend(
        student_level=request.english_level or student_profile.get("englishLevel", "A1"),
        all_courses=all_courses,
        quiz_results=quiz_results,
        limit=request.limit,
    )

    return RecommendationResponse(
        student_email=request.student_email,
        english_level=request.english_level or student_profile.get("englishLevel", "A1"),
        recommendations=recommendations,
        total=len(recommendations),
    )


@app.get("/api/recommendations/levels")
async def get_levels():
    """Returns supported English levels."""
    return {
        "levels": ["A1", "A2", "B1", "B2", "C1", "C2"],
        "descriptions": {
            "A1": "Beginner",
            "A2": "Elementary",
            "B1": "Intermediate",
            "B2": "Upper-Intermediate",
            "C1": "Advanced",
            "C2": "Proficiency",
        }
    }


@app.get("/api/recommendations/stats")
async def get_stats(authorization: str = Header(None)):
    """Returns recommendation engine statistics."""
    user_ctx = verify_jwt(authorization)
    if user_ctx is None:
        raise HTTPException(status_code=401, detail="Invalid or missing JWT token")
    return recommender.get_stats()
