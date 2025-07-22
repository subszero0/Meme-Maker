#!/bin/bash
echo "🔧 FIXING SCRIPT PERMISSIONS..."
echo "==============================="

# Add execute permissions to all fix scripts
chmod +x scripts/fix_staging_deployment.sh
chmod +x scripts/fix_staging_firewall.sh  
chmod +x scripts/fix_job_timeout.py

echo "✅ Execute permissions added to:"
echo "  - scripts/fix_staging_deployment.sh"
echo "  - scripts/fix_staging_firewall.sh"
echo "  - scripts/fix_job_timeout.py"

echo ""
echo "🎯 Now run the fixes in order:"
echo "1. ./scripts/fix_staging_deployment.sh"
echo "2. ./scripts/fix_staging_firewall.sh" 
echo "3. python3 scripts/fix_job_timeout.py (already done, need container restart)" 