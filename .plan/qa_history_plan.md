# 问答记录功能实现计划

## 需求概述

将问答历史持久化保存到数据库，用作评估素材。

**功能要求**：
1. 持久化保存问答记录
2. 保存到 PostgreSQL 数据库
3. 前端和后端都支持
4. 保存内容：问题 + 答案 + 检索到的上下文

---

## 实现方案

### 1. 数据库设计

新建表 `qa_history`：

```sql
CREATE TABLE qa_history (
    id VARCHAR(36) PRIMARY KEY,                    -- UUID
    question TEXT NOT NULL,                         -- 用户问题
    answer TEXT NOT NULL,                           -- AI 回答
    contexts JSONB NOT NULL DEFAULT '[]',           -- 检索上下文列表
    sources JSONB DEFAULT '{}',                     -- 来源引用（可选）
    retrieval_method VARCHAR(50),                   -- 检索方法
    confidence FLOAT DEFAULT 0.0,                   -- 置信度
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    conversation_id VARCHAR(36)                     -- 对话 ID（可选）
);
```

### 2. 后端实现

#### 2.1 新建服务：`services/qa_history_service.py`

```python
class QAHistoryService:
    """问答历史服务"""

    async def connect()           # 初始化数据库表
    async def disconnect()        # 断开连接
    async def add_record(...)     # 添加问答记录
    async def get_record(id)      # 获取单条记录
    async def list_records(...)   # 列出记录（分页）
    async def delete_record(id)   # 删除记录
    async def export_records(...) # 导出为 JSON
```

#### 2.2 新建路由：`routers/qa_history.py`

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/qa-history` | 获取问答历史列表 |
| GET | `/qa-history/{id}` | 获取单条问答详情 |
| DELETE | `/qa-history/{id}` | 删除问答记录 |
| POST | `/qa-history/export` | 导出问答为 JSON |

#### 2.3 修改 `routers/chat.py`

在 ChatResponse 返回前，自动保存问答记录。

#### 2.4 新增模型：`models/schemas.py`

```python
class QAHistoryRecord(BaseModel):
    """问答历史记录"""
    id: str
    question: str
    answer: str
    contexts: List[str]
    sources: Optional[List[SourceReference]] = None
    retrieval_method: Optional[str] = None
    confidence: float = 0.0
    created_at: datetime
    conversation_id: Optional[str] = None

class QAHistoryListResponse(BaseModel):
    """问答历史列表响应"""
    records: List[QAHistoryRecord]
    total: int
    page: int
    page_size: int
```

### 3. 前端实现

#### 3.1 更新 `api/client.ts`

```typescript
// 新增类型
interface QAHistoryRecord { ... }
interface QAHistoryListResponse { ... }

// 新增 API 函数
async function getQAHistoryList(page, pageSize): Promise<QAHistoryListResponse>
async function getQAHistoryDetail(id): Promise<QAHistoryRecord>
async function deleteQAHistory(id): Promise<void>
async function exportQAHistory(ids?): Promise<Blob>
```

#### 3.2 更新 `components/EvaluationPanel.tsx`

- 添加"从历史选择"按钮
- 添加历史问答列表模态框
- 选择后自动填充评估表单

---

## 修改文件清单

### 后端 (day5/backend/src/)

| 文件 | 操作 | 描述 |
|------|------|------|
| `services/qa_history_service.py` | 新建 | 问答历史服务 |
| `routers/qa_history.py` | 新建 | QA 历史 API 路由 |
| `routers/chat.py` | 修改 | 添加保存问答逻辑 |
| `models/schemas.py` | 修改 | 添加 QA 历史模型 |
| `main.py` | 修改 | 注册 qa_history 路由 |

### 前端 (day5/frontend/src/)

| 文件 | 操作 | 描述 |
|------|------|------|
| `api/client.ts` | 修改 | 添加 QA 历史 API |
| `components/EvaluationPanel.tsx` | 修改 | 添加历史选择功能 |

---

## 实现顺序

1. 后端：创建 qa_history_service.py
2. 后端：添加 schemas 模型
3. 后端：创建 qa_history.py 路由
4. 后端：修改 chat.py 添加保存逻辑
5. 后端：注册路由到 main.py
6. 前端：更新 api/client.ts
7. 前端：更新 EvaluationPanel.tsx
8. 测试验证

---

## 注意事项

- 保存是自动的（每次问答后自动记录）
- 历史记录支持分页查询
- 导出功能支持筛选特定记录
- 评估面板可直接选择历史记录
