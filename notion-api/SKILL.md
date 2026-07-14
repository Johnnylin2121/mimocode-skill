---
name: notion-api
description: Notion REST API integration for Windows/PowerShell environments. Use when working with Notion pages, databases, or blocks — creating, reading, updating, or searching content. Handles authentication, UTF-8 encoding for Chinese content, and the quirks of PowerShell's JSON handling.
---

# Notion API Integration

## Quick Start

### Authentication

Notion API requires an Internal Integration Token (static, no OAuth refresh needed for basic operations).

**Token location**: Stored in project MEMORY.md under `## Discovered durable knowledge`.

**Header format**:
```
Authorization: Bearer <token>
Notion-Version: 2022-06-28
Content-Type: application/json
```

### Critical PowerShell Encoding Rule

**Never use PowerShell `ConvertTo-Json` directly for Notion API requests with Chinese content.** It produces malformed JSON.

**Correct approach**: Write JSON to a UTF-8 file, then use .NET `WebClient`:

```powershell
# 1. Write JSON to file (UTF-8 without BOM)
$json = @{
    parent = @{ page_id = "your-page-id" }
    properties = @{
        title = @{
            title = @(@{ text = @{ content = "标题" } })
        }
    }
} | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText("C:\temp\notion_request.json", $json, [System.Text.UTF8Encoding]::new($false))

# 2. Send with WebClient
$webclient = New-Object System.Net.WebClient
$webclient.Headers.Add("Authorization", "Bearer ntn_YOUR_TOKEN")
$webclient.Headers.Add("Notion-Version", "2022-06-28")
$webclient.Headers.Add("Content-Type", "application/json")
$response = $webclient.UploadString("https://api.notion.com/v1/pages", "POST", $json)
```

## Common Operations

### Search Pages

```powershell
$body = @{ query = "search term"; filter = @{ property = "object"; value = "page" } } | ConvertTo-Json
# Write to file and send (see encoding rule above)
POST https://api.notion.com/v1/search
```

### Create Page

```powershell
$body = @{
    parent = @{ page_id = "parent-page-id" }
    properties = @{
        title = @{
            title = @(@{ text = @{ content = "Page Title" } })
        }
    }
    children = @(
        @{
            object = "block"
            type = "paragraph"
            paragraph = @{
                rich_text = @(@{ type = "text"; text = @{ content = "Content here" } })
            }
        }
    )
} | ConvertTo-Json -Depth 10
POST https://api.notion.com/v1/pages
```

### Update Block (Append Children)

```powershell
PATCH https://api.notion.com/v1/blocks/{block_id}/children
# Body: same structure as children array above
```

### Get Page Content

```powershell
GET https://api.notion.com/v1/blocks/{block_id}/children
```

## Block Types Reference

| Type | Structure |
|------|-----------|
| Paragraph | `paragraph.rich_text[]` |
| Heading 1/2/3 | `heading_1/2/3.rich_text[]` |
| Bulleted list | `bulleted_list_item.rich_text[]` |
| Numbered list | `numbered_list_item.rich_text[]` |
| Divider | `divider = {}` |
| Code | `code.rich_text[]`, `code.language` |
| Image | `image.external.url` or `image.file.url` |

## Rich Text Format

```json
{
    "type": "text",
    "text": {
        "content": "Text content",
        "link": { "url": "https://example.com" }
    },
    "annotations": {
        "bold": true,
        "italic": false,
        "code": false
    }
}
```

## Known Gotchas

1. **Chinese encoding**: Always write JSON to UTF-8 file first, never use raw PowerShell JSON
2. **Depth limit**: `ConvertTo-Json -Depth 10` for nested structures
3. **Rate limits**: Notion API allows ~3 requests/second
4. **Block limit**: Max 100 children per `append blocks` call
5. **Page size**: Max 2000 characters per rich_text block

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid/expired token | Check token in MEMORY.md |
| `400 Bad Request` | Malformed JSON | Use UTF-8 file approach |
| `409 Conflict` | Concurrent edit | Retry after delay |
| `429 Too Many Requests` | Rate limit | Wait 1 second and retry |
