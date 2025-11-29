"""
AI Interview Simulator - Web UI 后端服务
使用 Flask + WebSocket 实现实时面试交互

运行方式:
    python web/app.py

访问:
    http://localhost:5000
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import json
from datetime import datetime
from typing import Dict, Any, Optional

from core.workflow import InterviewWorkflow
from core.memory import UserMemory, SessionMemory
from core.report import ReportGenerator
from config import (
    DEFAULT_POSITION, QWEN_API_KEY, INTERVIEW_ROUNDS_CONFIG,
    get_score_level, OUTPUT_CONFIG, FOLLOW_UP_CONFIG
)

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.secret_key = 'ai-interview-simulator-secret-key-2024'

# 配置 WebSocket
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 全局存储活跃的面试会话
active_sessions: Dict[str, Dict[str, Any]] = {}


# ================== 页面路由 ==================

@app.route('/')
def index():
    """首页 - 面试准备"""
    return render_template('index.html')


@app.route('/interview')
def interview():
    """面试页面"""
    return render_template('interview.html')


@app.route('/history')
def history():
    """历史记录页面"""
    return render_template('history.html')


@app.route('/report/<session_id>')
def report(session_id):
    """查看面试报告"""
    return render_template('report.html', session_id=session_id)


# ================== API 接口 ==================

@app.route('/api/check_api_key')
def check_api_key():
    """检查 API Key 是否配置"""
    is_configured = QWEN_API_KEY and QWEN_API_KEY != "your-api-key-here"
    return jsonify({
        'configured': is_configured,
        'model': 'Qwen' if is_configured else 'Mock Mode'
    })


@app.route('/api/user/<user_id>')
def get_user_info(user_id):
    """获取用户信息和历史"""
    try:
        user_memory = UserMemory(user_id)
        stats = user_memory.data.get('statistics', {})
        history = user_memory.data.get('interview_history', [])
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'statistics': stats,
            'history': history[-10:],  # 最近10次
            'recommendations': user_memory.get_practice_recommendations()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/user/<user_id>/history')
def get_user_history(user_id):
    """获取用户详细历史记录"""
    try:
        user_memory = UserMemory(user_id)
        history = user_memory.data.get('interview_history', [])
        
        return jsonify({
            'success': True,
            'history': history
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/session/<session_id>')
def get_session_data(session_id):
    """获取会话详情"""
    try:
        from config import SESSIONS_DIR
        session_files = list(SESSIONS_DIR.glob(f'*{session_id}*.json'))
        
        if not session_files:
            return jsonify({'success': False, 'error': '会话不存在'})
        
        with open(session_files[0], 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/report/<session_id>')
def get_report(session_id):
    """生成并返回面试报告"""
    try:
        from config import SESSIONS_DIR
        session_files = list(SESSIONS_DIR.glob(f'*{session_id}*.json'))
        
        if not session_files:
            return jsonify({'success': False, 'error': '会话不存在'})
        
        with open(session_files[0], 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        generator = ReportGenerator()
        markdown_report = generator.generate_markdown_report(session_data)
        
        return jsonify({
            'success': True,
            'markdown': markdown_report,
            'session_data': session_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/export_report/<session_id>', methods=['POST'])
def export_report(session_id):
    """导出报告到文件"""
    try:
        format_type = request.json.get('format', 'markdown')
        
        from config import SESSIONS_DIR
        session_files = list(SESSIONS_DIR.glob(f'*{session_id}*.json'))
        
        if not session_files:
            return jsonify({'success': False, 'error': '会话不存在'})
        
        with open(session_files[0], 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        generator = ReportGenerator()
        filepath = generator.save_report(session_data, format=format_type)
        
        return jsonify({
            'success': True,
            'filepath': filepath
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ================== WebSocket 事件处理 ==================

@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    print(f'[WebSocket] 客户端已连接: {request.sid}')
    emit('connected', {'status': 'ok', 'sid': request.sid})


@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开"""
    print(f'[WebSocket] 客户端已断开: {request.sid}')
    # 清理会话
    if request.sid in active_sessions:
        del active_sessions[request.sid]


@socketio.on('start_interview')
def handle_start_interview(data):
    """开始面试"""
    user_id = data.get('user_id', 'guest')
    mode = data.get('mode', 'full')  # full 或 practice
    practice_round = data.get('practice_round')  # 快速练习指定轮次
    
    print(f'[面试开始] 用户: {user_id}, 模式: {mode}')
    
    # 创建工作流
    workflow = InterviewWorkflow()
    user_memory = UserMemory(user_id)
    session_memory = SessionMemory(user_id, DEFAULT_POSITION)
    
    # 存储会话信息
    active_sessions[request.sid] = {
        'workflow': workflow,
        'user_memory': user_memory,
        'session': session_memory,
        'user_id': user_id,
        'mode': mode,
        'practice_round': practice_round,
        'current_round_index': 0,
        'current_round': None,
        'waiting_for_answer': False,
        'round_results': [],
        'follow_up_count': 0,  # 当前轮次追问计数
    }
    
    # 发送面试开始确认
    emit('interview_started', {
        'user_id': user_id,
        'position': DEFAULT_POSITION,
        'mode': mode,
        'total_rounds': len(workflow.round_order) if mode == 'full' else 1,
    })
    
    # 开始第一轮
    if mode == 'practice' and practice_round:
        start_round(request.sid, practice_round)
    else:
        start_round(request.sid, workflow.round_order[0])


def start_round(sid: str, round_key: str):
    """开始一轮面试"""
    session_data = active_sessions.get(sid)
    if not session_data:
        return
    
    workflow = session_data['workflow']
    round_config = INTERVIEW_ROUNDS_CONFIG.get(round_key, {})
    round_name = round_config.get('name', round_key)
    
    session_data['current_round'] = round_key
    
    # 通知客户端轮次开始
    socketio.emit('round_start', {
        'round_key': round_key,
        'round_name': round_name,
        'round_index': session_data['current_round_index'] + 1,
        'total_rounds': len(workflow.round_order),
        'weight': round_config.get('weight', 0),
    }, room=sid)
    
    # 生成问题
    agent = workflow.agents.get(round_key)
    if agent:
        try:
            question = agent.generate_question(
                session_data['user_memory'].get_context_for_prompt(),
                session_data['session'].get_recent_context()
            )
            
            session_data['current_question'] = question
            session_data['waiting_for_answer'] = True
            
            # 发送问题
            socketio.emit('question', {
                'round_key': round_key,
                'round_name': round_name,
                'question': question,
            }, room=sid)
            
        except Exception as e:
            print(f'[错误] 生成问题失败: {e}')
            socketio.emit('error', {'message': f'生成问题失败: {str(e)}'}, room=sid)


@socketio.on('submit_answer')
def handle_submit_answer(data):
    """处理用户回答"""
    answer = data.get('answer', '')
    sid = request.sid
    
    session_data = active_sessions.get(sid)
    if not session_data or not session_data.get('waiting_for_answer'):
        return
    
    session_data['waiting_for_answer'] = False
    
    workflow = session_data['workflow']
    round_key = session_data['current_round']
    question = session_data.get('current_question', '')
    
    # 通知开始评估
    emit('evaluating', {'message': '面试官正在评估你的回答...'})
    
    # 评估回答
    agent = workflow.agents.get(round_key)
    if agent:
        try:
            evaluation = agent.evaluate_answer(
                question=question,
                answer=answer,
                user_context=session_data['user_memory'].get_context_for_prompt(),
            )
            
            # 规范化评估结果
            evaluation = agent._normalize_evaluation_result(evaluation)
            
            # 添加分数级别信息
            score = evaluation.get('score', 0)
            score_info = get_score_level(score)
            evaluation['score_level'] = score_info.get('level', '')
            evaluation['score_emoji'] = score_info.get('emoji', '📊')
            
            # 保存到会话
            session_data['session'].add_round(
                role=round_key,
                question=question,
                answer=answer,
                score=evaluation.get('score', 0),
                feedback=evaluation.get('feedback', ''),
                weakness_tags=evaluation.get('weakness_tags', []),
                strength_tags=evaluation.get('strength_tags', []),
                key_points=evaluation.get('key_points', []),
                improvement_hint=evaluation.get('improvement_hint', ''),
                is_follow_up=session_data.get('is_follow_up', False),
            )
            
            round_result = {
                'role': round_key,
                'question': question,
                'answer': answer,
                **evaluation,
            }
            session_data['round_results'].append(round_result)
            
            # 发送评估结果
            emit('evaluation', {
                'round_key': round_key,
                'question': question,
                'answer': answer,
                **evaluation,
            })
            
            # 检查是否需要追问（限制追问次数）
            max_follow_ups = FOLLOW_UP_CONFIG.get('max_follow_ups', 1)
            current_follow_count = session_data.get('follow_up_count', 0)
            
            should_follow, follow_reason = agent.should_follow_up(answer, evaluation)
            if should_follow and current_follow_count < max_follow_ups:
                follow_up_q = agent.generate_follow_up(question, answer, evaluation, follow_reason)
                if follow_up_q:
                    session_data['current_question'] = follow_up_q
                    session_data['waiting_for_answer'] = True
                    session_data['is_follow_up'] = True
                    session_data['follow_up_count'] = current_follow_count + 1  # 递增追问计数
                    
                    emit('follow_up', {
                        'reason': follow_reason or '需要进一步了解',
                        'question': follow_up_q,
                        'follow_up_number': session_data['follow_up_count'],
                        'max_follow_ups': max_follow_ups,
                    })
                    return
            
            # 进入下一轮
            proceed_to_next_round(sid)
            
        except Exception as e:
            print(f'[错误] 评估失败: {e}')
            import traceback
            traceback.print_exc()
            emit('error', {'message': f'评估失败: {str(e)}'})


def proceed_to_next_round(sid: str):
    """进入下一轮面试"""
    session_data = active_sessions.get(sid)
    if not session_data:
        return
    
    workflow = session_data['workflow']
    mode = session_data['mode']
    
    session_data['current_round_index'] += 1
    session_data['is_follow_up'] = False
    session_data['follow_up_count'] = 0  # 重置追问计数
    
    # 快速练习模式只进行一轮
    if mode == 'practice':
        finish_interview(sid)
        return
    
    # 检查是否还有更多轮次
    if session_data['current_round_index'] < len(workflow.round_order):
        next_round = workflow.round_order[session_data['current_round_index']]
        start_round(sid, next_round)
    else:
        # 进行终面评审
        run_committee_evaluation(sid)


def run_committee_evaluation(sid: str):
    """运行终面评审"""
    session_data = active_sessions.get(sid)
    if not session_data:
        return
    
    socketio.emit('committee_start', {
        'message': '所有面试轮次已完成，评审委员会正在进行最终评估...'
    }, room=sid)
    
    workflow = session_data['workflow']
    
    try:
        final_eval = workflow.run_committee_evaluation(
            session_data['user_memory'],
            session_data['session']
        )
        
        # 添加分数级别
        score = final_eval.get('final_score', 0)
        score_info = get_score_level(score)
        final_eval['score_level'] = score_info.get('level', '')
        final_eval['score_emoji'] = score_info.get('emoji', '📊')
        
        socketio.emit('final_evaluation', final_eval, room=sid)
        
    except Exception as e:
        print(f'[错误] 终面评审失败: {e}')
        socketio.emit('error', {'message': f'终面评审失败: {str(e)}'}, room=sid)
    
    finish_interview(sid)


def finish_interview(sid: str):
    """完成面试"""
    session_data = active_sessions.get(sid)
    if not session_data:
        return
    
    # 保存用户档案
    user_memory = session_data['user_memory']
    session_memory = session_data['session']
    
    # 更新用户统计
    user_memory.add_weakness_tags(session_memory.get_all_weakness_tags())
    user_memory.add_strength_tags(session_memory.get_all_strength_tags())
    
    # 计算平均分
    scores = [r.get('score', 0) for r in session_data['round_results'] if r.get('score')]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    user_memory.add_interview_summary({
        'timestamp': session_memory.started_at,
        'final_score': avg_score,
        'rounds_count': len(session_data['round_results']),
    })
    user_memory.save()
    
    # 保存会话
    session_path = session_memory.save()
    session_id = Path(session_path).stem
    
    socketio.emit('interview_complete', {
        'session_id': session_id,
        'session_path': session_path,
        'average_score': round(avg_score, 2),
        'rounds_count': len(session_data['round_results']),
    }, room=sid)


@socketio.on('skip_question')
def handle_skip_question(data):
    """跳过当前问题"""
    handle_submit_answer({'answer': '（候选人选择跳过此问题）'})


@socketio.on('end_interview')
def handle_end_interview(data):
    """提前结束面试"""
    sid = request.sid
    session_data = active_sessions.get(sid)
    
    if session_data:
        finish_interview(sid)
    
    emit('interview_ended', {'message': '面试已结束'})


# ================== 启动服务 ==================

if __name__ == '__main__':
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║       🌐 AI Interview Simulator - Web UI Server                        ║
╠════════════════════════════════════════════════════════════════════════╣
║   访问地址: http://localhost:5000                                      ║
║   按 Ctrl+C 停止服务                                                   ║
╚════════════════════════════════════════════════════════════════════════╝
    """)
    
    # 检查 API Key
    if not QWEN_API_KEY or QWEN_API_KEY == "your-api-key-here":
        print("⚠️  警告: 未配置 Qwen API Key，将使用模拟模式")
        print("   请在 config.py 中设置 QWEN_API_KEY\n")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
