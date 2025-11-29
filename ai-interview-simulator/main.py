"""
AI Multi-Agent Interview Simulator for Data Analyst
数据分析师多面试官智能面试模拟器

主程序入口 - 增强命令行交互版本

功能:
- 完整多轮面试流程
- 实时评分反馈
- 智能追问
- 面试报告生成
- 历史记录追踪
"""
import sys
import os
from typing import Dict, Any, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.workflow import InterviewWorkflow
from core.memory import UserMemory
from core.report import ReportGenerator, print_report_to_console
from config import (
    DEFAULT_POSITION, QWEN_API_KEY, INTERVIEW_ROUNDS_CONFIG,
    get_score_level, OUTPUT_CONFIG
)


class InterviewCLI:
    """命令行面试界面"""
    
    def __init__(self):
        self.workflow: Optional[InterviewWorkflow] = None
        self.current_round = 0
        self.total_rounds = len([r for r in INTERVIEW_ROUNDS_CONFIG if r != "Committee"])
    
    def print_banner(self):
        """打印欢迎横幅"""
        banner = """
╔════════════════════════════════════════════════════════════════════════╗
║       🎯 AI Multi-Agent Interview Simulator for Data Analyst 🎯        ║
║                   数据分析师多面试官智能面试模拟器                       ║
╠════════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║   📋 面试流程:                                                         ║
║      HR初筛 → 业务经理面 → 技术面 → 文化契合度面 → 终面评审            ║
║                                                                        ║
║   ✨ 特色功能:                                                         ║
║      • 多角色 AI 面试官，模拟真实面试场景                              ║
║      • 每轮即时评分 + 专业反馈 + 改进建议                              ║
║      • 智能追问，深挖你的回答                                          ║
║      • 长期记录追踪，分析你的成长轨迹                                  ║
║      • 完整面试报告导出                                                ║
║                                                                        ║
╚════════════════════════════════════════════════════════════════════════╝
"""
        print(banner)

    def print_divider(self, title: str = "", char: str = "═"):
        """打印分隔线"""
        width = 70
        if title:
            padding = (width - len(title) - 2) // 2
            print(f"\n{char*padding} {title} {char*padding}\n")
        else:
            print(f"\n{char*width}\n")

    def print_progress_bar(self, current: int, total: int, label: str = ""):
        """打印进度条"""
        filled = int(current / total * 20)
        bar = "█" * filled + "░" * (20 - filled)
        percent = int(current / total * 100)
        print(f"\n📊 面试进度: [{bar}] {percent}% ({current}/{total}) {label}")

    def check_api_key(self) -> bool:
        """检查 API Key 是否配置"""
        if QWEN_API_KEY == "your-api-key-here" or not QWEN_API_KEY:
            print("\n⚠️  警告: 未配置 Qwen API Key!")
            print("   请在 config.py 中设置 QWEN_API_KEY")
            print("   获取地址: https://dashscope.console.aliyun.com/")
            print()
            response = input("是否继续运行（将使用模拟响应）？[y/N]: ").strip().lower()
            return response == 'y'
        return True

    def get_user_id(self) -> str:
        """获取用户 ID"""
        print("\n请输入你的用户 ID（用于保存面试记录和追踪进步）:")
        print("（如果是第一次使用，输入新 ID 即可创建账户）")
        user_id = input("\n👤 User ID: ").strip()
        
        if not user_id:
            user_id = "guest"
            print(f"[系统] 使用默认 ID: {user_id}")
        
        return user_id

    def show_user_history(self, user_id: str):
        """显示用户历史记录"""
        user_memory = UserMemory(user_id)
        stats = user_memory.data.get("statistics", {})
        
        if stats.get("total_interviews", 0) > 0:
            print(f"\n📊 你的历史记录:")
            print(f"   • 总面试次数: {stats.get('total_interviews', 0)}")
            print(f"   • 平均得分: {stats.get('average_score', 'N/A')}/10")
            print(f"   • 最高得分: {stats.get('best_score', 'N/A')}/10")
            
            if stats.get("recent_trend"):
                trend_map = {
                    "improving": "📈 进步中",
                    "stable": "➡️ 保持稳定", 
                    "declining": "📉 需要加油"
                }
                print(f"   • 近期趋势: {trend_map.get(stats['recent_trend'], stats['recent_trend'])}")
            
            if stats.get("most_common_weakness"):
                print(f"   • 主要弱项: {stats['most_common_weakness']}")
            
            # 显示练习建议
            recommendations = user_memory.get_practice_recommendations()
            if recommendations:
                print(f"\n💡 基于历史的练习建议:")
                for rec in recommendations[:3]:
                    print(f"   • {rec}")
        else:
            print(f"\n👋 欢迎新用户 {user_id}！这是你的第一次模拟面试。")

    def show_menu(self) -> str:
        """显示菜单并获取选择"""
        print("\n请选择面试模式:")
        print("  [1] 完整面试 - 体验全部 5 轮面试流程")
        print("  [2] 快速练习 - 选择特定轮次进行针对性练习")
        print("  [3] 查看历史 - 查看过往面试记录和建议")
        print("  [q] 退出")
        
        choice = input("\n请输入选项: ").strip().lower()
        return choice

    def select_practice_round(self) -> Optional[str]:
        """选择练习轮次"""
        print("\n选择要练习的面试轮次:")
        print("  [1] HR 初筛 - 求职动机、职业规划")
        print("  [2] 业务经理面 - 项目经历、业务理解")
        print("  [3] 技术面 - SQL、统计、Python、实验设计")
        print("  [4] 文化契合度 - 团队协作、价值观")
        print("  [b] 返回主菜单")
        
        choice = input("\n请输入选项: ").strip().lower()
        
        mapping = {
            "1": "HR",
            "2": "HiringManager", 
            "3": "Technical",
            "4": "CultureFit",
        }
        
        return mapping.get(choice)

    def on_round_start(self, round_key: str, round_name: str):
        """轮次开始回调"""
        self.current_round += 1
        self.print_progress_bar(self.current_round, self.total_rounds + 1, round_name)
        self.print_divider(f"📋 {round_name}")
        
        # 显示轮次说明
        config = INTERVIEW_ROUNDS_CONFIG.get(round_key, {})
        weight = config.get("weight", 0)
        if weight > 0:
            print(f"[系统] 本轮权重: {weight*100:.0f}%")

    def on_question(self, question: str, round_name: str):
        """问题展示回调"""
        print(f"\n🎤 {round_name}面试官提问:")
        print(f"   {question}")

    def on_evaluation(self, evaluation: Dict[str, Any]):
        """评估完成回调"""
        if not OUTPUT_CONFIG.get("show_score_realtime", True):
            return
        
        score = evaluation.get("score", 0)
        score_info = get_score_level(score)
        feedback = evaluation.get("feedback", "")
        weakness = evaluation.get("weakness_tags", [])
        strength = evaluation.get("strength_tags", [])
        hint = evaluation.get("improvement_hint", "")
        
        print(f"\n{'─'*60}")
        print(f"{score_info['emoji']} 本轮评分: {score}/10 ({score_info['level']})")
        print(f"💬 反馈: {feedback}")
        
        if OUTPUT_CONFIG.get("show_tags_realtime", True):
            if strength:
                print(f"✅ 优势: {', '.join(strength)}")
            if weakness:
                print(f"⚠️ 待改进: {', '.join(weakness)}")
        
        if hint:
            print(f"💡 建议: {hint}")
        
        print(f"{'─'*60}")

    def on_follow_up(self, reason: str):
        """追问通知回调"""
        print(f"\n🔄 [追问] {reason}")
        print("   面试官将进一步了解你的回答...")

    def on_final_evaluation(self, evaluation: Dict[str, Any]):
        """最终评估回调"""
        self.print_divider("🏆 终面评审委员会最终评估")
        print_report_to_console({"final_evaluation": evaluation, "summary": {}})

    def get_user_answer(self, question: str, round_name: str) -> str:
        """获取用户回答"""
        print(f"\n📝 请输入你的回答:")
        print("   (输入完成后按回车提交，输入 'skip' 跳过此问题)")
        print()
        
        lines = []
        try:
            while True:
                line = input()
                if line.lower() == 'skip':
                    return "（候选人选择跳过此问题）"
                if line == "" and lines:
                    # 空行结束输入
                    break
                lines.append(line)
                if not lines[-1]:  # 连续空行结束
                    break
        except EOFError:
            pass
        
        answer = "\n".join(lines).strip()
        
        if not answer:
            answer = "（候选人未作答）"
        
        return answer

    def run_full_interview(self, user_id: str):
        """运行完整面试"""
        self.current_round = 0
        
        print(f"\n[系统] 正在为 {user_id} 准备面试...")
        print(f"[系统] 目标岗位: {DEFAULT_POSITION}")
        print("\n💡 面试技巧:")
        print("   • 使用 STAR 结构回答行为问题（情境-任务-行动-结果）")
        print("   • 尽量用具体数字和案例支撑你的回答")
        print("   • 如实回答，不要编造经历")
        
        input("\n按回车键开始面试...")
        
        self.workflow = InterviewWorkflow()
        
        try:
            session_path = self.workflow.run_full_interview(
                user_id=user_id,
                get_user_answer=self.get_user_answer,
                on_round_start=self.on_round_start,
                on_question=self.on_question,
                on_evaluation=self.on_evaluation,
                on_follow_up=self.on_follow_up,
                on_final_evaluation=self.on_final_evaluation,
            )
            
            self.print_divider("面试结束")
            print(f"✅ 面试记录已保存: {session_path}")
            
            # 询问是否导出报告
            if OUTPUT_CONFIG.get("export_report", True):
                export = input("\n是否导出完整面试报告？[Y/n]: ").strip().lower()
                if export != 'n':
                    self.export_report(session_path)
            
            print(f"\n📁 你的长期档案: storage/users/{user_id}.json")
            print("\n🎉 感谢参与模拟面试！祝你求职顺利！\n")
            
        except KeyboardInterrupt:
            print("\n\n[系统] 面试已中断。")

    def run_quick_practice(self, user_id: str, round_type: str):
        """运行快速练习"""
        round_config = INTERVIEW_ROUNDS_CONFIG.get(round_type, {})
        round_name = round_config.get("name", round_type)
        
        print(f"\n[系统] 开始 {round_name} 快速练习...")
        
        self.workflow = InterviewWorkflow()
        
        try:
            result = self.workflow.run_quick_practice(
                user_id=user_id,
                round_type=round_type,
                get_user_answer=self.get_user_answer,
                on_question=self.on_question,
                on_evaluation=self.on_evaluation,
            )
            
            print(f"\n✅ 练习完成！本轮得分: {result.get('final_score', 'N/A')}/10")
            
        except KeyboardInterrupt:
            print("\n\n[系统] 练习已中断。")

    def export_report(self, session_path: str):
        """导出面试报告"""
        import json
        
        try:
            with open(session_path, "r", encoding="utf-8") as f:
                session_data = json.load(f)
            
            generator = ReportGenerator()
            report_path = generator.save_report(
                session_data,
                format=OUTPUT_CONFIG.get("report_format", "markdown")
            )
            print(f"📄 报告已导出: {report_path}")
            
        except Exception as e:
            print(f"⚠️ 报告导出失败: {e}")

    def show_history(self, user_id: str):
        """显示详细历史记录"""
        user_memory = UserMemory(user_id)
        
        self.print_divider(f"📊 {user_id} 的面试历史")
        
        print(user_memory.get_history_summary())
        
        recommendations = user_memory.get_practice_recommendations()
        if recommendations:
            print(f"\n💡 个性化练习建议:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")

    def run(self):
        """运行主程序"""
        self.print_banner()
        
        if not self.check_api_key():
            return
        
        user_id = self.get_user_id()
        self.show_user_history(user_id)
        
        while True:
            choice = self.show_menu()
            
            if choice == '1':
                self.run_full_interview(user_id)
            elif choice == '2':
                round_type = self.select_practice_round()
                if round_type:
                    self.run_quick_practice(user_id, round_type)
            elif choice == '3':
                self.show_history(user_id)
            elif choice == 'q':
                print("\n👋 再见！祝你面试顺利！\n")
                break
            else:
                print("\n⚠️ 无效选项，请重新选择。")


def main():
    """主入口"""
    cli = InterviewCLI()
    
    try:
        cli.run()
    except KeyboardInterrupt:
        print("\n\n👋 再见！")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 程序出错: {e}")
        if os.environ.get("DEBUG"):
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()
