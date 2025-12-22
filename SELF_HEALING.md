# Self-Healing 적용 예시

## server.py에 적용하기

```python
from self_healing import with_self_healing

# 기존 코드
@mcp.tool()
@command_limiter
def run_command(command: str) -> str:
    # ...
    
# Self-Healing 적용
@mcp.tool()
@command_limiter
@with_self_healing("run_command", timeout_threshold=3)
def run_command(command: str) -> str:
    # 기존 구현
    # 3번 타임아웃 발생 시 자동으로 60초간 비활성화
    pass
```

## 모니터링과 연동

```python
from monitoring import monitoring_service
from self_healing import self_healing_manager

# 도구 호출 시
start_time = time.time()
try:
    result = run_command(cmd)
    response_time = (time.time() - start_time) * 1000
    monitoring_service.tool_monitor.record_call(
        "run_command", response_time, True
    )
except TimeoutError as e:
    response_time = (time.time() - start_time) * 1000
    monitoring_service.tool_monitor.record_call(
        "run_command", response_time, False, "timeout"
    )
```

## 상태 확인

```python
# 모든 도구 상태
status = self_healing_manager.get_status()
print(status)

# 특정 도구 리셋
self_healing_manager.reset_tool("run_command")
```
