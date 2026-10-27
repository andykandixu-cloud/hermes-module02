# Learning Brief 学习简报 — 使用指南

## 概述

Learning Brief 是一个**可重复使用的云谷课堂学习简报技能**，提供两种运行模式：

| 模式 | 文件名 | 用途 |
|------|--------|------|
| ☀️ 晨间简报 | `morning_brief.py` | 今日课表、教师信息、教学目标计划 |
| 🌙 晚间作业模式 | `evening_brief.py` | 回顾今日课程、反思区、明日准备 |

## 快速开始

```bash
cd ~/projects/hermes-module02

# 晨间简报（生成今日课程计划）
python3 skills/learning-brief/morning_brief.py

# 晚间作业模式（生成课后回顾）
python3 skills/learning-brief/evening_brief.py
```

输出文件位于 `data/` 目录（不在 Git 中）：
- `data/morning/latest.html` — 晨间简报 HTML
- `data/morning/latest.json` — 晨间简报 JSON 源数据
- `data/evening/latest.html` — 晚间简报 HTML
- `data/evening/latest.json` — 晚间简报 JSON 源数据
- `data/logs/*.log` — 运行日志

## 设计原则

1. **辅助复习，不做作业** — 只提供反思提示和任务清单，不提供答案
2. **来源透明** — 每个数据点标注来源 API 和时间戳
3. **缺失标记** — 当 API 无数据时，明确标记 `[MISSING]` 而非编造
4. **隐私隔离** — 凭据、生成简报、日志全部在 `.gitignore` 目录外
5. **单次服务 + 短延迟** — 每请求间隔 ≥ 2 秒，避免触发限流

## 数据流程

```
Session Cookie (data/.yungu.env)
    ↓
YunguClient API Client
    ↓
BriefGenerator (collects courses, teachers, reflections)
    ↓
JSON output (data/*/latest.json) + HTML output (data/*/latest.html)
```

## 两种模式对比

### ☀️ 晨间简报
- 获取 15 门课程的完整列表
- 每门课的授课教师（来自 `/api/list/lesson/teacher`）
- 教学反思提示（来自 `/api/lesson/lectureRecordAndTeachingReflection`）
- 昨日统计（来自 `/api/read/yesterdayStatistics`）

### 🌙 晚间作业模式
- 同样的课程+教师信息
- 本周反馈/计划数据（来自 `/api/feedback/parent/planWeek`）
- 每门课的自我评估提醒和反思区
- 未完成数据会显示 `[PENDING_API]` 标签

## GitLab 迁移说明

当前仓库为 GitHub (`github.com/andykandixu-cloud/hermes-module02`)。

GitLab 迁移步骤（待 gitlab.ygslife.org 可用后）：

```bash
# 1. 在 GitLab 创建私有仓库 hermes-learning-brief
# 2. 添加 GitLab remote
git remote add gitlab git@gitlab.ygslife.org:andy.xkd/hermes-learning-brief.git
# 3. 推送所有分支到 GitLab
git push --all gitlab
# 4. 设置 upstream branch
git branch --set-upstream-to=gitlab/main main
```

## 限制与已知问题

| 问题 | 状态 | 影响 |
|------|------|------|
| 每日课表 (`listCourseLesson`) | ❌ system error | 课表顺序/时间不可达 |
| 学生看板 (`timeMachine/*`) | ❌ 404 | 进度看板不可达 |
| 本周反馈 (`planWeek`) | ⚠️ 空响应 | 需要特定周参数 |
| 作业状态追踪 | ⚠️ [PENDING_API] | 需发现更多 homework API |

**这些缺失的数据会在简报中标记为 `[MISSING]` 或 `[PENDING_API]`，并给出建议。**
