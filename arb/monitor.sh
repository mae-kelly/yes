#!/bin/bash

# Monitor the arbitrage scanner performance
echo "📊 Arbitrage Scanner Monitor"
echo "============================"
echo ""

# Check if scanner is running
if pgrep -f "arb-scanner" > /dev/null; then
    echo "✅ Scanner is running"
    echo ""
    
    # Show recent profits from logs
    echo "Recent Opportunities Found:"
    tail -n 100 logs/*.log 2>/dev/null | grep "OPPORTUNITY FOUND" -A 5 | tail -n 20
    
    echo ""
    echo "Performance Metrics:"
    # Count opportunities
    OPPORTUNITIES=$(grep -c "OPPORTUNITY FOUND" logs/*.log 2>/dev/null)
    EXECUTIONS=$(grep -c "EXECUTED SUCCESSFULLY" logs/*.log 2>/dev/null)
    
    echo "  Total Opportunities: $OPPORTUNITIES"
    echo "  Successful Executions: $EXECUTIONS"
    
    if [ "$OPPORTUNITIES" -gt 0 ]; then
        SUCCESS_RATE=$((EXECUTIONS * 100 / OPPORTUNITIES))
        echo "  Success Rate: $SUCCESS_RATE%"
    fi
else
    echo "❌ Scanner is not running"
    echo "Run: ./run.sh"
fi
