# Yungu Classroom API Reference (Discovered 2026-10-27)

## Working Endpoints

### Semesters
```
GET /api/all/semester
GET /api/all/semester?semesterId=<id>
GET /api/all/course/grades?semesterId=<id>
```
Returns semester list with IDs. Current semester: **491** ("2026学年 第一学期")

### Courses
```
GET /api/course/listCoursesBySemId?semId=<semesterId>
```
Returns all courses for a semester. Each course has:
- `courseId`, `courseName`, `courseEnName`
- `suitGradeName` (grade levels), `subjectColor`
- `sortNo`, `grade`, `schoolYearId`, `schoolYearName`

### Teaching Reflection / Lesson Prompts
```
POST /api/lesson/lectureRecordAndTeachingReflection
Body: {"courseId": <id>, "semesterId": <sid>}
```
Returns `teachingReflectionPrompts` and `lectureAttendancePrompts`.

### User Profile & Identity
```
GET /api/currentUser
GET /api/user/info
```
Returns full student profile: userId, name, enName, avatar, identity (student/teacher),
grade, stage, studentNo, phoneNumber, email, loginId, etc.

### User Relations (Student-facing)
```
GET /api/user/relation/myLessonList?courseId=<id>        → returns [] (empty - may need different params)
GET /api/user/relation/lessonListStatistics                → myListenTotal, myListenInSchool, etc.
GET /api/user/relation/lessonDetail?courseId=<id>&semesterId=<sid>  → "系统异常" (needs context)
GET /api/user/relation/lessonRecordList                    → needs specific lessonId
GET /api/user/relation/openLessonList                      → needs semesterId
GET /api/user/relation/updateIsPublic                      → POST required
```

### Lesson Detail / List
```
GET /api/lesson/listCourseLesson?                        → "system error" (internal routing issue)
GET /api/lesson/listCourseLessonByTeacher?               → 404
GET /api/lesson/getGroupListByCourse?courseId=<id>       → "system error"
GET /api/lesson/learningSteps/detail?                    → no jurisdiction (teacher-only?)
POST /api/lesson/getTeachingReflectionOrRecord?courseId=<id>
GET /api/list/lesson/teacher?semesterId=<id>             → teacher list ✅
GET /api/get/openLessonList                              → data available ✅
GET /api/get/openLesson                                  → needs params
GET /api/getLessonDetail                                 → unknown
```

### Course Resources
```
GET /api/courseResourcesOverview?courseId=<cid>&semesterId=<sid>
GET /api/courseResources/teacher?courseId=<cid>  → 125 teachers
GET /api/course/bySubjectId?subjectId=<id>       → params required
GET /api/course/byTeacherIdList?semesterId=<sid>
GET /api/course/groups?semesterId=<sid>
GET /api/course/taskPublishs?courseId=<cid>&semesterId=<sid>  → system error
```

### Student Daily
```
GET /api/student/daily/countStudentDaily     → requires params
GET /api/student/daily/listStudentInfo       → requires params
GET /api/student/daily/listGroup             → returns []
GET /api/student/daily/getSchoolDailyConfigNew → requires params
GET /api/student/daily/dict/allListDailyDict → requires params
```

### Lesson Info
```
GET /api/lesson/listCourseLesson?            → system error (needs specific params/context)
GET /api/lesson/listCourseLesson?courseId=<id>&semesterId=<sid>
GET /api/lesson/listCourseLessonByTeacher?
GET /api/lesson/getGroupListByCourse?courseId=<id>
GET /api/lesson/learningSteps/detail?        → no jurisdiction (teacher only?)
GET /api/lesson/getTeachingReflectionOrRecord?courseId=<id>
GET /api/lesson/teachingReflectionList?      → params required
GET /api/lesson/getReflectionOrRecordByLessonId?lessonId=<id>
GET /api/lesson/lectureRecordAndTeachingReflection?courseId=<id> &semesterId=<sid> ✅
```

### Task/Homework
```
GET /api/task/my/courses                     → getUserExamPaperList.subjectId: empty
GET /api/task/unit/list                      → listUnitUnderCourse.courseId: empty
POST /api/homeworkManagement/status          → NO_PERMISSION (identity=student)
POST /api/homeworkManagement/status/batch/preview
POST /api/homeworkManagement/export
GET /api/homeworkManagement/offline/students?courseId=<id>
```

### Plan/Schedule (recipe namespace)
These returned **404 Not Found** when called directly — they may be served by a
different backend service or accessed through an internal app proxy.
```
POST /api/recipe/planWeek/parent
POST /api/recipe/weekDetail/parent  
POST /api/recipe/planList
POST /api/recipe/weekPlanTitleList
GET  /api/plan/detailWeek
GET  /api/plan/pageListPlanDay
GET  /api/plan/pageListPlanWeek
GET  /api/plan/listCourse
GET  /api/plan/detail (POST needed)
```

### Feedback / Student Weekly Plan
Partial success - returns structure but content is null without specific params.
```
GET /api/feedback/parent/planWeek?semesterId=<id>        → ✅ status=true, content=null
GET /api/feedback/parent/planWeekDetail                  → ✅ status=true, needs week/date params
GET /api/feedback/planContentList                        → needs more params
GET /api/feedback/planList                               → needs more params
```

### Time Machine (Student Board features)
Return 404 on direct HTTP — likely requires browser-based routing:
```
GET /api/timeMachine/listTimeMachinePlanModuleOfStuBoard
GET /api/timeMachine/getDataByPlanIdAndStudentUserId
```

### Admin/Teacher endpoints (not accessible for students)
```
/api/course/subject/course?           → 403/unauthorized
/api/courseEvaluation/...             → permission denied
/api/acl/adminClassList?              → 403
/calendar/api/...                     → admin/teacher features
```

## Key Discovery Notes

### Request Pattern in JS Bundle
The app uses Redux-Saga effects that call generator functions returning query URLs:
```javascript
// Example from bundle:
function(queryFn(t){
  return callGenerator(function*(){
    yield "/api/lesson/listCourseLesson?".concat(qs.stringify(t,{arrayFormat:"repeat"}))
  })
})
```

All discovered endpoints are **GET requests** with query string parameters. The
payload is serialized using `qs.stringify(t, {arrayFormat: "repeat"})`.

### Biz Module Routing
The bundle defines `bizModule` groupings with whitelisted API paths:
- `behavior_request`: /calendar/api/*
- `lesson_evaluation_request`: /api/user/relation/lessonEvaluation*
- `growth_record`: /api/home-school*, etc.

Some endpoints (like recipe/) aren't in any whitelist — they may use a different
transport mechanism or require internal routing.

### Auth Mechanism
Authentication is via `SESSION` cookie set after CAS login at `login.yungu.org`.
The cookie file format used:
```
# Netscape HTTP Cookie File
.yungu.org	TRUE	/	FALSE	1792328912	SESSION	<uuid-value>
```

All API responses include:
```json
{
  "ifLogin": true,
  "status": true/false,
  "message": "...",
  "code": 0,
  "content": ...,
  "ifAdmin": false
}
```

### Error Codes
| Code | Meaning |
|------|---------|
| 0 / 1001 | Success |
| 1000 | Please refresh (session issue) |
| 1001 | No jurisdiction / unauthorized |
| 1008 | System error |
| 9002 | Request params empty |
| 9004 | Parameter parsing exception |

## Next Steps to Discover More APIs

1. **Browser DevTools**: Open `task.yungu.org/#/student/course` and capture all XHR/Fetch calls during page load
2. **WebSocket inspection**: The page loads `socket.io.min.js` — there may be real-time data channels
3. **Chunk analysis**: Component chunks like `11940` (student/course) may have additional API calls not in the main bundle
4. **Internal API gateway**: Some routes (`/api/recipe/*`) may go through a different gateway/service than `/api/lesson/*`
