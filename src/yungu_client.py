"""
Yungu Classroom Client v2 — Full Read-Only Student Dashboard
=============================================================

All known API endpoints from task.yungu.org, organized by status.
"""

import requests
import json
from datetime import datetime, date
from typing import Optional, List, Dict


class YunguClient:
    """云谷课堂 API 客户端 — 只读查询"""

    BASE_URL = "https://task.yungu.org"

    def __init__(self, session_cookie: str):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/'
                          '537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://task.yungu.org/#/',
        })
        self.session.cookies.set('SESSION', session_cookie, domain='.yungu.org')

    # ── Helpers ──────────────────────────────────────────────────────

    def _get(self, path: str, params: dict = None) -> tuple:
        """GET → (data_dict, success_flag)"""
        try:
            r = self.session.get(f"{self.BASE_URL}{path}", params=params, timeout=15)
            d = r.json()
            if d.get("ifLogin") is not True:
                return {"_error": d.get("message", "login_expired")}, False
            return d, d.get("status", False)
        except Exception as e:
            return {"_error": str(e)}, False

    def _post(self, path: str, body: dict = None) -> tuple:
        """POST → (data_dict, success_flag)"""
        try:
            r = self.session.post(
                f"{self.BASE_URL}{path}", json=body,
                headers={"Content-Type": "application/json"}, timeout=15,
            )
            d = r.json()
            if d.get("ifLogin") is not True:
                return {"_error": d.get("message", "login_expired")}, False
            return d, d.get("status", False)
        except Exception as e:
            return {"_error": str(e)}, False

    # ── Public Query Methods ─────────────────────────────────────────

    def verify_session(self) -> bool:
        data, _ = self._get("/api/user/info")
        return isinstance(data, dict) and data.get("ifLogin") is True

    def get_user_info(self) -> dict:
        """Get detailed user profile (userId, identity, grade, stage)."""
        data, _ = self._get("/api/currentUser")
        return data.get("content", {}) if isinstance(data, dict) else {}

    def get_current_semester_id(self) -> int:
        sems = self.list_semesters()
        for s in sems:
            name = s.get("semesterName", "")
            if "第一学期" in name:
                return s["semesterId"]
        return sems[-1]["semesterId"] if sems else 491

    def list_semesters(self) -> list:
        data, _ = self._get("/api/all/semester")
        return data.get("content", []) if isinstance(data, dict) else []

    def list_courses(self, semester_id: int = None) -> list:
        """List all courses for a semester."""
        if semester_id is None:
            semester_id = self.get_current_semester_id()
        data, _ = self._get("/api/course/listCoursesBySemId", {"semId": semester_id})
        return data.get("content", []) if isinstance(data, dict) else []

    def get_teaching_reflection(self, course_id: int, semester_id: int = None) -> dict:
        """Get teaching reflection prompts for a course."""
        if semester_id is None:
            semester_id = self.get_current_semester_id()
        data, _ = self._post(
            "/api/lesson/lectureRecordAndTeachingReflection",
            {"courseId": course_id, "semesterId": semester_id},
        )
        return data.get("content", {}) if isinstance(data, dict) else {}

    def get_course_grades(self, semester_id: int = None) -> list:
        data, _ = self._get("/api/all/course/grades", {"semesterId": semester_id})
        return data.get("content", []) if isinstance(data, dict) else []

    def get_teachers_for_course(self, course_id: int) -> list:
        """Get teachers associated with a course."""
        data, _ = self._get("/api/list/lesson/teacher", {"semesterId": self.get_current_semester_id()})
        return data.get("content", []) if isinstance(data, dict) else []

    def get_my_lessons(self, **kwargs) -> list:
        """Get student's lesson list (requires specific context params)."""
        data, _ = self._get("/api/user/relation/myLessonList", kwargs)
        return data.get("content", []) if isinstance(data, dict) else []

    def get_feedback_plan_week(self, **kwargs) -> dict:
        """Get week plan/feedback data for student."""
        data, _ = self._get("/api/feedback/parent/planWeek", kwargs)
        return data.get("content", {}) if isinstance(data, dict) else {}

    def get_feedback_plan_week_detail(self, **kwargs) -> dict:
        """Get detailed week plan feedback."""
        data, _ = self._get("/api/feedback/parent/planWeekDetail", kwargs)
        return data.get("content", {}) if isinstance(data, dict) else {}

    def get_day_statistics(self, **kwargs) -> dict:
        """Get yesterday's statistics per course."""
        data, _ = self._get("/api/read/yesterdayStatistics", kwargs)
        return data.get("content", {}) if isinstance(data, dict) else {}

    # ── Full Data Export ─────────────────────────────────────────────

    def export_all_data(self, semester_id: int = None) -> dict:
        """Export all available data as JSON structure."""
        if semester_id is None:
            semester_id = self.get_current_semester_id()

        result = {
            "generated_at": datetime.now().isoformat(),
            "semester_id": semester_id,
            "user": self.get_user_info(),
            "semesters": self.list_semesters(),
            "courses": [],
        }

        courses = self.list_courses(semester_id)
        for c in courses:
            cid = c["courseId"]
            reflection = self.get_teaching_reflection(cid, semester_id)
            
            entry = {
                "courseId": cid,
                "name": c["courseName"],
                "enName": c.get("courseEnName"),
                "grade": c.get("suitGradeName"),
                "color": c.get("subjectColor"),
                "reflection_prompts": reflection.get("teachingReflectionPrompts", ""),
                "lecture_prompts": (reflection.get("lectureAttendancePrompts") or "")[:500],
            }
            result["courses"].append(entry)

        return result


def load_session_cookie(path: str = None) -> Optional[str]:
    if path is None:
        path = "/home/andy.xkd/.hermes/skills/yungu-classroom/.session_cookie"
    try:
        with open(path) as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("#") or not stripped:
                    continue
                parts = stripped.split("\t")
                if len(parts) >= 7 and parts[5] == "SESSION":
                    return parts[6]
    except FileNotFoundError:
        pass
    return None
