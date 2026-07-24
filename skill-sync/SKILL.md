---
name: skill-sync
description: >
  管理本地 skill 与 GitHub 远程仓库的同步。检测版本差异、自动 commit 和 push。
  当用户说"同步 skill"、"推送到 GitHub"、"skill 更新了吗"、"检查 skill 版本"、
  "skill-sync"时使用。
---

# Skill Sync

管理 `.mimocode/skills/` 目录与 GitHub 远程仓库 `Johnnylin2121/mimocode-skill` 的同步。

## 工作目录

`C:\Users\johnn\.mimocode\skills\`

远程：`git@github.com:Johnnylin2121/mimocode-skill.git`（origin/master）

## 流程

### Step 1：检测版本差异

```powershell
cd C:\Users\johnn\.mimocode\skills
git status
git log origin/master..HEAD --oneline  # 本地有但远程没有的提交
git log HEAD..origin/master --oneline  # 远程有但本地没有的提交
```

向用户报告：
- 本地未提交的更改（modified / untracked）
- 本地领先远程的提交数
- 远程领先本地的提交数

### Step 2：处理分歧（如有）

如果远程领先本地（`git pull` 会产生合并）：
- 先执行 `git pull origin master`
- 如有冲突，列出冲突文件并提醒用户手动解决
- 如无冲突，自动完成合并

### Step 3：提交本地更改

如果有未提交的更改：
```powershell
git add -A
git commit -m "<描述性提交信息>"
```

提交信息规则：
- 新增 skill：`feat: add <skill-name>`
- 更新 skill：`feat: update <skill-name> - <简述变更>`
- 删除 skill：`chore: remove <skill-name>`
- 合并桌面版：`feat: merge desktop version into <skill-name>`

### Step 4：推送到远程

```powershell
git push origin master
```

### Step 5：确认结果

执行 `git status` 和 `git log --oneline -3` 确认同步成功，向用户报告最终状态。

## 快捷模式

用户说"同步 skill"且无其他上下文时，直接执行 Step 1 → 按需执行 Step 2-4 → Step 5。

## 注意事项

- 不主动删除远程分支或强制推送
- push 被拒绝时先 pull 再 push，不使用 `--force`
- 每次操作前先确认当前在 master 分支
