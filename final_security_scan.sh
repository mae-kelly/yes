#!/bin/bash

echo "🔍 FINAL SECURITY VERIFICATION"
echo "=============================="

security_issues=0
warnings=0

echo "🔐 Checking for exposed API keys..."
if find . -name "*.py" -exec grep -l "api.*key.*=.*['\"][a-zA-Z0-9]\{20,\}['\"]" {} \; | grep -v "getenv\|input\|getpass\|example\|test" | head -1; then
    echo "❌ POTENTIAL EXPOSED API KEYS FOUND!"
    security_issues=$((security_issues + 1))
else
    echo "✅ No exposed API keys detected"
fi

echo "🔒 Checking for hardcoded credentials..."
if find . -name "*.py" -exec grep -l "password.*=.*['\"][^'\"]*['\"]" {} \; | grep -v "getenv\|input\|getpass\|example\|test" | head -1; then
    echo "❌ POTENTIAL HARDCODED PASSWORDS FOUND!"
    security_issues=$((security_issues + 1))
else
    echo "✅ No hardcoded credentials detected"
fi

echo "🧪 Checking sandbox enforcement..."
if grep -r "sandbox.*=.*False" . --include="*.py" | grep -v "config.get.*sandbox.*True"; then
    echo "⚠️ Found hardcoded live trading mode"
    warnings=$((warnings + 1))
else
    echo "✅ Sandbox mode properly enforced"
fi

echo "⚠️ Checking for dangerous functions..."
dangerous_patterns=("eval(" "exec(" "subprocess.call" "os.system")
found_dangerous=false

for pattern in "${dangerous_patterns[@]}"; do
    if find . -name "*.py" -exec grep -l "$pattern" {} \; | head -1; then
        echo "⚠️ Found potentially dangerous function: $pattern"
        warnings=$((warnings + 1))
        found_dangerous=true
    fi
done

if [ "$found_dangerous" = false ]; then
    echo "✅ No dangerous functions detected"
fi

echo "📁 Checking file permissions..."
if [ -f ".env" ] && [ "$(stat -c '%a' .env 2>/dev/null || stat -f '%A' .env 2>/dev/null)" != "600" ]; then
    echo "⚠️ .env file permissions should be 600"
    warnings=$((warnings + 1))
else
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
    echo "✅ System is secure and ready for production"
    exit 0
elif [ $security_issues -eq 0 ]; then
    echo ""
    echo "🛡️ SECURITY STATUS: GOOD"
    echo "⚠️ Minor warnings detected - review above"
    exit 0
else
    echo ""
    echo "🛡️ SECURITY STATUS: CRITICAL ISSUES"
    echo "❌ MUST FIX SECURITY ISSUES BEFORE USE"
    exit 1
fi
