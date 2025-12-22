#!/usr/bin/env python3
"""
SRE Monitoring Tool for MCP AI Agent
실시간 시스템 메트릭 수집 및 로깅
"""

import os
import time
import psutil
import logging
import json
from datetime import datetime
from typing import Dict, List
from collections import deque
from dataclasses import dataclass, asdict

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monitoring.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """시스템 메트릭 데이터 클래스"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float


@dataclass
class ToolMetrics:
    """MCP 도구 성능 메트릭"""
    tool_name: str
    response_time_ms: float
    success: bool
    error: str = None


class CircularBuffer:
    """순환 버퍼 (최근 N개 항목만 유지)"""
    
    def __init__(self, max_size: int = 100):
        self.buffer = deque(maxlen=max_size)
    
    def append(self, item):
        self.buffer.append(item)
    
    def get_all(self) -> List:
        return list(self.buffer)
    
    def get_average(self, key: str) -> float:
        """특정 키의 평균값 계산"""
        values = [getattr(item, key) for item in self.buffer if hasattr(item, key)]
        return sum(values) / len(values) if values else 0.0


class SystemMonitor:
    """시스템 리소스 모니터링"""
    
    def __init__(self):
        self.metrics_buffer = CircularBuffer(max_size=1000)
        self.process = psutil.Process(os.getpid())
    
    def collect_metrics(self) -> SystemMetrics:
        """시스템 메트릭 수집"""
        try:
            # CPU 사용률
            cpu_percent = self.process.cpu_percent(interval=1)
            
            # 메모리 사용률
            mem_info = self.process.memory_info()
            mem_percent = self.process.memory_percent()
            
            # 시스템 메모리
            virtual_mem = psutil.virtual_memory()
            
            # 디스크 사용률
            disk_usage = psutil.disk_usage('/')
            
            metrics = SystemMetrics(
                timestamp=datetime.utcnow().isoformat(),
                cpu_percent=round(cpu_percent, 2),
                memory_percent=round(mem_percent, 2),
                memory_used_mb=round(mem_info.rss / 1024 / 1024, 2),
                memory_available_mb=round(virtual_mem.available / 1024 / 1024, 2),
                disk_usage_percent=round(disk_usage.percent, 2),
                disk_free_gb=round(disk_usage.free / 1024 / 1024 / 1024, 2)
            )
            
            self.metrics_buffer.append(metrics)
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            return None
    
    def get_stats(self) -> Dict:
        """메트릭 통계 생성"""
        return {
            "avg_cpu": self.metrics_buffer.get_average('cpu_percent'),
            "avg_memory": self.metrics_buffer.get_average('memory_percent'),
            "samples": len(self.metrics_buffer.get_all())
        }
    
    def check_health(self) -> Dict:
        """시스템 건강 상태 확인"""
        metrics = self.collect_metrics()
        if not metrics:
            return {"status": "unhealthy", "reason": "Failed to collect metrics"}
        
        issues = []
        
        # CPU 체크
        if metrics.cpu_percent > 80:
            issues.append(f"High CPU usage: {metrics.cpu_percent}%")
        
        # 메모리 체크
        if metrics.memory_percent > 80:
            issues.append(f"High memory usage: {metrics.memory_percent}%")
        
        # 디스크 체크
        if metrics.disk_usage_percent > 90:
            issues.append(f"Low disk space: {metrics.disk_free_gb}GB free")
        
        return {
            "status": "healthy" if not issues else "warning",
            "issues": issues,
            "metrics": asdict(metrics)
        }


class ToolPerformanceMonitor:
    """MCP 도구 성능 모니터링"""
    
    def __init__(self):
        self.tool_metrics = {}  # tool_name -> CircularBuffer
        self.timeout_counts = {}  # tool_name -> count
    
    def record_call(self, tool_name: str, response_time_ms: float, 
                   success: bool, error: str = None):
        """도구 호출 기록"""
        if tool_name not in self.tool_metrics:
            self.tool_metrics[tool_name] = CircularBuffer(max_size=100)
            self.timeout_counts[tool_name] = 0
        
        metric = ToolMetrics(
            tool_name=tool_name,
            response_time_ms=response_time_ms,
            success=success,
            error=error
        )
        
        self.tool_metrics[tool_name].append(metric)
        
        # 타임아웃 카운트
        if error and "timeout" in error.lower():
            self.timeout_counts[tool_name] += 1
            logger.warning(f"Timeout in {tool_name}: {self.timeout_counts[tool_name]} times")
        
        # 로깅
        if success:
            logger.info(f"{tool_name}: {response_time_ms}ms")
        else:
            logger.error(f"{tool_name} failed: {error}")
    
    def get_tool_stats(self, tool_name: str) -> Dict:
        """특정 도구의 통계"""
        if tool_name not in self.tool_metrics:
            return {"error": "Tool not found"}
        
        buffer = self.tool_metrics[tool_name]
        metrics = buffer.get_all()
        
        if not metrics:
            return {"error": "No data"}
        
        response_times = [m.response_time_ms for m in metrics]
        success_rate = sum(1 for m in metrics if m.success) / len(metrics) * 100
        
        return {
            "tool_name": tool_name,
            "avg_response_time_ms": round(sum(response_times) / len(response_times), 2),
            "min_response_time_ms": round(min(response_times), 2),
            "max_response_time_ms": round(max(response_times), 2),
            "success_rate": round(success_rate, 2),
            "timeout_count": self.timeout_counts.get(tool_name, 0),
            "total_calls": len(metrics)
        }
    
    def get_all_stats(self) -> Dict:
        """모든 도구 통계"""
        return {
            tool: self.get_tool_stats(tool)
            for tool in self.tool_metrics.keys()
        }
    
    def should_disable_tool(self, tool_name: str) -> bool:
        """도구 비활성화 여부 판단 (3회 이상 타임아웃)"""
        return self.timeout_counts.get(tool_name, 0) >= 3
    
    def reset_timeout_count(self, tool_name: str):
        """타임아웃 카운트 리셋"""
        if tool_name in self.timeout_counts:
            self.timeout_counts[tool_name] = 0
            logger.info(f"Reset timeout count for {tool_name}")


class MonitoringService:
    """통합 모니터링 서비스"""
    
    def __init__(self, interval: int = 60):
        self.interval = interval
        self.system_monitor = SystemMonitor()
        self.tool_monitor = ToolPerformanceMonitor()
        self.running = False
    
    def start(self):
        """모니터링 시작"""
        self.running = True
        logger.info("Monitoring service started")
        
        try:
            while self.running:
                # 시스템 메트릭 수집
                health = self.system_monitor.check_health()
                
                # 로그 출력
                logger.info(f"System Health: {health['status']}")
                if health['issues']:
                    for issue in health['issues']:
                        logger.warning(f"⚠️  {issue}")
                
                # 도구 통계 출력
                tool_stats = self.tool_monitor.get_all_stats()
                if tool_stats:
                    logger.info(f"Tool Performance: {json.dumps(tool_stats, indent=2)}")
                
                # 자가 치유 체크
                self.check_self_healing()
                
                # 대기
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            logger.info("Monitoring service stopped by user")
        except Exception as e:
            logger.error(f"Monitoring service error: {e}", exc_info=True)
        finally:
            self.running = False
    
    def stop(self):
        """모니터링 중지"""
        self.running = False
        logger.info("Monitoring service stopped")
    
    def check_self_healing(self):
        """자가 치유 로직"""
        for tool_name in self.tool_monitor.tool_metrics.keys():
            if self.tool_monitor.should_disable_tool(tool_name):
                logger.critical(f"🚨 SELF-HEALING: Disabling {tool_name} due to repeated timeouts")
                # 실제 비활성화 로직은 server.py에서 구현
                # 여기서는 알림만 수행
    
    def get_report(self) -> Dict:
        """전체 모니터링 리포트"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system": self.system_monitor.check_health(),
            "system_stats": self.system_monitor.get_stats(),
            "tools": self.tool_monitor.get_all_stats()
        }
    
    def save_report(self, filename: str = None):
        """리포트를 파일로 저장"""
        if filename is None:
            filename = f"logs/monitoring_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump(self.get_report(), f, indent=2)
        
        logger.info(f"Report saved to {filename}")


# 전역 모니터링 인스턴스
monitoring_service = MonitoringService(interval=60)


def start_monitoring(interval: int = 60):
    """모니터링 시작 (별도 프로세스/스레드에서 실행)"""
    service = MonitoringService(interval=interval)
    service.start()


if __name__ == "__main__":
    # 독립 실행 시
    import argparse
    
    parser = argparse.ArgumentParser(description='MCP Agent Monitoring')
    parser.add_argument('--interval', type=int, default=60, help='Monitoring interval in seconds')
    parser.add_argument('--report', action='store_true', help='Generate report and exit')
    
    args = parser.parse_args()
    
    service = MonitoringService(interval=args.interval)
    
    if args.report:
        # 리포트만 생성
        report = service.get_report()
        print(json.dumps(report, indent=2))
        service.save_report()
    else:
        # 계속 모니터링
        service.start()
