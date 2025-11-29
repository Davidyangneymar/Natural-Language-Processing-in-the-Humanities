"""
Interview Workflow Engine - 面试流程引擎
负责调度各面试官、控制回合、收集评分、支持追问

特性:
- 多轮面试流程控制
- 智能追问机制
- 加权评分计算
- 完整的回调支持
"""
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime
from core.llm_client import LLMClient
from core.memory import UserMemory, SessionMemory
from agents.hr_agent import HRAgent
from agents.hiring_manager_agent import HiringManagerAgent
from agents.technical_agent import TechnicalAgent
from agents.culture_agent import CultureFitAgent
from agents.committee_agent import CommitteeAgent
from config import (
    DEFAULT_POSITION, INTERVIEW_ROUNDS, INTERVIEW_ROUNDS_CONFIG,
    FOLLOW_UP_CONFIG
)


class InterviewWorkflow:
    """
    面试流程引擎
    
    负责:
    - 调度各面试官按顺序面试
    - 控制每轮的问答和追问
    - 收集评分并计算加权总分
    - 触发各种回调通知 UI
    """

    def __init__(self, llm: Optional[LLMClient] = None):
        self.llm = llm or LLMClient()
        
        # 初始化各面试官
        self.agents = {
            "HR": HRAgent(self.llm),
            "HiringManager": HiringManagerAgent(self.llm),
            "Technical": TechnicalAgent(self.llm),
            "CultureFit": CultureFitAgent(self.llm),
        }
        self.committee = CommitteeAgent(self.llm)
        
        # 面试轮次顺序（不包含 Committee）
        self.round_order = [r for r in INTERVIEW_ROUNDS if r != "Committee"]

    def get_round_name(self, round_key: str) -> str:
        """获取轮次中文名称"""
        config = INTERVIEW_ROUNDS_CONFIG.get(round_key, {})
        return config.get("name", round_key)

    def get_round_weight(self, round_key: str) -> float:
        """获取轮次权重"""
        config = INTERVIEW_ROUNDS_CONFIG.get(round_key, {})
        return config.get("weight", 0.2)

    def run_single_round(
        self,
        agent_key: str,
        user_memory: UserMemory,
        session: SessionMemory,
        get_user_answer: Callable[[str, str], str],
        on_question: Optional[Callable[[str, str], None]] = None,
        on_evaluation: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_follow_up: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        运行单轮面试（包含可能的追问）
        
        Args:
            agent_key: 面试官标识
            user_memory: 用户长期记忆
            session: 当前会话记忆
            get_user_answer: 获取用户回答的回调 (question, round_name) -> answer
            on_question: 问题展示回调 (question, round_name)
            on_evaluation: 评估完成回调 (evaluation_result)
            on_follow_up: 追问通知回调 (reason)
            
        Returns:
            本轮完整结果（包含追问）
        """
        agent = self.agents[agent_key]
        round_name = self.get_round_name(agent_key)
        round_config = INTERVIEW_ROUNDS_CONFIG.get(agent_key, {})
        
        # 获取上下文
        user_context = self._build_user_context(user_memory)
        session_context = session.get_context_for_next_round()
        
        # 生成主问题
        question = agent.generate_question(user_context, session_context)
        
        if on_question:
            on_question(question, round_name)
        
        # 获取用户回答
        answer = get_user_answer(question, round_name)
        
        # 评估回答
        evaluation = agent.evaluate_answer(
            question=question,
            answer=answer,
            user_context=user_context,
        )
        
        if on_evaluation:
            on_evaluation(evaluation)
        
        # 记录到会话
        session.add_round(
            role=agent_key,
            question=question,
            answer=answer,
            score=evaluation["score"],
            feedback=evaluation["feedback"],
            weakness_tags=evaluation.get("weakness_tags", []),
            strength_tags=evaluation.get("strength_tags", []),
            key_points=evaluation.get("key_points", []),
            improvement_hint=evaluation.get("improvement_hint", ""),
        )
        
        result = {
            "round": agent_key,
            "round_name": round_name,
            "questions": [{
                "question": question,
                "answer": answer,
                "evaluation": evaluation,
                "is_follow_up": False,
            }],
            "final_score": evaluation["score"],
        }
        
        # 检查是否需要追问
        if round_config.get("follow_up_enabled", False):
            should_follow, reason = agent.should_follow_up(answer, evaluation)
            
            if should_follow and FOLLOW_UP_CONFIG.get("enabled", False):
                follow_up_result = self._handle_follow_up(
                    agent=agent,
                    original_question=question,
                    original_answer=answer,
                    evaluation=evaluation,
                    reason=reason,
                    user_memory=user_memory,
                    session=session,
                    get_user_answer=get_user_answer,
                    on_question=on_question,
                    on_evaluation=on_evaluation,
                    on_follow_up=on_follow_up,
                )
                
                if follow_up_result:
                    result["questions"].append(follow_up_result)
                    # 更新最终分数为追问后的分数
                    result["final_score"] = follow_up_result["evaluation"]["score"]
        
        return result

    def _handle_follow_up(
        self,
        agent,
        original_question: str,
        original_answer: str,
        evaluation: Dict[str, Any],
        reason: str,
        user_memory: UserMemory,
        session: SessionMemory,
        get_user_answer: Callable,
        on_question: Optional[Callable],
        on_evaluation: Optional[Callable],
        on_follow_up: Optional[Callable],
    ) -> Optional[Dict[str, Any]]:
        """处理追问逻辑"""
        if on_follow_up:
            on_follow_up(reason)
        
        # 生成追问
        follow_up_question = agent.generate_follow_up(
            original_question=original_question,
            answer=original_answer,
            evaluation=evaluation,
            follow_up_reason=reason,
        )
        
        if on_question:
            on_question(follow_up_question, f"{agent.role_cn}（追问）")
        
        # 获取追问回答
        follow_up_answer = get_user_answer(
            follow_up_question, 
            f"{self.get_round_name(agent.role)}（追问）"
        )
        
        # 评估追问回答
        user_context = self._build_user_context(user_memory)
        follow_up_eval = agent.evaluate_answer(
            question=follow_up_question,
            answer=follow_up_answer,
            user_context=user_context,
            conversation_history=[
                {"role": "interviewer", "content": original_question},
                {"role": "candidate", "content": original_answer},
            ]
        )
        
        if on_evaluation:
            on_evaluation(follow_up_eval)
        
        # 记录追问
        session.add_round(
            role=f"{agent.role}_followup",
            question=follow_up_question,
            answer=follow_up_answer,
            score=follow_up_eval["score"],
            feedback=follow_up_eval["feedback"],
            weakness_tags=follow_up_eval.get("weakness_tags", []),
            strength_tags=follow_up_eval.get("strength_tags", []),
            key_points=follow_up_eval.get("key_points", []),
            improvement_hint=follow_up_eval.get("improvement_hint", ""),
            is_follow_up=True,
        )
        
        return {
            "question": follow_up_question,
            "answer": follow_up_answer,
            "evaluation": follow_up_eval,
            "is_follow_up": True,
            "follow_up_reason": reason,
        }

    def _build_user_context(self, user_memory: UserMemory) -> str:
        """构建用户上下文"""
        data = user_memory.data
        parts = [f"岗位: {data.get('position', DEFAULT_POSITION)}"]
        
        profile = data.get("profile", {})
        if profile.get("experience_years"):
            parts.append(f"经验: {profile['experience_years']}年")
        if profile.get("skills"):
            parts.append(f"技能: {', '.join(profile['skills'][:5])}")
        
        # 添加历史弱项提示（帮助面试官针对性提问）
        top_weaknesses = user_memory.get_top_weaknesses(3)
        if top_weaknesses:
            parts.append(f"历史弱项: {', '.join([w[0] for w in top_weaknesses])}")
        
        return " | ".join(parts)

    def run_committee_evaluation(
        self,
        user_memory: UserMemory,
        session: SessionMemory,
    ) -> Dict[str, Any]:
        """运行终面评审委员会评估"""
        # 构建会话摘要
        session_dict = session.to_dict()
        session_summary = {
            "rounds": session_dict["rounds"],
            "average_score": session.get_average_score(),
            "weighted_score": self._calculate_weighted_score(session),
            "all_weakness_tags": session.get_all_weakness_tags(),
            "all_strength_tags": session.get_all_strength_tags(),
        }
        
        user_history = user_memory.get_history_summary()
        
        # 生成最终评估
        final_eval = self.committee.generate_final_evaluation(
            session_summary, user_history
        )
        
        # 如果有历史记录，生成对比分析
        if user_memory.data.get("interview_history"):
            comparative = self.committee.generate_comparative_analysis(
                final_eval,
                user_memory.data["interview_history"]
            )
            final_eval["comparative_analysis"] = comparative
        
        session.set_final_evaluation(final_eval)
        
        return final_eval

    def _calculate_weighted_score(self, session: SessionMemory) -> float:
        """计算加权总分"""
        total_weight = 0
        weighted_sum = 0
        
        for r in session.rounds:
            role = r["role"].replace("_followup", "")  # 追问归属原轮次
            weight = self.get_round_weight(role)
            weighted_sum += r["score"] * weight
            total_weight += weight
        
        if total_weight > 0:
            return round(weighted_sum / total_weight, 2)
        return 0.0

    def run_full_interview(
        self,
        user_id: str,
        get_user_answer: Callable[[str, str], str],
        on_round_start: Optional[Callable[[str, str], None]] = None,
        on_question: Optional[Callable[[str, str], None]] = None,
        on_evaluation: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_follow_up: Optional[Callable[[str], None]] = None,
        on_round_complete: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_final_evaluation: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> str:
        """
        运行完整面试流程
        
        Args:
            user_id: 用户ID
            get_user_answer: 获取用户回答 (question, round_name) -> answer
            on_round_start: 轮次开始回调 (round_key, round_name)
            on_question: 问题展示回调 (question, round_name)
            on_evaluation: 评估完成回调 (evaluation)
            on_follow_up: 追问通知回调 (reason)
            on_round_complete: 轮次完成回调 (round_result)
            on_final_evaluation: 最终评估回调 (evaluation)
            
        Returns:
            会话文件保存路径
        """
        # 加载/创建用户记忆
        user_memory = UserMemory(user_id)
        session = SessionMemory(user_id, DEFAULT_POSITION)
        
        round_results = []
        
        # 依次运行各轮面试
        for round_key in self.round_order:
            round_name = self.get_round_name(round_key)
            
            if on_round_start:
                on_round_start(round_key, round_name)
            
            result = self.run_single_round(
                agent_key=round_key,
                user_memory=user_memory,
                session=session,
                get_user_answer=get_user_answer,
                on_question=on_question,
                on_evaluation=on_evaluation,
                on_follow_up=on_follow_up,
            )
            
            round_results.append(result)
            
            if on_round_complete:
                on_round_complete(result)
        
        # 终面评审
        if on_round_start:
            on_round_start("Committee", self.get_round_name("Committee"))
        
        final_eval = self.run_committee_evaluation(user_memory, session)
        
        if on_final_evaluation:
            on_final_evaluation(final_eval)
        
        # 更新用户长期记忆
        user_memory.add_weakness_tags(session.get_all_weakness_tags())
        user_memory.add_strength_tags(session.get_all_strength_tags())
        user_memory.add_interview_summary({
            "timestamp": session.started_at,
            "final_score": final_eval.get("final_score"),
            "weighted_score": self._calculate_weighted_score(session),
            "decision": final_eval.get("decision"),
            "rounds_count": len(session.rounds),
            "key_strengths": final_eval.get("key_strengths", []),
            "key_weaknesses": final_eval.get("key_weaknesses", []),
        })
        user_memory.save()
        
        # 保存会话记录
        session_path = session.save()
        
        return session_path

    def run_quick_practice(
        self,
        user_id: str,
        round_type: str,
        get_user_answer: Callable[[str, str], str],
        on_question: Optional[Callable[[str, str], None]] = None,
        on_evaluation: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """
        快速单轮练习模式
        
        Args:
            user_id: 用户ID
            round_type: 练习类型 (HR/HiringManager/Technical/CultureFit)
            get_user_answer: 获取回答回调
            on_question: 问题回调
            on_evaluation: 评估回调
            
        Returns:
            练习结果
        """
        if round_type not in self.agents:
            raise ValueError(f"不支持的练习类型: {round_type}")
        
        user_memory = UserMemory(user_id)
        session = SessionMemory(user_id, f"快速练习-{round_type}")
        
        result = self.run_single_round(
            agent_key=round_type,
            user_memory=user_memory,
            session=session,
            get_user_answer=get_user_answer,
            on_question=on_question,
            on_evaluation=on_evaluation,
        )
        
        return result
