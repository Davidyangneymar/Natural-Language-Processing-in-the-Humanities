/**
 * AI Interview Simulator - Interview Page JS
 * 面试页面交互逻辑
 */

document.addEventListener('DOMContentLoaded', function() {
    // 从 sessionStorage 获取参数
    const userId = sessionStorage.getItem('interview_user_id') || 'guest';
    const mode = sessionStorage.getItem('interview_mode') || 'full';
    const practiceRound = sessionStorage.getItem('interview_practice_round');

    // 元素引用
    const userDisplay = document.getElementById('user-display');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const chatContainer = document.getElementById('chat-container');
    const answerInput = document.getElementById('answer-input');
    const submitBtn = document.getElementById('submit-btn');
    const skipBtn = document.getElementById('skip-btn');
    const endInterviewBtn = document.getElementById('end-interview-btn');
    const inputHint = document.getElementById('input-hint');
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingText = document.getElementById('loading-text');
    const finalModal = document.getElementById('final-modal');

    // 评估面板元素
    const evaluationContent = document.getElementById('evaluation-content');
    const evaluationResult = document.getElementById('evaluation-result');

    // 状态
    let socket = null;
    let currentRound = null;
    let totalRounds = 5;
    let completedRounds = 0;
    let sessionId = null;

    // 初始化显示
    userDisplay.textContent = `用户: ${userId}`;

    // 连接 WebSocket
    initSocket();

    // 提交回答
    submitBtn.addEventListener('click', submitAnswer);
    
    // Ctrl+Enter 提交
    answerInput.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.key === 'Enter') {
            e.preventDefault();
            submitAnswer();
        }
    });

    // 跳过问题
    skipBtn.addEventListener('click', function() {
        if (socket && socket.connected) {
            socket.emit('skip_question', {});
            disableInput();
        }
    });

    // 结束面试
    endInterviewBtn.addEventListener('click', function() {
        if (confirm('确定要提前结束面试吗？')) {
            if (socket && socket.connected) {
                socket.emit('end_interview', {});
            }
        }
    });

    // 初始化 WebSocket
    function initSocket() {
        socket = io();

        socket.on('connect', function() {
            console.log('WebSocket 已连接');
            addSystemMessage('连接服务器成功，正在准备面试...');
            
            // 开始面试
            socket.emit('start_interview', {
                user_id: userId,
                mode: mode,
                practice_round: practiceRound
            });
        });

        socket.on('disconnect', function() {
            console.log('WebSocket 已断开');
            addSystemMessage('⚠️ 连接已断开，请刷新页面重试');
        });

        socket.on('error', function(data) {
            console.error('错误:', data);
            addSystemMessage(`❌ 错误: ${data.message}`);
            hideLoading();
        });

        // 面试开始
        socket.on('interview_started', function(data) {
            console.log('面试开始:', data);
            totalRounds = data.total_rounds;
            addSystemMessage(`📋 ${data.mode === 'full' ? '完整面试' : '快速练习'}模式，共 ${totalRounds} 轮`);
            updateProgress(0, totalRounds);
        });

        // 轮次开始
        socket.on('round_start', function(data) {
            console.log('轮次开始:', data);
            currentRound = data.round_key;
            
            // 更新进度
            updateProgress(data.round_index - 1, totalRounds);
            progressText.textContent = `第 ${data.round_index}/${totalRounds} 轮: ${data.round_name}`;
            
            // 更新左侧面板
            updateRoundStatus(data.round_key, 'active');
            
            // 重置评估面板
            resetEvaluationPanel();
            
            addSystemMessage(`🎯 进入第 ${data.round_index} 轮: ${data.round_name}`);
        });

        // 收到问题
        socket.on('question', function(data) {
            console.log('问题:', data);
            addInterviewerMessage(data.round_name, data.question);
            enableInput();
            inputHint.classList.remove('hidden');
            hideLoading();
        });

        // 追问
        socket.on('follow_up', function(data) {
            console.log('追问:', data);
            addInterviewerMessage(currentRound, data.question, true, data.reason);
            enableInput();
            hideLoading();
        });

        // 正在评估
        socket.on('evaluating', function(data) {
            showLoading(data.message || '面试官正在评估你的回答...');
        });

        // 评估结果
        socket.on('evaluation', function(data) {
            console.log('评估结果:', data);
            hideLoading();
            showEvaluation(data);
            updateRoundScore(data.round_key, data.score);
        });

        // 终面委员会开始
        socket.on('committee_start', function(data) {
            addSystemMessage(data.message);
            showLoading('评审委员会正在进行最终评估...');
            updateRoundStatus('Committee', 'active');
        });

        // 最终评估
        socket.on('final_evaluation', function(data) {
            console.log('最终评估:', data);
            hideLoading();
            showFinalEvaluation(data);
            updateRoundStatus('Committee', 'completed');
            updateRoundScore('Committee', data.final_score);
        });

        // 面试完成
        socket.on('interview_complete', function(data) {
            console.log('面试完成:', data);
            sessionId = data.session_id;
            updateProgress(totalRounds, totalRounds);
            progressText.textContent = '面试已完成';
            
            // 设置报告按钮
            document.getElementById('view-report-btn').onclick = function() {
                window.location.href = `/report/${sessionId}`;
            };
            
            document.getElementById('back-home-btn').onclick = function() {
                window.location.href = '/';
            };
        });

        // 面试结束（提前结束）
        socket.on('interview_ended', function(data) {
            addSystemMessage(data.message);
            disableInput();
        });
    }

    // 提交回答
    function submitAnswer() {
        const answer = answerInput.value.trim();
        if (!answer) {
            alert('请输入你的回答');
            return;
        }

        if (socket && socket.connected) {
            // 显示用户消息
            addUserMessage(answer);
            
            // 发送到服务器
            socket.emit('submit_answer', { answer: answer });
            
            // 清空输入并禁用
            answerInput.value = '';
            disableInput();
            
            showLoading('面试官正在评估...');
        }
    }

    // 启用输入
    function enableInput() {
        answerInput.disabled = false;
        submitBtn.disabled = false;
        skipBtn.disabled = false;
        answerInput.focus();
    }

    // 禁用输入
    function disableInput() {
        answerInput.disabled = true;
        submitBtn.disabled = true;
        skipBtn.disabled = true;
        inputHint.classList.add('hidden');
    }

    // 添加系统消息
    function addSystemMessage(text) {
        const div = document.createElement('div');
        div.className = 'chat-message system-message';
        div.innerHTML = `<div class="message-content"><p>${text}</p></div>`;
        chatContainer.appendChild(div);
        scrollToBottom();
    }

    // 添加面试官消息
    function addInterviewerMessage(role, text, isFollowUp = false, followUpReason = '') {
        const roleNames = {
            'HR': 'HR 面试官',
            'HiringManager': '业务经理',
            'Technical': '技术面试官',
            'CultureFit': '文化契合度面试官',
            'Committee': '评审委员会'
        };
        
        const div = document.createElement('div');
        div.className = 'chat-message interviewer-message';
        
        let html = '<div class="message-content">';
        html += `<div class="message-header">
            <span class="interviewer-name">${roleNames[role] || role}</span>
        </div>`;
        
        if (isFollowUp) {
            html += `<div class="follow-up-badge">🔄 追问: ${followUpReason}</div>`;
        }
        
        html += `<div class="message-text">${text}</div>`;
        html += '</div>';
        
        div.innerHTML = html;
        chatContainer.appendChild(div);
        scrollToBottom();
    }

    // 添加用户消息
    function addUserMessage(text) {
        const div = document.createElement('div');
        div.className = 'chat-message user-message';
        div.innerHTML = `<div class="message-content">
            <div class="message-text">${escapeHtml(text)}</div>
        </div>`;
        chatContainer.appendChild(div);
        scrollToBottom();
    }

    // 滚动到底部
    function scrollToBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // 更新进度
    function updateProgress(current, total) {
        const percent = Math.round((current / total) * 100);
        progressBar.style.width = `${percent}%`;
    }

    // 更新轮次状态
    function updateRoundStatus(roundKey, status) {
        const items = document.querySelectorAll('.round-item');
        items.forEach(item => {
            if (item.dataset.round === roundKey) {
                item.classList.remove('active', 'completed');
                item.classList.add(status);
                
                const statusEl = item.querySelector('.round-status');
                if (status === 'active') {
                    statusEl.textContent = '🔵';
                } else if (status === 'completed') {
                    statusEl.textContent = '✅';
                }
            }
        });
    }

    // 更新轮次分数
    function updateRoundScore(roundKey, score) {
        const item = document.querySelector(`.round-item[data-round="${roundKey}"]`);
        if (item) {
            item.classList.remove('active');
            item.classList.add('completed');
            
            const scoreEl = item.querySelector('.round-score');
            scoreEl.textContent = `${score}/10`;
            scoreEl.classList.remove('hidden');
            
            const statusEl = item.querySelector('.round-status');
            statusEl.classList.add('hidden');
        }
    }

    // 重置评估面板
    function resetEvaluationPanel() {
        evaluationContent.innerHTML = `
            <div class="evaluation-placeholder">
                <p>等待你的回答...</p>
                <p>评估结果将在回答后显示</p>
            </div>
        `;
        evaluationResult.classList.add('hidden');
    }

    // 显示评估结果
    function showEvaluation(data) {
        evaluationContent.innerHTML = '';
        evaluationResult.classList.remove('hidden');
        
        document.getElementById('score-emoji').textContent = data.score_emoji || '📊';
        document.getElementById('score-value').textContent = data.score || '-';
        document.getElementById('score-level').textContent = data.score_level || '';
        document.getElementById('feedback-text').textContent = data.feedback || '';
        
        // 优势标签
        const strengthTags = document.getElementById('strength-tags');
        if (data.strength_tags && data.strength_tags.length > 0) {
            strengthTags.querySelector('.tags').innerHTML = 
                data.strength_tags.map(t => `<span class="tag">${t}</span>`).join('');
            strengthTags.classList.remove('hidden');
        } else {
            strengthTags.classList.add('hidden');
        }
        
        // 弱项标签
        const weaknessTags = document.getElementById('weakness-tags');
        if (data.weakness_tags && data.weakness_tags.length > 0) {
            weaknessTags.querySelector('.tags').innerHTML = 
                data.weakness_tags.map(t => `<span class="tag">${t}</span>`).join('');
            weaknessTags.classList.remove('hidden');
        } else {
            weaknessTags.classList.add('hidden');
        }
        
        // 建议
        const hintSection = document.getElementById('hint-section');
        if (data.improvement_hint) {
            document.getElementById('hint-text').textContent = data.improvement_hint;
            hintSection.classList.remove('hidden');
        } else {
            hintSection.classList.add('hidden');
        }
    }

    // 显示最终评估
    function showFinalEvaluation(data) {
        document.getElementById('final-emoji').textContent = data.score_emoji || '🎯';
        document.getElementById('final-score').textContent = data.final_score || '-';
        document.getElementById('final-level').textContent = data.score_level || '';
        document.getElementById('final-decision').textContent = data.decision || '';
        document.getElementById('final-feedback').textContent = data.overall_feedback || '';
        
        // 关键优势
        const strengthsList = document.getElementById('final-strengths');
        strengthsList.innerHTML = (data.key_strengths || [])
            .map(s => `<li>${s}</li>`).join('');
        
        // 待改进
        const weaknessesList = document.getElementById('final-weaknesses');
        weaknessesList.innerHTML = (data.key_weaknesses || [])
            .map(w => `<li>${w}</li>`).join('');
        
        // 改进建议
        const suggestionsList = document.getElementById('final-suggestions');
        suggestionsList.innerHTML = (data.improvement_suggestions || [])
            .map(s => `<li>${s}</li>`).join('');
        
        // 显示弹窗
        finalModal.classList.remove('hidden');
    }

    // 显示加载
    function showLoading(text) {
        loadingText.textContent = text || '处理中...';
        loadingOverlay.classList.remove('hidden');
    }

    // 隐藏加载
    function hideLoading() {
        loadingOverlay.classList.add('hidden');
    }

    // HTML 转义
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});
