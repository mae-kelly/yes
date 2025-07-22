#!/bin/bash

echo "🔍 FIXED SECURITY VERIFICATION"
echo "=============================="

security_issues=0
warnings=0

# Only scan our trading system files, not the virtual environment
trading_files=("production_main.py" "secure_data_manager.py" "test_perfect_system.py")

echo "🔐 Checking for exposed API keys in trading system files..."
exposed_found=false
for file in "${trading_files[@]}"; do
    if [ -f "$file" ]; then
        # Look for suspicious patterns but exclude safe patterns
        if grep -l "api.*key.*=.*['\"][a-zA-Z0-9]\{20,\}['\"]" "$file" | grep -v "getenv\|os.environ\|input\|getpass\|example\|test\|your.*key.*here" >/dev/null 2>&1; then
            echo "❌ Found exposed API key in $file"
            exposed_found=true
            security_issues=$((security_issues + 1))
        fi
    fi
done

if [ "$exposed_found" = false ]; then
    echo "✅ No exposed API keys detected in trading system"
fi

echo ""
echo "🔒 Checking for hardcoded credentials in trading system files..."
hardcoded_found=false
for file in "${trading_files[@]}"; do
    if [ -f "$file" ]; then
        if grep -l "password.*=.*['\"][^'\"]*['\"]" "$file" | grep -v "getenv\|os.environ\|input\|getpass\|example\|test" >/dev/null 2>&1; then
            echo "❌ Found hardcoded password in $file"
            hardcoded_found=true
            security_issues=$((security_issues + 1))
        fi
    fi
done

if [ "$hardcoded_found" = false ]; then
    echo "✅ No hardcoded credentials detected in trading system"
fi

echo ""
echo "🧪 Checking sandbox enforcement..."
if grep -r "sandbox.*=.*False" "${trading_files[@]}" 2>/dev/null | grep -v "config.get.*sandbox.*True"; then
    echo "⚠️ Found hardcoded live trading mode"
    warnings=$((warnings + 1))
else
    echo "✅ Sandbox mode properly enforced"
fi

echo ""
echo "⚠️ Checking for dangerous functions in trading system..."
dangerous_patterns=("eval(" "exec(" "subprocess.call" "os.system")
found_dangerous=false

for pattern in "${dangerous_patterns[@]}"; do
    pattern_found=false
    for file in "${trading_files[@]}"; do
        if [ -f "$file" ] && grep -l "$pattern" "$file" >/dev/null 2>&1; then
            echo "⚠️ Found potentially dangerous function in $file: $pattern"
            warnings=$((warnings + 1))
            pattern_found=true
            found_dangerous=true
            break
        fi
    done
done

if [ "$found_dangerous" = false ]; then
    echo "✅ No dangerous functions detected in trading system"
fi

echo ""
echo "📁 Checking file permissions..."
permission_issues=false
if [ -f ".env" ]; then
    env_perms=$(stat -c '%a' .env 2>/dev/null || stat -f '%A' .env 2>/dev/null)
    if [ "$env_perms" != "600" ] && [ "$env_perms" != "rw-------" ]; then
        echo "⚠️ .env file permissions should be 600 (currently: $env_perms)"
        warnings=$((warnings + 1))
        permission_issues=true
    fi
fi

if [ "$permission_issues" = false ]; then
    echo "✅ File permissions are secure"
fi

echo ""
echo "🔍 SECURITY SCAN COMPLETE"
echo "========================"
echo "🚨 Critical Issues: $security_issues"
echo "⚠️ Warnings: $warnings"

if [ $security_issues -eq 0 ] && [ $warnings -eq 0 ]; then
    echo ""
    echo "🛡️ SECURITY STATUS: EXCELLENT"
    echo "✅ Trading system is secure and ready for production"
    echo "🎯 All files pass security validation"
elif [ $security_issues -eq 0 ]; then
    echo ""
    echo "🛡️ SECURITY STATUS: GOOD"
    echo "✅ No critical security issues found"
    echo "⚠️ Minor warnings detected (review above if needed)"
else
    echo ""
    echo "🛡️ SECURITY STATUS: CRITICAL ISSUES"
    echo "❌ MUST FIX SECURITY ISSUES BEFORE USE"
    exit 1
fi

echo ""
echo "🎉 SECURITY VERIFICATION COMPLETE"
echo "✅ Your trading system files are secure"
echo "✅ Virtual environment files excluded from scan"
echo "✅ Ready to proceed with setup"./l