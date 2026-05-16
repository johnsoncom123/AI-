"""
Database Models and Storage Layer
数据库模型和存储层

支持 PostgreSQL、MongoDB、Redis 等多种数据存储
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import os


@dataclass
class Assignment:
    """作业数据模型"""
    id: str
    title: str
    subject: str
    grade_level: int
    teacher_id: str
    created_at: datetime
    due_date: datetime
    questions: List[Dict]
    total_score: float = 100.0


@dataclass
class Submission:
    """学生提交数据模型"""
    id: str
    assignment_id: str
    student_id: str
    submitted_at: datetime
    answers: Dict[str, str]
    auto_grade_result: Optional[Dict] = None
    teacher_review: Optional[Dict] = None
    final_score: Optional[float] = None
    status: str = "pending"  # pending, graded, reviewed


@dataclass
class Question:
    """题目数据模型"""
    id: str
    type: str  # objective, subjective, essay, math, code
    content: str
    standard_answer: str
    score: float
    keywords: Optional[List[str]] = None
    rubric: Optional[Dict] = None
    test_cases: Optional[List[Dict]] = None


class DatabaseManager:
    """
    数据库管理器
    
    支持多种数据库后端：
    - PostgreSQL: 结构化数据存储
    - MongoDB: 作业内容和提交记录
    - Redis: 缓存和会话管理
    """
    
    def __init__(self, db_type: str = "sqlite"):
        """
        初始化数据库管理器
        
        Args:
            db_type: 数据库类型 (sqlite, postgresql, mongodb)
        """
        self.db_type = db_type
        self.connection = None
        self._initialized = False
        
        # 模拟数据库存储（用于演示）
        self._memory_db = {
            'assignments': {},
            'submissions': {},
            'questions': {},
            'students': {},
            'teachers': {}
        }
    
    def connect(self, connection_string: Optional[str] = None):
        """
        连接数据库
        
        Args:
            connection_string: 数据库连接字符串
        """
        if self.db_type == "postgresql":
            try:
                import psycopg2
                self.connection = psycopg2.connect(connection_string or os.getenv('DATABASE_URL'))
                print("✓ PostgreSQL 连接成功")
            except ImportError:
                print("⚠ psycopg2 未安装，使用内存数据库")
                self.connection = None
        elif self.db_type == "mongodb":
            try:
                from pymongo import MongoClient
                client = MongoClient(connection_string or os.getenv('MONGODB_URI', 'mongodb://localhost:27017'))
                self.connection = client['homework_grading']
                print("✓ MongoDB 连接成功")
            except ImportError:
                print("⚠ pymongo 未安装，使用内存数据库")
                self.connection = None
        else:
            print("ℹ 使用 SQLite/内存数据库")
        
        self._initialized = True
    
    def save_assignment(self, assignment: Assignment) -> bool:
        """保存作业"""
        if not self._initialized:
            self.connect()
        
        # 内存存储（演示用）
        self._memory_db['assignments'][assignment.id] = asdict(assignment)
        return True
    
    def get_assignment(self, assignment_id: str) -> Optional[Assignment]:
        """获取作业"""
        data = self._memory_db['assignments'].get(assignment_id)
        if data:
            return Assignment(**data)
        return None
    
    def save_submission(self, submission: Submission) -> bool:
        """保存学生提交"""
        if not self._initialized:
            self.connect()
        
        self._memory_db['submissions'][submission.id] = asdict(submission)
        return True
    
    def get_submission(self, submission_id: str) -> Optional[Submission]:
        """获取提交"""
        data = self._memory_db['submissions'].get(submission_id)
        if data:
            return Submission(**data)
        return None
    
    def update_submission_grade(
        self,
        submission_id: str,
        grade_result: Dict,
        final_score: float
    ) -> bool:
        """更新提交评分"""
        if submission_id not in self._memory_db['submissions']:
            return False
        
        submission_data = self._memory_db['submissions'][submission_id]
        submission_data['auto_grade_result'] = grade_result
        submission_data['final_score'] = final_score
        submission_data['status'] = 'graded'
        submission_data['submitted_at'] = str(datetime.now())
        
        return True
    
    def get_student_submissions(
        self,
        student_id: str,
        limit: int = 10
    ) -> List[Submission]:
        """获取学生提交历史"""
        submissions = [
            Submission(**s)
            for s in self._memory_db['submissions'].values()
            if s['student_id'] == student_id
        ]
        
        # 按提交时间排序
        submissions.sort(key=lambda x: x.submitted_at, reverse=True)
        return submissions[:limit]
    
    def get_class_submissions(
        self,
        assignment_id: str,
        class_id: str
    ) -> List[Submission]:
        """获取班级提交情况"""
        # 简化实现：实际应根据 class_id 过滤
        submissions = [
            Submission(**s)
            for s in self._memory_db['submissions'].values()
            if s['assignment_id'] == assignment_id
        ]
        return submissions
    
    def save_question(self, question: Question) -> bool:
        """保存题目到题库"""
        if not self._initialized:
            self.connect()
        
        self._memory_db['questions'][question.id] = asdict(question)
        return True
    
    def get_questions_by_type(
        self,
        question_type: str,
        subject: Optional[str] = None
    ) -> List[Question]:
        """按类型获取题目"""
        questions = []
        for q_data in self._memory_db['questions'].values():
            if q_data['type'] == question_type:
                if subject is None or q_data.get('subject') == subject:
                    questions.append(Question(**q_data))
        return questions
    
    def get_statistics(self) -> Dict:
        """获取数据库统计信息"""
        return {
            'total_assignments': len(self._memory_db['assignments']),
            'total_submissions': len(self._memory_db['submissions']),
            'total_questions': len(self._memory_db['questions']),
            'graded_submissions': sum(
                1 for s in self._memory_db['submissions'].values()
                if s.get('status') == 'graded'
            ),
            'pending_submissions': sum(
                1 for s in self._memory_db['submissions'].values()
                if s.get('status') == 'pending'
            )
        }
    
    def export_data(self, output_path: str, data_type: str = "all") -> bool:
        """
        导出数据
        
        Args:
            output_path: 输出文件路径
            data_type: 数据类型 (assignments, submissions, questions, all)
        """
        export_data = {}
        
        if data_type in ["assignments", "all"]:
            export_data['assignments'] = self._memory_db['assignments']
        
        if data_type in ["submissions", "all"]:
            export_data['submissions'] = self._memory_db['submissions']
        
        if data_type in ["questions", "all"]:
            export_data['questions'] = self._memory_db['questions']
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"✓ 数据已导出到：{output_path}")
        return True


class CacheManager:
    """
    缓存管理器（基于 Redis）
    
    功能：
    - 批改结果缓存
    - 会话管理
    - 热点数据缓存
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        """初始化缓存管理器"""
        self.redis_client = None
        self._use_memory_cache = True
        self._memory_cache: Dict[str, Any] = {}
        self._cache_ttl: Dict[str, datetime] = {}
        
        # 尝试连接 Redis
        try:
            import redis
            self.redis_client = redis.from_url(
                redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379')
            )
            self.redis_client.ping()
            self._use_memory_cache = False
            print("✓ Redis 连接成功")
        except Exception as e:
            print(f"⚠ Redis 不可用，使用内存缓存：{e}")
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if self._use_memory_cache:
            # 检查 TTL
            if key in self._cache_ttl:
                if datetime.now() > self._cache_ttl[key]:
                    del self._memory_cache[key]
                    del self._cache_ttl[key]
                    return None
            return self._memory_cache.get(key)
        else:
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """设置缓存"""
        if self._use_memory_cache:
            self._memory_cache[key] = value
            self._cache_ttl[key] = datetime.now() + timedelta(seconds=ttl_seconds)
            return True
        else:
            self.redis_client.setex(
                key,
                ttl_seconds,
                json.dumps(value, default=str)
            )
            return True
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        if self._use_memory_cache:
            if key in self._memory_cache:
                del self._memory_cache[key]
            if key in self._cache_ttl:
                del self._cache_ttl[key]
            return True
        else:
            return bool(self.redis_client.delete(key))
    
    def clear_pattern(self, pattern: str) -> int:
        """批量删除匹配模式的缓存"""
        count = 0
        if self._use_memory_cache:
            keys_to_delete = [k for k in self._memory_cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self._memory_cache[key]
                if key in self._cache_ttl:
                    del self._cache_ttl[key]
            count = len(keys_to_delete)
        else:
            keys = self.redis_client.keys(pattern)
            if keys:
                count = self.redis_client.delete(*keys)
        return count


# 导入 timedelta（之前忘记导入）
from datetime import timedelta


if __name__ == "__main__":
    # 示例用法
    print("=" * 60)
    print("数据库模块演示")
    print("=" * 60)
    
    # 创建数据库管理器
    db = DatabaseManager(db_type="sqlite")
    db.connect()
    
    # 创建作业
    assignment = Assignment(
        id="A001",
        title="初二数学 - 一次函数练习",
        subject="math",
        grade_level=8,
        teacher_id="T001",
        created_at=datetime.now(),
        due_date=datetime.now() + timedelta(days=7),
        questions=[
            {"id": "Q1", "type": "objective", "content": "1+1=?"},
            {"id": "Q2", "type": "subjective", "content": "解释什么是函数"}
        ],
        total_score=100.0
    )
    
    db.save_assignment(assignment)
    print(f"\n✓ 作业已保存：{assignment.title}")
    
    # 创建题目
    question = Question(
        id="Q001",
        type="subjective",
        content="请解释光合作用的过程",
        standard_answer="光合作用是植物利用阳光将二氧化碳和水转化为有机物",
        score=10.0,
        keywords=["光合作用", "阳光", "二氧化碳", "水", "有机物"]
    )
    
    db.save_question(question)
    print(f"✓ 题目已保存：{question.content[:20]}...")
    
    # 创建学生提交
    submission = Submission(
        id="SUB001",
        assignment_id="A001",
        student_id="S001",
        submitted_at=datetime.now(),
        answers={
            "Q1": "2",
            "Q2": "函数是一种映射关系"
        },
        status="pending"
    )
    
    db.save_submission(submission)
    print(f"✓ 提交已保存：学生 S001")
    
    # 更新评分
    db.update_submission_grade(
        "SUB001",
        {"accuracy": 0.9, "feedback": "很好"},
        90.0
    )
    print("✓ 评分已更新")
    
    # 获取统计
    stats = db.get_statistics()
    print(f"\n数据库统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 测试缓存
    print("\n\n测试缓存系统...")
    cache = CacheManager()
    
    cache.set("test_key", {"data": "test_value"}, ttl_seconds=60)
    result = cache.get("test_key")
    print(f"缓存读取：{result}")
    
    # 导出测试
    db.export_data("/workspace/test_export.json", data_type="all")
