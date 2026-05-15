"""
AI Automatic Homework Grading API Service
AI 自动批改作业 API 服务
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uvicorn
import uuid
from datetime import datetime

from src.grading_engine import (
    AIGradingEngine, 
    GradingResult, 
    EssayRubric,
    math_validation,
    code_grading,
    hybrid_grading
)

# 创建 FastAPI 应用
app = FastAPI(
    title="AI Automatic Homework Grading API",
    description="AI 自动批改作业系统 API 接口",
    version="1.0.0"
)

# 全局批改引擎实例
grading_engine = AIGradingEngine()


# ==================== 数据模型 ====================

class ObjectiveQuestion(BaseModel):
    """客观题请求模型"""
    student_answer: str = Field(..., description="学生答案")
    standard_answer: str = Field(..., description="标准答案")
    tolerance: float = Field(default=0.9, ge=0, le=1, description="容错阈值")


class SubjectiveQuestion(BaseModel):
    """主观题请求模型"""
    student_answer: str = Field(..., description="学生答案")
    standard_answer: str = Field(..., description="标准答案")
    keywords: List[str] = Field(..., description="关键词列表")


class EssayRequest(BaseModel):
    """作文请求模型"""
    essay: str = Field(..., description="学生作文内容")
    prompt: str = Field(..., description="作文题目")
    max_score: float = Field(default=100.0, description="满分")


class MathProblem(BaseModel):
    """数学题请求模型"""
    student_solution: str = Field(..., description="学生解答（LaTeX 格式）")
    correct_solution: str = Field(..., description="正确答案（LaTeX 格式）")


class CodeSubmission(BaseModel):
    """编程题请求模型"""
    student_code: str = Field(..., description="学生代码")
    test_cases: List[Dict[str, Any]] = Field(..., description="测试用例")
    reference_code: Optional[str] = Field(None, description="参考代码")


class HybridGradingRequest(BaseModel):
    """混合批改请求模型"""
    student_answer: str = Field(..., description="学生答案")
    standard_answer: str = Field(..., description="标准答案")
    teacher_historical_avg: float = Field(default=0.75, description="教师历史平均分")


class GradingResponse(BaseModel):
    """批改响应模型"""
    id: str
    timestamp: str
    score: float
    confidence: float
    feedback: str
    details: Dict[str, Any]
    status: str = "success"


# ==================== API 端点 ====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AI Automatic Homework Grading API",
        "version": "1.0.0",
        "endpoints": [
            "/grade/objective",
            "/grade/subjective",
            "/grade/essay",
            "/grade/math",
            "/grade/code",
            "/grade/hybrid"
        ]
    }


@app.post("/grade/objective", response_model=GradingResponse)
async def grade_objective(question: ObjectiveQuestion):
    """
    批改客观题
    
    支持选择题、填空题、判断题等客观题型的自动批改
    """
    try:
        correct, similarity = grading_engine.grade_objective(
            question.student_answer,
            question.standard_answer,
            question.tolerance
        )
        
        return GradingResponse(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            score=1.0 if correct else 0.0,
            confidence=similarity,
            feedback="回答正确" if correct else "回答错误",
            details={
                "correct": correct,
                "similarity": similarity,
                "tolerance": question.tolerance
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/grade/subjective", response_model=GradingResponse)
async def grade_subjective(question: SubjectiveQuestion):
    """
    批改主观题
    
    使用语义相似度 + 关键词匹配进行主观题批改
    """
    try:
        result = grading_engine.grade_subjective(
            question.student_answer,
            question.standard_answer,
            question.keywords
        )
        
        return GradingResponse(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            score=result.score,
            confidence=result.confidence,
            feedback=result.feedback,
            details=result.details
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/grade/essay", response_model=GradingResponse)
async def grade_essay(request: EssayRequest):
    """
    批改作文
    
    多维度评分：内容、结构、语言、规范
    """
    try:
        rubric = EssayRubric(
            prompt=request.prompt,
            max_score=request.max_score
        )
        
        result = grading_engine.grade_essay(request.essay, rubric)
        
        return GradingResponse(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            score=result.score,
            confidence=result.confidence,
            feedback=result.feedback,
            details=result.details
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/grade/math", response_model=GradingResponse)
async def grade_math(problem: MathProblem):
    """
    批改数学题
    
    步骤分 + 结果分的综合评分
    """
    try:
        result = math_validation(
            problem.student_solution,
            problem.correct_solution
        )
        
        return GradingResponse(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            score=result['score'],
            confidence=0.8,
            feedback="; ".join(result['step_feedback']),
            details={
                "step_feedback": result['step_feedback'],
                "result_correct": result['result_correct']
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/grade/code", response_model=GradingResponse)
async def grade_code(submission: CodeSubmission):
    """
    批改编程题
    
    功能测试 + 代码质量 + 原创性检测
    """
    try:
        result = code_grading(
            submission.student_code,
            submission.test_cases,
            submission.reference_code
        )
        
        # 计算综合得分
        total_score = (
            result['functional'] * 0.6 +
            result['quality'] * 0.25 +
            result['originality'] * 0.15
        )
        
        return GradingResponse(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            score=total_score,
            confidence=0.85,
            feedback=f"功能：{result['functional']*100:.0f}%, 质量：{result['quality']*100:.0f}%, 原创性：{result['originality']*100:.0f}%",
            details=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/grade/hybrid", response_model=GradingResponse)
async def grade_hybrid(request: HybridGradingRequest):
    """
    混合批改（人机协同）
    
    AI 初评 + 人工复核机制
    """
    try:
        result = hybrid_grading(
            request.student_answer,
            request.standard_answer,
            grading_engine,
            request.teacher_historical_avg
        )
        
        return GradingResponse(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            score=result.score,
            confidence=result.confidence,
            feedback=result.feedback,
            details={
                "requires_review": "人工复核" in result.feedback
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


# ==================== 主程序 ====================

if __name__ == "__main__":
    uvicorn.run(
        "src.api_service:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
