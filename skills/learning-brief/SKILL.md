# Learning Brief — 云谷课堂学习简报技能 v0.1

## 目标

为云谷学校学生创建**可重复使用的晨间计划**和**晚间作业回顾**简报，基于真实 API 数据。

### 设计原则

| 原则 | 实现方式 |
|------|----------|
| **辅助复习，不做作业** | 提供反思提示、任务清单、待办追踪，不提供答案 |
| **来源透明** | 每个数据点标注来源 API 和时间戳 |
| **缺失标记** | 当 API 无数据时，明确标注 `[MISSING]` 而非编造 |
| **隐私隔离** | 凭据、生成简报、日志全部在 `.gitignore` 目录外 |
| **单次服务 + 短延迟** | 每请求间隔 ≥ 2 秒，避免触发限流 |

### 两种模式

#### ☀️ 晨间简报 (morning_brief)
```
0. 验证会话认证
1. 拉取今日课表
2. 获取每门课程的教师信息和教学反思提示
3. 检查教学计划/反馈数据的可用性
4. 输出结构化简报：课程列表 + 教师 + 学习目标 + 已知缺口
```

#### 🌙 晚间作业模式 (evening_brief)
```
0. 验证会话认证
1. 获取本周反馈/计划数据
2. 列出已完成与未完成的任务
3. 匹配今日课程与次日准备事项
4. 输出结构化简报：完成情况 + 明日优先级 + 反思区
```

## 文件结构

```
skills/learning-brief/        ← 技能代码（提交到 Git）
├── SKILL.md                  ← 本文件
├── brief_engine.py           ← 核心引擎
├── morning_brief.py          ← 晨间模式
├── evening_brief.py          ← 晚间模式
├── lib/__init__.py           ← 工具库
├── tests/                    ← 测试脚本（可选提交）

data/                          ← 数据文件（不在 Git 中）
├── .yungu.env                 ← 凭据
├── morning/                   ← 生成的晨间简报
├── evening/                   ← 生成的晚间简报
└── logs/                      ← 运行日志

src/yungu_client.py            ← Yungu Classroom API 客户端
```

## 用法

```bash
# 晨间简报
cd ~/projects/hermes-module02
python3 skills/learning-brief/morning_brief.py

# 晚间作业模式
python3 skills/learning-brief/evening_brief.py

# 查看上次生成的简报
cat data/morning/latest.json
cat data/evening/latest.json
```

## 限制与已知问题

| 问题 | 状态 | 影响 |
|------|------|------|
| `/api/lesson/listCourseLesson` 返回 system error | 未解决 | 无法直接获取每日课表 |
| `/api/timeMachine/*` 返回 404 | 未解决 | 学生看板数据不可达 |
| `/api/feedback/parent/planWeek` 无内容 | 部分 | 需要特定周参数 |
| Playwright 浏览器自动化受限 | 环境限制 | 无法用浏览器抓包发现更多端点 |

**这些缺失的数据会在简报中标记为 `[MISSING]`，并给出建议。**
