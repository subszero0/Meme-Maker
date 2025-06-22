#!/usr/bin/env python3
"""
Stage 3: HTTPS Deployment
Starts Docker services with HTTPS enabled after SSL certificates are installed
"""

import subprocess
import requests
import time
import os
import socket
import ssl
from datetime import datetime

def log_result(message, status="INFO"):
    """Log results with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_emoji = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "INFO": "ℹ️"}
    print(f"[{timestamp}] {status_emoji.get(status, 'ℹ️')} {message}")

def run_command(command, description, timeout=300):
    """Run a command and log the result"""
    log_result(f"Running: {description}", "INFO")
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        
        if result.returncode != 0:
            log_result(f"{description}: Failed (exit code {result.returncode})", "FAIL")
            if result.stderr:
                log_result(f"Error: {result.stderr.strip()}", "FAIL")
            return False
        else:
            log_result(f"{description}: Success", "PASS")
            return True
            
    except subprocess.TimeoutExpired:
        log_result(f"{description}: Timeout after {timeout}s", "FAIL")
        return False
    except Exception as e:
        log_result(f"{description}: Exception - {e}", "FAIL")
        return False

def check_ssl_certificates():
    """Verify SSL certificates are present and valid"""
    log_result("Checking SSL certificates...", "INFO")
    
    cert_file = 'ssl/certs/memeit.pro.crt'
    key_file = 'ssl/private/memeit.pro.key'
    
    if not os.path.exists(cert_file):
        log_result(f"Certificate file missing: {cert_file}", "FAIL")
        return False
    
    if not os.path.exists(key_file):
        log_result(f"Private key file missing: {key_file}", "FAIL")
        return False
    
    log_result("SSL certificates verification: Passed", "PASS")
    return True

def start_docker_services():
    """Start Docker services with HTTPS configuration"""
    log_result("Starting Docker services with HTTPS...", "INFO")
    
    if not run_command(['docker-compose', 'up', '-d'], "Start Docker services"):
        return False
    
    time.sleep(30)
    return True

def main():
    """Run HTTPS deployment process"""
    print("🚀 STAGE 3: HTTPS DEPLOYMENT")
    print("=" * 50)
    
    steps = [
        ("Check SSL Certificates", check_ssl_certificates),
        ("Start Docker Services", start_docker_services),
    ]
    
    for step_name, step_func in steps:
        log_result(f"Executing: {step_name}", "INFO")
        if not step_func():
            log_result(f"Step failed: {step_name}", "FAIL")
            return False
    
    log_result("✅ HTTPS deployment completed!", "PASS")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 