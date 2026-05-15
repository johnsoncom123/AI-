# AI 自动批改作业项目

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 项目概述

AI 自动批改作业系统通过智能化技术解决传统批改的四大痛点：**效率低下**、**成本高昂**、**反馈延迟**、**标准不一致**。系统可节省教师 70% 以上的批改时间，实现秒级反馈，并通过数据分析助力精准教学。

### 核心目标

- **准确率**：客观题>99%，主观题>85%
- **效率**：单题批改<3 秒，支持 1000+ 并发
- **体验**：提供个性化反馈和学情分析
- **覆盖**：支持 10+ 学科题型

## 系统架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  多端接入    │────▶│  API 网关    │────▶│ 作业管理服务 │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  教师复核    │◀────│  反馈生成    │◀────│ 结果聚合    │
└─────────────┘     └─────────────┘     └─────────────┘
                                              ▲
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
              ┌─────┴─────┐           ┌───────┴───────┐         ┌───────┴───────┐
              │ 客观题批改 │           │  主观题批改   │         │   作文批改    │
              └───────────┘           └───────────────┘         └───────────────┘
                                              ▲
                                              │
                                      ┌───────┴───────┐
                                      │  AI 批改引擎  │
                                      └───────────────┘
                                              ▲
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
              ┌─────┴─────┐           ┌───────┴───────┐         ┌───────┴───────┐
              │ OCR 识别   │           │  文本清洗     │         │  编程题批改   │
              └───────────┘           └───────────────┘         └───────────────┘
```

## 功能特性

### 支持的题型

| 题型 | 技术方案 | 评分维度 |
|------|----------|----------|
| **客观题** | 模糊匹配 + 精确匹配 | 正确/错误 |
| **主观题** | 语义相似度 + 关键词匹配 | 语义相关性、关键词覆盖率 |
| **作文** | BERT 微调 + 多维度评估 | 内容、结构、语言、规范 |
| **数学题** | LaTeX 解析 + 步骤验证 | 步骤分、结果分 |
| **编程题** | 测试用例 + 代码质量分析 | 功能、质量、原创性 |

### 核心功能

- ✅ **客观题自动批改**：支持选择题、填空题、判断题
- ✅ **主观题智能评分**：基于语义相似度和关键词匹配
- ✅ **作文多维度评估**：内容、结构、语言、规范四维评分
- ✅ **数学解题验证**：步骤分 + 结果分的综合评分
- ✅ **编程题批改**：功能测试、代码质量、原创性检测
- ✅ **人机协同模式**：低置信度自动转人工复核
- ✅ **RESTful API**：完整的 API 接口服务

## 快速开始

### 安装依赖

```bash
# 安装核心依赖（最小化）
pip install fastapi uvicorn pydantic scikit-learn

# 安装完整依赖（包含 AI 模型）
pip install -r requirements.txt

# 或仅安装基础功能（无外部 AI 模型）
pip install fastapi uvicorn pydantic fuzzywuzzy python-Levenshtein
```

### 运行测试

```bash
# 运行单元测试
python -m unittest tests.test_grading -v

# 或使用 pytest
pytest tests/ -v --cov=src
```

### 启动 API 服务

```bash
# 开发模式
uvicorn src.api_service:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn src.api_service:app --host 0.0.0.0 --port 8000 --workers 4
```

### 使用示例

#### 1. 客观题批改

```python
from src.grading_engine import AIGradingEngine

engine = AIGradingEngine()

# 精确匹配
correct, similarity = engine.grade_objective("北京", "北京")
print(f"正确：{correct}, 相似度：{similarity}")

# 模糊匹配
correct, similarity = engine.grade_objective("北京", "北京市")
print(f"正确：{correct}, 相似度：{similarity}")
```

#### 2. 主观题批改

```python
result = engine.grade_subjective(
    student_ans="光合作用是植物利用阳光将二氧化碳和水转化为有机物的过程",
    std_ans="光合作用是绿色植物通过叶绿体，利用光能，把二氧化碳和水转化成储存能量的有机物，并且释放出氧气的过程",
    keywords=["光合作用", "植物", "阳光", "二氧化碳", "水", "有机物"]
)

print(f"得分：{result.score:.2f}")
print(f"反馈：{result.feedback}")
print(f"详情：{result.details}")
```

#### 3. 作文批改

```python
from src.grading_engine import EssayRubric

rubric = EssayRubric(prompt="我的家乡", max_score=100)
essay = """
我的家乡是一个美丽的地方。首先，这里有清澈的小河。
其次，四周环绕着青山。然后，村里的人们都很友善。
最后，这里的空气非常清新。我爱我的家乡。
"""

result = engine.grade_essay(essay, rubric)
print(f"得分：{result.score:.2f}/{rubric.max_score}")
print(f"反馈：{result.feedback}")
```

#### 4. 数学题批改

```python
from src.grading_engine import math_validation

result = math_validation(
    student_solution="x + 2 = 5\nx = 5 - 2\nx = 3",
    correct_solution="x + 2 = 5\nx = 5 - 2\nx = 3"
)

print(f"得分：{result['score']:.2f}")
print(f"步骤反馈：{result['step_feedback']}")
```

#### 5. 编程题批改

```python
from src.grading_engine import code_grading

result = code_grading(
    student_code="def add(a, b): return a + b",
    test_cases=[
        {"input": [1, 2], "expected": 3},
        {"input": [5, 7], "expected": 12}
    ],
    reference_code="def add(x, y): return x + y"
)

print(f"功能：{result['functional']*100:.0f}%")
print(f"质量：{result['quality']*100:.0f}%")
print(f"原创性：{result['originality']*100:.0f}%")
```

### API 调用示例

```bash
# 客观题批改
curl -X POST "http://localhost:8000/grade/objective" \
  -H "Content-Type: application/json" \
  -d '{"student_answer": "北京", "standard_answer": "北京市", "tolerance": 0.9}'

# 主观题批改
curl -X POST "http://localhost:8000/grade/subjective" \
  -H "Content-Type: application/json" \
  -d '{
    "student_answer": "光合作用是植物利用阳光制造有机物",
    "standard_answer": "光合作用是植物通过光能合成有机物",
    "keywords": ["光合作用", "植物", "阳光", "有机物"]
  }'

# 作文批改
curl -X POST "http://localhost:8000/grade/essay" \
  -H "Content-Type: application/json" \
  -d '{
    "essay": "我的家乡是一个美丽的地方...",
    "prompt": "我的家乡",
    "max_score": 100
  }'
```

## 项目结构

```
Automatic-Homework-Grading-Project/
├── README.md              # 项目说明文档
├── requirements.txt       # Python 依赖
├── config/
│   └── settings.env      # 配置文件
├── src/
│   ├── __init__.py       # 包初始化
│   ├── grading_engine.py # 核心批改引擎
│   └── api_service.py    # API 服务
├── tests/
│   ├── __init__.py       # 测试包初始化
│   └── test_grading.py   # 单元测试
└── models/               # 模型文件目录（可选）
```

## 技术栈

### AI 开发
- **NLP 基础**: HuggingFace Transformers, spaCy
- **相似度计算**: Sentence-Transformers, FAISS
- **OCR 识别**: PaddleOCR, Tesseract, LaTeX-OCR
- **代码分析**: Tree-sitter, CodeBERT

### 后端开发
- **API 框架**: FastAPI（高性能）
- **异步处理**: Celery + Redis/RabbitMQ
- **数据库**: PostgreSQL（主库）, MongoDB（作业内容）
- **缓存**: Redis Cluster

### 基础设施
- **部署**: Docker + Kubernetes
- **监控**: Prometheus + Grafana + ELK
- **安全**: JWT 认证、数据加密、访问控制

## 实施路线图

### 第一阶段：MVP 验证（2-3 个月）
- ✅ 核心批改引擎实现
- ✅ 客观题、主观题支持
- ✅ 基础 API 服务
- 📋 教师复核界面

### 第二阶段：功能扩展（4-6 个月）
- 🔄 支持简答题和数学题
- 🔄 BERT 语义相似度
- 🔄 公式识别
- 🔄 基础学情看板

### 第三阶段：体验优化（7-9 个月）
- ⏳ 作文批改
- ⏳ 编程题支持
- ⏳ 个性化反馈
- ⏳ 智能推荐练习

### 第四阶段：规模推广（10-12 个月）
- ⏳ 性能优化
- ⏳ 多租户支持
- ⏳ 移动端适配
- ⏳ 多语言支持

## 关键挑战与解决方案

### 1. 主观题评分一致性
**问题**: AI 评分与教师存在偏差

**解决方案**:
- 混合批改模式：低置信度自动转人工
- 与历史教师评分对比，差异过大时触发复核
- 持续学习教师标注数据

### 2. 手写识别准确率
**问题**: 学生字迹潦草，拍照质量差

**解决策略**:
- 多 OCR 引擎融合投票
- 交互式纠错：无法识别区域高亮
- 上下文纠错：结合题目语义

### 3. 创造性答案识别
**问题**: 新颖但正确的解题思路被误判

**解决方案**:
- 构建可解释 AI(XAI) 模块
- 建立优秀新颖答案库
- 引入知识图谱验证概念关联
- 设置教师快速仲裁通道

## 质量保障

### 技术指标
| 指标 | 目标值 | 测量方法 |
|------|--------|----------|
| **批改准确率** | 客观题>99%，主观题>85% | 与专家评分对比 |
| **响应时间** | <3 秒/题 | P99 延迟监控 |
| **系统可用性** | >99.5% | 在线时长统计 |
| **并发能力** | 1000+ QPS | 压力测试 |

### 业务指标
- **教师效率提升**: 批改时间减少 70%+
- **学生满意度**: NPS>50
- **教师采纳率**: 月活>80%
- **错误率**: 误判率<5%

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 项目主页：[GitHub](https://github.com/johnsoncom123/Automatic-Homework-Grading-Project.)
- 问题反馈：[Issues](https://github.com/johnsoncom123/Automatic-Homework-Grading-Project./issues)

---

**总结**: AI 自动批改作业项目技术可行、市场刚需，关键是采用"人机协同"策略，让 AI 学习教师经验，同时保留教师最终裁决权。建议从简单客观题切入，快速验证产品市场匹配度，再逐步扩展到复杂主观题，最终实现规模化应用。
