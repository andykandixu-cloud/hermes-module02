#!/usr/bin/env python3
"""
Yungu Classroom CLI — Student Dashboard v2
===========================================
Read-only dashboard for 云谷课堂 (task.yungu.org).

Usage:
  python3 yungu_cli.py              # Show today's overview
  python3 yungu_cli.py --json       # Output full JSON data
  python3 yungu_cli.py --courses    # List all courses only
  python3 yungu_cli.py --user       # Show user profile
  python3 yungu_cli.py --export     # Export all data to file
  python3 yungu_cli.py --api-list   # List all known API endpoints
"""

import sys
import json
from datetime import date


sys.path.insert(0, "/home/andy.xkd/projects/hermes-module02/src")
from yungu_client import YunguClient, load_session_cookie


# Known working API endpoints for reference
API_ENDPOINTS = {
    "verified": [
        ("GET", "/api/currentUser"),
        ("GET", "/api/all/semester"),
        ("GET", "/api/course/listCoursesBySemId?semId="),
        ("POST", "/api/lesson/lectureRecordAndTeachingReflection"),
        ("GET", "/api/all/course/grades"),
        ("GET", "/api/list/lesson/teacher"),
        ("GET", "/api/user/relation/myLessonList"),
        ("GET", "/api/feedback/parent/planWeek"),
        ("GET", "/api/feedback/parent/planWeekDetail"),
        ("GET", "/api/read/yesterdayStatistics"),
    ],
    "partial": [
        ("GET", "/api/user/relation/lessonListStatistics"),
        ("GET", "/api/get/openLessonList"),
    ],
}

NEEDS_DISCOVERY = """
Endpoints returning empty/system error:
  - /api/lesson/listCourseLesson (system error)
  - /api/lesson/lessonDetail (system error)
  - /api/plan/* (need POST body or internal routing)
  - /api/recipe/* (404 on direct HTTP)
  - /api/timeMachine/* (404 on direct HTTP)
"""


def show_header():
    print("=" * 72)
    print("  📚 YUNGU CLASSROOM — 云谷课堂学生看板 (只读)")
    print("=" * 72)


def show_user(client):
    info = client.get_user_info()
    if not info:
        print("  No user info available.")
        return
    print(f"\n👤 User Profile:\n")
    for key, value in sorted(info.items()):
        if isinstance(value, (list, dict)):
            continue
        label = key.replace("_", " ").title()
        if len(str(value)) > 100:
            value = str(value)[:100] + "..."
        print(f"   {label:<35} {value}")


def show_courses(client):
    sid = client.get_current_semester_id()
    semesters = client.list_semesters()
    cur = next((s for s in semesters if s["semesterId"] == sid), None)
    
    if cur:
        print(f"\n📅 Semester: {cur['semesterName']}")
        if cur.get('semesterEnName'):
            print(f"           {cur['semesterEnName']}")
        print(f"   ID: {sid}")

    courses = client.list_courses(sid)
    print(f"\n📚 Courses ({len(courses)}):")
    print(f"  {'ID':>8} | {'Grade':<12} | Color   | Course Name")
    print(f"  {'-'*8}-+-{'-'*12}-+-{'-'*7}-+---{'-'*45}")
    
    for c in courses:
        grade = (c.get('suitGradeName') or '?')[:12]
        color = c.get('subjectColor', '#888888') or '#888888'
        name = c['courseName']
        print(f"  {c['courseId']:>8} | {grade:<12} | {color:<7} | {name}")


def show_overview(client, verbose=False):
    sid = client.get_current_semester_id()
    courses = client.list_courses(sid)
    today = date.today()
    
    print(f"\n📅 Today: {today.strftime('%A %B %d')}")
    print()
    
    # Show teachers
    teachers = client.get_teachers_for_course(1086)
    if teachers:
        student_teachers = teachers[:5]
        print(f"  👨‍🏫 Teachers: {len(teachers)} total (showing first 5)")
        for t in student_teachers:
            en_name = f" ({t.get('enName','')})" if t.get('enName') else ""
            print(f"      • {t.get('name','?')}{en_name} [ID:{t.get('userId','?')}]")
        print()
    
    print(f"  📚 All {len(courses)} courses & teaching prompts:\n")
    
    for i, c in enumerate(courses, 1):
        cid = c["courseId"]
        
        line = f"  [{i:>2}] {c['courseName']}"
        if verbose:
            line += f" (ID: {cid}, Grade: {c.get('suitGradeName','?')})"
        print(line)
        
        if verbose or len(courses) <= 8:
            reflection = client.get_teaching_reflection(cid, sid)
            if reflection:
                prompts = reflection.get("teachingReflectionPrompts", "")
                if prompts:
                    lines = prompts.split(".")
                    for j, line_text in enumerate(lines[:3], 1):
                        cleaned = line_text.strip()
                        if cleaned:
                            print(f"        Q{j}: {cleaned}.\n")


def show_api_list():
    print("\n=== Known API Endpoints ===\n")
    print("VERIFIED WORKING:")
    for method, path in API_ENDPOINTS["verified"]:
        print(f"  ✓ {method:5} {path}")
    
    print("\nPARTIAL / NEEDS DISCOVERY:")
    for method, path in API_ENDPOINTS["partial"]:
        print(f"  ~ {method:5} {path}")
    
    print("\nNOT DISCOVERABLE VIA DIRECT HTTP:")
    for line in NEEDS_DISCOVERY.strip().split('\n'):
        print(f"    {line}")


def show_json_output(client):
    """Output everything as structured JSON."""
    result = client.export_all_data()
    print(json.dumps(result, indent=2, ensure_ascii=False))


def main():
    cookie = load_session_cookie()
    if not cookie:
        print("❌ Error: No SESSION cookie found.")
        print("   File: ~/.hermes/skills/yungu-classroom/.session_cookie")
        return
    
    client = YunguClient(cookie)
    if not client.verify_session():
        print("❌ Error: Session expired. Please re-authenticate from task.yungu.org")
        return
    
    args = sys.argv[1:]
    is_json = "--json" in args
    is_verbose = "--verbose" in args
    is_courses = "--courses" in args
    is_user = "--user" in args
    is_export = "--export" in args
    is_api_list = "--api-list" in args
    
    if is_api_list:
        show_api_list()
        return
    
    if is_json or is_export:
        result = client.export_all_data()
        if is_export:
            output_path = "/tmp/yungu_export.json"
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"Data exported to {output_path}")
            print(json.dumps({k: str(v)[:200] for k, v in result.items()}, indent=2, ensure_ascii=False))
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    
    show_header()
    
    if is_user:
        show_user(client)
        return
    
    if is_courses:
        show_courses(client)
        return
    
    show_overview(client, verbose=is_verbose)
    print("  ✅ Done")


if __name__ == "__main__":
    main()
