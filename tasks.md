# Task List — Yungu Classroom Student App

## Current Status ✅

- [x] Git repo initialized on GitHub
- [x] `yungu-classroom` skill discovered with session cookie
- [x] Cookie authentication working (SESSION: 8574da2c-...)
- [x] API client built (`src/yungu_client.py`)
- [x] Course list retrieved (15 courses)
- [x] Semester info working
- [x] Teaching reflection prompts per course

## Remaining Discovery Tasks 🔍

### P0: Today's Timetable/Schedule

Need to find the endpoint that returns actual daily timetable data for a student.
The app likely uses Redux sagas/effects that call internal functions which then
route through an HTTP proxy on the backend. The actual HTTP endpoints are abstracted.

**Approach**: Use browser DevTools Network tab while logged into
`task.yungu.org/#/student/course` to capture all API calls during page load.

Key patterns found in JS bundle:
- `recipe/planWeek/parent?` — Week plan for students
- `recipe/weekDetail/parent?` — Week detail for students
- `listCourseLesson` — Lesson list per course
- `getCurrentCourses` — Student's current enrolled courses
- `getAttendCourseList` — Courses attending this period

### P1: Homework/Assignment Status

Per-course homework tracking. Relevant JS patterns:
- `/api/task/my/courses` — My tasks per course
- `/api/task/unit/list` — Unit list per course
- `homeworkManagement/status/batch/preview` — Batch homework status (POST)

### P2: Student Daily Activities

Daily checklist/activities for students. JS patterns:
- `api/student/daily/getSchoolDailyConfigNew` — Daily config
- `api/student/daily/listStudentInfo` — Student daily info
- `api/student/daily/countStudentDaily` — Daily count stats

### P3: Course Content/Lesson Plans

Per-lesson lesson plans, materials, and teaching content.
Pattern: `lesson/getTeachingReflectionOrRecord`, `listCourseLesson`

## How to Discover More Endpoints

1. Open Chrome DevTools → Network tab
2. Navigate to `https://task.yungu.org/#/student/course`
3. Filter by XHR/Fetch
4. Look at request URLs of all API calls
5. Note the full path, method, params, and response format
