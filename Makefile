.PHONY: help setup run estimate expert analyze clean install test

PROJECT_ID ?= $(GOOGLE_CLOUD_PROJECT)
CONFIG_FILE ?= intelligent_config.yaml
INTELLIGENCE_LEVEL ?= advanced
MAX_MEMORY ?= 512
MAX_DISK ?= 5

DATA_DIR ?= ./output
CACHE_DIR ?= ./.cache
DATABASE_FILE ?= ao1_intelligent_cmdb.db

help:
	@echo "♡₊˚ ｡⋅˚♡ ✧ ‧₊˚ ⋅   Intelligent AO1 Discovery System   ⋅ ˚₊‧ ✧ ♡˚⋅｡ ˚₊♡"
	@echo "=================================================================="
	@echo ""
	@echo "Quick Commands:"
	@echo "  make setup                - Complete intelligent setup"
	@echo "  make run                  - Run intelligent discovery"
	@echo "  make estimate             - Estimate discovery scope"
	@echo "  make expert               - Run with expert intelligence"
	@echo ""
	@echo "Analysis Commands:"
	@echo "  make analyze              - Analyze discovery results"
	@echo "  make stats                - Show database statistics"
	@echo "  make quality              - Show data quality metrics"
	@echo ""
	@echo "Management:"
	@echo "  make clean                - Clean generated files"
	@echo "  make install              - Install dependencies only"
	@echo "  make test                 - Test system connectivity"
	@echo ""
	@echo "Configuration:"
	@echo "  PROJECT_ID                - GCP Project ID ($(or $(PROJECT_ID),Not set))"
	@echo "  INTELLIGENCE_LEVEL        - Intelligence level ($(INTELLIGENCE_LEVEL))"
	@echo "  MAX_MEMORY                - Memory limit MB ($(MAX_MEMORY))"
	@echo "  MAX_DISK                  - Disk limit GB ($(MAX_DISK))"
	@echo ""
	@echo "Examples:"
	@echo "  make setup PROJECT_ID=my-project"
	@echo "  make run PROJECT_ID=my-project"
	@echo "  make expert PROJECT_ID=my-project MAX_MEMORY=2048"

setup:
	@echo "♡₊˚ ｡⋅˚♡   Setting up Intelligent AO1 Discovery System   ♡˚⋅｡ ˚₊♡"
	@echo "=============================================================="
	@echo ""
	@echo "1. Checking prerequisites..."
	@$(MAKE) check-prerequisites
	@echo ""
	@echo "2. Creating directories..."
	@$(MAKE) create-dirs
	@echo ""
	@echo "3. Installing dependencies..."
	@$(MAKE) install
	@echo ""
	@echo "4. Validating configuration..."
	@$(MAKE) validate-config
	@echo ""
	@echo "5. Testing connectivity..."
	@$(MAKE) test-connectivity
	@echo ""
	@echo "❀°｡ ‧˚♡ ˚‧ ｡°❀   Intelligent AO1 setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  make estimate PROJECT_ID=your-project-id"
	@echo "  make run PROJECT_ID=your-project-id"

run:
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "❌ PROJECT_ID not set"; \
		echo "Usage: make run PROJECT_ID=your-project-id"; \
		exit 1; \
	fi
	@echo "♡₊˚ 🌸 ⋆｡˚   Starting Intelligent AO1 Discovery   ⋆｡˚ 🌸 ˚₊♡"
	@echo "Project: $(PROJECT_ID)"
	@echo "Intelligence: $(INTELLIGENCE_LEVEL)"
	@echo "Memory: $(MAX_MEMORY)MB, Disk: $(MAX_DISK)GB"
	@echo ""
	@python3 intelligent_main.py \
		--project $(PROJECT_ID) \
		--intelligence-level $(INTELLIGENCE_LEVEL) \
		--max-memory $(MAX_MEMORY) \
		--max-disk $(MAX_DISK) \
		--config $(CONFIG_FILE) \
		--output-dir $(DATA_DIR) \
		--cache-dir $(CACHE_DIR) \
		--database $(DATABASE_FILE)

estimate:
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "❌ PROJECT_ID not set"; \
		echo "Usage: make estimate PROJECT_ID=your-project-id"; \
		exit 1; \
	fi
	@echo "⋆｡‧˚ʚ♡ɞ˚‧｡⋆   Intelligent Scope Estimation   ⋆｡‧˚ʚ♡ɞ˚‧｡⋆"
	@echo "Project: $(PROJECT_ID)"
	@echo ""
	@python3 intelligent_main.py \
		--project $(PROJECT_ID) \
		--dry-run \
		--intelligence-level $(INTELLIGENCE_LEVEL) \
		--config $(CONFIG_FILE) \
		--output-dir $(DATA_DIR)

expert:
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "❌ PROJECT_ID not set"; \
		echo "Usage: make expert PROJECT_ID=your-project-id"; \
		exit 1; \
	fi
	@echo "🧠 ♡₊˚   Expert Intelligence Discovery   ˚₊♡ 🧠"
	@echo "Project: $(PROJECT_ID)"
	@echo "Intelligence: EXPERT"
	@echo "Memory: 2048MB, Disk: 10GB"
	@echo ""
	@python3 intelligent_main.py \
		--project $(PROJECT_ID) \
		--intelligence-level expert \
		--max-memory 2048 \
		--max-disk 10 \
		--config $(CONFIG_FILE) \
		--output-dir $(DATA_DIR) \
		--cache-dir $(CACHE_DIR) \
		--database $(DATABASE_FILE)

analyze:
	@echo "📊 ♡₊˚   Intelligent Analysis Results   ˚₊♡ 📊"
	@echo ""
	@if [ ! -f "$(DATABASE_FILE)" ]; then \
		echo "❌ Database not found. Run discovery first:"; \
		echo "   make run PROJECT_ID=your-project-id"; \
		exit 1; \
	fi
	@echo "Asset Inventory Summary:"
	@duckdb $(DATABASE_FILE) "SELECT COUNT(*) as total_assets FROM intelligent_asset_inventory;" 2>/dev/null || echo "No assets found"
	@echo ""
	@echo "Intelligence Scores:"
	@duckdb $(DATABASE_FILE) "SELECT AVG(intelligence_score) as avg_intelligence, AVG(data_quality_score) as avg_quality FROM intelligent_asset_inventory;" 2>/dev/null || echo "No scores available"
	@echo ""
	@echo "Source Coverage:"
	@duckdb $(DATABASE_FILE) "SELECT SUM(CASE WHEN found_in_cmdb THEN 1 ELSE 0 END) as cmdb, SUM(CASE WHEN has_crowdstrike THEN 1 ELSE 0 END) as crowdstrike, SUM(CASE WHEN in_splunk THEN 1 ELSE 0 END) as splunk FROM intelligent_asset_inventory;" 2>/dev/null || echo "No coverage data"

stats:
	@echo "📈 ♡₊˚   Database Statistics   ˚₊♡ 📈"
	@echo ""
	@if [ ! -f "$(DATABASE_FILE)" ]; then \
		echo "❌ Database not found"; \
		exit 1; \
	fi
	@echo "Endpoints Discovered:"
	@duckdb $(DATABASE_FILE) "SELECT COUNT(*) FROM intelligent_endpoints;" 2>/dev/null
	@echo ""
	@echo "Data Points Collected:"
	@duckdb $(DATABASE_FILE) "SELECT COUNT(*) FROM intelligent_endpoint_data;" 2>/dev/null
	@echo ""
	@echo "Consolidated Assets:"
	@duckdb $(DATABASE_FILE) "SELECT COUNT(*) FROM intelligent_asset_inventory;" 2>/dev/null

quality:
	@echo "🎯 ♡₊˚   Data Quality Analysis   ˚₊♡ 🎯"
	@echo ""
	@if [ ! -f "$(DATABASE_FILE)" ]; then \
		echo "❌ Database not found"; \
		exit 1; \
	fi
	@echo "Quality Distribution:"
	@duckdb $(DATABASE_FILE) "SELECT CASE WHEN intelligence_score >= 0.8 THEN 'Excellent' WHEN intelligence_score >= 0.6 THEN 'Good' WHEN intelligence_score >= 0.4 THEN 'Fair' ELSE 'Poor' END as quality, COUNT(*) as count FROM intelligent_asset_inventory GROUP BY quality ORDER BY MIN(intelligence_score) DESC;" 2>/dev/null
	@echo ""
	@echo "Top Quality Assets:"
	@duckdb $(DATABASE_FILE) "SELECT hostname, intelligence_score, data_quality_score FROM intelligent_asset_inventory ORDER BY intelligence_score DESC LIMIT 5;" 2>/dev/null

check-prerequisites:
	@echo "Checking Python..."
	@python3 --version || (echo "❌ Python 3.8+ required" && exit 1)
	@echo "✅ Python OK"
	@echo "Checking pip..."
	@pip3 --version || (echo "❌ pip3 required" && exit 1)
	@echo "✅ pip OK"
	@echo "Checking gcloud (optional)..."
	@gcloud version --format="value(Google Cloud SDK)" 2>/dev/null && echo "✅ gcloud OK" || echo "⚠️  gcloud not found - using service account key"
	@echo "✅ Prerequisites checked"

create-dirs:
	@mkdir -p $(DATA_DIR) $(CACHE_DIR) logs
	@mkdir -p config backups
	@echo "✅ Directory structure created"

install:
	@echo "Installing Python dependencies..."
	@pip3 install -r requirements.txt
	@echo "✅ Dependencies installed"

validate-config:
	@if [ -f "$(CONFIG_FILE)" ]; then \
		echo "✅ Configuration file found: $(CONFIG_FILE)"; \
		python3 -c "import yaml; yaml.safe_load(open('$(CONFIG_FILE)'))" 2>/dev/null || \
		(echo "❌ Invalid YAML configuration" && exit 1); \
		echo "✅ Configuration valid"; \
	else \
		echo "⚠️  Configuration file not found: $(CONFIG_FILE)"; \
		echo "   Using default configuration"; \
	fi

test-connectivity:
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "⚠️  PROJECT_ID not set - skipping connectivity test"; \
		echo "   Set with: export GOOGLE_CLOUD_PROJECT=your-project-id"; \
	else \
		echo "Testing BigQuery connectivity..."; \
		python3 -c "from gcp_client import BigQueryClientManager; client = BigQueryClientManager('$(PROJECT_ID)'); assert client.test_connection(), 'Connection failed'" && \
		echo "✅ BigQuery connection successful" || \
		echo "❌ BigQuery connection failed - check authentication"; \
	fi

test:
	@echo "🧪 ♡₊˚   Testing Intelligent Discovery System   ˚₊♡ 🧪"
	@echo ""
	@$(MAKE) check-prerequisites
	@echo ""
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "⚠️  PROJECT_ID not set - run: export GOOGLE_CLOUD_PROJECT=your-project-id"; \
		echo "   Or use: make test PROJECT_ID=your-project-id"; \
	else \
		echo "Testing with PROJECT_ID: $(PROJECT_ID)"; \
		$(MAKE) test-connectivity PROJECT_ID=$(PROJECT_ID); \
	fi
	@echo ""
	@echo "Testing intelligent components..."
	@python3 -c "from intelligent_content_matcher import IntelligentContentMatcher; print('✅ Content matcher OK')" 2>/dev/null || echo "❌ Content matcher failed"
	@python3 -c "from intelligent_cache_manager import IntelligentCacheManager; print('✅ Cache manager OK')" 2>/dev/null || echo "❌ Cache manager failed"
	@echo ""
	@echo "✅ System test complete"

export:
	@echo "📤 ♡₊˚   Exporting Discovery Results   ˚₊♡ 📤"
	@mkdir -p $(DATA_DIR)/exports
	@if [ -f "$(DATABASE_FILE)" ]; then \
		echo "Exporting asset inventory..."; \
		duckdb $(DATABASE_FILE) "COPY (SELECT * FROM intelligent_asset_inventory) TO '$(DATA_DIR)/exports/intelligent_assets.csv' (HEADER, DELIMITER ',');" && \
		echo "✅ Assets exported to $(DATA_DIR)/exports/intelligent_assets.csv"; \
		echo "Exporting endpoint data..."; \
		duckdb $(DATABASE_FILE) "COPY (SELECT * FROM intelligent_endpoint_data) TO '$(DATA_DIR)/exports/endpoint_data.csv' (HEADER, DELIMITER ',');" && \
		echo "✅ Data exported to $(DATA_DIR)/exports/endpoint_data.csv"; \
		echo "Exporting quality analysis..."; \
		duckdb $(DATABASE_FILE) "COPY (SELECT hostname, intelligence_score, data_quality_score, source_systems FROM intelligent_asset_inventory ORDER BY intelligence_score DESC) TO '$(DATA_DIR)/exports/quality_analysis.csv' (HEADER, DELIMITER ',');" && \
		echo "✅ Quality analysis exported"; \
	else \
		echo "❌ Database not found. Run discovery first."; \
	fi

backup:
	@echo "💾 ♡₊˚   Creating Intelligent Backup   ˚₊♡ 💾"
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S) && \
	mkdir -p backups && \
	tar -czf "backups/intelligent_backup_$$TIMESTAMP.tar.gz" \
		$(DATABASE_FILE) \
		$(DATA_DIR) \
		$(CACHE_DIR) \
		logs/ \
		$(CONFIG_FILE) \
		2>/dev/null || true && \
	echo "✅ Backup created: backups/intelligent_backup_$$TIMESTAMP.tar.gz"

status:
	@echo "🔍 ♡₊˚   Intelligent System Status   ˚₊♡ 🔍"
	@echo "================================================="
	@echo ""
	@echo "Environment:"
	@echo "  Project ID: $(or $(PROJECT_ID),❌ Not set)"
	@echo "  Intelligence Level: $(INTELLIGENCE_LEVEL)"
	@echo "  Memory Limit: $(MAX_MEMORY)MB"
	@echo "  Disk Limit: $(MAX_DISK)GB"
	@echo ""
	@echo "Files:"
	@ls -la $(DATABASE_FILE) 2>/dev/null && echo "  ✅ Database exists" || echo "  ❌ Database not found"
	@ls -la $(CONFIG_FILE) 2>/dev/null && echo "  ✅ Config exists" || echo "  ❌ Config not found"
	@ls -d $(DATA_DIR) 2>/dev/null && echo "  ✅ Output directory exists" || echo "  ❌ Output directory not found"
	@ls -d $(CACHE_DIR) 2>/dev/null && echo "  ✅ Cache directory exists" || echo "  ❌ Cache directory not found"
	@echo ""
	@if [ -f "$(DATABASE_FILE)" ]; then \
		echo "Database Statistics:"; \
		duckdb $(DATABASE_FILE) "SELECT 'Assets: ' || COUNT(*) FROM intelligent_asset_inventory;" 2>/dev/null || echo "  ❌ Cannot read database"; \
		duckdb $(DATABASE_FILE) "SELECT 'Avg Intelligence: ' || ROUND(AVG(intelligence_score), 3) FROM intelligent_asset_inventory;" 2>/dev/null || true; \
	fi

logs:
	@echo "📋 ♡₊˚   Recent Discovery Logs   ˚₊♡ 📋"
	@echo ""
	@if [ -d "logs" ]; then \
		echo "Recent log files:"; \
		find logs -name "*.log" -type f -exec ls -lt {} + | head -5 2>/dev/null || echo "No log files found"; \
		echo ""; \
		echo "Latest log content:"; \
		find logs -name "*.log" -type f -exec ls -t {} + 2>/dev/null | head -1 | xargs tail -20 2>/dev/null || echo "No logs available"; \
	else \
		echo "❌ No logs directory found"; \
	fi

clean:
	@echo "🧹 ♡₊˚   Cleaning Generated Files   ˚₊♡ 🧹"
	@echo ""
	@echo "Removing cache..."
	@rm -rf $(CACHE_DIR) && echo "✅ Cache cleared" || echo "❌ Cache clear failed"
	@echo "Removing Python cache..."
	@rm -rf __pycache__ .pytest_cache *.pyc *.pyo && echo "✅ Python cache cleared"
	@echo "Removing logs..."
	@rm -rf logs/*.log && echo "✅ Logs cleared" || echo "No logs to clear"
	@echo "Removing checkpoints..."
	@rm -f discovery_checkpoint.json && echo "✅ Checkpoints cleared" || echo "No checkpoints to clear"
	@echo ""
	@echo "✅ Cleanup complete"
	@echo ""
	@echo "Database and output files preserved."
	@echo "To remove everything: rm -f $(DATABASE_FILE) && rm -rf $(DATA_DIR)"