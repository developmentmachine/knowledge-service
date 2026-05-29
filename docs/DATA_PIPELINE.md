# 数据流水线与工作流 (Data Pipelines & Workflow)

本服务提供两条核心流水线：**数据摄入（Ingestion Pipeline）**和**知识检索（Retrieval Pipeline）**。

## 1. 数据摄入流水线 (Ingestion Pipeline)

目标：将非结构化文件转化为可被检索的高质量向量切片。

### 1.1 流程图
```text
[Raw Document] -> (1. Parse & Chunk) -> (2. Embed) -> (3. Enrich Metadata) -> (4. Store)
```

### 1.2 步骤详解
1. **解析与切片 (Parse & Chunk):**
   - 当前采用 `RecursiveCharacterTextSplitter`。
   - **块大小 (Chunk Size):** 默认 1000 字符。
   - **重叠 (Overlap):** 默认 200 字符。保留重叠是为了防止关键句子被硬生生切断，从而导致语义丢失。
2. **向量化 (Embed):**
   - 提取切片中的文本内容，以批处理（Batch）方式送入本地 `SentenceTransformer` 模型，计算得到稠密向量（Dense Vector，当前维度为 384）。
3. **元数据绑定 (Enrich Metadata):**
   - 将文件的 `project_id`, `file_path`, 以及自动识别的 `chunk_type` 拍平（Flatten）注入到 Chunk 的 Metadata 中。
4. **持久化存储 (Store):**
   - 存入 ChromaDB，建立 HNSW（Hierarchical Navigable Small World）索引。

---

## 2. 知识检索流水线 (Retrieval Pipeline)

目标：根据 AI Agent 提供的查询和作用域，精准召回相关上下文。

### 2.1 流程图
```text
[Agent Query + Scopes] -> (1. Embed Query) -> (2. Filter DB) -> (3. Vector Search) -> (4. Format & Return)
```

### 2.2 步骤详解
1. **查询向量化 (Embed Query):**
   - 将 Agent 的提问转化为同等维度的查询向量。
2. **构建过滤器 (Build Filters):**
   - 根据 Agent 传入的 `scopes` 构建 DB 原生过滤条件。
   - 例如：`{"project_id": {"$in": ["agent-platform", "agent-framework"]}}`。
3. **相似度检索 (Vector Search):**
   - 在限定的作用域内，计算查询向量与库中向量的余弦相似度（Cosine Similarity）。
   - Chroma 默认返回 L2 距离，系统在内部将其转换为 `1.0 - distance` 的相似度得分（Score），得分越高越相关。
4. **组装结果:**
   - 提取 Top-K 结果（包含原始文本、文件路径、来源项目等），返回给 Agent 供其进行 RAG（检索增强生成）回答。

---

## 3. V3.0 未来演进方向 (Future Enhancements)

目前流水线已达到 V2.0 生产标准，未来可进一步增强：
1. **代码级语法切片 (AST Chunking):** 针对 Python/Java，引入 `Tree-sitter`，按完整的函数（Function）或类（Class）进行切片，而非单纯按字符数截断。
2. **混合检索 (Hybrid Search):** 在现有 Dense Vector 检索的基础上，加入基于 BM25 算法的稀疏检索（关键词检索），解决特定变量名、报错类名的精确匹配问题。
3. **重排序层 (Re-ranking):** 召回 Top-50 后，使用交叉编码器（Cross-Encoder，如 `bge-reranker`）进行二次打分，仅输出最精确的 Top-5 给大模型。
