#!/usr/bin/env python3
"""
Benchmarking Tool
보안 스캐너 및 도구 성능 벤치마크
"""

import time
import statistics
import json
from datetime import datetime
from typing import List, Dict, Callable
import logging

logger = logging.getLogger(__name__)


class Benchmark:
    """벤치마크 실행기"""
    
    def __init__(self, name: str):
        self.name = name
        self.results: List[float] = []
    
    def run(self, func: Callable, iterations: int = 10, warmup: int = 2):
        """
        벤치마크 실행
        
        Args:
            func: 실행할 함수
            iterations: 반복 횟수
            warmup: 워밍업 반복 횟수
        """
        print(f"\n🔬 Benchmarking: {self.name}")
        print(f"   Iterations: {iterations} (+ {warmup} warmup)")
        
        # Warmup
        for i in range(warmup):
            func()
            print(f"   Warmup {i+1}/{warmup}... ✓")
        
        # Actual benchmark
        self.results = []
        for i in range(iterations):
            start = time.perf_counter()
            func()
            elapsed = (time.perf_counter() - start) * 1000  # ms
            
            self.results.append(elapsed)
            print(f"   Run {i+1}/{iterations}: {elapsed:.2f}ms")
        
        self._print_stats()
    
    def _print_stats(self):
        """통계 출력"""
        if not self.results:
            return
        
        print(f"\n📊 Results for {self.name}:")
        print(f"   Average: {statistics.mean(self.results):.2f}ms")
        print(f"   Median:  {statistics.median(self.results):.2f}ms")
        print(f"   Min:     {min(self.results):.2f}ms")
        print(f"   Max:     {max(self.results):.2f}ms")
        print(f"   StdDev:  {statistics.stdev(self.results):.2f}ms")
    
    def get_stats(self) -> Dict:
        """통계 반환"""
        if not self.results:
            return {}
        
        return {
            "name": self.name,
            "iterations": len(self.results),
            "avg_ms": round(statistics.mean(self.results), 2),
            "median_ms": round(statistics.median(self.results), 2),
            "min_ms": round(min(self.results), 2),
            "max_ms": round(max(self.results), 2),
            "stddev_ms": round(statistics.stdev(self.results), 2)
        }


class SecurityScannerBenchmark:
    """보안 스캐너 벤치마크"""
    
    def __init__(self):
        self.baseline_results = None
        self.optimized_results = None
    
    def run_baseline(self, iterations: int = 10):
        """기존 버전 벤치마크"""
        bench = Benchmark("Security Scanner - Baseline")
        
        def baseline_scan():
            import subprocess
            result = subprocess.run(
                ['python3', 'security_audit.py'],
                capture_output=True,
                timeout=30
            )
            return result.returncode == 0
        
        bench.run(baseline_scan, iterations=iterations)
        self.baseline_results = bench.get_stats()
        return self.baseline_results
    
    def run_optimized(self, iterations: int = 10):
        """최적화 버전 벤치마크"""
        # 최적화된 스캐너 생성
        self._create_optimized_scanner()
        
        bench = Benchmark("Security Scanner - Optimized")
        
        def optimized_scan():
            import subprocess
            result = subprocess.run(
                ['python3', 'security_audit_optimized.py'],
                capture_output=True,
                timeout=30
            )
            return result.returncode == 0
        
        bench.run(optimized_scan, iterations=iterations)
        self.optimized_results = bench.get_stats()
        return self.optimized_results
    
    def _create_optimized_scanner(self):
        """최적화된 스캐너 생성"""
        optimized_code = '''#!/usr/bin/env python3
"""
Optimized Security Audit Script
- 병렬 처리
- 캐싱
- 조기 종료
"""

import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

def check_configuration():
    """설정 확인 (최적화)"""
    required = [
        ('.env', os.path.exists('.env')),
        ('.env.example', os.path.exists('.env.example')),
        ('config.py', os.path.exists('config.py')),
        ('security.py', os.path.exists('security.py')),
    ]
    
    passed = sum(1 for _, exists in required if exists)
    return passed, len(required)

def check_security_features():
    """보안 기능 확인 (캐싱)"""
    if not os.path.exists('server.py'):
        return 0, 1
    
    # 한 번만 읽기
    with open('server.py', 'r') as f:
        content = f.read()
    
    checks = [
        'from security import' in content,
        'from config import' in content,
        'shell=False' in content,
        'validate_' in content,
    ]
    
    return sum(checks), len(checks)

def check_hardcoded_paths():
    """하드코딩 확인 (조기 종료)"""
    if not os.path.exists('server.py'):
        return 0, 1
    
    with open('server.py', 'r') as f:
        for line in f:
            if '/Users/' in line and 'BASE_DIR' not in line:
                if not line.strip().startswith('#'):
                    return 0, 1
    
    return 1, 1

def main():
    """병렬 실행"""
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(check_configuration): 'config',
            executor.submit(check_security_features): 'security',
            executor.submit(check_hardcoded_paths): 'paths'
        }
        
        total_pass = 0
        total_checks = 0
        
        for future in as_completed(futures):
            passed, checks = future.result()
            total_pass += passed
            total_checks += checks
    
    score = (total_pass / total_checks) * 100 if total_checks > 0 else 0
    
    print(f"Score: {score:.1f}/100")
    return 0 if score >= 90 else 1

if __name__ == "__main__":
    sys.exit(main())
'''
        
        with open('security_audit_optimized.py', 'w') as f:
            f.write(optimized_code)
        
        os.chmod('security_audit_optimized.py', 0o755)
    
    def compare(self) -> Dict:
        """결과 비교"""
        if not self.baseline_results or not self.optimized_results:
            return {"error": "Run both benchmarks first"}
        
        baseline_avg = self.baseline_results['avg_ms']
        optimized_avg = self.optimized_results['avg_ms']
        
        improvement_ms = baseline_avg - optimized_avg
        improvement_pct = (improvement_ms / baseline_avg) * 100
        
        return {
            "baseline": self.baseline_results,
            "optimized": self.optimized_results,
            "improvement_ms": round(improvement_ms, 2),
            "improvement_percent": round(improvement_pct, 2),
            "faster": improvement_ms > 0
        }
    
    def generate_report(self) -> str:
        """벤치마크 리포트 생성"""
        comparison = self.compare()
        
        if "error" in comparison:
            return comparison["error"]
        
        report = []
        report.append("# 🚀 Benchmark Report: Security Scanner")
        report.append(f"\n**Date**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        
        report.append("## Baseline Performance")
        report.append(f"- Average: {comparison['baseline']['avg_ms']}ms")
        report.append(f"- Median: {comparison['baseline']['median_ms']}ms")
        report.append(f"- Min: {comparison['baseline']['min_ms']}ms")
        report.append(f"- Max: {comparison['baseline']['max_ms']}ms\n")
        
        report.append("## Optimized Performance")
        report.append(f"- Average: {comparison['optimized']['avg_ms']}ms")
        report.append(f"- Median: {comparison['optimized']['median_ms']}ms")
        report.append(f"- Min: {comparison['optimized']['min_ms']}ms")
        report.append(f"- Max: {comparison['optimized']['max_ms']}ms\n")
        
        report.append("## Improvement")
        if comparison['faster']:
            report.append(f"✅ **{comparison['improvement_percent']:.1f}% faster**")
            report.append(f"- Reduced by {comparison['improvement_ms']:.2f}ms")
        else:
            report.append(f"⚠️ No improvement detected")
        
        report.append("\n## Optimizations Applied")
        report.append("1. **Parallel Processing**: ThreadPoolExecutor for concurrent checks")
        report.append("2. **Caching**: Read files once and reuse content")
        report.append("3. **Early Exit**: Stop checking on first failure")
        report.append("4. **Reduced I/O**: Minimize file system operations")
        
        return "\n".join(report)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Benchmark Tool')
    parser.add_argument('--iterations', type=int, default=10, help='Number of iterations')
    parser.add_argument('--security-scanner', action='store_true', help='Benchmark security scanner')
    
    args = parser.parse_args()
    
    if args.security_scanner:
        bench = SecurityScannerBenchmark()
        
        print("Running baseline benchmark...")
        bench.run_baseline(args.iterations)
        
        print("\nCreating optimized version...")
        print("Running optimized benchmark...")
        bench.run_optimized(args.iterations)
        
        print("\n" + bench.generate_report())
        
        # Save report
        report = bench.generate_report()
        filename = f"logs/benchmark_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md"
        os.makedirs('logs', exist_ok=True)
        with open(filename, 'w') as f:
            f.write(report)
        print(f"\nReport saved: {filename}")
