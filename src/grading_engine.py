"""
AI Automatic Homework Grading Engine
AI 自动批改作业引擎核心模块
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    from transformers import BertForSequenceClassification
    from sklearn.metrics.pairwise import cosine_similarity
    from fuzzywuzzy import fuzz
except ImportError:
    # Mock classes for when dependencies are not installed
    SentenceTransformer = None
    BertForSequenceClassification = None
    cosine_similarity = None
    fuzz = None


@dataclass
class GradingResult:
    """批改结果数据类"""
    score: float
    confidence: float
    feedback: str
    details: Dict


@dataclass
class EssayRubric:
    """作文评分标准"""
    prompt: str
    max_score: float = 100.0
    content_weight: float = 0.4
    structure_weight: float = 0.3
    language_weight: float = 0.2
    convention_weight: float = 0.1


class AIGradingEngine:
    """
    AI 智能批改引擎
    支持客观题、主观题、作文等多种题型的自动批改
    """
    
    def __init__(self, model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2'):
        """
        初始化批改引擎
        
        Args:
            model_name: 语义相似度模型名称
        """
        self.nlp_model = None
        self.essay_model = None
        self._initialized = False
        
        # 延迟加载模型
        self.model_name = model_name
    
    def load_models(self):
        """加载预训练模型"""
        if self._initialized:
            return
            
        if SentenceTransformer is not None:
            self.nlp_model = SentenceTransformer(self.model_name)
        
        if BertForSequenceClassification is not None:
            self.essay_model = BertForSequenceClassification.from_pretrained(
                'hfl/chinese-bert-wwm', 
                num_labels=5
            )
        
        self._initialized = True
    
    def grade_objective(
        self, 
        student_ans: str, 
        std_ans: str, 
        tolerance: float = 0.9
    ) -> Tuple[bool, float]:
        """
        客观题批改：支持模糊匹配
        
        Args:
            student_ans: 学生答案
            std_ans: 标准答案
            tolerance: 容错阈值 (0-1)
            
        Returns:
            (是否正确，相似度分数)
        """
        if fuzz is None:
            # Fallback to simple string comparison
            student_clean = student_ans.lower().strip()
            std_clean = std_ans.lower().strip()
            similarity = 1.0 if student_clean == std_clean else 0.0
            return similarity >= tolerance, similarity
        
        similarity = fuzz.ratio(
            student_ans.lower().strip(), 
            std_ans.lower()
        ) / 100
        return similarity >= tolerance, similarity
    
    def grade_subjective(
        self, 
        student_ans: str, 
        std_ans: str, 
        keywords: List[str]
    ) -> GradingResult:
        """
        主观题批改：语义相似度 + 关键词覆盖
        
        Args:
            student_ans: 学生答案
            std_ans: 标准答案
            keywords: 关键词列表
            
        Returns:
            GradingResult: 批改结果
        """
        # 语义相似度
        if self.nlp_model is not None and cosine_similarity is not None:
            emb1 = self.nlp_model.encode(student_ans)
            emb2 = self.nlp_model.encode(std_ans)
            similarity = cosine_similarity([emb1], [emb2])[0][0]
        else:
            # Fallback: simple keyword-based similarity
            student_words = set(student_ans.lower().split())
            std_words = set(std_ans.lower().split())
            similarity = len(student_words & std_words) / max(len(std_words), 1)
        
        # 关键词匹配
        keyword_score = sum(
            1 for kw in keywords if kw.lower() in student_ans.lower()
        ) / len(keywords) if keywords else 0.0
        
        # 综合评分 (语义 60% + 关键词 40%)
        final_score = 0.6 * similarity + 0.4 * keyword_score
        final_score = min(1.0, final_score)
        
        # 生成反馈
        feedback = self._generate_subjective_feedback(
            final_score, 
            similarity, 
            keyword_score,
            keywords,
            student_ans
        )
        
        return GradingResult(
            score=final_score,
            confidence=0.85,
            feedback=feedback,
            details={
                'semantic_similarity': similarity,
                'keyword_coverage': keyword_score,
                'matched_keywords': [kw for kw in keywords if kw.lower() in student_ans.lower()]
            }
        )
    
    def _generate_subjective_feedback(
        self, 
        score: float, 
        semantic_sim: float, 
        keyword_cov: float,
        keywords: List[str],
        student_ans: str
    ) -> str:
        """生成主观题反馈"""
        feedback_parts = []
        
        if score >= 0.9:
            feedback_parts.append("回答非常优秀！")
        elif score >= 0.7:
            feedback_parts.append("回答良好，基本掌握了知识点。")
        elif score >= 0.5:
            feedback_parts.append("回答一般，需要加强对知识点的理解。")
        else:
            feedback_parts.append("回答有待改进，建议重新学习相关内容。")
        
        # 关键词反馈
        matched = [kw for kw in keywords if kw.lower() in student_ans.lower()]
        missed = [kw for kw in keywords if kw.lower() not in student_ans.lower()]
        
        if missed:
            feedback_parts.append(f"建议补充以下关键点：{', '.join(missed[:3])}")
        
        return " ".join(feedback_parts)
    
    def grade_essay(
        self, 
        essay: str, 
        rubric: EssayRubric
    ) -> GradingResult:
        """
        作文多维度评分
        
        Args:
            essay: 学生作文
            rubric: 评分标准
            
        Returns:
            GradingResult: 包含各维度得分的批改结果
        """
        scores = {
            'content': self._content_relevance(essay, rubric.prompt),
            'structure': self._structure_coherence(essay),
            'language': self._language_quality(essay),
            'convention': self._mechanics_check(essay)
        }
        
        # 加权计算
        weights = {
            'content': rubric.content_weight,
            'structure': rubric.structure_weight,
            'language': rubric.language_weight,
            'convention': rubric.convention_weight
        }
        
        final_score = sum(scores[k] * weights[k] for k in scores)
        final_score = min(1.0, final_score)
        
        # 转换为百分制
        percentage_score = final_score * rubric.max_score
        
        feedback = self._generate_essay_feedback(scores, rubric.max_score)
        
        return GradingResult(
            score=percentage_score,
            confidence=0.75,
            feedback=feedback,
            details=scores
        )
    
    def _content_relevance(self, essay: str, prompt: str) -> float:
        """评估内容相关性"""
        if self.nlp_model is not None and cosine_similarity is not None:
            emb1 = self.nlp_model.encode(essay)
            emb2 = self.nlp_model.encode(prompt)
            return cosine_similarity([emb1], [emb2])[0][0]
        else:
            # Simple fallback
            return 0.5
    
    def _structure_coherence(self, essay: str) -> float:
        """评估结构连贯性"""
        # 检查段落数量
        paragraphs = [p.strip() for p in essay.split('\n\n') if p.strip()]
        paragraph_count = len(paragraphs)
        
        # 检查连接词
        connectors = ['首先', '其次', '然后', '最后', '因此', '然而', '但是', '另外']
        connector_count = sum(1 for c in connectors if c in essay)
        
        # 简单评分逻辑
        structure_score = min(1.0, (paragraph_count / 3) * 0.5 + (connector_count / 5) * 0.5)
        return structure_score
    
    def _language_quality(self, essay: str) -> float:
        """评估语言质量"""
        # 词汇丰富度
        words = essay.split()
        unique_words = set(words)
        lexical_diversity = len(unique_words) / len(words) if words else 0
        
        # 句子长度变化
        sentences = [s.strip() for s in essay.replace('。', '\n').replace('!', '\n').replace('?', '\n').split('\n') if s.strip()]
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        
        # 理想句长 15-25 字
        length_score = 1.0 if 15 <= avg_sentence_length <= 25 else max(0.5, 1 - abs(avg_sentence_length - 20) / 20)
        
        return min(1.0, (lexical_diversity + length_score) / 2)
    
    def _mechanics_check(self, essay: str) -> float:
        """检查书写规范（标点、格式等）"""
        # 检查标点符号使用
        punctuation = '.,!?;:,.!?:;'
        punct_count = sum(1 for c in essay if c in punctuation)
        
        # 检查是否有明显的格式问题
        has_proper_spacing = ' ' in essay or '\n' in essay
        
        mechanics_score = min(1.0, punct_count / 10 * 0.7 + (0.3 if has_proper_spacing else 0))
        return mechanics_score
    
    def _generate_essay_feedback(self, scores: Dict, max_score: float) -> str:
        """生成作文反馈"""
        feedback_parts = []
        
        total = sum(scores.values())
        percentage = total / 4 * 100
        
        if percentage >= 85:
            feedback_parts.append("这是一篇优秀的作文！")
        elif percentage >= 70:
            feedback_parts.append("作文整体不错，有提升空间。")
        elif percentage >= 60:
            feedback_parts.append("作文基本符合要求，但需要改进。")
        else:
            feedback_parts.append("作文需要认真修改和提高。")
        
        # 各维度具体反馈
        if scores['content'] < 0.6:
            feedback_parts.append("内容方面：建议更紧扣主题，充实论据。")
        if scores['structure'] < 0.6:
            feedback_parts.append("结构方面：注意段落划分和逻辑连接。")
        if scores['language'] < 0.6:
            feedback_parts.append("语言方面：丰富词汇，优化句式。")
        if scores['convention'] < 0.6:
            feedback_parts.append("规范方面：注意标点符号和格式。")
        
        return " ".join(feedback_parts)


def math_validation(
    student_solution: str, 
    correct_solution: str
) -> Dict:
    """
    数学解题验证：步骤分 + 结果分
    
    Args:
        student_solution: 学生解答（LaTeX 格式）
        correct_solution: 正确答案（LaTeX 格式）
        
    Returns:
        Dict: 包含分数和步骤反馈的结果
    """
    # 简化实现：实际应使用 LaTeX 解析器
    student_steps = [s.strip() for s in student_solution.split('\n') if s.strip()]
    correct_steps = [s.strip() for s in correct_solution.split('\n') if s.strip()]
    
    # 步骤验证
    step_scores = []
    for i, step in enumerate(student_steps):
        if i >= len(correct_steps):
            break
        # 简化：直接字符串比较（实际应检查公式等价性）
        is_equivalent = step == correct_steps[i]
        step_scores.append(1.0 if is_equivalent else 0.5)
    
    # 最终答案验证（假设最后一行是答案）
    result_score = 1.0 if student_steps[-1] == correct_steps[-1] else 0.0
    
    # 综合评分（步骤 70% + 结果 30%）
    if step_scores:
        final_score = 0.7 * (sum(step_scores) / len(step_scores)) + 0.3 * result_score
    else:
        final_score = 0.0
    
    # 生成步骤反馈
    step_feedback = []
    for i, score in enumerate(step_scores):
        if score < 1.0:
            step_feedback.append(f"步骤{i+1}: 需要改进")
        else:
            step_feedback.append(f"步骤{i+1}: 正确")
    
    return {
        'score': final_score,
        'step_feedback': step_feedback,
        'result_correct': result_score == 1.0
    }


def code_grading(
    student_code: str, 
    test_cases: List[Dict],
    reference_code: Optional[str] = None
) -> Dict:
    """
    编程题批改：功能 + 质量 + 原创性
    
    Args:
        student_code: 学生代码
        test_cases: 测试用例列表
        reference_code: 参考代码（用于原创性检测）
        
    Returns:
        Dict: 包含各项评分的结果
    """
    results = {
        'functional': 0.0,
        'quality': 0.0,
        'originality': 1.0
    }
    
    # 1. 功能测试（模拟）
    passed_tests = 0
    for test in test_cases:
        # 实际应执行测试用例
        # 这里简化为随机通过
        passed_tests += 1
    results['functional'] = passed_tests / len(test_cases) if test_cases else 0.0
    
    # 2. 代码质量分析
    results['quality'] = code_quality_analysis(student_code)
    
    # 3. 原创性检测
    if reference_code:
        results['originality'] = 1.0 - similarity_check(student_code, reference_code)
    
    return results


def code_quality_analysis(code: str) -> float:
    """
    代码质量分析
    
    评估维度：
    - 命名规范
    - 注释完整性
    - 代码简洁度
    - 结构清晰度
    """
    score = 0.5  # 基础分
    
    # 检查命名（驼峰或下划线）
    import re
    if re.search(r'[a-z]+_[a-z]+', code) or re.search(r'[a-z]+[A-Z][a-z]+', code):
        score += 0.1
    
    # 检查注释
    if '#' in code or '//' in code or '/*' in code:
        score += 0.15
    
    # 检查函数定义
    if 'def ' in code or 'function ' in code:
        score += 0.15
    
    # 检查空行（代码结构）
    if '\n\n' in code:
        score += 0.1
    
    return min(1.0, score)


def similarity_check(code1: str, code2: str) -> float:
    """
    代码相似度检测（简化版）
    
    实际应使用 AST 分析或专业工具如 MOSS
    """
    # 移除空白和注释
    clean1 = ''.join(code1.split())
    clean2 = ''.join(code2.split())
    
    if clean1 == clean2:
        return 1.0
    
    # 简单字符级相似度
    common = sum(1 for c in clean1 if c in clean2)
    return common / max(len(clean1), len(clean2))


# 混合批改模式（人机协同）
def hybrid_grading(
    student_answer: str, 
    standard_answer: str,
    ai_model: AIGradingEngine,
    teacher_historical_avg: float = 0.75
) -> GradingResult:
    """
    混合批改模式：AI 初评 + 人工复核
    
    Args:
        student_answer: 学生答案
        standard_answer: 标准答案
        ai_model: AI 批改引擎
        teacher_historical_avg: 教师历史平均分
        
    Returns:
        GradingResult: 最终批改结果
    """
    ai_score = ai_model.grade_subjective(student_answer, standard_answer, [])
    
    # 低置信度自动转人工
    if ai_score.confidence < 0.7:
        ai_score.feedback += " [已标记人工复核]"
        return ai_score
    
    # 与历史教师评分差异过大时复核
    if abs(ai_score.score - teacher_historical_avg) > 0.2:
        ai_score.feedback += " [评分差异较大，建议复核]"
        return ai_score
    
    return ai_score


if __name__ == "__main__":
    # 示例用法
    engine = AIGradingEngine()
    
    # 客观题测试
    correct, similarity = engine.grade_objective("北京", "北京市")
    print(f"客观题批改：正确={correct}, 相似度={similarity:.2f}")
    
    # 主观题测试
    result = engine.grade_subjective(
        "光合作用是植物利用阳光将二氧化碳和水转化为有机物的过程",
        "光合作用是绿色植物通过叶绿体，利用光能，把二氧化碳和水转化成储存能量的有机物，并且释放出氧气的过程",
        ["光合作用", "植物", "阳光", "二氧化碳", "水", "有机物"]
    )
    print(f"\n主观题批改:")
    print(f"得分：{result.score:.2f}")
    print(f"反馈：{result.feedback}")
    print(f"详情：{result.details}")
    
    # 作文测试
    rubric = EssayRubric(prompt="我的家乡")
    essay = """
    我的家乡是一个美丽的地方。首先，这里有清澈的小河。其次，四周环绕着青山。
    然后，村里的人们都很友善。最后，这里的空气非常清新。
    我爱我的家乡，希望它越来越美好。
    """
    result = engine.grade_essay(essay, rubric)
    print(f"\n作文批改:")
    print(f"得分：{result.score:.2f}/{rubric.max_score}")
    print(f"反馈：{result.feedback}")
