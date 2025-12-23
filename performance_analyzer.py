#!/usr/bin/env python3
"""
Performance Analyzer for MCP AI Agent
도구별 성능 분석 및 최적화 제안 생성
"""

import json
import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import statistics

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """도구 호출 기록"""
    tool_name: str
    timestamp: str
    response_time_ms: float
    success: bool
    error: Optional[str] = None
    timeout: bool = False


@dataclass
class ToolStatistics:
    """도구 통계"""
    tool_name: str
    total_calls: int
    success_count: int
    failure_count: int
    timeout_count: int
    success_rate: float
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    median_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    common_errors: List[Tuple[str, int]]


class PerformanceAnalyzer:
    """성능 분석기"""
    
    def __init__(self, log_file: str = "logs/performance.log"):
        self.log_file = log_file
        self.calls: List[ToolCall] = []
        self._ensure_log_file()
    
    def _ensure_log_file(self):
        """로그 파일 생성"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                json.dump([], f)
    
    def record_call(self, tool_name: str, response_time_ms: float, 
                   success: bool, error: Optional[str] = None):
        """도구 호출 기록"""
        call = ToolCall(
            tool_name=tool_name,
            timestamp=datetime.utcnow().isoformat(),
            response_time_ms=response_time_ms,
            success=success,
            error=error,
            timeout="timeout" in (error or "").lower()
        )
        
        self.calls.append(call)
        self._append_to_log(call)
    
    def _append_to_log(self, call: ToolCall):
        """로그 파일에 추가"""
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
            
            data.append(asdict(call))
            
            with open(self.log_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to append to log: {e}")
    
    def load_history(self, days: int = 7) -> List[ToolCall]:
        """히스토리 로드"""
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
            
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            calls = []
            for item in data:
                timestamp = datetime.fromisoformat(item['timestamp'])
                if timestamp >= cutoff:
                    calls.append(ToolCall(**item))
            
            return calls
            
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            return []
    
    def analyze_tool(self, tool_name: str, calls: List[ToolCall]) -> ToolStatistics:
        """특정 도구 분석"""
        tool_calls = [c for c in calls if c.tool_name == tool_name]
        
        if not tool_calls:
            return None
        
        total = len(tool_calls)
        success_count = sum(1 for c in tool_calls if c.success)
        failure_count = total - success_count
        timeout_count = sum(1 for c in tool_calls if c.timeout)
        
        response_times = [c.response_time_ms for c in tool_calls]
        
        # 에러 집계
        error_counts = defaultdict(int)
        for call in tool_calls:
            if call.error:
                error_counts[call.error] += 1
        
        common_errors = sorted(
            error_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        # Percentile 계산
        sorted_times = sorted(response_times)
        p95_idx = int(len(sorted_times) * 0.95)
        p99_idx = int(len(sorted_times) * 0.99)
        
        return ToolStatistics(
            tool_name=tool_name,
            total_calls=total,
            success_count=success_count,
            failure_count=failure_count,
            timeout_count=timeout_count,
            success_rate=round(success_count / total * 100, 2),
            avg_response_time_ms=round(statistics.mean(response_times), 2),
            min_response_time_ms=round(min(response_times), 2),
            max_response_time_ms=round(max(response_times), 2),
            median_response_time_ms=round(statistics.median(response_times), 2),
            p95_response_time_ms=round(sorted_times[p95_idx], 2),
            p99_response_time_ms=round(sorted_times[p99_idx], 2),
            common_errors=common_errors
        )
    
    def analyze_all(self, days: int = 7) -> Dict[str, ToolStatistics]:
        """모든 도구 분석"""
        calls = self.load_history(days)
        
        tool_names = set(c.tool_name for c in calls)
        
        results = {}
        for tool_name in tool_names:
            stats = self.analyze_tool(tool_name, calls)
            if stats:
                results[tool_name] = stats
        
        return results
    
    def generate_report(self, days: int = 7) -> Dict:
        """분석 리포트 생성"""
        stats = self.analyze_all(days)
        
        # 문제 도구 식별
        problem_tools = []
        slow_tools = []
        timeout_tools = []
        
        for tool_name, tool_stats in stats.items():
            # 성공률 낮음
            if tool_stats.success_rate < 90:
                problem_tools.append({
                    "tool": tool_name,
                    "success_rate": tool_stats.success_rate,
                    "issue": "Low success rate"
                })
            
            # 느림
            if tool_stats.avg_response_time_ms > 5000:
                slow_tools.append({
                    "tool": tool_name,
                    "avg_time": tool_stats.avg_response_time_ms,
                    "issue": "Slow response"
                })
            
            # 타임아웃 많음
            if tool_stats.timeout_count >= 3:
                timeout_tools.append({
                    "tool": tool_name,
                    "timeout_count": tool_stats.timeout_count,
                    "issue": "Frequent timeouts"
                })
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "analysis_period_days": days,
            "statistics": {name: asdict(stat) for name, stat in stats.items()},
            "issues": {
                "problem_tools": problem_tools,
                "slow_tools": slow_tools,
                "timeout_tools": timeout_tools
            }
        }
    
    def save_report(self, filename: str = None):
        """리포트 저장"""
        if filename is None:
            filename = f"logs/performance_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = self.generate_report()
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to {filename}")
        return filename


class OptimizationAdvisor:
    """최적화 제안 생성기"""
    
    def __init__(self, analyzer: PerformanceAnalyzer):
        self.analyzer = analyzer
    
    def generate_suggestions(self, days: int = 7) -> List[Dict]:
        """최적화 제안 생성"""
        stats = self.analyzer.analyze_all(days)
        suggestions = []
        
        for tool_name, tool_stats in stats.items():
            # 1. 타임아웃 문제
            if tool_stats.timeout_count >= 3:
                suggestions.append({
                    "priority": "HIGH",
                    "tool": tool_name,
                    "issue": "Frequent timeouts",
                    "current_avg_time": tool_stats.avg_response_time_ms,
                    "p99_time": tool_stats.p99_response_time_ms,
                    "recommendation": f"Increase timeout from default to {int(tool_stats.p99_response_time_ms / 1000) + 5}s",
                    "code_change": self._generate_timeout_fix(tool_name, tool_stats)
                })
            
            # 2. 성공률 문제
            if tool_stats.success_rate < 90:
                suggestions.append({
                    "priority": "HIGH",
                    "tool": tool_name,
                    "issue": "Low success rate",
                    "current_success_rate": tool_stats.success_rate,
                    "common_errors": tool_stats.common_errors[:3],
                    "recommendation": "Add retry logic with exponential backoff",
                    "code_change": self._generate_retry_logic(tool_name)
                })
            
            # 3. 성능 문제
            if tool_stats.avg_response_time_ms > 5000:
                suggestions.append({
                    "priority": "MEDIUM",
                    "tool": tool_name,
                    "issue": "Slow performance",
                    "current_avg_time": tool_stats.avg_response_time_ms,
                    "recommendation": "Consider caching, async processing, or parallelization",
                    "code_change": self._generate_optimization_suggestion(tool_name, tool_stats)
                })
            
            # 4. 병렬화 가능
            if tool_stats.total_calls > 100 and tool_stats.avg_response_time_ms > 1000:
                suggestions.append({
                    "priority": "LOW",
                    "tool": tool_name,
                    "issue": "High usage with long response time",
                    "total_calls": tool_stats.total_calls,
                    "recommendation": "Consider implementing async/parallel execution",
                    "code_change": self._generate_async_pattern(tool_name)
                })
        
        return sorted(suggestions, key=lambda x: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[x["priority"]])
    
    def _generate_timeout_fix(self, tool_name: str, stats: ToolStatistics) -> str:
        """타임아웃 수정 코드 생성"""
        new_timeout = int(stats.p99_response_time_ms / 1000) + 5
        
        return f"""
# Increase timeout for {tool_name}
# Current: default timeout
# Recommended: {new_timeout}s based on P99 latency

@mcp.tool()
def {tool_name}(...):
    result = subprocess.run(
        ...,
        timeout={new_timeout},  # Increased from default
        ...
    )
"""
    
    def _generate_retry_logic(self, tool_name: str) -> str:
        """재시도 로직 생성"""
        return f"""
# Add retry logic to {tool_name}
import time

@mcp.tool()
def {tool_name}(...):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Original logic
            result = perform_operation()
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt  # Exponential backoff
            logger.warning(f"Retry {{attempt + 1}}/{{max_retries}} after {{wait_time}}s")
            time.sleep(wait_time)
"""
    
    def _generate_optimization_suggestion(self, tool_name: str, stats: ToolStatistics) -> str:
        """최적화 제안 생성"""
        return f"""
# Optimization options for {tool_name}
# Current avg: {stats.avg_response_time_ms}ms

# Option 1: Caching
from functools import lru_cache

@lru_cache(maxsize=100)
def {tool_name}_cached(key):
    return expensive_operation(key)

# Option 2: Async processing
import asyncio

async def {tool_name}_async(...):
    result = await async_operation()
    return result

# Option 3: Batch processing
def {tool_name}_batch(items):
    return [process(item) for item in items]
"""
    
    def _generate_async_pattern(self, tool_name: str) -> str:
        """비동기 패턴 생성"""
        return f"""
# Async pattern for {tool_name}
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def {tool_name}_parallel(items):
    with ThreadPoolExecutor() as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, {tool_name}, item)
            for item in items
        ]
        return await asyncio.gather(*tasks)
"""
    
    def generate_architecture_proposal(self, days: int = 7) -> str:
        """아키텍처 개선 제안서 생성"""
        suggestions = self.generate_suggestions(days)
        stats = self.analyzer.analyze_all(days)
        
        proposal = []
        proposal.append("# 🏗️ Architecture Improvement Proposal")
        proposal.append(f"\n**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        proposal.append(f"**Analysis Period**: Last {days} days\n")
        
        # Executive Summary
        proposal.append("## 📊 Executive Summary\n")
        proposal.append(f"- **Total Tools Analyzed**: {len(stats)}")
        proposal.append(f"- **Issues Identified**: {len(suggestions)}")
        proposal.append(f"- **High Priority**: {sum(1 for s in suggestions if s['priority'] == 'HIGH')}")
        proposal.append(f"- **Medium Priority**: {sum(1 for s in suggestions if s['priority'] == 'MEDIUM')}")
        proposal.append(f"- **Low Priority**: {sum(1 for s in suggestions if s['priority'] == 'LOW')}\n")
        
        # High Priority Issues
        high_priority = [s for s in suggestions if s['priority'] == 'HIGH']
        if high_priority:
            proposal.append("## 🚨 High Priority Issues\n")
            for i, suggestion in enumerate(high_priority, 1):
                proposal.append(f"### {i}. {suggestion['tool']}: {suggestion['issue']}\n")
                proposal.append(f"**Recommendation**: {suggestion['recommendation']}\n")
                proposal.append("**Proposed Code Change**:")
                proposal.append("```python")
                proposal.append(suggestion['code_change'].strip())
                proposal.append("```\n")
        
        # Medium Priority
        medium_priority = [s for s in suggestions if s['priority'] == 'MEDIUM']
        if medium_priority:
            proposal.append("## ⚠️ Medium Priority Optimizations\n")
            for suggestion in medium_priority:
                proposal.append(f"- **{suggestion['tool']}**: {suggestion['recommendation']}")
        
        # Performance Metrics
        proposal.append("\n## 📈 Performance Metrics\n")
        proposal.append("| Tool | Calls | Success Rate | Avg Time | P95 Time | P99 Time |")
        proposal.append("|------|-------|--------------|----------|----------|----------|")
        
        for tool_name, tool_stats in sorted(stats.items(), key=lambda x: x[1].avg_response_time_ms, reverse=True):
            proposal.append(
                f"| {tool_name} | {tool_stats.total_calls} | "
                f"{tool_stats.success_rate}% | {tool_stats.avg_response_time_ms:.0f}ms | "
                f"{tool_stats.p95_response_time_ms:.0f}ms | {tool_stats.p99_response_time_ms:.0f}ms |"
            )
        
        proposal.append("\n## 🎯 Implementation Roadmap\n")
        proposal.append("1. **Week 1**: Address high priority timeout issues")
        proposal.append("2. **Week 2**: Implement retry logic for unreliable tools")
        proposal.append("3. **Week 3**: Optimize slow tools with caching")
        proposal.append("4. **Week 4**: Consider async patterns for high-traffic tools\n")
        
        return "\n".join(proposal)
    
    def save_proposal(self, filename: str = None):
        """제안서 저장"""
        if filename is None:
            filename = f"logs/architecture_proposal_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md"
        
        proposal = self.generate_architecture_proposal()
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as f:
            f.write(proposal)
        
        logger.info(f"Proposal saved to {filename}")
        return filename


# 전역 인스턴스
performance_analyzer = PerformanceAnalyzer()
optimization_advisor = OptimizationAdvisor(performance_analyzer)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Performance Analyzer')
    parser.add_argument('--report', action='store_true', help='Generate performance report')
    parser.add_argument('--proposal', action='store_true', help='Generate architecture proposal')
    parser.add_argument('--days', type=int, default=7, help='Analysis period in days')
    
    args = parser.parse_args()
    
    if args.report:
        filename = performance_analyzer.save_report()
        print(f"Report saved: {filename}")
    
    if args.proposal:
        filename = optimization_advisor.save_proposal()
        print(f"Proposal saved: {filename}")
        
        # Print to console
        print("\n" + optimization_advisor.generate_architecture_proposal(args.days))
