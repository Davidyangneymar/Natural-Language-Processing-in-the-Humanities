/**
 * AI Interview Simulator - Index Page JS
 * 首页交互逻辑
 */

document.addEventListener('DOMContentLoaded', function() {
    // 元素引用
    const userIdInput = document.getElementById('user-id');
    const userStats = document.getElementById('user-stats');
    const recommendations = document.getElementById('recommendations');
    const recList = document.getElementById('rec-list');
    const modeOptions = document.querySelectorAll('.mode-option');
    const practiceOptions = document.getElementById('practice-options');
    const startBtn = document.getElementById('start-btn');
    const apiStatus = document.getElementById('api-status');

    // 状态
    let selectedMode = 'full';
    let debounceTimer = null;

    // 检查 API 状态
    checkApiStatus();

    // 用户 ID 输入事件（防抖）
    userIdInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            const userId = this.value.trim();
            if (userId) {
                loadUserStats(userId);
            } else {
                userStats.classList.add('hidden');
            }
        }, 500);
    });

    // 模式选择
    modeOptions.forEach(option => {
        option.addEventListener('click', function() {
            modeOptions.forEach(o => o.classList.remove('selected'));
            this.classList.add('selected');
            this.querySelector('input').checked = true;
            
            selectedMode = this.dataset.mode;
            
            if (selectedMode === 'practice') {
                practiceOptions.classList.remove('hidden');
            } else {
                practiceOptions.classList.add('hidden');
            }
        });
    });

    // 开始面试按钮
    startBtn.addEventListener('click', function() {
        const userId = userIdInput.value.trim() || 'guest';
        const mode = selectedMode;
        let practiceRound = null;

        if (mode === 'practice') {
            const selectedRound = document.querySelector('input[name="practice_round"]:checked');
            practiceRound = selectedRound ? selectedRound.value : 'Technical';
        }

        // 保存到 sessionStorage
        sessionStorage.setItem('interview_user_id', userId);
        sessionStorage.setItem('interview_mode', mode);
        if (practiceRound) {
            sessionStorage.setItem('interview_practice_round', practiceRound);
        }

        // 跳转到面试页面
        window.location.href = '/interview';
    });

    // 检查 API 状态
    async function checkApiStatus() {
        try {
            const response = await fetch('/api/check_api_key');
            const data = await response.json();
            
            const statusDot = apiStatus.querySelector('.status-dot');
            const statusText = apiStatus.querySelector('.status-text');
            
            if (data.configured) {
                apiStatus.classList.add('connected');
                statusText.textContent = `API 已连接 (${data.model})`;
            } else {
                apiStatus.classList.add('mock');
                statusText.textContent = '⚠️ 模拟模式 (未配置 API Key)';
            }
        } catch (error) {
            console.error('检查 API 状态失败:', error);
        }
    }

    // 加载用户统计
    async function loadUserStats(userId) {
        try {
            const response = await fetch(`/api/user/${encodeURIComponent(userId)}`);
            const data = await response.json();
            
            if (data.success && data.statistics.total_interviews > 0) {
                // 显示统计
                document.getElementById('stat-total').textContent = data.statistics.total_interviews || 0;
                document.getElementById('stat-avg').textContent = data.statistics.average_score || '-';
                document.getElementById('stat-best').textContent = data.statistics.best_score || '-';
                
                const trendMap = {
                    'improving': '📈 进步中',
                    'stable': '➡️ 稳定',
                    'declining': '📉 需加油'
                };
                document.getElementById('stat-trend').textContent = 
                    trendMap[data.statistics.recent_trend] || '-';
                
                userStats.classList.remove('hidden');
                
                // 显示建议
                if (data.recommendations && data.recommendations.length > 0) {
                    recList.innerHTML = data.recommendations
                        .slice(0, 3)
                        .map(rec => `<li>${rec}</li>`)
                        .join('');
                    recommendations.classList.remove('hidden');
                } else {
                    recommendations.classList.add('hidden');
                }
            } else {
                userStats.classList.add('hidden');
            }
        } catch (error) {
            console.error('加载用户统计失败:', error);
            userStats.classList.add('hidden');
        }
    }
});
