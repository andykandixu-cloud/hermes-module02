#!/usr/bin/env python3
"""
🌙 晚间作业模式 (Evening Homework Mode)

回顾今日课程、检查任务完成状态、为明日做准备。
提供反思区帮助你整理思路，不替你完成任何作业。
数据来源真实或明确标记为 [MISSING]。
"""

import json
import sys
from datetime import date
from pathlib import Path

# Ensure project root and src are in path BEFORE any imports
_project_root = str(Path(__file__).resolve().parents[2])  # hermes-module02/
_src_dir = str(Path(__file__).resolve().parents[2] / "src")
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from yungu_client import YunguClient, load_session_cookie
from brief_engine import BriefGenerator, ensure_dirs, LOGS_DIR


def generate_evening_brief() -> dict:
    """Generate the complete evening homework review brief."""
    ensure_dirs()
    PROJECT_ROOT = Path(__file__).resolve().parents[2]  # hermes-module02/
    DATA_DIR = PROJECT_ROOT / "data"

    # --- Load credentials ---
    cookie = load_session_cookie()
    if not cookie:
        print("❌ Error: No SESSION cookie found")
        return {"error": "missing_credentials", "hint": "Check data/.yungu.env"}

    client = YunguClient(cookie)
    if not client.verify_session():
        print("❌ Error: Session expired or invalid")
        return {"error": "session_expired", "hint": "Please refresh your session from task.yungu.org"}

    gen = BriefGenerator(client)
    sid = gen.client.get_current_semester_id()

    # --- Gather data ---
    user_info = gen.get_user_context()
    semesters = gen.client.list_semesters()
    current_sem = next((s for s in semesters if s["semesterId"] == sid), None)
    courses = gen.get_course_list(sid)

    # Get week feedback data
    week_feedback = gen.get_week_feedback(weekMonthNum="October", startDay=str(date.today()))

    # --- Build brief structure ---
    brief = {
        "metadata": {
            "type": "evening_brief",
            "generated_at": gen.timestamp,
            "date": gen.date_str,
            "weekday": gen.weekday,
            "mode": "homework_review",
            "student": {
                "name": user_info.get("name", "Unknown"),
                "enName": user_info.get("enName", ""),
                "userId": user_info.get("userId", ""),
                "grade": user_info.get("grade", ""),
                "stage": user_info.get("stage", ""),
                "studentNo": user_info.get("studentNo", ""),
            },
            "semester": {
                "id": sid,
                "name": current_sem.get("semesterName", "") if current_sem else "",
            },
        },
        "course_review": [],
        "week_feedback_summary": {},
        "self_assessment_reminder": [
            "今日课程中哪些目标已完成？请在下方记录。",
            "哪些部分还需要进一步理解和练习？",
            "明天的优先事项是什么？",
            "不要替自己写答案——先尝试独立完成！"
        ],
        "reflection_areas": {
            "completed_today": "",
            "needs_more_work": "",
            "tomorrow_priority": "",
        },
        "sources_used": gen.sources_used,
        "data_gaps": gen.gaps_found,
        "disclaimer": "本简报用于辅助复习，不提供作业答案。所有数据标注来源，缺失数据标记 [MISSING]。",
    }

    # --- Per-course review ---
    for course in courses:
        cid = course["courseId"]
        
        reflection = gen.get_reflection_prompts(cid, sid)
        prompts = reflection.get("teachingReflectionPrompts", "")
        
        entry = {
            "courseId": cid,
            "name": course["courseName"],
            "enName": course.get("courseEnName", ""),
            "subjectColor": course.get("subjectColor", "#888888"),
            
            # What we know about this course
            "today_goals": prompts[:500] if prompts else gen._missing(
                "今日学习目标/教学反思", 
                "API 未返回该课程的反思提示，建议使用浏览器查看"
            ),
            
            # Task status placeholder (homework tracking needs more API discovery)
            "task_status": {
                "pending": "需要发现更多作业 API 来追踪实际状态",
                "submitted": "[PENDING_API]",
                "graded": "[PENDING_API]",
            },
            
            # Self-review questions specific to this course
            "review_questions": [
                f"今天 {course['courseName']} 课的目标达成了吗？",
                f"哪些概念还需要课后练习？",
                f"明天上课需要准备什么？",
            ],
        }
        
        brief["course_review"].append(entry)

    # Week feedback summary
    brief["week_feedback_summary"] = week_feedback if week_feedback else {}

    # Export JSON via engine (sources_used & gaps_found now populated)
    output_path = DATA_DIR / "evening" / f"{gen.date_str}.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(brief, f, indent=2, ensure_ascii=False)
    
    latest_path = DATA_DIR / "evening" / "latest.json"
    with open(latest_path, 'w', encoding='utf-8') as f:
        json.dump(brief, f, indent=2, ensure_ascii=False)
    
    log_entry = {
        "timestamp": gen.timestamp,
        "brief_type": "evening_brief",
        "output_file": str(output_path),
        "sources_used": len(gen.sources_used),
        "gaps_found": len(gen.gaps_found),
        "status": "complete_with_gaps" if gen.gaps_found else "complete",
    }
    log_path = LOGS_DIR / f"evening_{gen.date_str.replace('-', '')}.log"
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    return brief


def format_evening_html(brief: dict) -> str:
    """Convert evening brief to clean HTML output."""
    
    meta = brief["metadata"]
    student = meta["student"]
    
    def css():
        return """
        <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
               max-width: 900px; margin: 2rem auto; padding: 0 1rem; line-height: 1.6; color: #333; }
        h1 { color: #7c4dff; border-bottom: 2px solid #7c4dff; padding-bottom: 0.5rem; }
        h2 { color: #ff6d00; margin-top: 2rem; }
        .header { background: #f3e5f5; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; }
        .course-card { border: 1px solid #e0e0e0; border-radius: 8px; padding: 1rem; margin: 1rem 0; }
        .color-bar { height: 4px; border-radius: 2px; margin-bottom: 0.5rem; }
        .missing { color: #d93025; font-style: italic; background: #fce8e6; padding: 2px 6px; border-radius: 3px; }
        .review-area { background: #fffde7; border-left: 3px solid #ffd600; padding: 1rem; margin: 0.5rem 0; border-radius: 0 4px 4px 0; }
        .reminder-box { background: #e8f5e9; padding: 1rem; border-radius: 8px; margin: 1.5rem 0; }
        .gaps-section { background: #fff3e0; padding: 1rem; border-radius: 8px; margin-top: 1.5rem; }
        .info-row { display: flex; gap: 2rem; flex-wrap: wrap; }
        .info-item { flex: 1; min-width: 200px; }
        .question-list { list-style: none; padding-left: 0; }
        .question-list li { padding: 0.3rem 0; }
        .question-list li:before { content: "❓ "; }
        .sources { font-size: 0.85em; color: #666; margin-top: 2rem; }
        .disclaimer { font-size: 0.8em; color: #999; margin-top: 1rem; border-top: 1px solid #eee; padding-top: 1rem; }
        </style>"""
    
    html_parts = []
    
    def header():
        return f"""
        <div class="header">
            <h1>🌙 晚间作业回顾</h1>
            <p><strong>{meta['date']} ({meta['weekday']}) — {meta.get('mode','')}</strong></p>
            <div class="info-row">
                <div class="info-item"><strong>学生：</strong>{student['name']} {student['enName']}</div>
                <div class="info-item"><strong>年级：</strong>G{student['grade']} · Stage {student['stage']}</div>
                <div class="info-item"><strong>学号：</strong>{student['studentNo']}</div>
            </div>
            <div class="info-row">
                <div class="info-item"><strong>学期：</strong>{meta['semester']['name']}</div>
                <div class="info-item"><strong>课程总数：</strong>{len(brief['course_review'])}</div>
            </div>
        </div>"""
    
    def reminders():
        items = "".join(f"<li>• {r}</li>" for r in brief["self_assessment_reminder"])
        return f'''
        <div class="reminder-box">
            <h2>💭 自我评估提醒</h2>
            <ul style="list-style: none; padding-left: 0;">{items}</ul>
        </div>'''
    
    def gaps_section():
        if brief["data_gaps"]:
            parts = "".join(f"<li>{gap}</li>" for gap in brief["data_gaps"])
            return f'''
            <div class="gaps-section">
                <h2>🔴 数据缺口 ({len(brief["data_gaps"])})</h2>
                <ul>{parts}</ul>
            </div>'''
        return ""
    
    def course_reviews():
        cards = []
        for c in brief["course_review"]:
            color = c.get("subjectColor", "#888888")
            name = c["name"]
            en_name = c.get("enName", "")
            
            goals = c.get("today_goals", "")
            if "[MISSING]" in str(goals):
                goals_html = f'<span class="missing">{goals}</span>'
            elif goals:
                lines = [p.strip() + "." for p in goals.split(".") if p.strip()]
                goals_html = "<br>".join(f"💡 {l}" for l in lines[:4])
            else:
                goals_html = '<span class="missing">[MISSING] 无教学目标数据</span>'
            
            questions = "".join(f'<li>{q}</li>' for q in c.get("review_questions", []))
            
            cards.append(f"""
            <div class="course-card">
                <div class="color-bar" style="background: {color};"></div>
                <h3>📖 {name}</h3>
                <p><em>{en_name}</em></p>
                <p><strong>今日目标/反思提示：</strong><br>{goals_html}</p>
                <div class="review-area">
                    <h4>📝 课后回顾区（手动填写）</h4>
                    <ul class="question-list">{questions}</ul>
                    <hr style="border: none; border-top: 1px dashed #ccc; margin: 0.5rem 0;">
                    <p><strong>今天完成了什么：</strong><br><br></p>
                    <p><strong>还需练习什么：</strong><br><br></p>
                    <p><strong>明天准备什么：</strong><br><br></p>
                </div>
            </div>""")
        return "\n".join(cards)
    
    sources_html = ""
    if brief["sources_used"]:
        sources_items = "".join(f'<li>{src}</li>' for src in brief["sources_used"])
        sources_html = f'<div class="sources"><h2>📡 数据来源</h2><ul>{sources_items}</ul></div>'
    
    disclaimer = f'<div class="disclaimer">⚠️ {brief["disclaimer"]}</div>'
    
    html_parts.extend([
        "<!DOCTYPE html>",
        "<html lang='zh-CN'>",
        "<head><meta charset='UTF-8'>",
        css(),
        "</head>",
        "<body>",
        header(),
        reminders(),
        gaps_section(),
        "<h2>📋 今日课程回顾 ({len(brief['course_review'])} 门课)</h2>",
        course_reviews(),
        sources_html,
        disclaimer,
        "</body>",
        "</html>",
    ])
    
    return "\n".join(html_parts)


def main():
    PROJECT_ROOT = Path(__file__).resolve().parents[2]  # hermes-module02/
    DATA_DIR = PROJECT_ROOT / "data"
    
    print("=" * 60)
    print("  🌙 云谷课堂 — 晚间作业回顾")
    print("=" * 60)
    print()
    
    brief = generate_evening_brief()
    
    if "error" in brief:
        print(f"ERROR: {brief['error']} - {brief.get('hint', '')}")
        sys.exit(1)
    
    # Generate HTML output
    html = format_evening_html(brief)
    
    output_path = DATA_DIR / "evening" / "latest.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ 简报已生成:")
    print(f"   📄 HTML: {output_path}")
    print(f"   📊 JSON: {DATA_DIR}/evening/latest.json")
    print()
    print(f"   课程数: {len(brief['course_review'])}")
    print(f"   数据来源: {len(brief['sources_used'])} 个 API")
    if brief["data_gaps"]:
        print(f"   ⚠️  缺失数据: {len(brief['data_gaps'])} 项")
        for gap in brief["data_gaps"]:
            print(f"      → {gap}")
    else:
        print(f"   ✅ 所有数据完整")
    print()
    
    # Print summary
    for i, c in enumerate(brief["course_review"], 1):
        name = c["name"]
        has_goals = "[MISSING]" not in str(c.get("today_goals",""))
        
        marker = "🎯" if has_goals else "❓"
        print(f"  [{i:>2}] {marker} {name}")
    
    print("\n✅ Done!")


if __name__ == "__main__":
    from pathlib import Path
    DATA_DIR = Path(__file__).parent.parent / "data"
    main()
