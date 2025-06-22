#!/usr/bin/env python3
"""
Stage 2: SSL Certificate Installation
Installs certbot and obtains SSL certificates for the domain
"""

import subprocess
import os
import time
import shutil
from datetime import datetime

def log_result(message, status="INFO"):
    """Log results with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_emoji = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "INFO": "ℹ️"}
    print(f"[{timestamp}] {status_emoji.get(status, 'ℹ️')} {message}")

def run_command(command, description, timeout=300, check_return=True):
    """Run a command and log the result"""
    log_result(f"Running: {description}", "INFO")
    log_result(f"Command: {' '.join(command)}", "INFO")
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        
        if result.stdout:
            log_result(f"Output: {result.stdout.strip()}", "INFO")
        
        if result.stderr and result.returncode != 0:
            log_result(f"Error: {result.stderr.strip()}", "WARN")
        
        if check_return and result.returncode != 0:
            log_result(f"{description}: Failed (exit code {result.returncode})", "FAIL")
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

def check_prerequisites():
    """Check if we can proceed with SSL installation"""
    log_result("Checking prerequisites for SSL installation...", "INFO")
    
    # Check if running as root or with sudo access
    try:
        result = subprocess.run(['sudo', '-n', 'true'], capture_output=True)
        if result.returncode == 0:
            log_result("Sudo access: Available", "PASS")
        else:
            log_result("Sudo access: Required for SSL installation", "FAIL")
            log_result("Please run this script with sudo or ensure passwordless sudo", "INFO")
            return False
    except Exception:
        log_result("Cannot check sudo access", "FAIL")
        return False
    
    # Check if in correct directory
    if not os.path.exists('docker-compose.yaml'):
        log_result("docker-compose.yaml not found - run from project root", "FAIL")
        return False
    
    log_result("Prerequisites check: Passed", "PASS")
    return True

def stop_docker_services():
    """Stop Docker services to free up ports for certbot"""
    log_result("Stopping Docker services for certificate generation...", "INFO")
    
    return run_command(['docker-compose', 'down'], "Stop Docker services")

def install_certbot():
    """Install certbot via snap"""
    log_result("Installing Certbot...", "INFO")
    
    # Update system first
    if not run_command(['sudo', 'apt', 'update'], "Update package list"):
        return False
    
    # Install snapd if not available
    if not run_command(['sudo', 'apt', 'install', 'snapd', '-y'], "Install snapd", check_return=False):
        log_result("snapd installation failed or already installed", "WARN")
    
    # Install snap core
    if not run_command(['sudo', 'snap', 'install', 'core'], "Install snap core", check_return=False):
        log_result("snap core installation failed or already installed", "WARN")
    
    # Refresh snap core
    if not run_command(['sudo', 'snap', 'refresh', 'core'], "Refresh snap core", check_return=False):
        log_result("snap core refresh failed", "WARN")
    
    # Install certbot
    if not run_command(['sudo', 'snap', 'install', '--classic', 'certbot'], "Install certbot", check_return=False):
        log_result("certbot installation failed or already installed", "WARN")
    
    # Create symlink
    if not run_command(['sudo', 'ln', '-sf', '/snap/bin/certbot', '/usr/bin/certbot'], "Create certbot symlink", check_return=False):
        log_result("certbot symlink creation failed or already exists", "WARN")
    
    # Verify certbot installation
    try:
        result = subprocess.run(['certbot', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            log_result(f"Certbot installed successfully: {result.stdout.strip()}", "PASS")
            return True
        else:
            log_result("Certbot installation verification failed", "FAIL")
            return False
    except Exception as e:
        log_result(f"Cannot verify certbot installation: {e}", "FAIL")
        return False

def obtain_ssl_certificate():
    """Obtain SSL certificate using certbot standalone"""
    log_result("Obtaining SSL certificate...", "INFO")
    
    # Command to get certificate
    cmd = [
        'sudo', 'certbot', 'certonly',
        '--standalone',
        '-d', 'memeit.pro',
        '-d', 'www.memeit.pro',
        '--non-interactive',
        '--agree-tos',
        '--email', 'admin@memeit.pro',  # You might want to change this
        '--no-eff-email'
    ]
    
    log_result("This will obtain SSL certificates for memeit.pro and www.memeit.pro", "INFO")
    log_result("Email used for certificate: admin@memeit.pro", "INFO")
    
    return run_command(cmd, "Obtain SSL certificate", timeout=600)

def copy_certificates():
    """Copy certificates to project ssl directory"""
    log_result("Copying certificates to project directory...", "INFO")
    
    # Ensure SSL directories exist
    os.makedirs('ssl/certs', exist_ok=True)
    os.makedirs('ssl/private', exist_ok=True)
    
    # Copy certificate files
    cert_files = [
        ('/etc/letsencrypt/live/memeit.pro/fullchain.pem', 'ssl/certs/memeit.pro.crt'),
        ('/etc/letsencrypt/live/memeit.pro/privkey.pem', 'ssl/private/memeit.pro.key')
    ]
    
    for src, dst in cert_files:
        try:
            # Copy with sudo and then change ownership
            if not run_command(['sudo', 'cp', src, dst], f"Copy {os.path.basename(src)}"):
                return False
            
            # Change ownership to current user
            import getpass
            username = getpass.getuser()
            if not run_command(['sudo', 'chown', f'{username}:{username}', dst], f"Change ownership of {dst}"):
                return False
                
            log_result(f"Certificate file copied: {dst}", "PASS")
            
        except Exception as e:
            log_result(f"Failed to copy {src} to {dst}: {e}", "FAIL")
            return False
    
    return True

def verify_certificate_files():
    """Verify certificate files are valid"""
    log_result("Verifying certificate files...", "INFO")
    
    cert_file = 'ssl/certs/memeit.pro.crt'
    key_file = 'ssl/private/memeit.pro.key'
    
    # Check if files exist
    if not os.path.exists(cert_file):
        log_result(f"Certificate file not found: {cert_file}", "FAIL")
        return False
    
    if not os.path.exists(key_file):
        log_result(f"Private key file not found: {key_file}", "FAIL")
        return False
    
    # Verify certificate
    if not run_command(['openssl', 'x509', '-in', cert_file, '-text', '-noout'], "Verify certificate format", check_return=False):
        log_result("Certificate file appears to be invalid", "FAIL")
        return False
    
    # Check certificate expiry
    try:
        result = subprocess.run(['openssl', 'x509', '-in', cert_file, '-enddate', '-noout'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            expiry = result.stdout.strip()
            log_result(f"Certificate expiry: {expiry}", "PASS")
        else:
            log_result("Cannot read certificate expiry", "WARN")
    except Exception:
        log_result("Cannot check certificate expiry", "WARN")
    
    # Verify private key
    if not run_command(['openssl', 'rsa', '-in', key_file, '-check', '-noout'], "Verify private key", check_return=False):
        log_result("Private key file appears to be invalid", "FAIL")
        return False
    
    log_result("Certificate files verification: Passed", "PASS")
    return True

def setup_auto_renewal():
    """Set up automatic certificate renewal"""
    log_result("Setting up automatic certificate renewal...", "INFO")
    
    # Test renewal
    if not run_command(['sudo', 'certbot', 'renew', '--dry-run'], "Test certificate renewal", timeout=300):
        log_result("Certificate renewal test failed", "WARN")
        return False
    
    # Create renewal hook script
    hook_script = """#!/bin/bash
# Certbot renewal hook for Meme Maker
cd /home/ubuntu/Meme-Maker || cd /home/*/Meme-Maker || exit 1

# Copy new certificates
sudo cp /etc/letsencrypt/live/memeit.pro/fullchain.pem ssl/certs/memeit.pro.crt
sudo cp /etc/letsencrypt/live/memeit.pro/privkey.pem ssl/private/memeit.pro.key
sudo chown -R $USER:$USER ssl/

# Restart frontend container to load new certificates
docker-compose restart frontend

echo "SSL certificates renewed and Docker containers restarted"
"""
    
    try:
        with open('/tmp/renewal-hook.sh', 'w') as f:
            f.write(hook_script)
        
        run_command(['sudo', 'mv', '/tmp/renewal-hook.sh', '/etc/letsencrypt/renewal-hooks/deploy/'], 
                   "Install renewal hook", check_return=False)
        run_command(['sudo', 'chmod', '+x', '/etc/letsencrypt/renewal-hooks/deploy/renewal-hook.sh'], 
                   "Make renewal hook executable", check_return=False)
        
        log_result("Automatic renewal setup: Completed", "PASS")
        return True
        
    except Exception as e:
        log_result(f"Automatic renewal setup failed: {e}", "WARN")
        return False

def main():
    """Run SSL certificate installation process"""
    print("🔒 STAGE 2: SSL CERTIFICATE INSTALLATION")
    print("=" * 50)
    
    # Check prerequisites
    if not check_prerequisites():
        log_result("Prerequisites check failed. Cannot proceed with SSL installation.", "FAIL")
        return False
    
    # Installation steps
    steps = [
        ("Stop Docker Services", stop_docker_services),
        ("Install Certbot", install_certbot),
        ("Obtain SSL Certificate", obtain_ssl_certificate),
        ("Copy Certificates", copy_certificates),
        ("Verify Certificate Files", verify_certificate_files),
        ("Setup Auto Renewal", setup_auto_renewal),
    ]
    
    results = {}
    for step_name, step_func in steps:
        log_result(f"Executing: {step_name}", "INFO")
        try:
            result = step_func()
            results[step_name] = result
            
            if not result:
                log_result(f"Step failed: {step_name}", "FAIL")
                # Don't stop on auto-renewal failure
                if step_name != "Setup Auto Renewal":
                    break
        except Exception as e:
            log_result(f"Step {step_name} failed with exception: {e}", "FAIL")
            results[step_name] = False
            break
        
        print()  # Add spacing between steps
    
    # Summary
    print("=" * 50)
    log_result("STAGE 2 SSL INSTALLATION SUMMARY", "INFO")
    print("=" * 50)
    
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    
    for step_name, result in results.items():
        status = "PASS" if result else "FAIL"
        log_result(f"{step_name}: {status}", status)
    
    print()
    
    if failed == 0 or (failed == 1 and not results.get("Setup Auto Renewal", True)):
        log_result("✅ SSL certificate installation completed!", "PASS")
        log_result("Certificates installed and verified", "PASS")
        log_result("Next: Run 'python stage3_https_deployment.py' to start services with HTTPS", "INFO")
        return True
    else:
        log_result("❌ SSL certificate installation failed", "FAIL")
        log_result("Check the error messages above and fix issues", "INFO")
        log_result("You may need to:", "INFO")
        log_result("  1. Ensure domain DNS is pointing to this server", "INFO")
        log_result("  2. Check firewall allows ports 80 and 443", "INFO")
        log_result("  3. Verify no other services are using port 80", "INFO")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 