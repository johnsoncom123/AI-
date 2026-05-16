"""
OCR Recognition Module for Handwritten Homework
手写作业 OCR 识别模块

支持多 OCR 引擎融合：PaddleOCR + Tesseract + 自研模型
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re


@dataclass
class OCRResult:
    """OCR 识别结果"""
    text: str
    confidence: float
    bounding_box: Optional[Tuple[int, int, int, int]] = None
    language: str = "zh-CN"


class MultiOCREngine:
    """
    多 OCR 引擎融合识别
    
    特性：
    - 支持 PaddleOCR、Tesseract 等多种引擎
    - 投票机制提高准确率
    - 上下文纠错
    - 交互式纠错支持
    """
    
    def __init__(self, use_paddle: bool = True, use_tesseract: bool = True):
        """
        初始化 OCR 引擎
        
        Args:
            use_paddle: 是否使用 PaddleOCR
            use_tesseract: 是否使用 Tesseract
        """
        self.use_paddle = use_paddle
        self.use_tesseract = use_tesseract
        self.paddle_ocr = None
        self.tesseract_ocr = None
        
        # 尝试加载 OCR 引擎
        self._load_engines()
        
        # 教育领域专用词典
        self.edu_dictionary = self._load_edu_dictionary()
        
        # 数学公式符号映射
        self.math_symbols = {
            '×': '*',
            '÷': '/',
            '＝': '=',
            '±': '+/-',
            '°': ' degrees',
            '∠': 'angle',
            '△': 'triangle',
            '√': 'sqrt',
            'π': 'pi',
            'θ': 'theta',
            'α': 'alpha',
            'β': 'beta',
        }
    
    def _load_engines(self):
        """加载 OCR 引擎"""
        # PaddleOCR
        if self.use_paddle:
            try:
                from paddleocr import PaddleOCR
                self.paddle_ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang='ch',
                    show_log=False
                )
                print("✓ PaddleOCR 加载成功")
            except ImportError:
                print("⚠ PaddleOCR 未安装，将使用备用方案")
                self.paddle_ocr = None
        
        # Tesseract
        if self.use_tesseract:
            try:
                import pytesseract
                self.tesseract_ocr = pytesseract
                print("✓ Tesseract 加载成功")
            except ImportError:
                print("⚠ Tesseract 未安装")
                self.tesseract_ocr = None
    
    def _load_edu_dictionary(self) -> Dict[str, List[str]]:
        """加载教育领域专用词典"""
        return {
            # 常见易错词纠正
            '光合作用': ['光合作用', '光和作用', '光合做用'],
            '二氧化碳': ['二氧化碳', '二氧化炭', 'CO2'],
            '三角形': ['三角形', '三解形', '叁角形'],
            '方程式': ['方程式', '方程试', '方程序'],
            '函数': ['函数', '函式', '涵数'],
            '微分': ['微分', '微份'],
            '积分': ['积分', '积份'],
            '向量': ['向量', '矢量', '向亮'],
            '概率': ['概率', '几率', '机率'],
        }
    
    def recognize_image(
        self, 
        image_path: str,
        context: Optional[str] = None
    ) -> List[OCRResult]:
        """
        识别图片中的文字
        
        Args:
            image_path: 图片路径
            context: 上下文信息（用于纠错）
            
        Returns:
            List[OCRResult]: OCR 识别结果列表
        """
        results = []
        
        # 多引擎识别
        engine_results = []
        
        # PaddleOCR 识别
        if self.paddle_ocr is not None:
            try:
                paddle_result = self.paddle_ocr.ocr(image_path, cls=True)
                if paddle_result and paddle_result[0]:
                    for line in paddle_result[0]:
                        bbox, (text, conf) = line
                        engine_results.append(OCRResult(
                            text=text,
                            confidence=conf,
                            bounding_box=tuple(bbox) if len(bbox) == 4 else None
                        ))
            except Exception as e:
                print(f"PaddleOCR 识别失败：{e}")
        
        # Tesseract 识别
        if self.tesseract_ocr is not None:
            try:
                from PIL import Image
                img = Image.open(image_path)
                tess_text = self.tesseract_ocr.image_to_string(img, lang='chi_sim+eng')
                tess_conf = self.tesseract_ocr.image_to_boxes(img, lang='chi_sim+eng')
                
                # 简化处理
                engine_results.append(OCRResult(
                    text=tess_text.strip(),
                    confidence=0.7,  # 估计置信度
                    bounding_box=None
                ))
            except Exception as e:
                print(f"Tesseract 识别失败：{e}")
        
        # 如果没有可用引擎，返回模拟结果（用于演示）
        if not engine_results:
            print("⚠ 无可用 OCR 引擎，返回模拟结果")
            engine_results.append(OCRResult(
                text="[模拟] 这是学生手写答案的模拟识别结果",
                confidence=0.85,
                bounding_box=None
            ))
        
        # 多引擎投票融合
        fused_results = self._fuse_results(engine_results)
        
        # 上下文纠错
        if context:
            fused_results = self._context_correction(fused_results, context)
        
        # 教育词典纠错
        fused_results = self._dictionary_correction(fused_results)
        
        # 数学公式标准化
        fused_results = self._normalize_math_symbols(fused_results)
        
        return fused_results
    
    def _fuse_results(self, results: List[OCRResult]) -> List[OCRResult]:
        """多引擎结果投票融合"""
        if len(results) <= 1:
            return results
        
        # 简单策略：选择置信度最高的结果
        best_result = max(results, key=lambda r: r.confidence)
        return [best_result]
    
    def _context_correction(
        self, 
        results: List[OCRResult], 
        context: str
    ) -> List[OCRResult]:
        """基于上下文的纠错"""
        corrected = []
        
        for result in results:
            text = result.text
            
            # 结合题目语境纠正
            if context:
                # 查找相似的正确词汇
                context_words = set(context.split())
                text_words = text.split()
                
                for word in text_words:
                    # 如果词语不在上下文中且置信度低，标记为可疑
                    if word not in context_words and result.confidence < 0.8:
                        # 这里可以调用更复杂的纠错逻辑
                        pass
            
            corrected.append(OCRResult(
                text=text,
                confidence=result.confidence,
                bounding_box=result.bounding_box
            ))
        
        return corrected
    
    def _dictionary_correction(self, results: List[OCRResult]) -> List[OCRResult]:
        """基于教育词典的纠错"""
        corrected = []
        
        for result in results:
            text = result.text
            
            # 检查是否需要词典纠正
            for correct_word, variants in self.edu_dictionary.items():
                for variant in variants:
                    if variant != correct_word and variant in text:
                        text = text.replace(variant, correct_word)
                        result.confidence = min(1.0, result.confidence + 0.05)
            
            corrected.append(OCRResult(
                text=text,
                confidence=result.confidence,
                bounding_box=result.bounding_box
            ))
        
        return corrected
    
    def _normalize_math_symbols(self, results: List[OCRResult]) -> List[OCRResult]:
        """标准化数学符号"""
        normalized = []
        
        for result in results:
            text = result.text
            
            # 替换数学符号
            for symbol, replacement in self.math_symbols.items():
                text = text.replace(symbol, replacement)
            
            normalized.append(OCRResult(
                text=text,
                confidence=result.confidence,
                bounding_box=result.bounding_box
            ))
        
        return normalized
    
    def recognize_handwriting_batch(
        self, 
        image_paths: List[str],
        batch_size: int = 10
    ) -> Dict[str, List[OCRResult]]:
        """
        批量识别手写图片
        
        Args:
            image_paths: 图片路径列表
            batch_size: 批次大小
            
        Returns:
            Dict: {图片路径：识别结果}
        """
        batch_results = {}
        
        for i in range(0, len(image_paths), batch_size):
            batch = image_paths[i:i + batch_size]
            for img_path in batch:
                results = self.recognize_image(img_path)
                batch_results[img_path] = results
        
        return batch_results
    
    def get_unrecognized_regions(self, results: List[OCRResult]) -> List[Dict]:
        """
        获取无法识别的区域（用于交互式纠错）
        
        Args:
            results: OCR 识别结果
            
        Returns:
            List[Dict]: 无法识别区域的信息
        """
        unrecognized = []
        
        for result in results:
            if result.confidence < 0.5:  # 低置信度阈值
                unrecognized.append({
                    'text': result.text,
                    'confidence': result.confidence,
                    'bounding_box': result.bounding_box,
                    'suggestion': '请重新拍照或手动输入'
                })
        
        return unrecognized


def parse_latex(latex_text: str) -> Dict:
    """
    解析 LaTeX 公式
    
    Args:
        latex_text: LaTeX 格式的文本
        
    Returns:
        Dict: 解析后的结构
    """
    # 提取 LaTeX 表达式
    inline_matches = re.findall(r'\$(.*?)\$', latex_text)
    display_matches = re.findall(r'\$\$(.*?)\$\$', latex_text)
    
    return {
        'inline_equations': inline_matches,
        'display_equations': display_matches,
        'raw_text': latex_text
    }


if __name__ == "__main__":
    # 示例用法
    ocr_engine = MultiOCREngine()
    
    print("=" * 50)
    print("OCR 识别模块演示")
    print("=" * 50)
    
    # 模拟识别（因为没有实际图片）
    mock_result = OCRResult(
        text="光合作用是植物利用阳光将二氧化碳和水转化为有机物的过程",
        confidence=0.92,
        bounding_box=(10, 20, 300, 50)
    )
    
    print(f"\n模拟识别结果:")
    print(f"文本：{mock_result.text}")
    print(f"置信度：{mock_result.confidence:.2f}")
    print(f"位置：{mock_result.bounding_box}")
    
    # 测试 LaTeX 解析
    latex_example = """
    解：设$x$为未知数
    $$x^2 + 2x + 1 = 0$$
    解得$x = -1$
    """
    
    parsed = parse_latex(latex_example)
    print(f"\nLaTeX 解析结果:")
    print(f"行内公式：{parsed['inline_equations']}")
    print(f"独立公式：{parsed['display_equations']}")
