"""
Report Generator - 面试报告生成器
支持 Markdown、HTML 格式导出

功能:
- 完整面试报告导出
- 各轮次详细记录
- 评分可视化
- 个性化改进建议
"""
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from config import REPORTS_DIR, get_score_level, INTERVIEW_ROUNDS_CONFIG


class ReportGenerator:
    """面试报告生成器"""
    
    def __init__(self):
        self.reports_dir = REPORTS_DIR
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_markdown_report(
        self,
        session_data: Dict[str, Any],
        user_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        生成 Markdown 格式的面试报告
        
        Args:
            session_data: 会话数据（from session.to_dict()）
            user_data: 用户档案数据（可选）
            
        Returns:
            Markdown 格式的报告内容
        """
        final_eval = session_data.get("final_evaluation", {})
        summary = session_data.get("summary", {})
        rounds = session_data.get("rounds", [])
        
        score = final_eval.get("final_score", summary.get("average_score", "N/A"))
        score_info = get_score_level(score) if isinstance(score, (int, float)) else {}
        
        report = []
        
        # 标题
        report.append(f"# 🎯 AI 模拟面试报告")
        report.append("")
        report.append(f"**候选人 ID**: {session_data.get('user_id', 'Unknown')}")
        report.append(f"**目标岗位**: {session_data.get('position', '数据分析师')}")
        report.append(f"**面试时间**: {session_data.get('started_at', '')[:10]}")
        report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append("")
        
        # 总评
        report.append("---")
        report.append("## 📊 总体评估")
        report.append("")
        
        emoji = score_info.get("emoji", "📊")
        level = score_info.get("level", "")
        decision = final_eval.get("decision", score_info.get("decision", ""))
        
        report.append(f"### {emoji} 综合得分: {score}/10 ({level})")
        report.append("")
        report.append(f"**面试结论**: {decision}")
        report.append("")
        
        if final_eval.get("decision_reason"):
            report.append(f"**决策理由**: {final_eval['decision_reason']}")
            report.append("")
        
        if final_eval.get("overall_feedback"):
            report.append(f"**整体评价**: {final_eval['overall_feedback']}")
            report.append("")
        
        # 维度得分
        dim_scores = final_eval.get("dimension_scores", {})
        if dim_scores:
            report.append("### 📈 各维度得分")
            report.append("")
            report.append("| 维度 | 得分 | 评级 |")
            report.append("|------|------|------|")
            for dim, score in dim_scores.items():
                dim_info = get_score_level(score) if isinstance(score, (int, float)) else {}
                report.append(f"| {dim} | {score}/10 | {dim_info.get('level', '')} |")
            report.append("")
        
        # 优势与待改进
        report.append("### ✅ 关键优势")
        report.append("")
        for s in final_eval.get("key_strengths", []):
            report.append(f"- {s}")
        report.append("")
        
        report.append("### ⚠️ 待改进点")
        report.append("")
        for w in final_eval.get("key_weaknesses", []):
            report.append(f"- {w}")
        report.append("")
        
        # 各轮详情
        report.append("---")
        report.append("## 📝 各轮面试详情")
        report.append("")
        
        for i, r in enumerate(rounds):
            if r.get("is_follow_up"):
                continue  # 追问合并到主轮次
            
            role = r.get("role", "Unknown")
            role_config = INTERVIEW_ROUNDS_CONFIG.get(role, {})
            role_name = role_config.get("name", role)
            
            report.append(f"### {i+1}. {role_name}")
            report.append("")
            report.append(f"**得分**: {r.get('score', 'N/A')}/10")
            report.append("")
            report.append(f"**面试问题**:")
            report.append(f"> {r.get('question', '')}")
            report.append("")
            report.append(f"**你的回答**:")
            report.append(f"> {r.get('answer', '')}")
            report.append("")
            report.append(f"**面试官反馈**: {r.get('feedback', '')}")
            report.append("")
            
            if r.get("improvement_hint"):
                report.append(f"**改进建议**: {r['improvement_hint']}")
                report.append("")
            
            if r.get("weakness_tags"):
                report.append(f"**弱项标签**: {', '.join(r['weakness_tags'])}")
            if r.get("strength_tags"):
                report.append(f"**优势标签**: {', '.join(r['strength_tags'])}")
            report.append("")
        
        # 改进建议
        report.append("---")
        report.append("## 💡 改进建议")
        report.append("")
        
        for i, sug in enumerate(final_eval.get("improvement_suggestions", []), 1):
            report.append(f"{i}. {sug}")
        report.append("")
        
        if final_eval.get("practice_focus"):
            report.append("### 🎯 重点练习方向")
            report.append("")
            for focus in final_eval["practice_focus"]:
                report.append(f"- {focus}")
            report.append("")
        
        if final_eval.get("next_steps"):
            report.append("### 📌 下一步行动")
            report.append("")
            report.append(final_eval["next_steps"])
            report.append("")
        
        # 历史对比
        if final_eval.get("comparative_analysis"):
            report.append("---")
            report.append("## 📈 历史对比分析")
            report.append("")
            report.append(final_eval["comparative_analysis"])
            report.append("")
        
        # 页脚
        report.append("---")
        report.append("*本报告由 AI Multi-Agent Interview Simulator 自动生成*")
        
        return "\n".join(report)

    def save_report(
        self,
        session_data: Dict[str, Any],
        user_data: Optional[Dict[str, Any]] = None,
        format: str = "markdown",
    ) -> str:
        """
        保存面试报告到文件
        
        Args:
            session_data: 会话数据
            user_data: 用户数据
            format: 格式 (markdown / html / json)
            
        Returns:
            保存的文件路径
        """
        user_id = session_data.get("user_id", "unknown")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "markdown":
            content = self.generate_markdown_report(session_data, user_data)
            filename = f"{user_id}_{ts}_report.md"
        elif format == "html":
            md_content = self.generate_markdown_report(session_data, user_data)
            content = self._markdown_to_html(md_content)
            filename = f"{user_id}_{ts}_report.html"
        else:  # json
            import json
            content = json.dumps(session_data, ensure_ascii=False, indent=2)
            filename = f"{user_id}_{ts}_report.json"
        
        filepath = self.reports_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        return str(filepath)

    def _markdown_to_html(self, md_content: str) -> str:
        """简单的 Markdown 转 HTML（不依赖外部库）"""
        html_lines = [
            "<!DOCTYPE html>",
            "<html lang='zh-CN'>",
            "<head>",
            "  <meta charset='UTF-8'>",
            "  <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            "  <title>AI 模拟面试报告</title>",
            "  <style>",
            "    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; ",
            "           max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }",
            "    h1, h2, h3 { color: #333; }",
            "    blockquote { border-left: 3px solid #ddd; margin: 0; padding-left: 15px; color: #666; }",
            "    table { border-collapse: collapse; width: 100%; margin: 15px 0; }",
            "    th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }",
            "    th { background: #f5f5f5; }",
            "    hr { border: none; border-top: 1px solid #eee; margin: 30px 0; }",
            "    .score { font-size: 24px; font-weight: bold; color: #2196F3; }",
            "  </style>",
            "</head>",
            "<body>",
        ]
        
        # 简单转换
        lines = md_content.split("\n")
        in_list = False
        in_table = False
        
        for line in lines:
            # 标题
            if line.startswith("# "):
                html_lines.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("## "):
                html_lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("### "):
                html_lines.append(f"<h3>{line[4:]}</h3>")
            # 粗体
            elif line.startswith("**") and "**:" in line:
                parts = line.split("**:")
                key = parts[0].replace("**", "")
                value = parts[1] if len(parts) > 1 else ""
                html_lines.append(f"<p><strong>{key}:</strong>{value}</p>")
            # 引用
            elif line.startswith("> "):
                html_lines.append(f"<blockquote>{line[2:]}</blockquote>")
            # 分隔线
            elif line.strip() == "---":
                html_lines.append("<hr>")
            # 表格
            elif line.startswith("|"):
                if not in_table:
                    html_lines.append("<table>")
                    in_table = True
                if "---" not in line:
                    cells = [c.strip() for c in line.split("|")[1:-1]]
                    tag = "th" if not any("<td>" in l for l in html_lines[-5:]) else "td"
                    html_lines.append("<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in cells) + "</tr>")
            elif in_table and not line.startswith("|"):
                html_lines.append("</table>")
                in_table = False
            # 列表
            elif line.startswith("- "):
                if not in_list:
                    html_lines.append("<ul>")
                    in_list = True
                html_lines.append(f"<li>{line[2:]}</li>")
            elif line.startswith(("1.", "2.", "3.", "4.", "5.")):
                if not in_list:
                    html_lines.append("<ol>")
                    in_list = True
                html_lines.append(f"<li>{line[3:]}</li>")
            elif in_list and not line.strip():
                html_lines.append("</ul>" if "ul" in "".join(html_lines[-10:]) else "</ol>")
                in_list = False
            # 普通段落
            elif line.strip():
                html_lines.append(f"<p>{line}</p>")
        
        html_lines.extend(["</body>", "</html>"])
        return "\n".join(html_lines)


def print_report_to_console(session_data: Dict[str, Any]):
    """在控制台打印简化版报告"""
    final_eval = session_data.get("final_evaluation", {})
    summary = session_data.get("summary", {})
    
    score = final_eval.get("final_score", summary.get("average_score", "N/A"))
    score_info = get_score_level(score) if isinstance(score, (int, float)) else {}
    
    print("\n" + "="*60)
    print("📊 面试报告摘要")
    print("="*60)
    
    print(f"\n{score_info.get('emoji', '📊')} 综合得分: {score}/10 ({score_info.get('level', '')})")
    print(f"📋 面试结论: {final_eval.get('decision', 'N/A')}")
    
    if final_eval.get("overall_feedback"):
        print(f"\n💬 整体评价:\n   {final_eval['overall_feedback']}")
    
    if final_eval.get("key_strengths"):
        print(f"\n✅ 关键优势:")
        for s in final_eval["key_strengths"]:
            print(f"   • {s}")
    
    if final_eval.get("key_weaknesses"):
        print(f"\n⚠️ 待改进点:")
        for w in final_eval["key_weaknesses"]:
            print(f"   • {w}")
    
    if final_eval.get("improvement_suggestions"):
        print(f"\n💡 改进建议:")
        for i, sug in enumerate(final_eval["improvement_suggestions"], 1):
            print(f"   {i}. {sug}")
    
    if final_eval.get("next_steps"):
        print(f"\n🎯 下一步: {final_eval['next_steps']}")
    
    print("\n" + "="*60)
