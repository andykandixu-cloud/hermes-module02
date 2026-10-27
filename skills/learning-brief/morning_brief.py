#!/usr/bin/env python3
"""
☀️ 晨间学习简报 (Morning Brief)

生成今日课程计划、教师信息和教学目标的简明列表。
仅使用只读 API，不提交或修改任何内容。
数据来源真实或明确标记为 [MISSING]。
"""

import json
import sys
from pathlib import Path

# Ensure project root and src are in path BEFORE any imports
_project_root = str(Path(__file__).resolve().parents[2])  # goes from skills/learning-brief/ -> hermes-module02/
_src_dir = str(Path(__file__).resolve().parents[2] / "src")
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from yungu_client import YunguClient, load_session_cookie
from brief_engine import BriefGenerator, ensure_dirs, LOGS_DIR


def generate_morning_brief() -> dict:
    """Generate the complete morning learning brief."""
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

    # --- Build brief structure ---
    brief = {
        "metadata": {
            "type": "morning_brief",
            "generated_at": gen.timestamp,
            "date": gen.date_str,
            "weekday": gen.weekday,
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
                "enName": current_sem.get("semesterEnName", "") if current_sem else "",
            },
        },
        "course_plan": [],
        "sources_used": gen.sources_used,
        "data_gaps": gen.gaps_found,
        "disclaimer": "本简报基于公开只读 API 数据生成。缺失的数据已标记 [MISSING]。",
    }

    # --- Per-course details ---
    for course in courses:
        cid = course["courseId"]
        
        # Get teachers for this course
        teachers = gen.get_teachers_for_course(cid)
        
        # Get reflection prompts (teaching goals/ideas)
        reflection = gen.get_reflection_prompts(cid, sid)
        prompts = reflection.get("teachingReflectionPrompts", "")
        
        # Get yesterday's stats (if available)
        ystats = gen.get_yesterday_stats(cid)

        entry = {
            "order": len(brief["course_plan"]) + 1,
            "courseId": cid,
            "name": course["courseName"],
            "enName": course.get("courseEnName", ""),
            "gradeLevel": course.get("suitGradeName", ""),
            "subjectColor": course.get("subjectColor", "#888888"),
            "teachers": [],
            "reflection_prompts": prompts[:500] if prompts else gen._missing(
                "教学反思提示", "API 未返回该课程的教学反思目标"
            ),
            "yesterday_stats": ystats if ystats else {},
            "source": f"/api/course/listCoursesBySemId + /api/lesson/lectureRecordAndTeachingReflection",
        }

        # Format teacher list
        if teachers:
            entry["teachers"] = [
                {
                    "name": t.get("name", ""),
                    "enName": t.get("enName", ""),
                    "userId": t.get("userId", ""),
                }
                for t in teachers[:3]  # Limit to first 3 teachers per course
            ]
        else:
            entry["teachers"] = [{"name": gen._missing("教师姓名", "API 未返回该课程的具体教师信息")}]

        brief["course_plan"].append(entry)

    # Export JSON via engine (sources_used & gaps_found now populated)
    ensure_dirs()
    output_path = DATA_DIR / "morning" / f"{gen.date_str}.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(brief, f, indent=2, ensure_ascii=False)
    
    latest_path = DATA_DIR / "morning" / "latest.json"
    with open(latest_path, 'w', encoding='utf-8') as f:
        json.dump(brief, f, indent=2, ensure_ascii=False)
    
    log_entry = {
        "timestamp": gen.timestamp,
        "brief_type": "morning_brief",
        "output_file": str(output_path),
        "sources_used": len(gen.sources_used),
        "gaps_found": len(gen.gaps_found),
        "status": "complete_with_gaps" if gen.gaps_found else "complete",
    }
    log_path = LOGS_DIR / f"morning_{gen.date_str.replace('-', '')}.log"
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    return brief


def format_brief_html(brief: dict) -> str:
    """Convert brief JSON to a clean HTML output for reading."""
    
    meta = brief["metadata"]
    student = meta["student"]
    semester = meta["semester"]
    
    html_parts = []
    
    def h(tag, content=""):
        return f"<{tag}>{content}</{tag}>"
    
    def css():
        return """
        <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
               max-width: 900px; margin: 2rem auto; padding: 0 1rem; line-height: 1.6; color: #333; }
        h1 { color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 0.5rem; }
        h2 { color: #34a853; margin-top: 2rem; }
        .header { background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; }
        .course-card { border: 1px solid #e0e0e0; border-radius: 8px; padding: 1rem; margin: 1rem 0; }
        .color-bar { height: 4px; border-radius: 2px; margin-bottom: 0.5rem; }
        .missing { color: #d93025; font-style: italic; background: #fce8e6; padding: 2px 6px; border-radius: 3px; }
        .info-row { display: flex; gap: 2rem; flex-wrap: wrap; }
        .info-item { flex: 1; min-width: 200px; }
        .teacher-tag { display: inline-block; background: #e8f0fe; padding: 2px 8px; 
                      border-radius: 12px; margin-right: 4px; font-size: 0.85em; }
        .gaps-section { background: #fff3e0; padding: 1rem; border-radius: 8px; margin-top: 1.5rem; }
        .sources { font-size: 0.85em; color: #666; margin-top: 2rem; }
        .disclaimer { font-size: 0.8em; color: #999; margin-top: 1rem; border-top: 1px solid #eee; padding-top: 1rem; }
        </style>"""
    
    def header():
        return f"""
        <div class="header">
            <h1>☀️ 晨间学习简报</h1>
            <p><strong>{meta['date']} ({meta['weekday']})</strong></p>
            <div class="info-row">
                <div class="info-item"><strong>学生：</strong>{student['name']} {student['enName']}</div>
                <div class="info-item"><strong>年级：</strong>G{student['grade']} · Stage {student['stage']}</div>
                <div class="info-item"><strong>学号：</strong>{student['studentNo']}</div>
            </div>
            <div class="info-row">
                <div class="info-item"><strong>学期：</strong>{semester['name']}</div>
                <div class="info-item"><strong>课程总数：</strong>{len(brief['course_plan'])}</div>
                <div class="info-item"><strong>数据来源数：</strong>{len(brief['sources_used'])}</div>
            </div>
        </div>"""
    
    def disclaimer():
        return f'<div class="disclaimer">⚠️ {brief["disclaimer"]}</div>'
    
    def gaps_section():
        if brief["data_gaps"]:
            parts = [f"<li>{gap}</li>" for gap in brief["data_gaps"]]
            return f'''
            <div class="gaps-section">
                <h2>🔴 缺失数据提醒 ({len(brief["data_gaps"])})</h2>
                <ul>{" ".join(parts)}</ul>
            </div>'''
        return ""
    
    def course_cards():
        cards = []
        for c in brief["course_plan"]:
            color = c.get("subjectColor", "#888888")
            name = c["name"]
            en_name = c.get("enName", "")
            grade = c.get("gradeLevel", "")
            order = c.get("order", "?")
            
            teachers_html = ""
            for t in c["teachers"]:
                tname = t.get("name", "")
                ten = t.get("enName", "")
                if "[MISSING]" in str(tname):
                    teachers_html += f'<span class="missing">{tname}</span>'
                else:
                    teachers_html += f'<span class="teacher-tag">{tname}{f" ({ten})" if ten else ""}</span>'
            
            prompts_text = c.get("reflection_prompts", "")
            if "[MISSING]" in str(prompts_text):
                prompts_html = f'<span class="missing">{prompts_text}</span>'
            elif prompts_text:
                prompt_lines = [p.strip() + "." for p in prompts_text.split(".") if p.strip()]
                prompt_list = "".join(f"<p>💡 {pl}</p>" for pl in prompt_lines[:3])
                prompts_html = prompt_list
            else:
                prompts_html = '<span class="missing">[MISSING] 无教学反思提示</span>'
            
            cards.append(f"""
            <div class="course-card">
                <div class="color-bar" style="background: {color};"></div>
                <h3>课程 {order}: {name}</h3>
                <p><em>{en_name}</em> · Grade: {grade}</p>
                <p><strong>教师：</strong>{teachers_html}</p>
                <p><strong>学习目标：</strong>{prompts_html}</p>
            </div>""")
        return "\n".join(cards)
    
    sources_html = ""
    if brief["sources_used"]:
        sources_items = "".join(f'<li>{src}</li>' for src in brief["sources_used"])
        sources_html = f'<div class="sources"><h2>📡 数据来源</h2><ul>{sources_items}</ul></div>'
    
    html_parts.extend([
        "<!DOCTYPE html>",
        "<html lang='zh-CN'>",
        "<head><meta charset='UTF-8'>",
        css(),
        "</head>",
        "<body>",
        header(),
        gaps_section(),
        "<h2>📋 今日课程计划 ({len(brief['course_plan'])} 门课)</h2>",
        course_cards(),
        sources_html,
        disclaimer(),
        "</body>",
        "</html>",
    ])
    
    return "\n".join(html_parts)


def main():
    PROJECT_ROOT = Path(__file__).resolve().parents[2]  # hermes-module02/
    DATA_DIR = PROJECT_ROOT / "data"
    
    print("=" * 60)
    print("  ☀️ 云谷课堂 — 晨间学习简报")
    print("=" * 60)
    print()
    
    brief = generate_morning_brief()
    
    if "error" in brief:
        print(f"ERROR: {brief['error']} - {brief.get('hint', '')}")
        sys.exit(1)
    
    # Generate HTML output
    html = format_brief_html(brief)
    
    # Write files
    output_path = DATA_DIR / "morning" / "latest.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ 简报已生成:")
    print(f"   📄 HTML: {output_path}")
    print(f"   📊 JSON: {DATA_DIR}/morning/latest.json")
    print()
    print(f"   课程数: {len(brief['course_plan'])}")
    print(f"   数据来源: {len(brief['sources_used'])} 个 API")
    if brief["data_gaps"]:
        print(f"   ⚠️  缺失数据: {len(brief['data_gaps'])} 项")
        for gap in brief["data_gaps"]:
            print(f"      → {gap}")
    else:
        print(f"   ✅ 所有数据完整")
    print()
    
    # Print summary
    for i, c in enumerate(brief["course_plan"], 1):
        name = c["name"]
        color = c.get("subjectColor", "")
        has_teachers = any("[MISSING]" not in str(t.get("name","")) for t in c["teachers"])
        has_prompts = "[MISSING]" not in str(c.get("reflection_prompts",""))
        
        status = []
        if has_teachers:
            status.append("👨‍🏫")
        else:
            status.append("❓")
        if has_prompts:
            status.append("🎯")
        else:
            status.append("❓")
        
        marker = " ".join(status)
        print(f"  [{i:>2}] {marker} {name}")
    
    print("\n✅ Done!")


if __name__ == "__main__":
    from pathlib import Path
    DATA_DIR = Path(__file__).parent.parent / "data" / "morning"
    main()
