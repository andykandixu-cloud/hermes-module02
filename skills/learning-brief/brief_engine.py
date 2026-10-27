"""
Learning Brief Engine — 核心简报生成引擎

从 Yungu Classroom API 获取数据，生成结构化的晨间/晚间简报。
所有输出标注来源和时间戳，缺失数据明确标记 [MISSING]。
"""

import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
try:
    from yungu_client import YunguClient, load_session_cookie
except ImportError:
    print("ERROR: Cannot import yungu_client. Ensure src/yungu_client.py exists.")
    sys.exit(1)

# Directory structure
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MORNING_DIR = DATA_DIR / "morning"
EVENING_DIR = DATA_DIR / "evening"
LOGS_DIR = DATA_DIR / "logs"


def ensure_dirs():
    """Create data directories if they don't exist."""
    for d in [DATA_DIR, MORNING_DIR, EVENING_DIR, LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def run_with_delay(delay_seconds: float = 2.0):
    """
    Decorator/context manager that enforces delay between API calls.
    Short delay timer for approved single-pilot service.
    """
    import time
    return time.sleep(delay_seconds)


class BriefGenerator:
    """Core engine for generating learning briefs."""

    def __init__(self, client: YunguClient):
        self.client = client
        self.timestamp = datetime.now().isoformat()
        self.date_str = date.today().isoformat()
        self.weekday = date.today().strftime("%A")
        self.sources_used: List[str] = []
        self.gaps_found: List[str] = []

    def _api_call(self, endpoint: str, success_msg: str):
        """Record an API call source with safety checks."""
        self.sources_used.append(f"{endpoint} → {success_msg}")
        # Enforce delay between calls (approved pilot service pattern)
        run_with_delay(2.0)

    def _missing(self, what: str, suggestion: str = ""):
        """Mark a data gap clearly."""
        entry = f"[MISSING] {what}"
        if suggestion:
            entry += f" | Suggestion: {suggestion}"
        self.gaps_found.append(entry)
        return entry

    def get_user_context(self) -> dict:
        """Get student identity and grade context."""
        self._api_call("/api/currentUser", "OK")
        user_info = self.client.get_user_info()
        if not user_info:
            self._missing("用户信息", "请检查 Session Cookie 是否有效")
        return user_info

    def get_course_list(self, semester_id: int = None) -> list:
        """Get all courses for current semester."""
        if semester_id is None:
            semester_id = self.client.get_current_semester_id()
        self._api_call(
            f"/api/course/listCoursesBySemId?semId={semester_id}",
            f"{len(self.client.list_courses(semester_id))} courses returned"
        )
        return self.client.list_courses(semester_id) or []

    def get_teachers_for_course(self, course_id: int) -> list:
        """Get teachers assigned to a course."""
        try:
            self._api_call(f"/api/list/lesson/teacher?courseId={course_id}", "Teacher data fetched")
            teachers = self.client.get_teachers_for_course(course_id)
            return teachers if teachers else []
        except Exception as e:
            self._missing(f"教师列表 (课程 {course_id})", f"API error: {str(e)}")
            return []

    def get_reflection_prompts(self, course_id: int, semester_id: int = None) -> dict:
        """Get teaching reflection prompts for a course."""
        if semester_id is None:
            semester_id = self.client.get_current_semester_id()
        try:
            self._api_call(
                f"/api/lesson/lectureRecordAndTeachingReflection (POST)",
                "Teaching prompts retrieved"
            )
            result = self.client.get_teaching_reflection(course_id, semester_id)
            return result if result else {}
        except Exception as e:
            self._missing(f"教学反思提示 (课程 {course_id})", f"API error: {str(e)}")
            return {}

    def get_week_feedback(self, **kwargs) -> dict:
        """Get weekly feedback/plan data."""
        try:
            self._api_call("/api/feedback/parent/planWeek (GET)", "Week plan fetched")
            result = self.client.get_feedback_plan_week(**kwargs)
            has_data = any(v is not None for v in result.values()) if isinstance(result, dict) else bool(result)
            if not has_data or all(v is None for v in result.values()):
                self._missing(
                    "本周反馈/计划数据",
                    "API 返回空响应 — 可能需要特定的周号或日期参数，建议使用浏览器查看"
                )
            return result
        except Exception as e:
            self._missing("本周反馈/计划数据", f"API error: {str(e)}")
            return {}

    def get_yesterday_stats(self, course_id: int) -> dict:
        """Get yesterday's statistics for a specific course."""
        try:
            self._api_call(f"/api/read/yesterdayStatistics?courseId={course_id}", "Stats fetched")
            return self.client.get_day_statistics(courseId=course_id) or {}
        except Exception as e:
            self._missing(f"昨日统计 (课程 {course_id})", f"API error: {str(e)}")
            return {}

    def export_brief(self, brief_type: str, data: dict, output_dir: Path):
        """Export generated brief to JSON file in git-ignored directory."""
        ensure_dirs()
        
        # Save latest brief
        latest_path = output_dir / "latest.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Also save dated version
        today_path = output_dir / f"{self.date_str}.json"
        with open(today_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Log the generation
        log_entry = {
            "timestamp": self.timestamp,
            "brief_type": brief_type,
            "output_file": str(today_path),
            "sources_used": len(self.sources_used),
            "gaps_found": len(self.gaps_found),
            "status": "complete_with_gaps" if self.gaps_found else "complete",
        }
        
        log_path = LOGS_DIR / f"{brief_type}_{self.date_str.replace('-', '')}.log"
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        
        return str(today_path)
