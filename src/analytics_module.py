"""
Learning Analytics Module
学情分析模块

提供学生学情分析、知识点掌握度评估、个性化推荐等功能
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import json


@dataclass
class KnowledgePoint:
    """知识点数据类"""
    id: str
    name: str
    subject: str
    grade_level: int
    mastery_score: float = 0.0  # 掌握度 0-1
    last_practiced: Optional[datetime] = None
    error_count: int = 0
    total_attempts: int = 0


@dataclass
class StudentProfile:
    """学生画像数据类"""
    student_id: str
    name: str
    grade: int
    knowledge_points: Dict[str, KnowledgePoint] = field(default_factory=dict)
    average_score: float = 0.0
    learning_trend: List[float] = field(default_factory=list)
    weak_areas: List[str] = field(default_factory=list)
    strong_areas: List[str] = field(default_factory=list)


@dataclass
class ClassAnalytics:
    """班级学情分析数据类"""
    class_id: str
    subject: str
    total_students: int
    average_score: float
    score_distribution: Dict[str, int]
    knowledge_mastery: Dict[str, float]
    common_errors: List[Dict]


class LearningAnalyticsEngine:
    """
    学情分析引擎
    
    功能：
    - 学生个人学情分析
    - 班级整体学情统计
    - 知识点掌握度评估
    - 学习趋势分析
    - 个性化练习推荐
    """
    
    def __init__(self):
        """初始化分析引擎"""
        self.student_profiles: Dict[str, StudentProfile] = {}
        self.class_analytics: Dict[str, ClassAnalytics] = {}
        self.knowledge_graph: Dict[str, List[str]] = {}  # 知识点依赖关系
        
        # 初始化知识图谱（简化版）
        self._init_knowledge_graph()
    
    def _init_knowledge_graph(self):
        """初始化知识点图谱"""
        # 数学知识点依赖关系示例
        self.knowledge_graph = {
            'algebra_basic': ['arithmetic', 'equation_solving'],
            'equation_solving': ['linear_equation', 'quadratic_equation'],
            'linear_equation': ['system_of_equations'],
            'quadratic_equation': ['function_concept'],
            'geometry_basic': ['point_line_plane', 'triangle'],
            'triangle': ['pythagorean_theorem', 'similar_triangle'],
            'function_concept': ['linear_function', 'quadratic_function'],
        }
    
    def create_student_profile(
        self,
        student_id: str,
        name: str,
        grade: int
    ) -> StudentProfile:
        """
        创建学生画像
        
        Args:
            student_id: 学生 ID
            name: 姓名
            grade: 年级
            
        Returns:
            StudentProfile: 学生画像
        """
        profile = StudentProfile(
            student_id=student_id,
            name=name,
            grade=grade
        )
        self.student_profiles[student_id] = profile
        return profile
    
    def update_knowledge_mastery(
        self,
        student_id: str,
        knowledge_point_id: str,
        score: float,
        is_correct: bool
    ):
        """
        更新知识点掌握度
        
        Args:
            student_id: 学生 ID
            knowledge_point_id: 知识点 ID
            score: 本次得分
            is_correct: 是否正确
        """
        if student_id not in self.student_profiles:
            raise ValueError(f"学生 {student_id} 不存在")
        
        profile = self.student_profiles[student_id]
        
        # 创建或更新知识点
        if knowledge_point_id not in profile.knowledge_points:
            kp = KnowledgePoint(
                id=knowledge_point_id,
                name=knowledge_point_id,
                subject='math',
                grade_level=profile.grade
            )
            profile.knowledge_points[knowledge_point_id] = kp
        else:
            kp = profile.knowledge_points[knowledge_point_id]
        
        # 更新统计数据
        kp.total_attempts += 1
        if not is_correct:
            kp.error_count += 1
        
        # 指数移动平均更新掌握度
        alpha = 0.3  # 平滑系数
        kp.mastery_score = alpha * score + (1 - alpha) * kp.mastery_score
        kp.last_practiced = datetime.now()
        
        # 更新强弱项
        self._update_strength_weakness(profile)
    
    def _update_strength_weakness(self, profile: StudentProfile):
        """更新学生的强弱项"""
        weak_areas = []
        strong_areas = []
        
        for kp_id, kp in profile.knowledge_points.items():
            if kp.total_attempts >= 3:  # 至少练习 3 次
                if kp.mastery_score < 0.6:
                    weak_areas.append(kp_id)
                elif kp.mastery_score > 0.85:
                    strong_areas.append(kp_id)
        
        profile.weak_areas = weak_areas
        profile.strong_areas = strong_areas
    
    def analyze_class_performance(
        self,
        class_id: str,
        subject: str,
        student_scores: List[float]
    ) -> ClassAnalytics:
        """
        分析班级整体表现
        
        Args:
            class_id: 班级 ID
            subject: 科目
            student_scores: 学生分数列表
            
        Returns:
            ClassAnalytics: 班级分析结果
        """
        total = len(student_scores)
        avg_score = sum(student_scores) / total if total > 0 else 0
        
        # 分数分布
        distribution = {
            'excellent': 0,  # 90-100
            'good': 0,       # 75-89
            'average': 0,    # 60-74
            'poor': 0        # 0-59
        }
        
        for score in student_scores:
            if score >= 90:
                distribution['excellent'] += 1
            elif score >= 75:
                distribution['good'] += 1
            elif score >= 60:
                distribution['average'] += 1
            else:
                distribution['poor'] += 1
        
        analytics = ClassAnalytics(
            class_id=class_id,
            subject=subject,
            total_students=total,
            average_score=avg_score,
            score_distribution=distribution,
            knowledge_mastery={},
            common_errors=[]
        )
        
        self.class_analytics[class_id] = analytics
        return analytics
    
    def generate_learning_report(
        self,
        student_id: str,
        include_recommendations: bool = True
    ) -> Dict:
        """
        生成学生学习报告
        
        Args:
            student_id: 学生 ID
            include_recommendations: 是否包含推荐
            
        Returns:
            Dict: 学习报告
        """
        if student_id not in self.student_profiles:
            raise ValueError(f"学生 {student_id} 不存在")
        
        profile = self.student_profiles[student_id]
        
        report = {
            'student_info': {
                'id': profile.student_id,
                'name': profile.name,
                'grade': profile.grade
            },
            'overall_performance': {
                'average_score': profile.average_score,
                'total_knowledge_points': len(profile.knowledge_points),
                'mastered_count': len(profile.strong_areas),
                'needs_improvement_count': len(profile.weak_areas)
            },
            'knowledge_analysis': {
                'strong_areas': [
                    {
                        'id': kp_id,
                        'mastery': profile.knowledge_points[kp_id].mastery_score
                    }
                    for kp_id in profile.strong_areas
                ],
                'weak_areas': [
                    {
                        'id': kp_id,
                        'mastery': profile.knowledge_points[kp_id].mastery_score,
                        'error_rate': (
                            profile.knowledge_points[kp_id].error_count /
                            profile.knowledge_points[kp_id].total_attempts
                        ) if profile.knowledge_points[kp_id].total_attempts > 0 else 0
                    }
                    for kp_id in profile.weak_areas
                ]
            },
            'learning_trend': profile.learning_trend[-10:]  # 最近 10 次
        }
        
        if include_recommendations:
            report['recommendations'] = self._generate_recommendations(profile)
        
        return report
    
    def _generate_recommendations(self, profile: StudentProfile) -> List[Dict]:
        """生成个性化学习建议"""
        recommendations = []
        
        # 基于弱项推荐
        for weak_area in profile.weak_areas[:3]:  # 最多推荐 3 个
            kp = profile.knowledge_points[weak_area]
            
            # 找到前置知识点
            prerequisites = self._get_prerequisites(weak_area)
            
            recommendations.append({
                'type': 'practice',
                'knowledge_point': weak_area,
                'priority': 'high',
                'reason': f'掌握度仅为{kp.mastery_score*100:.0f}%',
                'suggested_exercises': 10,
                'prerequisites': prerequisites
            })
        
        # 基于强项推荐拓展
        for strong_area in profile.strong_areas[:2]:  # 最多推荐 2 个
            # 找到后续知识点
            next_topics = self._get_next_topics(strong_area)
            
            if next_topics:
                recommendations.append({
                    'type': 'advance',
                    'knowledge_point': strong_area,
                    'priority': 'medium',
                    'reason': f'已掌握良好，可以学习进阶内容',
                    'next_topics': next_topics
                })
        
        return recommendations
    
    def _get_prerequisites(self, knowledge_point_id: str) -> List[str]:
        """获取前置知识点"""
        prerequisites = []
        for kp, deps in self.knowledge_graph.items():
            if knowledge_point_id in deps:
                prerequisites.append(kp)
        return prerequisites
    
    def _get_next_topics(self, knowledge_point_id: str) -> List[str]:
        """获取后续知识点"""
        return self.knowledge_graph.get(knowledge_point_id, [])
    
    def calculate_similarity_between_students(
        self,
        student_id1: str,
        student_id2: str
    ) -> float:
        """
        计算两个学生的学习相似度
        
        Args:
            student_id1: 学生 1 ID
            student_id2: 学生 2 ID
            
        Returns:
            float: 相似度 0-1
        """
        if student_id1 not in self.student_profiles or \
           student_id2 not in self.student_profiles:
            return 0.0
        
        profile1 = self.student_profiles[student_id1]
        profile2 = self.student_profiles[student_id2]
        
        # 共同的知识点
        common_kps = set(profile1.knowledge_points.keys()) & \
                     set(profile2.knowledge_points.keys())
        
        if not common_kps:
            return 0.0
        
        # 计算掌握度相似性
        similarity_sum = 0
        for kp_id in common_kps:
            mastery1 = profile1.knowledge_points[kp_id].mastery_score
            mastery2 = profile2.knowledge_points[kp_id].mastery_score
            similarity_sum += 1 - abs(mastery1 - mastery2)
        
        return similarity_sum / len(common_kps)
    
    def export_analytics_json(
        self,
        student_id: str,
        file_path: str
    ):
        """
        导出学情分析为 JSON
        
        Args:
            student_id: 学生 ID
            file_path: 文件路径
        """
        report = self.generate_learning_report(student_id)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"✓ 学情报告已导出到：{file_path}")


def generate_class_report_card(
    analytics: ClassAnalytics,
    school_name: str = "示例学校"
) -> str:
    """
    生成班级成绩单
    
    Args:
        analytics: 班级分析数据
        school_name: 学校名称
        
    Returns:
        str: 格式化的成绩单文本
    """
    report = f"""
{'='*60}
{school_name} - 班级学情分析报告
{'='*60}

班级信息:
  班级 ID: {analytics.class_id}
  科目：{analytics.subject}
  学生人数：{analytics.total_students}

成绩概况:
  平均分：{analytics.average_score:.1f}

分数分布:
  优秀 (90-100): {analytics.score_distribution['excellent']} 人
  良好 (75-89):  {analytics.score_distribution['good']} 人
  及格 (60-74):  {analytics.score_distribution['average']} 人
  待提高 (<60):  {analytics.score_distribution['poor']} 人

{'='*60}
生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*60}
"""
    return report


if __name__ == "__main__":
    # 示例用法
    print("=" * 60)
    print("学情分析模块演示")
    print("=" * 60)
    
    # 创建分析引擎
    engine = LearningAnalyticsEngine()
    
    # 创建学生画像
    student1 = engine.create_student_profile("S001", "张三", 9)
    student2 = engine.create_student_profile("S002", "李四", 9)
    
    # 模拟更新知识点掌握度
    print("\n更新知识点掌握度...")
    for i in range(5):
        engine.update_knowledge_mastery("S001", "linear_equation", 0.7 + i*0.05, i >= 2)
        engine.update_knowledge_mastery("S001", "quadratic_equation", 0.5 + i*0.08, i >= 3)
        engine.update_knowledge_mastery("S002", "linear_equation", 0.8 + i*0.03, True)
        engine.update_knowledge_mastery("S002", "triangle", 0.6 + i*0.06, i >= 1)
    
    # 生成学习报告
    print("\n生成学生学习报告...")
    report = engine.generate_learning_report("S001")
    
    print(f"\n学生：{report['student_info']['name']}")
    print(f"年级：{report['student_info']['grade']}")
    print(f"强势领域：{len(report['knowledge_analysis']['strong_areas'])} 个")
    print(f"薄弱领域：{len(report['knowledge_analysis']['weak_areas'])} 个")
    
    if report.get('recommendations'):
        print(f"\n个性化推荐 ({len(report['recommendations'])} 条):")
        for rec in report['recommendations']:
            print(f"  - [{rec['priority']}] {rec['type']}: {rec['knowledge_point']}")
            print(f"    原因：{rec['reason']}")
    
    # 班级分析
    print("\n\n班级整体分析...")
    scores = [85, 92, 78, 65, 88, 95, 72, 81, 69, 90]
    class_analytics = engine.analyze_class_performance("C001", "math", scores)
    
    report_card = generate_class_report_card(class_analytics)
    print(report_card)
    
    # 学生相似度
    similarity = engine.calculate_similarity_between_students("S001", "S002")
    print(f"\n学生相似度：{similarity:.2f}")
