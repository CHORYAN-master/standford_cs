"""
Self-Healing Module for MCP AI Agent
자가 치유 로직: 도구 자동 비활성화/재시작
"""

import logging
import time
from typing import Dict, Callable
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    Circuit Breaker 패턴 구현
    도구가 반복적으로 실패하면 자동으로 차단
    """
    
    # 상태
    CLOSED = "closed"      # 정상 작동
    OPEN = "open"          # 차단됨
    HALF_OPEN = "half_open"  # 테스트 중
    
    def __init__(self, 
                 tool_name: str,
                 failure_threshold: int = 3,
                 timeout_threshold: int = 3,
                 recovery_timeout: int = 60):
        """
        Args:
            tool_name: 도구 이름
            failure_threshold: 실패 임계값
            timeout_threshold: 타임아웃 임계값
            recovery_timeout: 복구 시도 대기 시간(초)
        """
        self.tool_name = tool_name
        self.failure_threshold = failure_threshold
        self.timeout_threshold = timeout_threshold
        self.recovery_timeout = recovery_timeout
        
        self.failure_count = 0
        self.timeout_count = 0
        self.state = self.CLOSED
        self.last_failure_time = None
        self.open_time = None
    
    def call(self, func: Callable, *args, **kwargs):
        """함수 호출 (Circuit Breaker 적용)"""
        
        # OPEN 상태: 차단됨
        if self.state == self.OPEN:
            if self._should_attempt_reset():
                logger.info(f"Circuit breaker for {self.tool_name}: Attempting reset (HALF_OPEN)")
                self.state = self.HALF_OPEN
            else:
                logger.warning(f"Circuit breaker for {self.tool_name}: Still OPEN")
                raise CircuitBreakerError(f"{self.tool_name} is currently disabled")
        
        # 함수 실행 시도
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except TimeoutError as e:
            self._on_timeout()
            raise
            
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """성공 시 처리"""
        if self.state == self.HALF_OPEN:
            logger.info(f"Circuit breaker for {self.tool_name}: Reset successful (CLOSED)")
            self.state = self.CLOSED
        
        self.failure_count = 0
        self.timeout_count = 0
    
    def _on_failure(self):
        """실패 시 처리"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        logger.warning(
            f"Circuit breaker for {self.tool_name}: "
            f"Failure {self.failure_count}/{self.failure_threshold}"
        )
        
        if self.failure_count >= self.failure_threshold:
            self._open_circuit()
    
    def _on_timeout(self):
        """타임아웃 시 처리"""
        self.timeout_count += 1
        self.last_failure_time = datetime.now()
        
        logger.warning(
            f"Circuit breaker for {self.tool_name}: "
            f"Timeout {self.timeout_count}/{self.timeout_threshold}"
        )
        
        if self.timeout_count >= self.timeout_threshold:
            self._open_circuit()
    
    def _open_circuit(self):
        """회로 차단"""
        self.state = self.OPEN
        self.open_time = datetime.now()
        
        logger.critical(
            f"🚨 Circuit breaker OPENED for {self.tool_name}: "
            f"Too many failures/timeouts. Tool disabled for {self.recovery_timeout}s"
        )
    
    def _should_attempt_reset(self) -> bool:
        """복구 시도 여부 판단"""
        if not self.open_time:
            return False
        
        elapsed = (datetime.now() - self.open_time).total_seconds()
        return elapsed >= self.recovery_timeout
    
    def manual_reset(self):
        """수동 리셋"""
        self.state = self.CLOSED
        self.failure_count = 0
        self.timeout_count = 0
        self.open_time = None
        logger.info(f"Circuit breaker for {self.tool_name}: Manually reset")
    
    def get_status(self) -> Dict:
        """상태 정보"""
        return {
            "tool_name": self.tool_name,
            "state": self.state,
            "failure_count": self.failure_count,
            "timeout_count": self.timeout_count,
            "is_enabled": self.state != self.OPEN
        }


class CircuitBreakerError(Exception):
    """Circuit Breaker 차단 에러"""
    pass


class SelfHealingManager:
    """자가 치유 관리자"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    def register_tool(self, 
                     tool_name: str,
                     failure_threshold: int = 3,
                     timeout_threshold: int = 3,
                     recovery_timeout: int = 60):
        """도구 등록"""
        self.circuit_breakers[tool_name] = CircuitBreaker(
            tool_name=tool_name,
            failure_threshold=failure_threshold,
            timeout_threshold=timeout_threshold,
            recovery_timeout=recovery_timeout
        )
        logger.info(f"Registered circuit breaker for {tool_name}")
    
    def protect(self, tool_name: str):
        """데코레이터: 도구를 Circuit Breaker로 보호"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if tool_name not in self.circuit_breakers:
                    self.register_tool(tool_name)
                
                breaker = self.circuit_breakers[tool_name]
                
                try:
                    return breaker.call(func, *args, **kwargs)
                except CircuitBreakerError as e:
                    logger.error(f"Circuit breaker blocked call to {tool_name}")
                    return f"Error: {tool_name} is temporarily disabled due to repeated failures. Please try again later."
            
            return wrapper
        return decorator
    
    def get_status(self, tool_name: str = None) -> Dict:
        """상태 조회"""
        if tool_name:
            breaker = self.circuit_breakers.get(tool_name)
            return breaker.get_status() if breaker else {"error": "Tool not found"}
        
        return {
            name: breaker.get_status()
            for name, breaker in self.circuit_breakers.items()
        }
    
    def reset_tool(self, tool_name: str):
        """도구 수동 리셋"""
        if tool_name in self.circuit_breakers:
            self.circuit_breakers[tool_name].manual_reset()
            logger.info(f"Reset circuit breaker for {tool_name}")
        else:
            logger.warning(f"Tool {tool_name} not found")
    
    def reset_all(self):
        """모든 도구 리셋"""
        for breaker in self.circuit_breakers.values():
            breaker.manual_reset()
        logger.info("Reset all circuit breakers")


# 전역 인스턴스
self_healing_manager = SelfHealingManager()


# 사용 예시 데코레이터
def with_self_healing(tool_name: str, 
                      failure_threshold: int = 3,
                      timeout_threshold: int = 3):
    """
    Self-healing 데코레이터
    
    사용법:
        @with_self_healing("run_command", failure_threshold=3, timeout_threshold=3)
        def run_command(cmd: str):
            # 구현
            pass
    """
    if tool_name not in self_healing_manager.circuit_breakers:
        self_healing_manager.register_tool(
            tool_name=tool_name,
            failure_threshold=failure_threshold,
            timeout_threshold=timeout_threshold
        )
    
    return self_healing_manager.protect(tool_name)
