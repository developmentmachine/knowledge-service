# API 接口规范 (API Reference)

供外部自动化脚本及 AI Agents 调用的 RESTful API 契约说明。

## 1. 摄入知识 (Ingest Document)

将单个文档（文本、代码）推送到知识库中。系统会自动完成切分、向量化和存储。

**Endpoint:** `POST /api/v1/ingest`
**Content-Type:** `application/json`

### 请求体 (Request Body)
```json
{
  "project_id": "agent-platform",
  "file_path": "/src/core/utils.py",
  "content": "def calculate_metrics():\n    pass",
  "metadata": {
    "extension": ".py",
    "author": "admin"
  }
}
```
*参数说明：*
- `project_id` (Required, string): 必须提供，用于严格隔离不同项目的数据。
- `file_path` (Required, string): 原始文件路径。将在检索时返回，供 Agent 溯源。
- `content` (Required, string): 文档的完整文本内容。
- `metadata` (Optional, dict): 附加的业务元数据。

### 响应体 (Response Body)
```json
{
  "status": "success",
  "chunks_ingested": 5
}
```

---

## 2. 检索知识 (Retrieve Knowledge)

执行 RAG 检索的核心接口。强制要求 Agent 指定作用域，防止知识污染。

**Endpoint:** `POST /api/v1/retrieve`
**Content-Type:** `application/json`

### 请求体 (Request Body)
```json
{
  "query": "如何在 docker-compose 中配置数据库？",
  "scopes": ["agent-platform"],
  "top_k": 5,
  "hybrid_search": true
}
```
*参数说明：*
- `query` (Required, string): 用户的自然语言提问。
- `scopes` (Required, array of strings): 必须提供。查询将**严格限制**在这些 `project_id` 范围内。如果涉及多个项目关联，可传入多个，如 `["proj_A", "proj_B"]`。
- `top_k` (Optional, int): 返回的最佳匹配切片数量，默认 5。
- `hybrid_search` (Optional, bool): 是否开启混合检索（V3.0 预留字段），当前版本固定走向量检索。

### 响应体 (Response Body)
```json
[
  {
    "chunk_id": "123e4567-e89b-12d3-a456-426614174000",
    "project_id": "agent-platform",
    "file_path": "docker-compose.yml",
    "content": "services:\n  db:\n    image: postgres:14...",
    "score": 0.9231,
    "metadata": {
      "file_path": "docker-compose.yml",
      "importance_score": 1.0,
      "chunk_type": "markdown",
      "project_id": "agent-platform"
    }
  }
]
```
*字段说明：*
- `score`: 语义相似度得分，范围通常在 0.0 ~ 1.0 之间。分数越高代表内容与 `query` 越匹配。
- `content`: 返回给大模型的上下文片段（Context Chunk）。
