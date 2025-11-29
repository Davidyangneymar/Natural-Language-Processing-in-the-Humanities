/**
 * AI Interview Simulator - History Page JS
 * 历史记录页面交互逻辑
 */

document.addEventListener('DOMContentLoaded', function() {
    const userIdInput = document.getElementById('history-user-id');
    const loadHistoryBtn = document.getElementById('load-history-btn');
    const historyStats = document.getElementById('history-stats');
    const historyRecommendations = document.getElementById('history-recommendations');
    const historyListSection = document.getElementById('history-list-section');
    const historyList = document.getElementById('history-list');
    const emptyState = document.getElementById('empty-state');

    // 加载历史
    loadHistoryBtn.addEventListener('click', loadHistory);
    
    // 回车键加载
    userIdInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            loadHistory();
        }
    });

    async function loadHistory() {
        const userId = userIdInput.value.trim();
        if (!userId) {
            alert('请输入用户 ID');
            return;
        }

        try {
            const response = await fetch(`/api/user/${encodeURIComponent(userId)}`);
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error);
            }

            document.getElementById('history-user-name').textContent = userId;

            if (data.statistics.total_interviews > 0) {
                // 显示统计
                document.getElementById('h-stat-total').textContent = data.statistics.total_interviews || 0;
                document.getElementById('h-stat-avg').textContent = data.statistics.average_score || '-';
                document.getElementById('h-stat-best').textContent = data.statistics.best_score || '-';
                
                const trendMap = {
                    'improving': '进步中',
                    'stable': '稳定',
                    'declining': '需加油'
                };
                const trendIconMap = {
                    'improving': '📈',
                    'stable': '➡️',
                    'declining': '📉'
                };
                
                document.getElementById('h-stat-trend').textContent = 
                    trendMap[data.statistics.recent_trend] || '-';
                document.getElementById('h-trend-icon').textContent = 
                    trendIconMap[data.statistics.recent_trend] || '📊';

                historyStats.classList.remove('hidden');

                // 显示建议
                if (data.recommendations && data.recommendations.length > 0) {
                    document.getElementById('h-rec-list').innerHTML = 
                        data.recommendations.map(rec => `<li>${rec}</li>`).join('');
                    historyRecommendations.classList.remove('hidden');
                } else {
                    historyRecommendations.classList.add('hidden');
                }

                // 显示历史列表
                if (data.history && data.history.length > 0) {
                    historyList.innerHTML = data.history
                        .slice()
                        .reverse()
                        .map(item => createHistoryItem(item))
                        .join('');
                    historyListSection.classList.remove('hidden');
                } else {
                    historyListSection.classList.add('hidden');
                }

                emptyState.classList.add('hidden');
            } else {
                historyStats.classList.add('hidden');
                historyRecommendations.classList.add('hidden');
                historyListSection.classList.add('hidden');
                emptyState.classList.remove('hidden');
            }
        } catch (error) {
            console.error('加载历史失败:', error);
            alert('加载历史失败: ' + error.message);
        }
    }

    function createHistoryItem(item) {
        const date = item.timestamp ? new Date(item.timestamp).toLocaleString('zh-CN') : '-';
        const score = item.final_score || item.weighted_score || '-';
        const decision = item.decision || '';
        
        const scoreClass = score >= 7 ? 'good' : (score >= 5 ? 'average' : 'poor');
        
        return `
            <div class="history-item">
                <div class="history-item-info">
                    <div class="history-item-score ${scoreClass}">${score}</div>
                    <div class="history-item-meta">
                        <h4>${decision || '模拟面试'}</h4>
                        <p>${date} · ${item.rounds_count || 0} 轮</p>
                    </div>
                </div>
            </div>
        `;
    }
});
