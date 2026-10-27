"""
Yungu Classroom Client - v1.0
==============================
Provides read-only access to student data from task.yungu.org (云谷课堂).

Known working API endpoints (discovered 2026-10-26):
┌─────────────────────────────────────────────┬───────┐
│ Endpoint                                    │ Method│
├─────────────────────────────────────────────┼───────┤
│ /api/all/semester                           │ GET   │
│ /api/course/listCoursesBySemId?semId=       │ GET   │
│ /api/lesson/lectureRecordAndTeachingReflection│ POST │
│ /api/all/course/grades                      │ GET   │
│ /api/user/relation/updateIsPublic           │ POST  │
└─────────────────────────────────────────────┴───────┘

NOT YET DISCOVERED (need browser/network trace):
- Today's schedule/timetable
- Per-course lesson plan details
- Homework/assignment status  
- Student daily activities
"""

import requests
import json
from datetime import datetime, date, timedelta
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

    def _get(self, path: str, params: dict = None) -> Optional[dict]:
        """GET request → (json_data, success_flag)"""
        try:
            r = self.session.get(f"{self.BASE_URL}{path}", params=params, timeout=15)
            d = r.json()
            if d.get("ifLogin") is not True:
                return {"_error": d.get("message", "login_required")}, False
            return d, d.get("status", False)
        except Exception as e:
            return {"_error": str(e)}, False

    def _post(self, path: str, body: dict = None) -> Optional[dict]:
        """POST request → (json_data, success_flag)"""
        try:
            r = self.session.post(
                f"{self.BASE_URL}{path}",
                json=body, headers={"Content-Type": "application/json"},
                timeout=15,
            )
            d = r.json()
            if d.get("ifLogin") is not True:
                return {"_error": d.get("message", "login_required")}, False
            return d, d.get("status", False)
        except Exception as e:
            return {"_error": str(e)}, False

    # ── Public query methods ────────────────────────────────────────

    def verify_session(self) -> bool:
        """Check whether the current session cookie is still valid."""
        data, _ = self._get("/api/user/info")
        return isinstance(data, dict) and data.get("ifLogin") is True

    def get_current_semester_id(self) -> int:
        """Return the current semester ID (prefers first semester)."""
        sems = self.list_semesters()
        for s in sems:
            name = s.get("semesterName", "")
            if "第一学期" in name:
                return s["semesterId"]
        return sems[-1]["semesterId"] if sems else 491

    def list_semesters(self) -> list:
        """List all available semesters."""
        data, _ = self._get("/api/all/semester")
        return data.get("content", []) if isinstance(data, dict) else []

    def list_courses(self, semester_id: int = None) -> list:
        """List all courses for a given semester."""
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
        """Get grade information for courses."""
        if semester_id is None:
            semester_id = self.get_current_semester_id()
        data, _ = self._get("/api/all/course/grades", {"semesterId": semester_id})
        return data.get("content", []) if isinstance(data, dict) else []

    def today_schedule(self) -> dict:
        """
        Build today's simplified schedule from known data.
        
        TODO: This returns basic info only. Full schedule requires
        additional endpoints that were not discoverable without 
        browser-based API tracing.
        """
        sid = self.get_current_semester_id()
        courses = self.list_courses(sid)
        todays_plan = {
            "date": date.today().isoformat(),
            "weekday": date.today().strftime("%A"),
            "courses": [],
        }
        for c in courses:
            cid = c["courseId"]
            reflection = self.get_teaching_reflection(cid, sid)
            entry = {
                "courseId": cid,
                "name": c["courseName"],
                "enName": c.get("courseEnName"),
                "grade": c.get("suitGradeName"),
                "color": c.get("subjectColor", "#888888"),
            }
            prompts = reflection.get("teachingReflectionPrompts", "")
            if prompts:
                entry["reflections"] = prompts[:300]
            todays_plan["courses"].append(entry)
        return todays_plan


def load_session_cookie(path: str = None) -> Optional[str]:
    """Load SESSION cookie from Netscape-format file."""
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


# ── CLI entry point ────────────────────────────────────────────────

def main():
    cookie = load_session_cookie()
    if not cookie:
        print("Error: No SESSION cookie found.")
        return

    client = YunguClient(cookie)

    if not client.verify_session():
        print("Error: Session expired or invalid.")
        return

    sid = client.get_current_semester_id()
    semesters = client.list_semesters()
    cur = next((s for s in semesters if s["semesterId"] == sid), None)

    print("=" * 60)
    print("  Yungu Classroom — Read-Only Data Query")
    print("=" * 60)
    print(f"\n  Semester : {cur.get('semesterName') if cur else '?'}")
    print(f"  Semester ID : {sid}")
    print()

    # Courses
    courses = client.list_courses(sid)
    print(f"  📚 Courses ({len(courses)}):")
    for i, c in enumerate(courses, 1):
        print(f"     {i:>2}. {c['courseName']} ({c['courseId']}) | Grade: {c.get('suitGradeName','?')}")

    # Today's schedule
    sched = client.today_schedule()
    print(f"\n  📅 Today ({sched['date']}) — {sched['weekday']}")
    for c in sched["courses"]:
        ref = c.pop("reflections", "")
        marker = "🟦" if c["color"] else "⬛"
        print(f"     {marker} {c['name']}")
        if ref:
            print(f"        💡 {ref[:120]}...")

    print(f"\n  ✅ Done")


if __name__ == "__main__":
    main()
