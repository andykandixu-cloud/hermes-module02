# hermes-module02 — Yungu Classroom Student App

**Goal**: A student-facing application that fetches today's class schedule from `task.yungu.org` (云谷学校) and retrieves content for each class.

## Architecture

```
yungu_client.py          ← Core API client (read-only)
├── Session management via Netscape cookie file
├── Works: courses list, semesters, teaching reflections
└── TODO: timetable, homework, lesson plans
```

## Authentication

Uses a session cookie from `.hermes/skills/yungu-classroom/.session_cookie`:
```bash
# Manual export: login → DevTools → Application → Cookies → copy SESSION value
echo ".yungu.org	TRUE	/	FALSE	1792328912	SESSION	<your-cookie>" > ~/.hermes/skills/yungu-classroom/.session_cookie
```

## Running

```bash
python3 src/yungu_client.py
```

## Known Working Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/all/semester` | GET | List all semesters |
| `/api/course/listCoursesBySemId?semId=` | GET | Get course list |
| `/api/lesson/lectureRecordAndTeachingReflection` | POST | Get teaching prompts per course |
| `/api/all/course/grades` | GET | Grade information |

## Not Yet Discovered

Full timetable/lesson schedule requires endpoint discovery via browser network trace. See tasks below.
