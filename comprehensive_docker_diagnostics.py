#!/usr/bin/env python3
"""
Comprehensive Docker Diagnostics Script
Follows best practices for systematic troubleshooting
"""

import subprocess
import json
import os
import sys
import time
from datetime import datetime

class DockerDiagnostics:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.results = {}
        
    def log(self, message, level="INFO"):
        """Structured logging with timestamps"""
        print(f"[{self.timestamp}] {level}: {message}")
        
    def run_command(self, command, description):
        """Run command with proper error handling and logging"""
        self.log(f"Running: {description}")
        self.log(f"Command: {' '.join(command) if isinstance(command, list) else command}")
        
        try:
            if isinstance(command, str):
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            else:
                result = subprocess.run(command, capture_output=True, text=True, timeout=30)
                
            if result.returncode == 0:
                self.log(f"✅ {description} - SUCCESS")
                return result.stdout.strip()
            else:
                self.log(f"❌ {description} - FAILED (exit code: {result.returncode})", "ERROR")
                self.log(f"STDERR: {result.stderr}", "ERROR")
                return None
                
        except subprocess.TimeoutExpired:
            self.log(f"⏰ {description} - TIMEOUT", "ERROR")
            return None
        except Exception as e:
            self.log(f"💥 {description} - EXCEPTION: {e}", "ERROR")
            return None
    
    def check_docker_system(self):
        """Check Docker system health"""
        self.log("🔍 CHECKING DOCKER SYSTEM HEALTH", "INFO")
        
        # Docker version
        version = self.run_command(["docker", "--version"], "Docker version check")
        if version:
            self.results['docker_version'] = version
            
        # Docker system info
        info = self.run_command(["docker", "system", "info", "--format", "json"], "Docker system info")
        if info:
            try:
                docker_info = json.loads(info)
                self.results['docker_info'] = {
                    'containers_running': docker_info.get('ContainersRunning', 0),
                    'containers_stopped': docker_info.get('ContainersStopped', 0),
                    'images': docker_info.get('Images', 0),
                    'storage_driver': docker_info.get('Driver', 'unknown')
                }
                self.log(f"📊 Docker stats: {self.results['docker_info']}")
            except json.JSONDecodeError:
                self.log("❌ Failed to parse Docker info JSON", "ERROR")
        
        # Check Docker daemon
        daemon_status = self.run_command(["docker", "info"], "Docker daemon connectivity")
        self.results['docker_daemon_accessible'] = daemon_status is not None
        
    def analyze_docker_compose_config(self):
        """Analyze Docker Compose configuration"""
        self.log("🔍 ANALYZING DOCKER COMPOSE CONFIGURATION", "INFO")
        
        # Check if docker-compose.yaml exists
        if not os.path.exists('docker-compose.yaml'):
            self.log("❌ docker-compose.yaml not found", "ERROR")
            return
            
        # Validate Docker Compose configuration
        config_check = self.run_command(["docker-compose", "config"], "Docker Compose config validation")
        if config_check:
            self.log("✅ Docker Compose configuration is valid")
            self.results['compose_config_valid'] = True
        else:
            self.log("❌ Docker Compose configuration is invalid", "ERROR")
            self.results['compose_config_valid'] = False
            
        # Show current compose configuration
        config_output = self.run_command(["docker-compose", "config", "--services"], "List services")
        if config_output:
            services = config_output.split('\n')
            self.log(f"📋 Services defined: {services}")
            self.results['services'] = services
    
    def check_container_states(self):
        """Check detailed container states"""
        self.log("🔍 CHECKING CONTAINER STATES", "INFO")
        
        # Get container states
        containers = self.run_command(["docker-compose", "ps", "--format", "json"], "Container states")
        if containers:
            try:
                # Handle both single JSON object and multiple lines of JSON
                container_data = []
                for line in containers.strip().split('\n'):
                    if line.strip():
                        container_data.append(json.loads(line))
                
                self.results['containers'] = container_data
                
                for container in container_data:
                    name = container.get('Name', 'unknown')
                    state = container.get('State', 'unknown')
                    ports = container.get('Ports', 'none')
                    
                    if state == 'running':
                        self.log(f"✅ {name}: {state} - Ports: {ports}")
                    else:
                        self.log(f"❌ {name}: {state} - Ports: {ports}", "ERROR")
                        
                        # Get detailed logs for failed containers
                        self.get_container_logs(name)
                        
            except json.JSONDecodeError as e:
                self.log(f"❌ Failed to parse container JSON: {e}", "ERROR")
                # Fallback to regular ps command
                self.run_command(["docker-compose", "ps"], "Container states (fallback)")
    
    def get_container_logs(self, container_name):
        """Get detailed logs for a specific container"""
        self.log(f"📋 Getting logs for {container_name}")
        
        logs = self.run_command(
            ["docker-compose", "logs", "--tail=20", container_name], 
            f"Last 20 log lines for {container_name}"
        )
        
        if logs:
            self.log(f"📝 {container_name} logs:")
            for line in logs.split('\n')[-10:]:  # Show last 10 lines
                if line.strip():
                    self.log(f"   {line}", "DEBUG")
    
    def check_nginx_configuration(self):
        """Check nginx configuration specifically"""
        self.log("🔍 CHECKING NGINX CONFIGURATION", "INFO")
        
        nginx_conf_path = "frontend-new/nginx.conf"
        if os.path.exists(nginx_conf_path):
            self.log("✅ nginx.conf exists")
            
            # Check file size and basic content
            file_size = os.path.getsize(nginx_conf_path)
            self.log(f"📏 nginx.conf size: {file_size} bytes")
            
            if file_size < 100:
                self.log("⚠️  nginx.conf seems too small", "WARNING")
                
            # Read and analyze config
            try:
                with open(nginx_conf_path, 'r') as f:
                    content = f.read()
                    
                # Check for common issues
                if 'listen 80' in content:
                    self.log("✅ nginx configured to listen on port 80")
                else:
                    self.log("❌ nginx not configured to listen on port 80", "ERROR")
                    
                if 'proxy_pass' in content:
                    self.log("✅ nginx has proxy configuration")
                else:
                    self.log("❌ nginx missing proxy configuration", "ERROR")
                    
                if 'backend:8000' in content:
                    self.log("✅ nginx configured to proxy to backend")
                else:
                    self.log("❌ nginx not configured to proxy to backend", "ERROR")
                    
                # Show the actual config (truncated)
                self.log("📄 nginx.conf content (first 20 lines):")
                for i, line in enumerate(content.split('\n')[:20]):
                    self.log(f"   {i+1:2}: {line}", "DEBUG")
                    
            except Exception as e:
                self.log(f"❌ Error reading nginx.conf: {e}", "ERROR")
        else:
            self.log("❌ nginx.conf not found", "ERROR")
    
    def check_port_availability(self):
        """Check if required ports are available"""
        self.log("🔍 CHECKING PORT AVAILABILITY", "INFO")
        
        ports_to_check = [80, 443, 8000, 6379]
        
        for port in ports_to_check:
            # Check if port is in use
            netstat_check = self.run_command(
                f"netstat -tlnp | grep :{port}", 
                f"Check if port {port} is in use"
            )
            
            if netstat_check:
                self.log(f"🔍 Port {port} is in use: {netstat_check}")
            else:
                self.log(f"✅ Port {port} appears to be free")
    
    def check_file_permissions(self):
        """Check file permissions"""
        self.log("🔍 CHECKING FILE PERMISSIONS", "INFO")
        
        files_to_check = [
            'docker-compose.yaml',
            'frontend-new/nginx.conf',
            'frontend-new/Dockerfile'
        ]
        
        for file_path in files_to_check:
            if os.path.exists(file_path):
                stat_info = os.stat(file_path)
                permissions = oct(stat_info.st_mode)[-3:]
                self.log(f"📋 {file_path}: permissions {permissions}")
            else:
                self.log(f"❌ {file_path}: not found", "ERROR")
    
    def attempt_docker_cleanup(self):
        """Attempt to clean up Docker issues"""
        self.log("🧹 ATTEMPTING DOCKER CLEANUP", "INFO")
        
        # Stop all containers
        self.run_command(["docker-compose", "down"], "Stop all containers")
        
        # Remove dangling images
        self.run_command(["docker", "image", "prune", "-f"], "Remove dangling images")
        
        # Remove unused volumes
        self.run_command(["docker", "volume", "prune", "-f"], "Remove unused volumes")
        
        # Check disk space
        df_output = self.run_command(["df", "-h", "/"], "Check disk space")
        if df_output:
            self.log(f"💾 Disk usage: {df_output}")
    
    def generate_fix_recommendations(self):
        """Generate specific fix recommendations based on findings"""
        self.log("💡 GENERATING FIX RECOMMENDATIONS", "INFO")
        
        recommendations = []
        
        if not self.results.get('docker_daemon_accessible'):
            recommendations.append("1. Restart Docker daemon: sudo systemctl restart docker")
            
        if not self.results.get('compose_config_valid'):
            recommendations.append("2. Fix Docker Compose configuration syntax errors")
            
        # Check for specific container issues
        containers = self.results.get('containers', [])
        failed_containers = [c for c in containers if c.get('State') != 'running']
        
        if failed_containers:
            recommendations.append("3. Rebuild failing containers:")
            for container in failed_containers:
                service_name = container.get('Service', 'unknown')
                recommendations.append(f"   docker-compose build --no-cache {service_name}")
                
        if not any(c.get('Name', '').endswith('frontend') and c.get('State') == 'running' for c in containers):
            recommendations.append("4. Frontend container issues detected:")
            recommendations.append("   - Check nginx.conf syntax")
            recommendations.append("   - Verify port mappings in docker-compose.yaml")
            recommendations.append("   - Check for permission issues")
            
        recommendations.append("5. Complete rebuild if issues persist:")
        recommendations.append("   docker-compose down")
        recommendations.append("   docker system prune -f")
        recommendations.append("   docker-compose build --no-cache")
        recommendations.append("   docker-compose up -d")
        
        for i, rec in enumerate(recommendations):
            self.log(f"   {rec}")
    
    def run_full_diagnosis(self):
        """Run complete diagnostic suite"""
        self.log("🚀 STARTING COMPREHENSIVE DOCKER DIAGNOSTICS", "INFO")
        self.log("=" * 60)
        
        # Run all diagnostic checks
        self.check_docker_system()
        self.analyze_docker_compose_config()
        self.check_container_states()
        self.check_nginx_configuration()
        self.check_port_availability()
        self.check_file_permissions()
        self.attempt_docker_cleanup()
        
        self.log("=" * 60)
        self.generate_fix_recommendations()
        
        self.log("🏁 DIAGNOSTICS COMPLETE", "INFO")
        return self.results

def main():
    """Main diagnostic function"""
    diagnostics = DockerDiagnostics()
    results = diagnostics.run_full_diagnosis()
    
    # Save results to file for reference
    try:
        with open(f'diagnostic_results_{int(time.time())}.json', 'w') as f:
            json.dump(results, f, indent=2)
        print("\n📄 Diagnostic results saved to diagnostic_results_*.json")
    except Exception as e:
        print(f"⚠️  Could not save results: {e}")

if __name__ == "__main__":
    main() 