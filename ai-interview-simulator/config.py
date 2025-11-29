"""
AI Multi-Agent Interview Simulator - 配置文件
数据分析师多面试官智能面试模拟器

使用说明:
1. 将 QWEN_API_KEY 替换为你的阿里云 DashScope API Key
2. 获取地址: https://dashscope.console.aliyun.com/
"""
import os
from pathlib import Path
from typing import Dict, List

# ==================== 路径配置 ====================
BASE_DIR = Path(__file__).parent
STORAGE_DIR = BASE_DIR / "storage"
USERS_DIR = STORAGE_DIR / "users"
SESSIONS_DIR = STORAGE_DIR / "sessions"
REPORTS_DIR = STORAGE_DIR / "reports"  # 面试报告导出目录
DATA_DIR = BASE_DIR / "data"

# ==================== Qwen API 配置 ====================
# 请在此处填入你的 Qwen API Key，或通过环境变量 QWEN_API_KEY 设置
QWEN_API_KEY = os.environ.get("QWEN_API_KEY", "sk-01a157549b014287abd473b6b0ddcad7")
QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_MODEL = "qwen-plus"  # 可选: qwen-turbo, qwen-plus, qwen-max

# API 调用配置
API_TIMEOUT = 60  # 秒
API_MAX_RETRIES = 3
API_RETRY_DELAY = 2  # 秒

# ==================== 面试配置 ====================
DEFAULT_POSITION = "数据分析师 (Data Analyst)"

# 面试轮次配置
INTERVIEW_ROUNDS_CONFIG: Dict[str, Dict] = {
    "HR": {
        "name": "HR 初筛",
        "weight": 0.15,  # 综合评分权重
        "min_questions": 1,
        "max_questions": 2,
        "follow_up_enabled": True,
    },
    "HiringManager": {
        "name": "业务用人经理面试", 
        "weight": 0.25,
        "min_questions": 1,
        "max_questions": 2,
        "follow_up_enabled": True,
    },
    "Technical": {
        "name": "技术/分析面试",
        "weight": 0.35,
        "min_questions": 1,
        "max_questions": 2,
        "follow_up_enabled": True,
    },
    "CultureFit": {
        "name": "文化契合度面试",
        "weight": 0.15,
        "min_questions": 1,
        "max_questions": 1,
        "follow_up_enabled": True,
    },
    "Committee": {
        "name": "终面评审委员会",
        "weight": 0.10,
        "min_questions": 0,
        "max_questions": 0,
        "follow_up_enabled": False,
    },
}

# 面试轮次顺序
INTERVIEW_ROUNDS = ["HR", "HiringManager", "Technical", "CultureFit", "Committee"]

# ==================== 评分配置 ====================
SCORE_MIN = 0
SCORE_MAX = 10

# 评分等级定义
SCORE_LEVELS = {
    (9, 10): {"level": "优秀", "emoji": "🌟", "decision": "强烈推荐"},
    (7, 8): {"level": "良好", "emoji": "👍", "decision": "推荐通过"},
    (5, 6): {"level": "中等", "emoji": "💪", "decision": "候补/观察"},
    (3, 4): {"level": "待提升", "emoji": "📚", "decision": "暂不推荐"},
    (0, 2): {"level": "不足", "emoji": "⚠️", "decision": "不通过"},
}

def get_score_level(score: float) -> Dict:
    """根据分数获取等级信息"""
    for (low, high), info in SCORE_LEVELS.items():
        if low <= score <= high:
            return info
    return SCORE_LEVELS[(5, 6)]

# ==================== 标签体系 ====================
# 弱项标签（按类别组织）
WEAKNESS_TAGS_BY_CATEGORY = {
    "表达与结构": [
        "结构不清晰",
        "表达冗长",
        "逻辑不连贯",
        "缺少具体案例",
    ],
    "技术能力": [
        "统计基础薄弱",
        "SQL细节欠缺",
        "Python能力待加强",
        "实验设计不完整",
        "指标理解不深",
    ],
    "业务理解": [
        "缺少业务视角",
        "与岗位不够相关",
        "缺少落地结果",
        "缺乏数据思维",
        "业务敏感度不足",
    ],
    "软技能": [
        "沟通表达待加强",
        "项目深度不够",
        "案例准备不充分",
        "自我认知不足",
        "团队协作经验少",
    ],
}

# 优势标签（按类别组织）
STRENGTH_TAGS_BY_CATEGORY = {
    "表达与结构": [
        "结构清晰",
        "表达简洁",
        "逻辑严谨",
        "案例具体生动",
    ],
    "技术能力": [
        "统计功底扎实",
        "SQL能力强",
        "Python熟练",
        "实验设计规范",
        "指标体系清晰",
    ],
    "业务理解": [
        "业务理解深",
        "数据驱动思维",
        "有落地成果",
        "数据敏感度高",
        "能产出洞察",
    ],
    "软技能": [
        "沟通表达好",
        "项目经验丰富",
        "学习能力强",
        "有成长心态",
        "团队协作好",
    ],
}

# 扁平化标签列表（向后兼容）
WEAKNESS_TAGS = [tag for tags in WEAKNESS_TAGS_BY_CATEGORY.values() for tag in tags]
STRENGTH_TAGS = [tag for tags in STRENGTH_TAGS_BY_CATEGORY.values() for tag in tags]

# ==================== 追问配置 ====================
FOLLOW_UP_CONFIG = {
    "enabled": True,
    "max_follow_ups": 1,  # 每轮最多追问次数
    "trigger_score_threshold": 6,  # 低于此分数触发追问
    "trigger_keywords": ["不清楚", "不太确定", "可能", "大概"],  # 触发追问的关键词
}

# ==================== 输出配置 ====================
OUTPUT_CONFIG = {
    "show_score_realtime": True,  # 实时显示评分
    "show_tags_realtime": True,   # 实时显示标签
    "export_report": True,        # 导出面试报告
    "report_format": "markdown",  # markdown / html / json
}

# ==================== 调试配置 ====================
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
