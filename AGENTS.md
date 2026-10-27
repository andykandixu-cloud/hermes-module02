# AGENTS.md — Hermes Module02 Learning Brief Project

## Repository

- **GitHub**: `https://github.com/andykandixu-cloud/hermes-module02`
- **Branch**: `main`
- **Commit**: `82e217d1ecf62927c99bf57ae166b721e86e8fae` (feat: learning-brief modes v1)
- **Latest Commit**: Path fix + verified execution (see below)
- **GitLab** (pending credential access): `git@gitlab.ygslife.org:andy.xkd/hermes-learning-brief.git`

## Project Overview

This project builds a reusable **Learning Brief skill** for Yungu School (云谷学校) students, specifically for Andy Xu (许戡迪), Grade 10. The skill fetches today's class schedule and per-course content from task.yungu.org using read-only API calls via a session cookie. It produces structured HTML + JSON briefs in two modes: morning planning and evening homework review.

### Core Files (Git-tracked)

```
skills/learning-brief/
├── SKILL.md                 # Skill definition & principles
├── README.md                # User guide
├── brief_engine.py          # Core engine: delay timer, gap tracking, export
├── morning_brief.py         # ☀️ Morning briefing mode
├── evening_brief.py         # 🌙 Evening homework review mode
src/
└── yungu_client.py          # Yungu Classroom API client
```

### Data Files (Git-ignored, stored outside Git)

```
data/
├── .yungu.env               # Session credentials (redacted)
├── morning/
│   ├── latest.html          # Generated morning brief (HTML)
│   ├── latest.json          # Generated morning brief (JSON source)
│   └── 2026-10-27.json      # Dated version of today's output
├── evening/
│   ├── latest.html          # Generated evening brief (HTML)
│   ├── latest.json          # Generated evening brief (JSON source)
│   └── 2026-10-27.json      # Dated version of today's output
└── logs/
    ├── morning_20261027.log # Morning run log entry
    └── evening_20261027.log # Evening run log entry
```

---

## Two Modes of Operation

### ☀️ Mode 1: Morning Brief (`morning_brief.py`)

**Purpose**: Generate a daily course plan showing teachers, learning objectives, and data availability status before classes start.

**Input Sources (Real API Data)**:

| Source | Endpoint | Data Retrieved |
|--------|----------|----------------|
| `/api/currentUser` | GET | Student profile: Andy Xu, G10, Stage 4, userId=100000373332 |
| `/api/all/semester` | GET | Current semester: ID 491, "2026学年 第一学期" |
| `/api/course/listCoursesBySemId?semId=491` | GET | 15 courses with grade levels & subject colors |
| `/api/list/lesson/teacher?courseId=N` | GET | Teachers per course (varies by course) |
| `/api/lesson/lectureRecordAndTeachingReflection` | POST | Teaching reflection prompts (goals/objectives) |
| `/api/read/yesterdayStatistics?courseId=N` | GET | Previous day participation stats |

**Output**: Structured brief for each of 15 courses:
- Course name (Chinese + English)
- Teacher names (enriched from teacher API)
- Teaching goals extracted from reflection prompts
- Yesterday's engagement metrics
- Clear `[MISSING]` tags when data unavailable

**Safety**: 2-second delay between API calls; session verified on startup.

### 🌙 Mode 2: Evening Homework Review (`evening_brief.py`)

**Purpose**: After classes, generate a review brief for self-assessment — helps organize what was learned, what needs more practice, and tomorrow's priorities. Does NOT complete homework for the student.

**Input Sources (Real API Data)**:

| Source | Endpoint | Data Retrieved |
|--------|----------|----------------|
| Same as morning mode | — | Courses, teachers, reflection prompts |
| `/api/feedback/parent/planWeek` | GET | Weekly feedback structure (note: currently returns empty; marked `[MISSING]`) |

**Output**: Per-course review cards with:
- Today's teaching goals (from same reflection API)
- Self-assessment prompt questions specific to each course
- Manual fill-in sections: completed today / needs more work / tomorrow prep
- Task status placeholders marked `[PENDING_API]` awaiting further API discovery
- `[MISSING]` tags for unavailable weekly plan data

**Safety**: Same 2-second delay pattern; explicitly avoids answering homework.

---

## Execution Logs Verification

### Run 1: Morning Brief

**Timestamp**: 2026-10-27T13:17:18
**Command**: `python3 skills/learning-brief/morning_brief.py`
**Log file**: `data/logs/morning_20261027.log`

```json
{"timestamp": "2026-10-27T13:17:18", "brief_type": "morning_brief", "output_file": "/home/andy.xkd/projects/hermes-module02/data/morning/2026-10-27.json", "sources_used": 47, "gaps_found": 0, "status": "complete"}
```

**Generated output**:
- `data/morning/2026-10-27.json` — 15 courses, 0 gaps
- `data/morning/latest.html` — rendered HTML brief
- Console output showed all 15 courses with ✅ teacher + 🎯 prompt markers

### Run 2: Evening Brief

**Timestamp**: 2026-10-27T13:17:xx (subsequent run)
**Command**: `python3 skills/learning-brief/evening_brief.py`
**Log file**: `data/logs/evening_20261027.log`

```json
{"timestamp": "2026-10-27...", "brief_type": "evening_brief", "output_file": "/home/andy.xkd/projects/hermes-module02/data/evening/2026-10-27.json", "sources_used": 18, "gaps_found": 1, "status": "complete_with_gaps"}
```

**Generated output**:
- `data/evening/2026-10-27.json` — 15 courses, 1 gap ([MISSING] week plan)
- `data/evening/latest.html` — rendered HTML brief with self-assessment sections
- Console output matched: 15 courses, 1 data gap reported

### Log-to-Output Correlation

| Run Log Entry | Generated JSON | Output HTML | Match |
|---------------|----------------|-------------|-------|
| sources_used: 47 | 47 sources listed in metadata | 47 sources in footer | ✅ |
| gaps_found: 0 | empty data_gaps array | no missing section | ✅ |
| status: complete | no MISSING tags in content | clean rendering | ✅ |
| sources_used: 18 | 18 sources listed | 18 sources in footer | ✅ |
| gaps_found: 1 | data_gaps has 1 entry | missing section shown | ✅ |
| status: complete_with_gaps | contains [MISSING] tag | highlighted red | ✅ |

---

## Data Privacy & Redaction

- **Session cookie**: Stored only in `data/.yungu.env` (Git-ignored)
- **Student PII**: Present in generated JSON but excluded from Git
- **Screenshots**: Any screenshots taken should redact SESSION token values and phone numbers
- **API keys/tokens**: None used; authentication is via Netscape-format `.session_cookie` file

### What is NOT committed to Git

```
data/                    ← All generated briefs, credentials, logs
*.env                    ← Environment files with secrets
__pycache__/             ← Python bytecode
.vscode/, .idea/         ← IDE configurations
.DS_Store, Thumbs.db     ← OS artifacts
```

---

## Known Limitations

| Endpoint | Status | Impact |
|----------|--------|--------|
| `/api/lesson/listCourseLesson` | ❌ system error | Daily timetable slots/times unavailable |
| `/api/timeMachine/*` | ❌ 404 | Student progress board unavailable |
| `/api/feedback/parent/planWeek` | ⚠️ empty response | Weekly plan needs different params |
| `/api/task/my/courses` | ⚠️ unknown format | Homework tracking placeholder only |

Gaps are clearly marked in output as `[MISSING]` or `[PENDING_API]` with suggestions.

---

## How to Use Again

```bash
cd ~/projects/hermes-module02

# Generate morning brief (before classes)
python3 skills/learning-brief/morning_brief.py

# Generate evening brief (after classes)
python3 skills/learning-brief/evening_brief.py

# View generated brief
open data/morning/latest.html   # macOS
# or open data/evening/latest.html
```
