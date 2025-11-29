"""
HR 面试官 Agent
关注：求职动机、简历匹配度、稳定性、沟通表达

评估维度:
1. 求职动机 - 是否真诚、与岗位匹配
2. 职业规划 - 目标清晰、与公司发展契合
3. 稳定性 - 对工作的承诺和长期意愿
4. 沟通表达 - 逻辑清晰、表达流畅
"""
from typing import List, Dict
from agents.base_agent import BaseAgent
from core.llm_client import LLMClient


class HRAgent(BaseAgent):
    """HR 面试官 - 负责初筛环节"""

    def __init__(self, llm: LLMClient):
        super().__init__(llm, role="HR")
        self.role_cn = "HR 面试官"
        self.role_description = "负责初筛环节，评估候选人的求职动机、职业规划和沟通能力"
        self.evaluation_dimensions = [
            "求职动机真诚度",
            "职业规划清晰度", 
            "稳定性与承诺",
            "沟通表达能力",
            "与岗位匹配度"
        ]
        
        # HR 常用问题库
        self.question_templates = [
            "请用2-3分钟简单介绍一下你自己，重点说说你的数据分析背景和为什么对这个岗位感兴趣。",
            "你未来3-5年的职业规划是什么？数据分析在你的职业发展中扮演什么角色？",
            "能谈谈你离开上一份工作（或想换工作）的原因吗？在选择新机会时你最看重什么？",
            "你了解我们公司吗？为什么想加入我们？",
            "如果有多个offer，你会如何做选择？",
            "你期望的薪资范围是多少？这个期望是基于什么考虑？",
        ]

    def get_system_prompt(self) -> str:
        return """你是一位经验丰富的 HR 面试官，正在面试「数据分析师」岗位的候选人。

【你的角色定位】
- 公司的第一道面试关卡，负责初步筛选
- 需要判断候选人是否值得进入下一轮
- 关注软技能和文化匹配度

【你的职责】
1. 评估候选人的求职动机是否真诚、是否与数据分析岗位匹配
2. 了解候选人的职业规划，判断稳定性
3. 观察候选人的沟通表达能力和逻辑思维
4. 初步判断候选人的职业素养和工作态度

【面试风格】
- 专业但亲和，让候选人感到舒适、愿意真诚表达
- 善于倾听，适当追问以了解真实想法
- 问题循序渐进，从轻松话题逐渐深入
- 注意非语言信息（在文字面试中体现为回答的流畅度和逻辑性）

【关注的红旗信号】
- 频繁跳槽且无合理解释
- 对岗位理解偏差大
- 表达混乱、逻辑不清
- 态度傲慢或过于敷衍

【评分重点】
- 自我介绍结构性（是否有重点、是否与岗位相关）
- 动机真实性（是否能说出具体原因）
- 规划合理性（是否有思考、是否现实）
- 表达清晰度（是否逻辑清晰、简洁有力）

请用自然的中文交流，像真正的 HR 面试官一样。"""

    def generate_question(self, user_context: str, session_context: str) -> str:
        """生成 HR 面试问题"""
        system_prompt = self.get_system_prompt() + """

【任务】生成一个高质量的 HR 面试问题

问题要求：
1. 考察求职动机、职业规划或沟通能力之一
2. 开放式问题，给候选人充分表达空间
3. 与数据分析师岗位相关
4. 用自然、友好的语气

只输出问题本身，不要有任何多余内容。"""

        user_message = f"""候选人信息: {user_context if user_context else '首次面试，暂无历史信息'}

当前面试进度: {session_context if session_context else 'HR 初筛第一轮'}

请生成一个合适的 HR 面试问题:"""

        return self.llm.generate_with_system(system_prompt, user_message, temperature=0.8)
