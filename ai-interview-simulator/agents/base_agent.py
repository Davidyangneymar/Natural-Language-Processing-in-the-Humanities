"""
BaseAgent - 面试官抽象基类
定义所有面试官的通用接口、评分结构与追问机制
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from core.llm_client import LLMClient
from config import (
    WEAKNESS_TAGS, STRENGTH_TAGS,
    WEAKNESS_TAGS_BY_CATEGORY, STRENGTH_TAGS_BY_CATEGORY,
    FOLLOW_UP_CONFIG, SCORE_MIN, SCORE_MAX
)


class BaseAgent(ABC):
    """
    面试官抽象基类
    
    所有面试官需要实现:
    - get_system_prompt(): 返回角色提示词
    - generate_question(): 生成面试问题
    - get_evaluation_criteria(): 返回评估维度
    """

    def __init__(self, llm: LLMClient, role: str = "base"):
        self.llm = llm
        self.role = role
        self.role_cn = ""  # 中文角色名
        self.role_description = ""
        self.evaluation_dimensions: List[str] = []
        self.question_bank: List[Dict] = []  # 可选的题库

    @abstractmethod
    def get_system_prompt(self) -> str:
        """返回该面试官的系统提示词"""
        raise NotImplementedError()

    @abstractmethod
    def generate_question(self, user_context: str, session_context: str) -> str:
        """生成面试问题"""
        raise NotImplementedError()

    def get_evaluation_criteria(self) -> str:
        """返回评估维度说明（用于 prompt）"""
        if self.evaluation_dimensions:
            return "评估维度: " + ", ".join(self.evaluation_dimensions)
        return ""

    def _build_evaluation_prompt(self) -> str:
        """构建评估提示词"""
        weakness_tags_str = "\n".join(
            f"  - {cat}: {', '.join(tags)}" 
            for cat, tags in WEAKNESS_TAGS_BY_CATEGORY.items()
        )
        strength_tags_str = "\n".join(
            f"  - {cat}: {', '.join(tags)}" 
            for cat, tags in STRENGTH_TAGS_BY_CATEGORY.items()
        )
        
        return f"""
你需要评估候选人的回答质量。请从以下维度评估:
{self.get_evaluation_criteria()}

评分标准 (0-10分):
- 9-10分: 优秀，回答全面、深入、有洞察力
- 7-8分: 良好，回答完整、有具体例子
- 5-6分: 中等，基本回答了问题，但缺乏深度
- 3-4分: 待提升，回答不完整或有明显问题
- 0-2分: 不足，未能有效回答问题

请严格按以下 JSON 格式返回评估结果:
{{
    "score": <{SCORE_MIN}-{SCORE_MAX}的整数>,
    "feedback": "<2-4句针对性反馈，先肯定优点，再指出改进空间>",
    "weakness_tags": ["<从下方标签中选择0-3个最相关的>"],
    "strength_tags": ["<从下方标签中选择0-3个最相关的>"],
    "key_points": ["<回答中的关键要点，2-3个>"],
    "improvement_hint": "<一句话具体改进建议>"
}}

可选弱项标签:
{weakness_tags_str}

可选优势标签:
{strength_tags_str}"""

    def evaluate_answer(
        self,
        question: str,
        answer: str,
        user_context: str = "",
        conversation_history: List[Dict] = None,
    ) -> Dict[str, Any]:
        """
        评估候选人回答
        
        Args:
            question: 面试问题
            answer: 候选人回答
            user_context: 用户背景信息
            conversation_history: 本轮对话历史（用于追问场景）
            
        Returns:
            评估结果字典
        """
        system_prompt = f"""{self.get_system_prompt()}

{self._build_evaluation_prompt()}"""

        # 构建上下文
        context_parts = []
        if user_context:
            context_parts.append(f"候选人背景: {user_context}")
        if conversation_history:
            history_str = "\n".join(
                f"- {h['role']}: {h['content'][:100]}..." 
                for h in conversation_history[-4:]  # 最近4轮
            )
            context_parts.append(f"对话历史:\n{history_str}")
        
        context_str = "\n\n".join(context_parts) if context_parts else "暂无额外背景"

        user_message = f"""面试问题: {question}

候选人回答: {answer}

{context_str}

请评估这个回答。"""

        result = self.llm.generate_json(system_prompt, user_message)
        
        # 确保返回格式正确
        return self._normalize_evaluation_result(result)

    def _normalize_evaluation_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """标准化评估结果"""
        if "error" in result:
            return {
                "score": 5,
                "feedback": "评估过程出现问题，请重试。",
                "weakness_tags": [],
                "strength_tags": [],
                "key_points": [],
                "improvement_hint": "",
                "raw_error": result.get("raw", "")
            }
        
        # 确保分数在有效范围内
        score = result.get("score", 5)
        if isinstance(score, (int, float)):
            score = max(SCORE_MIN, min(SCORE_MAX, int(score)))
        else:
            score = 5
        
        # 过滤无效标签
        weakness_tags = [
            t for t in result.get("weakness_tags", []) 
            if t in WEAKNESS_TAGS
        ]
        strength_tags = [
            t for t in result.get("strength_tags", []) 
            if t in STRENGTH_TAGS
        ]
        
        return {
            "score": score,
            "feedback": result.get("feedback", ""),
            "weakness_tags": weakness_tags,
            "strength_tags": strength_tags,
            "key_points": result.get("key_points", []),
            "improvement_hint": result.get("improvement_hint", ""),
        }

    def should_follow_up(
        self,
        answer: str,
        evaluation: Dict[str, Any],
    ) -> Tuple[bool, str]:
        """
        判断是否需要追问
        
        Returns:
            (是否追问, 追问原因)
        """
        if not FOLLOW_UP_CONFIG.get("enabled", False):
            return False, ""
        
        # 分数低于阈值
        if evaluation.get("score", 10) < FOLLOW_UP_CONFIG.get("trigger_score_threshold", 6):
            return True, "回答需要更多细节"
        
        # 包含不确定关键词
        trigger_keywords = FOLLOW_UP_CONFIG.get("trigger_keywords", [])
        for keyword in trigger_keywords:
            if keyword in answer:
                return True, f"回答中提到「{keyword}」，需要澄清"
        
        # 回答过短
        if len(answer.strip()) < 50:
            return True, "回答较简短，可以展开"
        
        return False, ""

    def generate_follow_up(
        self,
        original_question: str,
        answer: str,
        evaluation: Dict[str, Any],
        follow_up_reason: str,
    ) -> str:
        """生成追问问题"""
        system_prompt = f"""{self.get_system_prompt()}

你需要基于候选人的回答生成一个追问问题。追问应该:
1. 针对回答中不够清晰或深入的部分
2. 帮助候选人展示更多能力
3. 自然、友好，不要让人感到被质疑

只输出追问问题本身，不要有多余内容。"""

        user_message = f"""原问题: {original_question}

候选人回答: {answer}

回答评估: 
- 得分: {evaluation.get('score', 'N/A')}/10
- 待改进: {', '.join(evaluation.get('weakness_tags', [])) or '无明显问题'}

追问原因: {follow_up_reason}

请生成一个自然的追问问题:"""

        return self.llm.generate_with_system(system_prompt, user_message, temperature=0.7)

    def ask(self, question: str) -> str:
        """简单问答（用于交互式场景）"""
        return self.llm.generate_with_system(self.get_system_prompt(), question)
