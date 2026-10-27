#!/usr/bin/env python3
"""
Yungu Classroom CLI — Student Dashboard
========================================
Read-only dashboard showing daily courses, teaching prompts, and semester info.

Usage:
  python3 yungu_cli.py              # Show today's overview
  python3 yungu_cli.py --json       # Output as JSON
  python3 yungu_cli.py --courses    # List all courses only
  python3 yungu_cli.py --verbose    # Show full details per course
"""

import sys
import json
from datetime import date, timedelta


# Import from package
sys.path.insert(0, "/home/andy.xkd/projects/hermes-module02/src")
from yungu_client import YunguClient, load_session_cookie


def print_header():
    print("=" * 72)
    print("  📚 YUNGU CLASSROOM — 云谷课堂学生看板 (只读)")
    print("=" * 72)


def show_courses_only(client):
    sid = client.get_current_semester_id()
    courses = client.list_courses(sid)
    
    print(f"\n📅 Semester {sid}:")
    semesters = client.list_semesters()
    cur = next((s for s in semesters if s["semesterId"] == sid), None)
    if cur:
        print(f"   {cur['semesterName']} ({cur.get('semesterEnName','')})")
    
    print(f"\n📚 Courses ({len(courses)}):")
    print(f"  {'ID':>8} | {'Grade':<15} | {'Color':<8} | Course Name")
    print(f"  {'-'*8}-+-{'-'*15}-+-{'-'*8}-+---{'-'*40}")
    
    for c in courses:
        grade = c.get('suitGradeName', '?')[:15]
        color = c.get('subjectColor', '#888888') or '#888888'
        name = c.get('courseName', '')
        print(f"  {c['courseId']:>8} | {grade:<15} | {color:<8} | {name}")


def show_today_overview(client, verbose=False):
    sid = client.get_current_semester_id()
    courses = client.list_courses(sid)
    
    today = date.today()
    day_name = today.strftime("%A %B %d")
    
    print(f"\n📅 Today: {day_name} (Semester ID: {sid})\n")
    
    # Try to show grades
    try:
        grades = client.get_course_grades(sid)
        if grades:
            print(f"  📊 Grade levels available: {len(grades)}")
    except Exception:
        pass
    
    print(f"\n  All Courses & Teaching Prompts:\n")
    
    for i, c in enumerate(courses, 1):
        cid = c["courseId"]
        
        marker_color = c.get("subjectColor", "#4CAF50") or "#4CAF50"
        
        line = f"  [{i:>2}] {marker_color} {c['courseName']}"
        if verbose:
            line += f" (ID: {cid}, Grade: {c.get('suitGradeName', 'N/A')})"
        print(line)
        
        if verbose or len(courses) <= 8:
            reflection = client.get_teaching_reflection(cid, sid)
            if reflection:
                prompts = reflection.get("teachingReflectionPrompts", "")
                if prompts:
                    prompt_preview = prompts[:200].replace("\n", " ")
                    print(f"        💡 {prompt_preview}")
                    
                    if not prompts.endswith("..."):
                        print(f"        ...")
    
    print()


def show_json_output(client):
    """Output all data as structured JSON."""
    sid = client.get_current_semester_id()
    semesters = client.list_semesters()
    courses = client.list_courses(sid)
    
    result = {
        "today": date.today().isoformat(),
        "semester": {},
        "courses": [],
    }
    
    # Current semester
    cur = next((s for s in semesters if s["semesterId"] == sid), None)
    if cur:
        result["semester"] = cur
    
    # Each course with its data
    for c in courses:
        cid = c["courseId"]
        reflection = client.get_teaching_reflection(cid, sid)
        
        entry = {
            "courseId": cid,
            "courseName": c["courseName"],
            "courseEnName": c.get("courseEnName"),
            "grade": c.get("suitGradeName"),
            "subjectColor": c.get("subjectColor"),
            "reflection_prompts": reflection.get("teachingReflectionPrompts", ""),
            "lecture_prompts": reflection.get("lectureAttendancePrompts", ""),
        }
        result["courses"].append(entry)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))


def main():
    cookie = load_session_cookie()
    if not cookie:
        print("❌ Error: No SESSION cookie found.")
        print("   Expected at: ~/.hermes/skills/yungu-classroom/.session_cookie")
        return
    
    client = YunguClient(cookie)
    if not client.verify_session():
        print("❌ Error: Session expired or invalid. Please re-authenticate.")
        return
    
    args = sys.argv[1:]
    is_json = "--json" in args
    is_verbose = "--verbose" in args
    is_courses = "--courses" in args
    
    if is_json:
        show_json_output(client)
    elif is_courses:
        show_courses_only(client)
    else:
        print_header()
        show_today_overview(client, verbose=is_verbose)


if __name__ == "__main__":
    main()
