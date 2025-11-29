"""
Memory 模块 - 用户档案与会话记忆
支持长期记忆、弱项标签累积、历史面试追踪

特性:
- UserMemory: 用户长期档案，跨会话持久化
- SessionMemory: 单次面试会话记录
- 弱项/优势标签累积统计
- 历史对比分析支持
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from config import USERS_DIR, SESSIONS_DIR


class UserMemory:
    """
    用户长期记忆档案
    
    存储:
    - 用户基本信息
    - 累积弱项/优势标签（带计数）
    - 历史面试摘要
    - 统计数据
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.path = USERS_DIR / f"{user_id}.json"
        self.data: Dict[str, Any] = self._default_profile()
        self._load()

    def _default_profile(self) -> Dict[str, Any]:
        """默认用户档案结构"""
        return {
            "user_id": self.user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "position": "数据分析师 (Data Analyst)",
            "profile": {
                "name": "",
                "experience_years": 0,
                "skills": [],
                "target_companies": [],
                "notes": "",
            },
            "weakness_tags": {},      # {"tag": count}
            "strength_tags": {},      # {"tag": count}
            "interview_history": [],  # 历史面试摘要列表
            "statistics": {
                "total_interviews": 0,
                "average_score": 0.0,
                "best_score": 0,
                "recent_trend": "",    # "improving" / "stable" / "declining"
                "most_common_weakness": "",
                "most_common_strength": "",
            }
        }

    def _load(self):
        """加载已有用户档案"""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    # 合并默认值（兼容旧版本档案）
                    default = self._default_profile()
                    for key, value in default.items():
                        if key not in loaded:
                            loaded[key] = value
                        elif isinstance(value, dict) and isinstance(loaded.get(key), dict):
                            for k, v in value.items():
                                if k not in loaded[key]:
                                    loaded[key][k] = v
                    self.data = loaded
            except json.JSONDecodeError:
                # 文件损坏，使用默认值
                pass

    def save(self):
        """保存用户档案"""
        self.data["updated_at"] = datetime.now().isoformat()
        self._update_statistics()
        
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def _update_statistics(self):
        """更新统计数据"""
        history = self.data.get("interview_history", [])
        stats = self.data["statistics"]
        
        stats["total_interviews"] = len(history)
        
        if history:
            scores = [h.get("final_score", 0) for h in history if h.get("final_score")]
            if scores:
                stats["average_score"] = round(sum(scores) / len(scores), 2)
                stats["best_score"] = max(scores)
                
                # 计算趋势（最近3次 vs 之前）
                if len(scores) >= 4:
                    recent = sum(scores[-3:]) / 3
                    earlier = sum(scores[:-3]) / len(scores[:-3])
                    if recent > earlier + 0.5:
                        stats["recent_trend"] = "improving"
                    elif recent < earlier - 0.5:
                        stats["recent_trend"] = "declining"
                    else:
                        stats["recent_trend"] = "stable"
        
        # 最常见标签
        top_weak = self.get_top_weaknesses(1)
        if top_weak:
            stats["most_common_weakness"] = top_weak[0][0]
        
        top_strong = self.get_top_strengths(1)
        if top_strong:
            stats["most_common_strength"] = top_strong[0][0]

    def add_weakness_tags(self, tags: List[str]):
        """累积弱项标签"""
        for tag in tags:
            if tag:  # 过滤空标签
                self.data["weakness_tags"][tag] = self.data["weakness_tags"].get(tag, 0) + 1

    def add_strength_tags(self, tags: List[str]):
        """累积优势标签"""
        for tag in tags:
            if tag:
                self.data["strength_tags"][tag] = self.data["strength_tags"].get(tag, 0) + 1

    def add_interview_summary(self, summary: Dict[str, Any]):
        """添加面试摘要到历史记录"""
        summary["added_at"] = datetime.now().isoformat()
        self.data["interview_history"].append(summary)

    def get_top_weaknesses(self, n: int = 5) -> List[tuple]:
        """获取出现频率最高的弱项"""
        tags = self.data.get("weakness_tags", {})
        return sorted(tags.items(), key=lambda x: x[1], reverse=True)[:n]

    def get_top_strengths(self, n: int = 5) -> List[tuple]:
        """获取出现频率最高的优势"""
        tags = self.data.get("strength_tags", {})
        return sorted(tags.items(), key=lambda x: x[1], reverse=True)[:n]

    def get_history_summary(self) -> str:
        """获取历史面试摘要（用于提供给 Committee）"""
        history = self.data.get("interview_history", [])
        stats = self.data.get("statistics", {})
        
        if not history:
            return "这是该候选人的第一次模拟面试，暂无历史记录。"
        
        lines = [
            f"📊 历史统计:",
            f"  - 总面试次数: {stats.get('total_interviews', len(history))}",
            f"  - 平均得分: {stats.get('average_score', 'N/A')}/10",
            f"  - 最高得分: {stats.get('best_score', 'N/A')}/10",
        ]
        
        if stats.get("recent_trend"):
            trend_map = {
                "improving": "📈 上升趋势",
                "stable": "➡️ 保持稳定",
                "declining": "📉 需要关注"
            }
            lines.append(f"  - 近期趋势: {trend_map.get(stats['recent_trend'], stats['recent_trend'])}")
        
        # 最近3次面试
        recent = history[-3:]
        lines.append(f"\n📋 最近 {len(recent)} 次面试:")
        for i, h in enumerate(recent, 1):
            decision = h.get('decision', 'N/A')
            score = h.get('final_score', 'N/A')
            lines.append(f"  {i}. 得分 {score}/10 - {decision}")
            if h.get('key_weaknesses'):
                lines.append(f"     主要问题: {', '.join(h['key_weaknesses'][:2])}")
        
        # 累积弱项
        top_weak = self.get_top_weaknesses(3)
        if top_weak:
            weak_str = ", ".join([f"{t[0]}({t[1]}次)" for t in top_weak])
            lines.append(f"\n⚠️ 累积弱项: {weak_str}")
        
        # 累积优势
        top_strong = self.get_top_strengths(3)
        if top_strong:
            strong_str = ", ".join([f"{t[0]}({t[1]}次)" for t in top_strong])
            lines.append(f"✅ 累积优势: {strong_str}")
        
        return "\n".join(lines)

    def get_practice_recommendations(self) -> List[str]:
        """基于历史弱项生成练习建议"""
        recommendations = []
        top_weak = self.get_top_weaknesses(5)
        
        # 弱项到建议的映射
        suggestion_map = {
            "结构不清晰": "练习使用 STAR 结构（情境-任务-行动-结果）组织回答",
            "统计基础薄弱": "复习假设检验、置信区间、回归分析等核心概念",
            "SQL细节欠缺": "刷 SQL 练习题，重点练习窗口函数和复杂查询",
            "缺少业务视角": "每次回答时想想「这对业务有什么影响」",
            "缺少落地结果": "准备项目案例时，确保包含可量化的业务结果",
            "沟通表达待加强": "练习简洁表达，避免冗长，突出重点",
            "案例准备不充分": "准备3-5个深度项目案例，用 STAR 结构梳理",
            "项目深度不够": "选择1-2个项目深入准备，能讲清楚每个细节",
            "缺乏数据思维": "培养用数据说话的习惯，多举有数字的例子",
            "实验设计不完整": "复习 A/B 测试流程，包括样本量计算和结果解读",
        }
        
        for tag, count in top_weak:
            if tag in suggestion_map:
                recommendations.append(f"【{tag}】{suggestion_map[tag]}")
            else:
                recommendations.append(f"【{tag}】建议针对性加强练习")
        
        return recommendations[:5]  # 最多5条

    def get_context_for_prompt(self) -> str:
        """
        获取用户上下文信息，用于生成面试问题
        
        Returns:
            用户历史信息摘要，供 Agent 参考
        """
        lines = []
        
        # 基本信息
        profile = self.data.get("profile", {})
        if profile.get("name"):
            lines.append(f"候选人: {profile['name']}")
        if profile.get("experience_years"):
            lines.append(f"工作经验: {profile['experience_years']} 年")
        if profile.get("skills"):
            lines.append(f"技能: {', '.join(profile['skills'][:5])}")
        
        # 历史统计
        stats = self.data.get("statistics", {})
        if stats.get("total_interviews", 0) > 0:
            lines.append(f"\n历史面试次数: {stats['total_interviews']}")
            if stats.get("average_score"):
                lines.append(f"平均得分: {stats['average_score']}/10")
            if stats.get("recent_trend"):
                trend_map = {"improving": "进步中", "stable": "稳定", "declining": "需加油"}
                lines.append(f"近期趋势: {trend_map.get(stats['recent_trend'], stats['recent_trend'])}")
        
        # 累积弱项（提示面试官关注）
        top_weak = self.get_top_weaknesses(3)
        if top_weak:
            weak_tags = [t[0] for t in top_weak]
            lines.append(f"\n历史弱项（可重点考察）: {', '.join(weak_tags)}")
        
        # 累积优势
        top_strong = self.get_top_strengths(3)
        if top_strong:
            strong_tags = [t[0] for t in top_strong]
            lines.append(f"历史优势: {', '.join(strong_tags)}")
        
        if not lines:
            return "新用户，暂无历史记录。"
        
        return "\n".join(lines)


class SessionMemory:
    """
    单次面试会话记忆
    
    记录:
    - 每轮问答详情
    - 各轮评分与反馈
    - 最终评估结果
    """

    def __init__(self, user_id: str, position: str = "数据分析师"):
        self.user_id = user_id
        self.position = position
        self.started_at = datetime.now().isoformat()
        self.rounds: List[Dict[str, Any]] = []
        self.final_evaluation: Optional[Dict[str, Any]] = None

    def add_round(
        self,
        role: str,
        question: str,
        answer: str,
        score: float,
        feedback: str,
        weakness_tags: List[str] = None,
        strength_tags: List[str] = None,
        key_points: List[str] = None,
        improvement_hint: str = "",
        is_follow_up: bool = False,
    ):
        """记录一轮面试"""
        self.rounds.append({
            "role": role,
            "question": question,
            "answer": answer,
            "score": score,
            "feedback": feedback,
            "weakness_tags": weakness_tags or [],
            "strength_tags": strength_tags or [],
            "key_points": key_points or [],
            "improvement_hint": improvement_hint,
            "is_follow_up": is_follow_up,
            "timestamp": datetime.now().isoformat(),
        })

    def set_final_evaluation(self, evaluation: Dict[str, Any]):
        """设置终面评审结果"""
        self.final_evaluation = evaluation

    def get_all_weakness_tags(self) -> List[str]:
        """获取本次面试所有弱项标签（去重）"""
        tags = []
        for r in self.rounds:
            tags.extend(r.get("weakness_tags", []))
        return list(set(tags))

    def get_all_strength_tags(self) -> List[str]:
        """获取本次面试所有优势标签（去重）"""
        tags = []
        for r in self.rounds:
            tags.extend(r.get("strength_tags", []))
        return list(set(tags))

    def get_average_score(self) -> float:
        """计算本次面试简单平均分"""
        scores = [r["score"] for r in self.rounds if r.get("score") is not None]
        return round(sum(scores) / len(scores), 2) if scores else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        return {
            "user_id": self.user_id,
            "position": self.position,
            "started_at": self.started_at,
            "ended_at": datetime.now().isoformat(),
            "rounds": self.rounds,
            "final_evaluation": self.final_evaluation,
            "summary": {
                "total_rounds": len(self.rounds),
                "main_rounds": len([r for r in self.rounds if not r.get("is_follow_up")]),
                "follow_up_rounds": len([r for r in self.rounds if r.get("is_follow_up")]),
                "average_score": self.get_average_score(),
                "all_weakness_tags": self.get_all_weakness_tags(),
                "all_strength_tags": self.get_all_strength_tags(),
            }
        }

    def save(self) -> str:
        """保存会话记录到文件"""
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = SESSIONS_DIR / f"{self.user_id}_{ts}.json"
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        
        return str(path)

    def get_context_for_next_round(self) -> str:
        """生成供下一轮面试官参考的上下文摘要"""
        if not self.rounds:
            return "这是本次面试的第一轮。"
        
        # 只看主轮次（不含追问）
        main_rounds = [r for r in self.rounds if not r.get("is_follow_up")]
        
        lines = ["前面轮次的面试情况摘要:"]
        for r in main_rounds[-3:]:  # 最近3轮
            lines.append(f"- {r['role']}轮: 得分 {r['score']}/10")
            if r.get("weakness_tags"):
                lines.append(f"  待改进: {', '.join(r['weakness_tags'][:2])}")
            if r.get("key_points"):
                lines.append(f"  关键点: {', '.join(r['key_points'][:2])}")
        
        return "\n".join(lines)

    def generate_round_summary(self, round_index: int) -> str:
        """生成指定轮次的摘要"""
        if round_index >= len(self.rounds):
            return ""
        
        r = self.rounds[round_index]
        lines = [
            f"【{r['role']}轮】",
            f"问题: {r['question'][:100]}...",
            f"得分: {r['score']}/10",
            f"反馈: {r['feedback']}",
        ]
        
        if r.get("improvement_hint"):
            lines.append(f"改进建议: {r['improvement_hint']}")
        
        return "\n".join(lines)

    def get_recent_context(self) -> str:
        """
        获取最近的面试上下文（别名方法）
        
        用于供下一轮面试官参考
        """
        return self.get_context_for_next_round()
