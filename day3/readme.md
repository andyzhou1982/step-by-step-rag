# Day 2: Enhanced Document Processing
# Day 2: 增强的文档处理

Multi-format document support with intelligent chunking and metadata extraction.
多格式文档支持，智能分块和元数据提取。

## Day 2 Features / Day 2 功能

### Multi-Format Support / 多格式支持
| Format | Extension | Description |
|--------|-----------|-------------|
| Text | `.txt` | Plain text files / 纯文本文件 |
| Markdown | `.md` | Markdown documents / Markdown 文档 |
| PDF | `.pdf` | PDF documents / PDF 文档 |
| Word | `.docx` | Microsoft Word (2007+) / Microsoft Word 文档 (2007+) |
| HTML | `.html`, `.htm` | HTML web pages / HTML 网页 |

### Smart Chunking / 智能分块
- **Text/PDF/Word**: RecursiveCharacterTextSplitter
- **Markdown**: MarkdownHeaderTextSplitter (preserves headers / 保留标题)
- **HTML**: HTMLHeaderTextSplitter (preserves structure / 保留结构)

### Metadata Extraction / 元数据提取
- Document title (extracted from content / 从内容中提取)
- File type / 文件类型
- File size / 文件大小
- Custom metadata / 自定义元数据

## Architecture / 架构

```
day2/
├── backend/
│   ├── src/
│   │   ├── main.py              # FastAPI entry point / FastAPI 入口
│   │   ├── config.py             # Configuration / 配置
│   │   ├── routers/
│   │   │   ├── documents.py      # Document API (Day 2 enhanced) / 文档 API (Day 2 增强)
│   │   │   └── chat.py            # Chat API / 聊天 API
│   │   ├── services/
│   │   │   ├── document_parser.py # NEW: Multi-format parser / 新增: 多格式解析器
│   │   │   ├── embedding.py       # Embedding service / 嵌入服务
│   │   │   ├── llm.py             # LLM service / LLM 服务
│   │   │   └── vector_store.py    # Vector store (Day 2 enhanced) / 向量存储 (Day 2 增强)
│   │   └── models/
│   │       └── schemas.py         # Data models (Day 2 enhanced) / 数据模型 (Day 2 增强)
│   ├── pyproject.toml             # uv dependencies / uv 依赖
│   └── .env.example
└── frontend/
    └── ...
```

## New API Endpoints / 新 API 端点

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/documents/formats` | List supported formats / 列出支持的格式 |
| POST | `/documents/upload` | Upload any supported format / 上传任何支持的格式 |
| GET | `/documents/list` | List with file type info / 带文件类型信息的列表 |

## Quick Start / 快速开始

### 1. Setup Database / 设置数据库

```bash
cd day2
docker-compose up -d
```

### 2. Setup Backend / 设置后端

```bash
cd day2/backend

# Install dependencies with uv
# 使用 uv 安装依赖
uv sync

# Configure environment
# 配置环境
cp .env.example .env
# Edit .env with your API key
# 编辑 .env 填入你的 API key

# Run server
# 运行服务器
uv run python -m uvicorn src.main:app --reload --port 8000
```

### 3. Setup Frontend / 设置前端

```bash
cd day2/frontend
npm install
npm run dev
```

### 4. Access the Application / 访问应用

- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

## Testing Multi-Format / 测试多格式

```bash
# Upload PDF
# 上传 PDF
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@document.pdf"

# Upload Word
# 上传 Word
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@document.docx"

# Upload Markdown
# 上传 Markdown
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@readme.md"

# Check supported formats
# 检查支持的格式
curl "http://localhost:8000/documents/formats"
```

## Changes from Day 1 / 与 Day 1 的区别

See [CHANGES.md](./CHANGES.md) for detailed documentation of all changes.
详细修改说明请查看 [CHANGES.md](./CHANGES.md)。

### Key Files Changed / 主要修改的文件:
| File | Change |
|------|--------|
| `services/document_parser.py` | **NEW** - Multi-format parser |
| `routers/documents.py` | Multi-format upload support |
| `models/schemas.py` | Added metadata models |
| `services/vector_store.py` | Metadata storage support |

### New Dependencies / 新增依赖:
| Package | Purpose |
|---------|---------|
| `pypdf` | PDF parsing / PDF 解析 |
| `python-docx` | Word parsing / Word 解析 |
| `beautifulsoup4` | HTML parsing / HTML 解析 |
| `lxml` | XML/HTML backend / XML/HTML 后端 |
| `chardet` | Encoding detection / 编码检测 |

## Next: Day 3 / 下一步: Day 3

Retrieval optimization:
- Hybrid search (vector + BM25)
- Query rewriting
- Re-ranking with Cross-Encoder

检索优化:
- 混合检索 (向量 + BM25)
- 查询重写
- 使用 Cross-Encoder 重排序
