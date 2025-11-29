"""
LLM Client - 封装 Qwen 大模型调用
使用 OpenAI 兼容接口调用阿里云 DashScope

特性:
- 自动重试机制
- 结构化 JSON 输出
- 流式响应支持
- 完善的错误处理
"""
import json
import time
import logging
from typing import Optional, List, Dict, Any, Generator
from openai import OpenAI, APIError, RateLimitError, APIConnectionError
from config import (
    QWEN_API_KEY, QWEN_BASE_URL, QWEN_MODEL,
    API_TIMEOUT, API_MAX_RETRIES, API_RETRY_DELAY, DEBUG
)

# 配置日志
logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)
logger = logging.getLogger(__name__)


class LLMClient:
    """
    Qwen 大模型客户端
    
    使用 OpenAI 兼容接口，支持:
    - 普通对话
    - JSON 结构化输出
    - 流式响应
    - 自动重试
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or QWEN_API_KEY
        self.base_url = base_url or QWEN_BASE_URL
        self.model = model or QWEN_MODEL
        self.timeout = API_TIMEOUT
        self.max_retries = API_MAX_RETRIES
        self.retry_delay = API_RETRY_DELAY
        
        # 检查 API Key
        if self.api_key == "your-api-key-here" or not self.api_key:
            logger.warning("未配置有效的 API Key，将使用模拟模式")
            self._mock_mode = True
        else:
            self._mock_mode = False
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
            )

    def _mock_response(self, messages: List[Dict[str, str]]) -> str:
        """模拟模式下的响应（用于测试）"""
        user_msg = messages[-1].get("content", "") if messages else ""
        return f"[模拟响应] 收到消息: {user_msg[:50]}..."

    def _retry_with_backoff(self, func, *args, **kwargs) -> Any:
        """带指数退避的重试机制"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except RateLimitError as e:
                last_error = e
                wait_time = self.retry_delay * (2 ** attempt)
                logger.warning(f"触发速率限制，等待 {wait_time}s 后重试 (尝试 {attempt + 1}/{self.max_retries})")
                time.sleep(wait_time)
            except APIConnectionError as e:
                last_error = e
                wait_time = self.retry_delay * (2 ** attempt)
                logger.warning(f"连接错误，等待 {wait_time}s 后重试 (尝试 {attempt + 1}/{self.max_retries})")
                time.sleep(wait_time)
            except APIError as e:
                last_error = e
                if e.status_code and e.status_code >= 500:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"服务器错误，等待 {wait_time}s 后重试 (尝试 {attempt + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                else:
                    raise
        
        raise last_error

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        发送对话请求
        
        Args:
            messages: 消息列表，格式为 [{"role": "system/user/assistant", "content": "..."}]
            temperature: 生成温度，越高越随机
            max_tokens: 最大生成token数
            
        Returns:
            模型生成的回复文本
        """
        if self._mock_mode:
            return self._mock_response(messages)
        
        def _call():
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        
        try:
            return self._retry_with_backoff(_call)
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            return f"[模型调用失败: {e}]"

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> Generator[str, None, None]:
        """
        流式对话请求
        
        Yields:
            逐字符/token 的响应
        """
        if self._mock_mode:
            mock_response = self._mock_response(messages)
            for char in mock_response:
                yield char
                time.sleep(0.02)
            return
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"流式调用失败: {e}")
            yield f"[流式调用失败: {e}]"

    def generate_with_system(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        history: List[Dict[str, str]] = None,
    ) -> str:
        """
        便捷方法：使用系统提示词 + 用户消息生成回复
        
        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            temperature: 生成温度
            history: 可选的历史对话记录
        """
        messages = [{"role": "system", "content": system_prompt}]
        
        if history:
            messages.extend(history)
        
        messages.append({"role": "user", "content": user_message})
        
        return self.chat(messages, temperature=temperature)

    def generate_json(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.5,
        schema_hint: str = "",
    ) -> Dict[str, Any]:
        """
        生成 JSON 格式的响应
        
        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            temperature: 生成温度（JSON 输出建议用较低温度）
            schema_hint: 可选的 JSON schema 提示
            
        Returns:
            解析后的 JSON 字典，解析失败返回带 error 的字典
        """
        json_instruction = """
请严格以 JSON 格式返回结果。要求:
1. 只输出 JSON，不要有其他文字
2. 不要使用 markdown 代码块
3. 确保 JSON 格式正确，可以被解析"""
        
        if schema_hint:
            json_instruction += f"\n4. 输出格式: {schema_hint}"
        
        full_system = f"{system_prompt}\n\n{json_instruction}"
        response = self.generate_with_system(full_system, user_message, temperature)
        
        return self._parse_json_response(response)

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """解析可能包含 markdown 代码块的 JSON 响应"""
        original_response = response
        
        # 清理常见的包装格式
        response = response.strip()
        
        # 移除 markdown 代码块
        if response.startswith("```json"):
            response = response[7:]
        elif response.startswith("```"):
            response = response[3:]
        
        if response.endswith("```"):
            response = response[:-3]
        
        response = response.strip()
        
        # 尝试解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # 尝试提取 JSON 对象
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass
        
        # 尝试提取 JSON 数组
        try:
            start = response.find("[")
            end = response.rfind("]") + 1
            if start != -1 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass
        
        logger.warning(f"JSON 解析失败: {original_response[:200]}...")
        return {"error": "JSON解析失败", "raw": original_response}

    def is_available(self) -> bool:
        """检查 API 是否可用"""
        if self._mock_mode:
            return True
        
        try:
            response = self.chat(
                [{"role": "user", "content": "Hello"}],
                max_tokens=10,
            )
            return not response.startswith("[模型调用失败")
        except Exception:
            return False
