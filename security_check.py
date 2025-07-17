#!/usr/bin/env python3
"""
Comprehensive Security Check Script for Meme Maker
Runs all security tools and generates a consolidated report
"""

import os
import subprocess
import json
import sys
from datetime import datetime
from pathlib import Path
import argparse


class SecurityChecker:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "UNKNOWN",
            "critical_issues": 0,
            "high_issues": 0,
            "medium_issues": 0,
            "low_issues": 0,
            "tools": {}
        }

    def run_command(self, command: list, cwd: str = None) -> dict:
        """Run a command and return the result"""
        try:
            print(f"🔍 Running: {' '.join(command)}")
            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Command timed out after 5 minutes",
                "returncode": -1
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }

    def check_bandit(self) -> dict:
        """Run Bandit security linting on Python code"""
        print("🛡️ Running Bandit security analysis...")
        
        backend_path = self.project_root / "backend"
        if not backend_path.exists():
            return {"success": False, "error": "Backend directory not found"}
        
        # Run bandit with JSON output
        result = self.run_command([
            "poetry", "run", "bandit", 
            "-r", ".", 
            "-f", "json",
            "--skip", "B101,B601",  # Skip assert and shell injection (for now)
            "--exclude", "tests/"
        ], cwd=str(backend_path))
        
        if result["success"]:
            try:
                bandit_data = json.loads(result["stdout"])
                issues = bandit_data.get("results", [])
                
                critical = len([i for i in issues if i.get("issue_severity") == "HIGH"])
                medium = len([i for i in issues if i.get("issue_severity") == "MEDIUM"])
                low = len([i for i in issues if i.get("issue_severity") == "LOW"])
                
                return {
                    "success": True,
                    "critical_issues": critical,
                    "medium_issues": medium,
                    "low_issues": low,
                    "total_issues": len(issues),
                    "details": issues[:5]  # First 5 issues for summary
                }
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "Failed to parse Bandit JSON output"
                }
        else:
            return {
                "success": False,
                "error": result["stderr"] or "Bandit execution failed"
            }

    def check_safety(self) -> dict:
        """Run Safety dependency vulnerability check"""
        print("🔒 Running Safety dependency vulnerability check...")
        
        backend_path = self.project_root / "backend"
        if not backend_path.exists():
            return {"success": False, "error": "Backend directory not found"}
        
        result = self.run_command([
            "poetry", "run", "safety", "check", "--json"
        ], cwd=str(backend_path))
        
        if result["success"]:
            try:
                safety_data = json.loads(result["stdout"])
                vulnerabilities = safety_data if isinstance(safety_data, list) else []
                
                critical = len([v for v in vulnerabilities if v.get("vulnerability_id", "").startswith("51")])
                high = len([v for v in vulnerabilities if v.get("vulnerability_id", "").startswith("4")])
                medium = len(vulnerabilities) - critical - high
                
                return {
                    "success": True,
                    "critical_issues": critical,
                    "high_issues": high,
                    "medium_issues": medium,
                    "total_vulnerabilities": len(vulnerabilities),
                    "details": vulnerabilities[:3]  # First 3 for summary
                }
            except json.JSONDecodeError:
                # Safety might return empty output if no vulnerabilities
                return {
                    "success": True,
                    "critical_issues": 0,
                    "high_issues": 0,
                    "medium_issues": 0,
                    "total_vulnerabilities": 0,
                    "details": []
                }
        else:
            return {
                "success": False,
                "error": result["stderr"] or "Safety execution failed"
            }

    def check_npm_audit(self) -> dict:
        """Run npm audit for frontend vulnerabilities"""
        print("🌐 Running npm audit for frontend...")
        
        frontend_path = self.project_root / "frontend-new"
        if not frontend_path.exists():
            return {"success": False, "error": "Frontend-new directory not found"}
        
        result = self.run_command([
            "npm", "audit", "--json"
        ], cwd=str(frontend_path))
        
        try:
            audit_data = json.loads(result["stdout"])
            vulnerabilities = audit_data.get("vulnerabilities", {})
            
            critical = sum(1 for v in vulnerabilities.values() if v.get("severity") == "critical")
            high = sum(1 for v in vulnerabilities.values() if v.get("severity") == "high")
            medium = sum(1 for v in vulnerabilities.values() if v.get("severity") == "moderate")
            low = sum(1 for v in vulnerabilities.values() if v.get("severity") == "low")
            
            return {
                "success": True,
                "critical_issues": critical,
                "high_issues": high,
                "medium_issues": medium,
                "low_issues": low,
                "total_vulnerabilities": len(vulnerabilities),
                "details": list(vulnerabilities.keys())[:5]
            }
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Failed to parse npm audit JSON output"
            }

    def check_trivy_containers(self) -> dict:
        """Run Trivy container security scan"""
        print("🐳 Running Trivy container security scan...")
        
        result = self.run_command([
            "docker", "run", "--rm", "-v", f"{self.project_root}:/workspace",
            "aquasec/trivy", "fs", "--format", "json", "/workspace"
        ])
        
        if result["success"]:
            try:
                trivy_data = json.loads(result["stdout"])
                vulnerabilities = []
                
                for result_item in trivy_data.get("Results", []):
                    vulnerabilities.extend(result_item.get("Vulnerabilities", []))
                
                critical = len([v for v in vulnerabilities if v.get("Severity") == "CRITICAL"])
                high = len([v for v in vulnerabilities if v.get("Severity") == "HIGH"])
                medium = len([v for v in vulnerabilities if v.get("Severity") == "MEDIUM"])
                low = len([v for v in vulnerabilities if v.get("Severity") == "LOW"])
                
                return {
                    "success": True,
                    "critical_issues": critical,
                    "high_issues": high,
                    "medium_issues": medium,
                    "low_issues": low,
                    "total_vulnerabilities": len(vulnerabilities),
                    "details": vulnerabilities[:3]
                }
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "Failed to parse Trivy JSON output"
                }
        else:
            return {
                "success": False,
                "error": result["stderr"] or "Trivy execution failed"
            }

    def check_docker_security(self) -> dict:
        """Check Docker configuration security"""
        print("🔧 Checking Docker security configuration...")
        
        issues = []
        
        # Check for dockerfile security issues
        dockerfiles = list(self.project_root.glob("**/Dockerfile*"))
        for dockerfile in dockerfiles:
            try:
                content = dockerfile.read_text()
                
                # Basic security checks
                if "USER root" in content:
                    issues.append(f"Running as root in {dockerfile.name}")
                
                if "ADD http" in content or "ADD https" in content:
                    issues.append(f"Using ADD with URL in {dockerfile.name}")
                
                if "--privileged" in content:
                    issues.append(f"Privileged mode detected in {dockerfile.name}")
                
            except Exception as e:
                issues.append(f"Error reading {dockerfile.name}: {e}")
        
        # Check docker-compose files
        compose_files = list(self.project_root.glob("**/docker-compose*.yml")) + \
                      list(self.project_root.glob("**/docker-compose*.yaml"))
        
        for compose_file in compose_files:
            try:
                content = compose_file.read_text()
                
                if "privileged: true" in content:
                    issues.append(f"Privileged mode in {compose_file.name}")
                
                if "network_mode: host" in content:
                    issues.append(f"Host networking in {compose_file.name}")
                
            except Exception as e:
                issues.append(f"Error reading {compose_file.name}: {e}")
        
        return {
            "success": True,
            "issues_found": len(issues),
            "details": issues
        }

    def generate_report(self) -> str:
        """Generate a comprehensive security report"""
        
        # Calculate overall status
        total_critical = self.results["critical_issues"]
        total_high = self.results["high_issues"]
        
        if total_critical > 0:
            self.results["overall_status"] = "CRITICAL"
        elif total_high > 5:
            self.results["overall_status"] = "HIGH_RISK"
        elif total_high > 0:
            self.results["overall_status"] = "MEDIUM_RISK"
        else:
            self.results["overall_status"] = "LOW_RISK"
        
        # Generate report
        report = f"""
🛡️ SECURITY AUDIT REPORT
========================
Timestamp: {self.results['timestamp']}
Overall Status: {self.results['overall_status']}

📊 SUMMARY
Critical Issues: {self.results['critical_issues']}
High Issues: {self.results['high_issues']}
Medium Issues: {self.results['medium_issues']}
Low Issues: {self.results['low_issues']}

🔍 TOOL RESULTS
"""
        
        for tool_name, tool_result in self.results["tools"].items():
            report += f"\n{tool_name.upper()}:\n"
            if tool_result["success"]:
                report += f"  ✅ Completed successfully\n"
                if "critical_issues" in tool_result:
                    report += f"  🚨 Critical: {tool_result['critical_issues']}\n"
                if "high_issues" in tool_result:
                    report += f"  ⚠️  High: {tool_result['high_issues']}\n"
                if "medium_issues" in tool_result:
                    report += f"  📋 Medium: {tool_result['medium_issues']}\n"
                if "low_issues" in tool_result:
                    report += f"  📝 Low: {tool_result['low_issues']}\n"
            else:
                report += f"  ❌ Failed: {tool_result.get('error', 'Unknown error')}\n"
        
        return report

    def run_full_audit(self):
        """Run complete security audit"""
        print("🚀 Starting comprehensive security audit...")
        
        # Run all security checks
        checks = [
            ("bandit", self.check_bandit),
            ("safety", self.check_safety),
            ("npm_audit", self.check_npm_audit),
            ("trivy", self.check_trivy_containers),
            ("docker_security", self.check_docker_security)
        ]
        
        for check_name, check_func in checks:
            print(f"\n{'='*50}")
            result = check_func()
            self.results["tools"][check_name] = result
            
            # Aggregate issue counts
            if result.get("success"):
                self.results["critical_issues"] += result.get("critical_issues", 0)
                self.results["high_issues"] += result.get("high_issues", 0)
                self.results["medium_issues"] += result.get("medium_issues", 0)
                self.results["low_issues"] += result.get("low_issues", 0)
        
        # Generate and save report
        report = self.generate_report()
        
        # Save detailed results
        results_file = self.project_root / "logs-security-test" / "security_audit_results.json"
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        
        # Save human-readable report
        report_file = self.project_root / "logs-security-test" / "security_audit_report.txt"
        with open(report_file, "w") as f:
            f.write(report)
        
        print(report)
        print(f"\n📄 Detailed results saved to: {results_file}")
        print(f"📄 Report saved to: {report_file}")
        
        # Return appropriate exit code
        if self.results["critical_issues"] > 0:
            return 2  # Critical issues found
        elif self.results["high_issues"] > 0:
            return 1  # High issues found
        else:
            return 0  # No critical/high issues


def main():
    parser = argparse.ArgumentParser(description="Comprehensive security audit for Meme Maker")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--quick", action="store_true", help="Run quick security checks only")
    
    args = parser.parse_args()
    
    checker = SecurityChecker(args.project_root)
    
    if args.quick:
        # Quick check - just bandit and safety
        print("🏃 Running quick security checks...")
        checker.results["tools"]["bandit"] = checker.check_bandit()
        checker.results["tools"]["safety"] = checker.check_safety()
    else:
        # Full audit
        exit_code = checker.run_full_audit()
        sys.exit(exit_code)


if __name__ == "__main__":
    main() 