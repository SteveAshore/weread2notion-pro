# WeRead2Notion Pro - AI Agent Guide

## Project Overview

WeRead2Notion Pro (微信读书同步到 Notion Pro 版) is a Python automation tool that synchronizes WeChat Reading (微信读书) highlights, notes, and reading progress to Notion. It runs via GitHub Actions on a scheduled basis.

**Key Features:**
- Automatic sync of bookshelf, highlights, notes, and reading time
- CookieCloud integration for automatic cookie retrieval
- Cookie validation and automatic refresh
- Reading time heatmap generation
- Multi-database relationship management in Notion

**Project Language:** Chinese (documentation and comments)

## Technology Stack

- **Language:** Python 3.6+
- **CI/CD:** GitHub Actions
- **External APIs:** Notion API, WeRead API, CookieCloud
- **Key Libraries:**
  - `notion-client` - Official Notion API client
  - `requests` - HTTP requests
  - `pendulum` - Date/time handling
  - `pycryptodome` - AES decryption for CookieCloud
  - `python-dotenv` - Environment variable management
  - `retrying` - Retry decorators
  - `github-heatmap` - Reading heatmap generation

## Project Structure

```
weread2notion-pro/
├── weread2notionpro/           # Main Python package
│   ├── __init__.py             # Empty package init
│   ├── __main__.py             # Entry point (calls book.main)
│   ├── book.py                 # Bookshelf sync - main entry
│   ├── weread.py               # Notes/highlights sync
│   ├── read_time.py            # Reading time & heatmap sync
│   ├── weread_api.py           # WeRead API client
│   ├── notion_helper.py        # Notion API helper
│   ├── cookie_manager.py       # CookieCloud & cookie management
│   ├── utils.py                # Utility functions
│   └── config.py               # Configuration constants
├── .github/workflows/          # GitHub Actions
│   ├── weread.yml              # Main sync workflow (every 2h)
│   └── read_time.yml           # Reading time sync (every 3h)
├── docs/
│   └── weread_api.md           # WeRead API documentation
├── asset/                      # Image assets for README
├── test_cookie.py              # Local cookie testing script
├── requirements.txt            # Python dependencies
├── setup.py                    # Package setup
└── README.md                   # User documentation (Chinese)
```

## Module Responsibilities

### Core Sync Modules

| Module | Purpose | Console Command |
|--------|---------|-----------------|
| `book.py` | Sync bookshelf, book metadata, authors, categories | `book` |
| `weread.py` | Sync highlights and notes to book pages | `weread` |
| `read_time.py` | Sync daily reading time and update heatmap | `read_time` |

### Supporting Modules

| Module | Purpose |
|--------|---------|
| `weread_api.py` | WeRead API client with automatic cookie refresh |
| `notion_helper.py` | Notion database operations, relation management |
| `cookie_manager.py` | CookieCloud fetch, AES decrypt, validation |
| `utils.py` | Notion block builders, date formatting helpers |
| `config.py` | Database property type mappings, timezone config |

## GitHub Actions Workflows

### 1. `weread.yml` - Main Sync
- **Trigger:** Schedule (every 2 hours) or manual dispatch
- **Jobs:**
  1. Verify Cookie (using CookieManager)
  2. Run `book` command (sync bookshelf)
  3. Run `weread` command (sync notes)

### 2. `read_time.yml` - Reading Time Sync
- **Trigger:** Schedule (every 3 hours) or manual dispatch
- **Jobs:**
  1. Verify Cookie
  2. Generate reading heatmap SVG using `github-heatmap`
  3. Push heatmap to repository
  4. Run `read_time` command (sync reading time data)

## Environment Variables

### Required Secrets (GitHub Secrets)

| Variable | Description |
|----------|-------------|
| `NOTION_TOKEN` | Notion Integration Token (format: `secret_xxx`) |
| `NOTION_PAGE` | Full Notion page URL containing databases |

### Cookie Configuration (One method required)

**Method 1: CookieCloud (Recommended)**
| Variable | Description |
|----------|-------------|
| `CC_URL` | CookieCloud server URL (default: https://cookiecloud.malinkang.com) |
| `CC_ID` | User UUID from browser extension |
| `CC_PASSWORD` | End-to-end encryption password |

**Method 2: Direct Cookie (Fallback)**
| Variable | Description |
|----------|-------------|
| `WEREAD_COOKIE` | Raw cookie string from browser |

### Optional Variables (GitHub Variables)

Database name customization:
- `BOOK_DATABASE_NAME` (default: "书架")
- `AUTHOR_DATABASE_NAME` (default: "作者")
- `CATEGORY_DATABASE_NAME` (default: "分类")
- `BOOKMARK_DATABASE_NAME` (default: "划线")
- `REVIEW_DATABASE_NAME` (default: "笔记")
- `CHAPTER_DATABASE_NAME` (default: "章节")
- `YEAR_DATABASE_NAME` (default: "年")
- `WEEK_DATABASE_NAME` (default: "周")
- `MONTH_DATABASE_NAME` (default: "月")
- `DAY_DATABASE_NAME` (default: "日")

Heatmap colors (optional):
- `background_color`, `track_color`, `special_color`, `special_color2`, `dom_color`, `text_color`

## Local Development

### Setup

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/weread2notion-pro.git
cd weread2notion-pro

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
CC_URL=https://cookiecloud.malinkang.com
CC_ID=your_uuid
CC_PASSWORD=your_password
NOTION_TOKEN=secret_xxx
NOTION_PAGE=https://www.notion.so/xxx
EOF
```

### Running Tests

```bash
# Test cookie configuration
python test_cookie.py

# Run sync commands locally
python -m weread2notionpro.book
python -m weread2notionpro.weread
python -m weread2notionpro.read_time
```

### Entry Points (from setup.py)

```bash
book        # Sync bookshelf
weread      # Sync notes/highlights
read_time   # Sync reading time
```

## Code Style Guidelines

### Python Style
- Follow PEP 8 conventions
- Use type hints where applicable (newer modules like `cookie_manager.py`)
- Chinese comments for business logic
- Google-style docstrings for complex functions

### Module Patterns

**API Client Pattern (weread_api.py):**
```python
class WeReadApi:
    def __init__(self):
        self.cookie_manager = CookieManager()
        # ...
    
    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def api_method(self):
        # Retry decorator for all API calls
        pass
```

**Notion Helper Pattern (notion_helper.py):**
```python
class NotionHelper:
    database_name_dict = {...}  # Database name mapping
    
    def __init__(self):
        # Auto-discover databases from page
        self.search_database(self.page_id)
```

## Database Schema

### Notion Database Structure

The project manages multiple related databases:

1. **书架 (Books)** - Main book database
2. **作者 (Authors)** - Author relation database
3. **分类 (Categories)** - Category relation database
4. **划线 (Bookmarks)** - Highlight storage
5. **笔记 (Reviews)** - Note storage
6. **章节 (Chapters)** - Chapter structure
7. **阅读记录 (Read)** - Daily reading time records
8. **设置 (Settings)** - Configuration storage

### Book Properties (from config.py)

Key properties synced for each book:
- `书名` (Title)
- `BookId` (Rich text)
- `作者` (Relation to Authors)
- `分类` (Relation to Categories)
- `阅读状态` (Status: 想读/在读/已读)
- `阅读时长` (Number - seconds)
- `阅读进度` (Number - percentage)
- `阅读天数` (Number)
- `评分` (Number)
- `封面` (Files)
- `书架分类` (Select)

## Security Considerations

### Cookie Management
- Cookies are never logged in full (truncated in logs)
- CookieCloud uses AES-256-CBC encryption with OpenSSL EVP_BytesToKey key derivation
- Automatic cookie validation before each sync
- Fallback from CookieCloud to direct cookie if needed

### CookieCloud Encryption Details

CookieCloud 使用 CryptoJS 进行 AES 加密，Python 解密需要实现 OpenSSL 兼容的 EVP_BytesToKey 密钥派生算法：

**加密流程：**
1. 生成密钥：`MD5(uuid + "-" + password)[:16]`
2. CryptoJS.AES.encrypt 自动生成随机 8 字节 salt
3. 密文格式：`Salted__` + salt + ciphertext
4. 密钥派生：使用 EVP_BytesToKey 从 password + salt 派生 32-byte key 和 16-byte IV

**参考实现：**
- CookieCloud 官方: https://github.com/easychen/CookieCloud
- obsidian-weread-plugin: https://github.com/zhaohongxuan/obsidian-weread-plugin
- 加密算法详解: `docs/cookiecloud_encryption.md`

### API Tokens
- All tokens stored in GitHub Secrets (never in code)
- `.env` file in `.gitignore` for local development
- Notion token format: `secret_xxx`

### Required Cookie for WeRead
- `wr_vid` - User ID (critical for authentication)
- `wr_name` - User name

## Testing Strategy

### Cookie Testing (test_cookie.py)
```bash
# Tests:
1. Environment variable check
2. Direct CookieCloud fetch
3. CookieManager integration
4. Cookie validation
```

### Manual Testing Workflow
1. Run `python test_cookie.py` to verify cookie setup
2. Run `book` command to sync bookshelf
3. Check Notion for book entries
4. Run `weread` command to sync notes
5. Verify highlights appear in book pages

## Troubleshooting

### Common Issues

**Cookie Expired:**
- CookieCloud will auto-refresh if configured
- Check browser extension is running and synced

**Notion API Errors:**
- Verify Integration has access to the page
- Check `NOTION_PAGE` is the full URL

**Missing Databases:**
- Must duplicate the official Notion template first
- Integration must be added to the page

## Architecture Decisions

### Why CookieCloud?
- WeRead cookies expire frequently
- Manual cookie copying is tedious
- CookieCloud browser extension auto-syncs cookies

### Sync Strategy
- Incremental sync based on `Sort` timestamp
- Books only synced if reading time changes
- Notes use blockId tracking to avoid duplicates

### Notion Block Types for Highlights
- Default: `callout` with emoji icons
- Configurable via Settings database: callout/quote/paragraph/bulleted_list_item/numbered_list_item
- Color support based on highlight color

## Resources

- **WeRead API Docs:** `docs/weread_api.md`
- **User Guide:** `README.md` (Chinese)
- **CookieCloud:** https://github.com/easychen/CookieCloud
- **Notion API:** https://developers.notion.com/

---

## CookieCloud 解密问题分析（2026-03-31）

### 问题描述

用户报告 CookieCloud 解密失败，错误信息：`PKCS#7 padding is incorrect`

### 根因分析

原代码实现的解密算法与 CookieCloud 实际使用的加密格式不兼容：

| 项目 | 原代码实现 | CookieCloud 实际 |
|------|-----------|------------------|
| 密钥派生 | 直接用 MD5[:16] 作为 key | EVP_BytesToKey 派生 |
| 密文格式 | 假设 IV + Ciphertext | `Salted__` + salt + ciphertext |
| AES 模式 | AES-128-CBC | AES-256-CBC |
| IV 来源 | 密文前 16 字节 | EVP_BytesToKey 派生 |

### 正确实现

参考 **obsidian-weread-plugin** 的实现：

```typescript
// obsidian-weread-plugin/src/cookieCloud.ts
private cookieDecrypt(uuid: string, encrypted: string, password: string) {
    const the_key = CryptoJS.MD5(uuid + '-' + password)
        .toString()
        .substring(0, 16);
    
    // CryptoJS.AES.decrypt 内部使用 EVP_BytesToKey 派生 key/iv
    const decrypted = CryptoJS.AES.decrypt(encrypted, the_key)
        .toString(CryptoJS.enc.Utf8);
    return JSON.parse(decrypted);
}
```

Python 端需要实现 **EVP_BytesToKey** 算法：

```python
def evp_bytes_to_key(password, salt, key_len=32, iv_len=16):
    """OpenSSL EVP_BytesToKey 密钥派生"""
    derived = b''
    block = b''
    while len(derived) < key_len + iv_len:
        hasher = hashlib.md5()
        hasher.update(block + password + salt)
        block = hasher.digest()
        derived += block
    return derived[:key_len], derived[key_len:key_len + iv_len]
```

### 解密流程

1. 生成初始密钥：`MD5(uuid + "-" + password)[:16]`
2. Base64 解码密文
3. 提取 salt（`Salted__` 后的 8 字节）
4. EVP_BytesToKey 派生 32-byte key 和 16-byte IV
5. AES-256-CBC 解密
6. PKCS7 去填充
7. JSON 解析

### 参考文档

- 详细加密原理：`docs/cookiecloud_encryption.md`
- CookieCloud 官方文档：https://github.com/easychen/CookieCloud
- obsidian-weread-plugin：https://github.com/zhaohongxuan/obsidian-weread-plugin
