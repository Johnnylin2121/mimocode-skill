---
name: obsidian-vault-sync
description: 自动将文件同步到Obsidian知识库，包括复制文件、创建/更新wiki entities和topics。Use when user says "添加到知识库", "同步到Obsidian", "更新wiki", "把文件放到vault里", "归档", "添加到vault", or asks to organize files into the knowledge base.
---

# Obsidian Vault Sync

自动将文件同步到Obsidian知识库，完成文件复制、entity创建/更新、topic关联更新。

## 触发条件

用户说以下任一短语时触发：
- "添加到知识库"
- "同步到Obsidian"
- "更新wiki"
- "把文件放到vault里"
- "归档"
- "添加到vault"

## 工作流程

### Step 1: 确定源文件和目标位置

读取用户提供的文件路径，根据文件名判断类型：

| 文件名模式 | 目标位置 |
|-----------|---------|
| `*财经早读*` 或 `*财经早餐*` | `交易体系/财经早读/` + `附件/2.财经早读/` + `wiki/sources/` |
| `*复盘*` | `交易体系/复盘/` |
| 其他 | 询问用户目标位置 |

### Step 2: 复制文件

```
# MD文件 → 交易体系/财经早读/YYYY-MM-DD-财经早读.md
# DOCX文件 → 附件/2.财经早读/YYYY年M月D日财经早餐.docx
# 同时创建wiki source文件 → wiki/sources/YYYY-MM-DD-财经早读-关键词.md
```

### Step 3: 解析内容，提取关键词

从文件内容中提取：
- **公司名**：如"华友钴业"、"三一重工"、"中国建筑"
- **人名/机构**：如"证监会"、"花旗"、"DeepSeek"
- **主题**：如"回购增持"、"科技股"、"大宗商品"
- **事件**：如"胡塞武装禁运"、"V4峰谷定价"

### Step 4: 更新wiki/entities

对每个提取的关键词：

1. 检查 `wiki/entities/{关键词}.md` 是否存在
2. **存在**：更新frontmatter中的`sources`和`updated`字段，添加新的财经早读引用
3. **不存在**：创建新entity文件，包含：
   - frontmatter（type: entity, created, updated, tags, sources, related）
   - 基本信息
   - 近期动态（从文件内容提取）

### Step 5: 更新wiki/topics

对每个提取的主题：

1. 检查 `wiki/topics/{主题}.md` 是否存在
2. **存在**：更新frontmatter中的`sources`和`updated`字段，添加新的财经早读引用
3. **不存在**：创建新topic文件，包含：
   - frontmatter（type: topic, created, updated, tags, sources, related）
   - 概述
   - 关联

### Step 6: 生成更新报告

输出完成的操作清单：
- 复制的文件列表
- 更新的entity文件列表
- 新建的entity文件列表
- 更新的topic文件列表
- 新建的topic文件列表

## Wiki文件格式参考

### Entity文件格式

```yaml
---
type: entity
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [标签1, 标签2]
sources: ["[[YYYY-MM-DD-财经早读-关键词]]"]
related: ["[[关联1]]", "[[关联2]]"]
---
# 实体名称

## 基本信息
- 行业：xxx
- 产业链：xxx

## 近期动态
### YYYY年M月：事件标题
- 事件描述

## 关联
- [[关联实体]]
```

### Topic文件格式

```yaml
---
type: topic
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [主题标签]
sources: ["[[YYYY-MM-DD-财经早读-关键词]]"]
related: [关联主题]
---
# 主题名称

## 概述
主题描述

## 近期动态
### YYYY-MM-DD 动态
- 动态内容

## 关联
- [[关联主题]]
```

## 文件命名规则

| 文件类型 | 命名格式 | 示例 |
|---------|---------|------|
| 财经早读(MD) | `YYYY-MM-DD-财经早读.md` | `2026-07-21-财经早读.md` |
| 财经早餐(DOCX) | `YYYY年M月D日财经早餐.docx` | `2026年7月21日财经早餐.docx` |
| Wiki Source | `YYYY-MM-DD-财经早读-关键词.md` | `2026-07-21-财经早读-监管政策与DeepSeek定价.md` |
| Entity | `{实体名称}.md` | `证监会.md` |
| Topic | `{主题名称}.md` | `科技股.md` |

## 错误处理

- **文件不存在**：提示用户确认文件路径
- **目标目录不存在**：自动创建目录
- **Entity已存在**：追加更新sources字段，不覆盖现有内容
- **关键词提取失败**：询问用户提供关键词列表

## 示例

用户说："把这个文件添加到我的Obsidian知识库：C:\Users\johnn\Desktop\2026年7月21日财经早餐.md"

操作：
1. 读取文件内容
2. 复制MD到 `交易体系/财经早读/2026-07-21-财经早读.md`
3. 复制DOCX到 `附件/2.财经早读/2026年7月21日财经早餐.docx`
4. 创建 `wiki/sources/2026-07-21-财经早读-监管政策与DeepSeek定价.md`
5. 更新/创建entities: 证监会、DeepSeek、华友钴业、三一重工、中国建筑、花旗、胡塞武装、沙特
6. 更新/创建topics: 科技股、回购与分红策略、大宗商品
7. 输出更新报告