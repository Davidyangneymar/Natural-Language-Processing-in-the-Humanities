/**
 * AI Interview Simulator - Report Page JS
 * 报告页面交互逻辑
 */

document.addEventListener('DOMContentLoaded', function() {
    // 从 URL 获取 session_id
    const pathParts = window.location.pathname.split('/');
    const sessionId = pathParts[pathParts.length - 1];

    if (sessionId) {
        loadReport(sessionId);
    }

    // 导出按钮
    document.getElementById('export-md-btn').addEventListener('click', () => exportReport('markdown'));
    document.getElementById('export-html-btn').addEventListener('click', () => exportReport('html'));
    document.getElementById('print-btn').addEventListener('click', () => window.print());

    async function loadReport(sessionId) {
        try {
            const response = await fetch(`/api/report/${sessionId}`);
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error);
            }

            renderReport(data.session_data);
        } catch (error) {
            console.error('加载报告失败:', error);
            alert('加载报告失败: ' + error.message);
        }
    }

    function renderReport(sessionData) {
        const finalEval = sessionData.final_evaluation || {};
        const summary = sessionData.summary || {};
        const rounds = sessionData.rounds || [];

        // 基本信息
        document.getElementById('report-user').textContent = `候选人: ${sessionData.user_id || '-'}`;
        document.getElementById('report-position').textContent = `岗位: ${sessionData.position || '数据分析师'}`;
        document.getElementById('report-date').textContent = `时间: ${formatDate(sessionData.started_at)}`;
        document.getElementById('generate-time').textContent = `生成时间: ${new Date().toLocaleString('zh-CN')}`;

        // 总评
        const score = finalEval.final_score || summary.average_score || 0;
        const scoreInfo = getScoreLevel(score);
        
        document.getElementById('summary-emoji').textContent = scoreInfo.emoji;
        document.getElementById('summary-score').textContent = score;
        document.getElementById('summary-level').textContent = scoreInfo.level;
        document.getElementById('summary-decision-text').textContent = finalEval.decision || scoreInfo.decision;
        document.getElementById('summary-feedback-text').textContent = finalEval.overall_feedback || '-';

        // 各维度得分
        const dimScores = finalEval.dimension_scores || {};
        const dimensionsChart = document.getElementById('dimensions-chart');
        dimensionsChart.innerHTML = Object.entries(dimScores)
            .map(([dim, score]) => `
                <div class="dimension-item">
                    <span class="dimension-name">${dim}</span>
                    <div class="dimension-bar-container">
                        <div class="dimension-bar" style="width: ${score * 10}%"></div>
                    </div>
                    <span class="dimension-score">${score}/10</span>
                </div>
            `).join('');

        // 优势
        const strengthsList = document.getElementById('strengths-list');
        strengthsList.innerHTML = (finalEval.key_strengths || [])
            .map(s => `<li>${s}</li>`).join('') || '<li>-</li>';

        // 弱项
        const weaknessesList = document.getElementById('weaknesses-list');
        weaknessesList.innerHTML = (finalEval.key_weaknesses || [])
            .map(w => `<li>${w}</li>`).join('') || '<li>-</li>';

        // 各轮详情
        const roundsList = document.getElementById('rounds-list');
        const roleNames = {
            'HR': 'HR 初筛',
            'HiringManager': '业务经理面',
            'Technical': '技术面',
            'CultureFit': '文化契合度面',
            'Committee': '终面评审'
        };
        
        roundsList.innerHTML = rounds
            .filter(r => !r.is_follow_up)
            .map((r, i) => `
                <div class="round-detail">
                    <div class="round-detail-header">
                        <h4>${i + 1}. ${roleNames[r.role] || r.role}</h4>
                        <span class="round-detail-score">${r.score || '-'}/10</span>
                    </div>
                    <div class="round-qa">
                        <h5>面试问题</h5>
                        <p>${r.question || '-'}</p>
                    </div>
                    <div class="round-qa">
                        <h5>你的回答</h5>
                        <p>${r.answer || '-'}</p>
                    </div>
                    <div class="round-feedback">
                        <strong>反馈:</strong> ${r.feedback || '-'}
                    </div>
                </div>
            `).join('');

        // 改进建议
        const suggestionsList = document.getElementById('suggestions-list');
        suggestionsList.innerHTML = (finalEval.improvement_suggestions || [])
            .map(s => `<li>${s}</li>`).join('') || '<li>暂无建议</li>';
    }

    async function exportReport(format) {
        const pathParts = window.location.pathname.split('/');
        const sessionId = pathParts[pathParts.length - 1];

        try {
            const response = await fetch(`/api/export_report/${sessionId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ format: format })
            });
            const data = await response.json();

            if (data.success) {
                alert(`报告已导出到: ${data.filepath}`);
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            console.error('导出失败:', error);
            alert('导出失败: ' + error.message);
        }
    }

    function formatDate(dateStr) {
        if (!dateStr) return '-';
        return new Date(dateStr).toLocaleString('zh-CN');
    }

    function getScoreLevel(score) {
        if (score >= 9) return { level: '卓越', emoji: '🌟', decision: '强烈推荐录用' };
        if (score >= 8) return { level: '优秀', emoji: '⭐', decision: '推荐录用' };
        if (score >= 7) return { level: '良好', emoji: '👍', decision: '建议录用' };
        if (score >= 6) return { level: '合格', emoji: '✅', decision: '可考虑录用' };
        if (score >= 5) return { level: '待提升', emoji: '📈', decision: '暂不建议录用' };
        return { level: '需加强', emoji: '💪', decision: '不建议录用' };
    }
});
