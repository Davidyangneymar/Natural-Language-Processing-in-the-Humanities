"""
终面评审委员会 Agent
汇总各轮面试结果，给出整体评分、优势分析和改进建议

职责:
1. 综合各轮面试评估
2. 结合历史表现分析
3. 给出最终录用建议
4. 提供个性化改进建议
"""
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from core.llm_client import LLMClient
from config import INTERVIEW_ROUNDS_CONFIG, get_score_level


class CommitteeAgent(BaseAgent):
    """终面评审委员会 - 综合评估候选人"""

    def __init__(self, llm: LLMClient):
        super().__init__(llm, role="Committee")
        self.role_cn = "终面评审委员会"
        self.role_description = "汇总各轮面试结果，给出整体评分、优势分析和改进建议"
        self.evaluation_dimensions = [
            "综合能力评估",
            "岗位匹配度",
            "成长潜力",
            "风险评估",
            "录用建议"
        ]

    def get_system_prompt(self) -> str:
        return """你是面试评审委员会的主席，负责汇总「数据分析师」岗位候选人的所有面试结果，给出最终评估和录用建议。

【你的角色定位】
- 公正、客观的最终决策者
- 需要综合各方面信息做出判断
- 既要指出问题，也要看到潜力

【你的职责】
1. 综合各轮面试官的评分和反馈
2. 分析候选人的整体表现模式
3. 结合历史面试记录（如有）评估进步
4. 给出公正、全面的最终评估
5. 提供具体、可执行的改进建议

【评估框架】
1. 硬技能评估（40%权重）
   - 统计/SQL/Python 等技术能力
   - 实验设计和指标体系理解
   
2. 软技能评估（30%权重）
   - 沟通表达能力
   - 业务理解和落地能力
   - 跨部门协作能力

3. 文化匹配（20%权重）
   - 价值观契合度
   - 团队协作意愿
   - 成长心态

4. 综合印象（10%权重）
   - 求职动机
   - 稳定性
   - 发展潜力

【评分标准】
- 8-10分: 强烈推荐，表现优秀，可直接录用
- 6-7分: 推荐通过，有小问题但可接受
- 4-5分: 候补，需要针对性提升后再考虑
- 0-3分: 不推荐，存在明显短板

【输出要求】
- 评价要具体，引用面试中的实际表现
- 优势和劣势都要提及，但语气建设性
- 改进建议要具体、可操作，不要泛泛而谈
- 如有历史记录，要指出进步或退步

请用专业、客观的语气，像真正的面试委员会一样做出评估。"""

    def generate_question(self, user_context: str, session_context: str) -> str:
        """委员会不提问，返回空"""
        return ""

    def generate_final_evaluation(
        self,
        session_summary: Dict[str, Any],
        user_history: str,
    ) -> Dict[str, Any]:
        """
        生成最终评估报告
        
        Args:
            session_summary: 本次面试各轮摘要
            user_history: 用户历史面试记录
            
        Returns:
            完整的评估报告
        """
        system_prompt = self.get_system_prompt() + """

【任务】根据所有面试轮次的结果，生成最终评估报告。

请严格按以下 JSON 格式返回:
{
    "final_score": <0-10的整数，加权综合评分>,
    "decision": "<强烈推荐/推荐通过/候补/暂不推荐>",
    "decision_reason": "<一句话说明决策理由>",
    "overall_feedback": "<3-5句整体评价，要具体引用面试表现>",
    "dimension_scores": {
        "技术能力": <0-10>,
        "业务理解": <0-10>,
        "沟通表达": <0-10>,
        "文化匹配": <0-10>
    },
    "key_strengths": ["<优势1，要具体>", "<优势2>", "<优势3>"],
    "key_weaknesses": ["<待改进1，要具体>", "<待改进2>"],
    "improvement_suggestions": [
        "<具体建议1，如：建议用 STAR 结构讲项目，先说背景再说你做了什么>",
        "<具体建议2，如：A/B测试部分建议补充样本量计算的知识>",
        "<具体建议3>"
    ],
    "practice_focus": ["<重点练习方向1>", "<重点练习方向2>"],
    "next_steps": "<给候选人的下一步行动建议>"
}"""

        # 构建各轮面试摘要
        rounds_text = self._format_rounds_summary(session_summary)
        
        # 计算加权分数提示
        weights_text = self._format_weights()

        user_message = f"""【本次面试各轮结果】
{rounds_text}

【评分权重参考】
{weights_text}

【本次面试统计】
- 总轮数: {len(session_summary.get('rounds', []))}
- 简单平均分: {session_summary.get('average_score', 'N/A')}/10
- 累积弱项标签: {', '.join(session_summary.get('all_weakness_tags', [])) or '无'}
- 累积优势标签: {', '.join(session_summary.get('all_strength_tags', [])) or '无'}

【候选人历史记录】
{user_history}

请生成最终评估报告:"""

        result = self.llm.generate_json(system_prompt, user_message, temperature=0.5)
        
        return self._normalize_final_evaluation(result, session_summary)

    def _format_rounds_summary(self, session_summary: Dict[str, Any]) -> str:
        """格式化各轮面试摘要"""
        rounds_text = []
        for r in session_summary.get("rounds", []):
            round_config = INTERVIEW_ROUNDS_CONFIG.get(r['role'], {})
            round_name = round_config.get('name', r['role'])
            weight = round_config.get('weight', 0.2)
            
            text = f"""
【{round_name}】（权重: {weight*100:.0f}%）
- 问题: {r['question'][:150]}{'...' if len(r['question']) > 150 else ''}
- 回答摘要: {r['answer'][:200]}{'...' if len(r['answer']) > 200 else ''}
- 得分: {r['score']}/10
- 反馈: {r['feedback']}
- 弱项: {', '.join(r.get('weakness_tags', [])) or '无'}
- 优势: {', '.join(r.get('strength_tags', [])) or '无'}
- 关键点: {', '.join(r.get('key_points', [])) or '无'}"""
            rounds_text.append(text)
        
        return "\n".join(rounds_text)

    def _format_weights(self) -> str:
        """格式化权重说明"""
        weights = []
        for role, config in INTERVIEW_ROUNDS_CONFIG.items():
            if config.get('weight', 0) > 0:
                weights.append(f"- {config['name']}: {config['weight']*100:.0f}%")
        return "\n".join(weights)

    def _normalize_final_evaluation(
        self, 
        result: Dict[str, Any], 
        session_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """标准化最终评估结果"""
        if "error" in result:
            avg_score = session_summary.get("average_score", 5)
            return {
                "final_score": avg_score,
                "decision": "候补",
                "decision_reason": "评估生成过程出现问题，请参考各轮反馈。",
                "overall_feedback": "系统暂时无法生成完整评估，建议查看各轮次的详细反馈。",
                "dimension_scores": {},
                "key_strengths": session_summary.get("all_strength_tags", [])[:3],
                "key_weaknesses": session_summary.get("all_weakness_tags", [])[:3],
                "improvement_suggestions": ["建议重新进行面试模拟以获取完整评估"],
                "practice_focus": [],
                "next_steps": "请重试面试模拟",
                "raw_error": result.get("raw", "")
            }
        
        # 确保分数在有效范围
        final_score = result.get("final_score", 5)
        if isinstance(final_score, (int, float)):
            final_score = max(0, min(10, int(final_score)))
        else:
            final_score = 5
        
        # 根据分数确定决策（如果模型没给或给错了）
        score_info = get_score_level(final_score)
        decision = result.get("decision", score_info["decision"])
        
        return {
            "final_score": final_score,
            "decision": decision,
            "decision_reason": result.get("decision_reason", ""),
            "overall_feedback": result.get("overall_feedback", ""),
            "dimension_scores": result.get("dimension_scores", {}),
            "key_strengths": result.get("key_strengths", []),
            "key_weaknesses": result.get("key_weaknesses", []),
            "improvement_suggestions": result.get("improvement_suggestions", []),
            "practice_focus": result.get("practice_focus", []),
            "next_steps": result.get("next_steps", ""),
        }

    def generate_comparative_analysis(
        self,
        current_evaluation: Dict[str, Any],
        historical_evaluations: List[Dict[str, Any]],
    ) -> str:
        """
        生成与历史表现的对比分析
        
        Args:
            current_evaluation: 当前评估结果
            historical_evaluations: 历史评估列表
        """
        if not historical_evaluations:
            return "这是您的第一次模拟面试，暂无历史对比数据。"
        
        system_prompt = """你是一个数据分析专家，需要对比分析候选人的面试表现变化趋势。

请分析：
1. 分数变化趋势（进步/退步/稳定）
2. 哪些方面有明显改善
3. 哪些问题反复出现
4. 给出针对性的下一步建议

用2-3段简洁的中文输出分析结果。"""

        # 构建历史数据摘要
        history_text = []
        for i, h in enumerate(historical_evaluations[-5:], 1):  # 最近5次
            history_text.append(
                f"第{i}次: 得分 {h.get('final_score', 'N/A')}/10, "
                f"决策: {h.get('decision', 'N/A')}, "
                f"主要弱项: {', '.join(h.get('key_weaknesses', [])[:2]) or '无'}"
            )
        
        user_message = f"""当前面试结果:
- 得分: {current_evaluation.get('final_score', 'N/A')}/10
- 决策: {current_evaluation.get('decision', 'N/A')}
- 主要弱项: {', '.join(current_evaluation.get('key_weaknesses', []))}
- 主要优势: {', '.join(current_evaluation.get('key_strengths', []))}

历史面试记录（从早到近）:
{chr(10).join(history_text)}

请分析变化趋势并给出建议:"""

        return self.llm.generate_with_system(system_prompt, user_message, temperature=0.6)
