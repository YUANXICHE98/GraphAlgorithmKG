# 多领域知识图谱构建系统完整流程图

## 🏗️ **系统总体架构图**

```mermaid
graph TB
    subgraph "文档输入层"
        A1[多格式文档] --> A2[格式解析器]
        A2 --> A3[文本清洗器]
        A3 --> A4[智能分块器]
        A4 --> A5[标准文本块]
    end
    
    subgraph "Schema检测与本体适配层"
        B1[Schema检测器] --> B2[特征提取器]
        B2 --> B3[多Schema匹配器]
        B3 --> B4{置信度差异<10%?}
        B4 -->|是| B5[LLM辅助决策]
        B4 -->|否| B6[最优Schema选择]
        B5 --> B6
        B6 --> B7[本体管理器]
        B7 --> B8[领域词库构建器]
        B8 --> B9[Schema配置]
    end
    
    subgraph "智能推断层"
        C1[6层分层推断器] --> C2[第1层: 缓存查找]
        C2 --> C3{缓存命中?}
        C3 -->|是| C4[返回缓存结果]
        C3 -->|否| C5[第2层: Schema匹配]
        C5 --> C6{Schema匹配成功?}
        C6 -->|是| C7[返回Schema类型]
        C6 -->|否| C8[第3层: 模式匹配]
        C8 --> C9{模式匹配成功?}
        C9 -->|是| C10[返回模式类型]
        C9 -->|否| C11[第4层: 关键词匹配]
        C11 --> C12{关键词匹配成功?}
        C12 -->|是| C13[返回关键词类型]
        C12 -->|否| C14[第5层: 上下文分析]
        C14 --> C15{上下文推断成功?}
        C15 -->|是| C16[返回上下文类型]
        C15 -->|否| C17[第6层: 标记为Unknown]
        C4 --> C18[实体类型结果]
        C7 --> C18
        C10 --> C18
        C13 --> C18
        C16 --> C18
        C17 --> C18
    end
    
    subgraph "混合三元组抽取层"
        D1[混合抽取器] --> D2[阶段1: 规则抽取]
        D2 --> D3[规则模式匹配]
        D3 --> D4[生成规则三元组]
        D4 --> D5{规则抽取充分?}
        D5 -->|是| D6[返回规则结果]
        D5 -->|否| D7[阶段2: LLM兜底抽取]
        D7 --> D8[动态Prompt生成]
        D8 --> D9[LLM三元组抽取]
        D9 --> D10[阶段3: 结果合并去重]
        D6 --> D11[最终三元组结果]
        D10 --> D11
    end
    
    subgraph "语义验证与质量控制层"
        E1[规则验证引擎] --> E2[本体约束检查]
        E2 --> E3[类型验证器]
        E3 --> E4{规则验证通过?}
        E4 -->|是| E5[语义一致性检查]
        E4 -->|否| E6[LLM语义验证器]
        E5 --> E7[质量评分系统]
        E6 --> E7
        E7 --> E8{质量分数>阈值?}
        E8 -->|是| E9[高质量三元组]
        E8 -->|否| E10[标记待审核]
    end
    
    subgraph "知识图谱构建与存储层"
        F1[实体去重器] --> F2[编辑距离计算]
        F2 --> F3[语义相似度分析]
        F3 --> F4[关系融合器]
        F4 --> F5[冲突解决器]
        F5 --> F6[图结构构建器]
        F6 --> F7[索引优化器]
        F7 --> F8[增量更新管理器]
        F8 --> F9[知识图谱数据库]
    end
    
    subgraph "实时监控与反馈层"
        G1[性能监控器] --> G2[指标收集器]
        G2 --> G3[质量评估器]
        G3 --> G4[异常检测器]
        G4 --> G5[反馈学习器]
        G5 --> G6[系统优化建议]
    end
    
    subgraph "KAG兼容层"
        H1[标准化接口] --> H2[数据格式转换器]
        H2 --> H3[KAG SDK适配器]
        H3 --> H4[增量更新管理器]
        H4 --> H5[外部系统集成]
    end
    
    %% 数据流连接
    A5 --> B1
    B9 --> C1
    B9 --> D1
    C18 --> D1
    D11 --> E1
    E9 --> F1
    F9 --> G1
    F9 --> H1
    G6 --> B1
    G6 --> C1
    G6 --> D1
    E10 --> G3
```

## 🔍 **智能推断层详细流程图**

```mermaid
graph LR
    A[新实体输入] --> B[分层推断系统]
    
    B --> C1[第1层: 缓存查找]
    C1 --> D1{缓存命中?}
    D1 -->|是,置信度>0.9| E1[返回缓存结果]
    D1 -->|否| C2[第2层: Schema匹配]
    
    C2 --> D2{Schema匹配成功?}
    D2 -->|是,置信度>0.8| E2[返回Schema结果]
    D2 -->|否| C3[第3层: 模式识别]
    
    C3 --> D3{正则模式匹配?}
    D3 -->|是,置信度>0.7| E3[返回模式结果]
    D3 -->|否| C4[第4层: 关键词匹配]
    
    C4 --> D4{关键词匹配?}
    D4 -->|是,置信度>0.6| E4[返回关键词结果]
    D4 -->|否| C5[第5层: 上下文分析]
    
    C5 --> D5{上下文推断成功?}
    D5 -->|是,置信度>0.5| E5[返回上下文结果]
    D5 -->|否| C6[第6层: LLM推断]
    
    C6 --> E6[LLM语义推断]
    
    %% 结果处理
    E1 --> F[验证结果]
    E2 --> F
    E3 --> F
    E4 --> F
    E5 --> F
    E6 --> F
    
    F --> G{验证通过?}
    G -->|是| H[更新缓存]
    G -->|否| I[标记为待审核]
    
    H --> J[提升命中率]
    I --> K[人工审核队列]
    K --> L{审核通过?}
    L -->|是| H
    L -->|否| M[丢弃结果]
    
    J --> N[下次查询更快]
    M --> O[避免错误传播]
    
    %% 性能优化反馈
    N --> P[性能统计]
    O --> P
    P --> Q[优化建议]
    Q --> B
```

## 📊 **Schema检测详细流程图**

```mermaid
graph TD
    A[文档输入] --> B[特征提取]
    
    B --> C1[方法1: 本体实体匹配]
    B --> C2[方法2: 种子知识匹配]
    B --> C3[方法3: 文档结构匹配]
    
    C1 --> D1[关键词频率分析]
    D1 --> D2[实体示例匹配]
    D2 --> E1[本体匹配分数]
    
    C2 --> D3[关系类型匹配]
    D3 --> D4[实体类型推断]
    D4 --> E2[种子知识分数]
    
    C3 --> D5[结构化模式识别]
    D5 --> D6[命名规律分析]
    D6 --> E3[文档结构分数]
    
    E1 --> F[加权融合]
    E2 --> F
    E3 --> F
    
    F --> G[候选Schema排序]
    G --> H{前两名置信度差异<10%?}
    
    H -->|否| I[返回最高分Schema]
    H -->|是| J[LLM辅助决策]
    
    J --> K[构建决策Prompt]
    K --> L[GPT语义分析]
    L --> M[提取LLM选择]
    M --> N[更新置信度]
    N --> O[返回LLM优化结果]
    
    I --> P[Schema配置加载]
    O --> P
    P --> Q[本体切换完成]
```

## 🔄 **数据流转详细图**

```mermaid
sequenceDiagram
    participant Doc as 文档输入
    participant Parser as 文档解析器
    participant Detector as Schema检测器
    participant Inferer as 实体推断器
    participant RuleExtractor as 规则抽取器
    participant LLM as LLM抽取器
    participant HybridExtractor as 混合抽取器
    participant Validator as 语义验证器
    participant Builder as 图构建器
    participant Storage as 存储系统
    participant Monitor as 监控系统
    
    Doc->>Parser: 多格式文档
    Parser->>Parser: 格式转换+文本清洗
    Parser->>Detector: 标准化文本块
    
    Detector->>Detector: 特征提取+多Schema匹配
    alt 置信度相近
        Detector->>LLM: LLM辅助决策
        LLM-->>Detector: 最优Schema选择
    end
    Detector->>Inferer: Schema配置
    
    Inferer->>Inferer: 6层分层推断
    Inferer->>HybridExtractor: 实体类型信息

    HybridExtractor->>RuleExtractor: 阶段1: 规则抽取
    RuleExtractor->>RuleExtractor: 模式匹配+规则应用
    RuleExtractor->>HybridExtractor: 规则三元组

    HybridExtractor->>HybridExtractor: 评估规则抽取质量
    alt 规则抽取不充分
        HybridExtractor->>LLM: 阶段2: LLM兜底抽取
        LLM->>LLM: 动态Prompt生成
        LLM->>LLM: 语义三元组抽取
        LLM->>HybridExtractor: LLM三元组
    end

    HybridExtractor->>HybridExtractor: 阶段3: 结果合并去重
    HybridExtractor->>Validator: 最终三元组
    
    Validator->>Validator: 规则验证
    alt 规则验证失败
        Validator->>LLM: 语义验证请求
        LLM-->>Validator: 语义验证结果
    end
    Validator->>Builder: 高质量三元组
    
    Builder->>Builder: 实体去重+关系融合
    Builder->>Storage: 知识图谱数据
    
    Storage->>Monitor: 处理结果
    Monitor->>Monitor: 性能分析+质量评估
    Monitor-->>Detector: 优化建议
    Monitor-->>Inferer: 缓存优化
    Monitor-->>LLM: Prompt优化
```

## 🎯 **关键决策点说明**

### **Schema检测决策点**
- **置信度阈值**: 10%差异作为LLM介入阈值
- **特征权重**: 本体匹配40% + 种子知识30% + 文档结构30%
- **LLM触发条件**: 前两名Schema置信度相近时
- **LLM模式**: 支持API模式和模拟模式，自动降级

### **实体推断决策点**
- **第1层-缓存查找**: 置信度>阈值直接返回，避免重复计算
- **第2层-Schema匹配**: 基于本体定义的精确匹配，置信度0.9
- **第3层-模式匹配**: 基于正则表达式的命名规律识别，置信度0.8
- **第4层-关键词匹配**: 基于领域词汇的类型推断，置信度0.7
- **第5层-上下文分析**: 基于语义环境的类型推断，置信度0.6
- **第6层-未知标记**: 所有层都失败时标记为Unknown，不调用LLM

### **质量控制决策点**
- **规则验证优先**: 先进行快速规则验证
- **语义验证兜底**: 规则失败时使用LLM语义验证
- **质量分数阈值**: 综合评分决定是否接受三元组

这个完整的流程图展示了系统的每个细节，包括决策逻辑、数据流转和优化反馈机制。
