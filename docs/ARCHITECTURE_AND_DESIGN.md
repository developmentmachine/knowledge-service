# 核心架构与设计思想 (Architecture & Design Philosophy)

本文档详细阐述了 `Knowledge-Service` V2.0 的核心架构设计、领域驱动设计（DDD）落地方式以及解决复杂工作空间知识管理的设计哲学。

## 1. 设计哲学 (Design Philosophy)

### 1.1 面向 AI Agent 的 RAG 优先 (RAG-First for Agents)
与传统的 Wiki 或 Confluence 不同，本知识库不追求“人类阅读时的排版美观”，而是追求**“机器检索时的语义精准度与上下文完整度”**。因此，系统严格约束了数据摄入必须经过切片（Chunking）与向量化（Embedding）。

### 1.2 逻辑多租户隔离 (Multi-Tenant Logical Isolation)
在拥有数百个项目（如 `agent-platform`, `hadoop`, `flink`）的工作空间中，将所有知识混入一个无区分的向量空间会导致灾难性的“知识污染”和“AI 幻觉”。
- **反模式 (Anti-Pattern):** 为每个项目启动一个独立的 ChromaDB 实例。这会导致巨大的内存开销和运维灾难。
- **最佳实践 (Our Approach):** 物理上共享单一向量空间，逻辑上强制通过强元数据（Metadata）进行隔离。所有知识切片必须绑定 `project_id`。Agent 在检索时通过 `scopes` 字段下推条件到 VectorStore，在数据库底层过滤，实现 100% 隔离。同时，该设计天然支持传入多个 `project_id` 以实现跨项目关联。

### 1.3 极简抽象与插件化 (Pluggability via DDD)
系统采用**依赖倒置原则**构建。领域层（Domain Layer）定义了 `BaseVectorStore`, `BaseEmbedder` 等接口。
当前基础设施层（Infrastructure Layer）提供的是基于 `ChromaDB` 和本地 `SentenceTransformers` 的实现（保护隐私、可离线）。未来当需要处理海量数据时，只需新增实现类即可无缝切换至 `Milvus` 或 `OpenAI API`，而无需修改任何业务逻辑代码。

---

## 2. 领域驱动架构 (DDD Architecture)

本服务严格遵循四层架构，目录结构映射如下：

```text
app/
├── domain/            # 领域层 (最核心，无外部依赖)
│   ├── models/        # 核心实体: Document, Chunk, QueryContext, RetrievalResult
│   └── repositories/  # 抽象接口: BaseVectorStore, BaseEmbedder, BaseParser
├── services/          # 应用服务层 (业务编排)
│   └── knowledge_service.py # 负责将 Parser, Embedder, VectorStore 串联成完整流水线
├── infrastructure/    # 基础设施层 (具体技术实现)
│   ├── embedding/     # SentenceTransformers 实现
│   ├── vector_store/  # ChromaDB 实现
│   └── parsing/       # Langchain Markdown 解析器实现
└── api/               # 接入层
    └── v1/            # FastAPI 路由定义与请求响应模型
```

---

## 3. 性能与资源优化设计 (Performance & Resource Optimization)

### 3.1 深度学习模型的单例模式 (Singleton Pattern for ML Models)
向量化模型（如 `all-MiniLM-L6-v2`）加载到内存通常需要数百兆并伴随几秒钟的延迟。为了支撑高并发的自动化灌库脚本，系统在 API 依赖注入层采用了 `functools.lru_cache`：
```python
@lru_cache()
def get_knowledge_service() -> KnowledgeService:
    # 确保 Embedder 和 ChromaDB 实例在 FastAPI 进程生命周期内只被初始化一次
    ...
```
这消除了每次 HTTP 请求重新加载模型的开销，极大提升了吞吐量。

### 3.2 可靠的防御性编程 (Defensive Programming)
在外部脚本 (`scripts/ingest_workspace.py`) 的设计中，充分考虑了企业级文件系统的复杂性：
1. **自动跳过二进制/非UTF-8文件**，防止进程崩溃。
2. **黑名单过滤 (`IGNORE_DIRS`)**：强制跳过 `.git`, `node_modules`, `venv`, `target` 等编译输出目录，避免垃圾代码污染向量库。
3. **长时超时控制 (`timeout=300`)**：应对单次请求中长文档拆分成数百个 Chunk 时的嵌入推理耗时。
