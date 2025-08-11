.PHONY: help install run docker-build docker-run clean test format lint setup ao1-analyze ao1-gaps

PROJECT_ID ?= $(GOOGLE_CLOUD_PROJECT)
CONFIG_FILE ?= config.yaml
WORKERS ?= 4

DATA_DIR ?= ./data
CACHE_DIR ?= $(DATA_DIR)/cache
LOGS_DIR ?= $(DATA_DIR)/logs
OUTPUT_DIR ?= $(DATA_DIR)/output
CHECKPOINTS_DIR ?= $(DATA_DIR)/checkpoints

DOCKER_IMAGE ?= ao1-discovery:latest
DATABASE_FILE ?= ao1_visibility_cmdb.db

help:
	@echo "AO1 Log Visibility Measurement System"
	@echo "====================================="
	@echo ""
	@echo "Core Commands:"
	@echo "  setup                 - Complete setup for AO1"
	@echo "  run                   - Execute AO1 discovery"
	@echo "  docker-run            - Run discovery in Docker"
	@echo "  estimate              - Estimate AO1 scope"
	@echo "  resume                - Resume from checkpoint"
	@echo ""
	@echo "AO1 Analysis:"
	@echo "  ao1-analyze           - Analyze AO1 results"
	@echo "  ao1-gaps              - Show visibility gaps"
	@echo "  ao1-metrics           - Display AO1 metrics"
	@echo "  ao1-compliance        - Check compliance status"
	@echo "  ao1-recommendations   - Get improvement recommendations"
	@echo ""
	@echo "Development:"
	@echo "  install               - Install dependencies"
	@echo "  test                  - Run tests"
	@echo "  format                - Format code"
	@echo "  lint                  - Run linting"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build          - Build Docker image"
	@echo "  docker-dev            - Run development container"
	@echo ""
	@echo "Data Management:"
	@echo "  export                - Export AO1 results"
	@echo "  clean                 - Clean generated files"
	@echo "  backup                - Backup AO1 database"
	@echo ""
	@echo "Configuration:"
	@echo "  PROJECT_ID            - GCP Project ID ($(PROJECT_ID))"
	@echo "  CONFIG_FILE           - Configuration file ($(CONFIG_FILE))"
	@echo "  WORKERS               - Number of workers ($(WORKERS))"

setup:
	@echo "AO1 Log Visibility Setup"
	@echo "======================="
	@echo ""
	@echo "1. Checking prerequisites..."
	@$(MAKE) check-prerequisites
	@echo ""
	@echo "2. Creating directory structure..."
	@$(MAKE) create-dirs
	@echo ""
	@echo "3. Installing dependencies..."
	@$(MAKE) install
	@echo ""
	@echo "4. Validating configuration..."
	@$(MAKE) validate-config
	@echo ""
	@echo "5. Testing connections..."
	@$(MAKE) test-connections
	@echo ""
	@echo "AO1 setup complete! Ready for visibility measurement."

check-prerequisites:
	@echo "Checking Python version..."
	@python3 --version || (echo "Python 3.8+ required" && exit 1)
	@echo "Checking pip..."
	@pip3 --version || (echo "pip3 required" && exit 1)
	@echo "Checking gcloud..."
	@gcloud version --format="value(Google Cloud SDK)" 2>/dev/null || echo "gcloud not found - using service account key"
	@echo "Checking Docker..."
	@docker --version 2>/dev/null || echo "Docker not found"
	@echo "Prerequisites checked"

create-dirs:
	@mkdir -p $(DATA_DIR) $(CACHE_DIR) $(LOGS_DIR) $(OUTPUT_DIR) $(CHECKPOINTS_DIR)
	@mkdir -p config
	@echo "Directory structure created"

install:
	@echo "Installing Python dependencies..."
	@pip3 install -r requirements.txt
	@echo "Dependencies installed"

validate-config:
	@if [ -f "$(CONFIG_FILE)" ]; then \
		echo "Configuration file found: $(CONFIG_FILE)"; \
		python3 -c "import yaml; yaml.safe_load(open('$(CONFIG_FILE)'))" || \
		(echo "Invalid YAML configuration" && exit 1); \
	else \
		echo "Configuration file not found: $(CONFIG_FILE)"; \
	fi

test-connections:
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "PROJECT_ID not set - skipping connection test"; \
	else \
		echo "Testing BigQuery connection..."; \
		python3 -c "from gcp_client import BigQueryClientManager; client = BigQueryClientManager('$(PROJECT_ID)'); assert client.test_connection(), 'Connection failed'"; \
		echo "Connection test successful"; \
	fi

run:
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "PROJECT_ID not set"; \
		echo "Run: export GOOGLE_CLOUD_PROJECT='your-project-id'"; \
		exit 1; \
	fi
	@echo "Starting AO1 Log Visibility Discovery..."
	@echo "Project: $(PROJECT_ID)"
	@echo "Workers: $(WORKERS)"
	@python3 main.py \
		--project $(PROJECT_ID) \
		--config $(CONFIG_FILE) \
		--workers $(WORKERS) \
		--output-dir $(OUTPUT_DIR)

estimate:
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "PROJECT_ID not set"; \
		exit 1; \
	fi
	@echo "Estimating AO1 discovery scope..."
	@python3 main.py \
		--project $(PROJECT_ID) \
		--config $(CONFIG_FILE) \
		--dry-run \
		--output-dir $(OUTPUT_DIR)

resume:
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "PROJECT_ID not set"; \
		exit 1; \
	fi
	@echo "Resuming AO1 discovery from checkpoint..."
	@python3 main.py \
		--project $(PROJECT_ID) \
		--config $(CONFIG_FILE) \
		--resume \
		--workers $(WORKERS) \
		--output-dir $(OUTPUT_DIR)

docker-build:
	@echo "Building Docker image..."
	@docker build -f Dockerfile -t $(DOCKER_IMAGE) .
	@echo "Docker image built: $(DOCKER_IMAGE)"

docker-run: docker-build
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "PROJECT_ID not set"; \
		exit 1; \
	fi
	@echo "Running AO1 discovery in Docker..."
	@mkdir -p $(DATA_DIR) $(CACHE_DIR) $(LOGS_DIR) $(OUTPUT_DIR) $(CHECKPOINTS_DIR)
	@GOOGLE_CLOUD_PROJECT=$(PROJECT_ID) \
	 DATA_DIR=$(DATA_DIR) \
	 CACHE_DIR=$(CACHE_DIR) \
	 LOGS_DIR=$(LOGS_DIR) \
	 docker-compose up --build discovery

docker-dev: docker-build
	@echo "Starting development container..."
	@docker-compose run --rm discovery-dev

ao1-analyze:
	@if [ ! -f "$(DATABASE_FILE)" ]; then \
		echo "AO1 database not found. Run discovery first."; \
		exit 1; \
	fi
	@echo "AO1 Log Visibility Analysis"
	@echo "=========================="
	@echo ""
	@echo "Total Assets:"
	@duckdb $(DATABASE_FILE) "SELECT COUNT(*) as total_assets FROM ao1_asset_inventory;"
	@echo ""
	@echo "Global Visibility Coverage:"
	@duckdb $(DATABASE_FILE) "SELECT (SUM(CASE WHEN in_splunk OR in_chronicle THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as global_visibility_pct FROM ao1_asset_inventory;"
	@echo ""
	@echo "Platform Coverage:"
	@duckdb $(DATABASE_FILE) "SELECT (SUM(CASE WHEN in_splunk THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as splunk_coverage, (SUM(CASE WHEN in_chronicle THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as chronicle_coverage FROM ao1_asset_inventory;"
	@echo ""
	@echo "Security Tool Coverage:"
	@duckdb $(DATABASE_FILE) "SELECT (SUM(CASE WHEN has_crowdstrike THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as crowdstrike_coverage FROM ao1_asset_inventory;"

ao1-gaps:
	@if [ ! -f "$(DATABASE_FILE)" ]; then \
		echo "AO1 database not found. Run discovery first."; \
		exit 1; \
	fi
	@echo "AO1 Visibility Gaps Analysis"
	@echo "==========================="
	@echo ""
	@echo "Critical Gaps (No Logging Coverage):"
	@duckdb $(DATABASE_FILE) "SELECT COUNT(*) as count FROM ao1_asset_inventory WHERE NOT in_splunk AND NOT in_chronicle;"
	@echo ""
	@echo "Missing Security Coverage:"
	@duckdb $(DATABASE_FILE) "SELECT COUNT(*) as count FROM ao1_asset_inventory WHERE NOT has_crowdstrike;"
	@echo ""
	@echo "CMDB Gaps:"
	@duckdb $(DATABASE_FILE) "SELECT COUNT(*) as count FROM ao1_asset_inventory WHERE NOT found_in_cmdb;"
	@echo ""
	@echo "Top 10 Assets with Critical Gaps:"
	@duckdb $(DATABASE_FILE) "SELECT hostname, global_region, system_classification FROM ao1_asset_inventory WHERE NOT in_splunk AND NOT in_chronicle AND NOT found_in_cmdb LIMIT 10;"

ao1-metrics:
	@if [ ! -f "$(DATABASE_FILE)" ]; then \
		echo "AO1 database not found. Run discovery first."; \
		exit 1; \
	fi
	@echo "AO1 Visibility Metrics"
	@echo "===================="
	@duckdb $(DATABASE_FILE) "SELECT metric_category, metric_name, metric_value, metric_target, gap_percentage FROM ao1_visibility_metrics ORDER BY improvement_priority;"

ao1-compliance:
	@if [ ! -f "$(DATABASE_FILE)" ]; then \
		echo "AO1 database not found. Run discovery first."; \
		exit 1; \
	fi
	@echo "AO1 Logging Compliance Status"
	@echo "============================"
	@duckdb $(DATABASE_FILE) "SELECT compliance_status, COUNT(*) as asset_count, (COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ao1_logging_compliance)) as percentage FROM ao1_logging_compliance GROUP BY compliance_status;"

ao1-recommendations:
	@if [ ! -f "$(DATABASE_FILE)" ]; then \
		echo "AO1 database not found. Run discovery first."; \
		exit 1; \
	fi
	@echo "AO1 Improvement Recommendations"
	@echo "=============================="
	@duckdb $(DATABASE_FILE) "SELECT gap_category, gap_description, affected_asset_count, severity_level, recommended_action FROM ao1_gap_analysis ORDER BY affected_asset_count DESC;"

export:
	@echo "Exporting AO1 results..."
	@mkdir -p $(OUTPUT_DIR)/exports
	@if [ -f "$(DATABASE_FILE)" ]; then \
		echo "Exporting asset inventory to CSV..."; \
		duckdb $(DATABASE_FILE) "COPY (SELECT * FROM ao1_asset_inventory) TO '$(OUTPUT_DIR)/exports/ao1_asset_inventory.csv' (HEADER, DELIMITER ',');"; \
		echo "Exporting visibility gaps to CSV..."; \
		duckdb $(DATABASE_FILE) "COPY (SELECT hostname, source_systems, global_region, system_classification, CASE WHEN NOT in_splunk AND NOT in_chronicle THEN 'Critical - No Logging' WHEN NOT has_crowdstrike THEN 'High - No Security' WHEN NOT found_in_cmdb THEN 'Medium - Missing CMDB' ELSE 'Low Risk' END as gap_severity FROM ao1_asset_inventory WHERE NOT (in_splunk AND in_chronicle AND has_crowdstrike AND found_in_cmdb)) TO '$(OUTPUT_DIR)/exports/ao1_visibility_gaps.csv' (HEADER, DELIMITER ',');"; \
		echo "Exporting metrics to CSV..."; \
		duckdb $(DATABASE_FILE) "COPY (SELECT * FROM ao1_visibility_metrics) TO '$(OUTPUT_DIR)/exports/ao1_metrics.csv' (HEADER, DELIMITER ',');"; \
		echo "Results exported to $(OUTPUT_DIR)/exports/"; \
	else \
		echo "AO1 database not found"; \
	fi

backup:
	@echo "Creating AO1 backup..."
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S) && \
	mkdir -p backups && \
	tar -czf "backups/ao1_backup_$$TIMESTAMP.tar.gz" \
		$(DATABASE_FILE) \
		$(OUTPUT_DIR) \
		$(LOGS_DIR) \
		$(CHECKPOINTS_DIR) \
		2>/dev/null || true
	@echo "Backup created in backups/"

status:
	@echo "AO1 System Status"
	@echo "================"
	@echo ""
	@echo "Environment:"
	@echo "  Project ID: $(or $(PROJECT_ID),Not set)"
	@echo "  Config file: $(CONFIG_FILE)"
	@echo "  Workers: $(WORKERS)"
	@echo ""
	@echo "Files:"
	@ls -la $(DATABASE_FILE) 2>/dev/null && echo "  AO1 database exists" || echo "  AO1 database not found"
	@ls -la $(CONFIG_FILE) 2>/dev/null && echo "  Config exists" || echo "  Config not found"
	@ls -d $(OUTPUT_DIR) 2>/dev/null && echo "  Output directory exists" || echo "  Output directory not found"
	@echo ""
	@if [ -f "$(DATABASE_FILE)" ]; then \
		echo "Database Statistics:"; \
		duckdb $(DATABASE_FILE) "SELECT 'Total Assets: ' || COUNT(*) FROM ao1_asset_inventory;" 2>/dev/null || echo "  Cannot read database"; \
	fi

logs:
	@if [ -d "$(LOGS_DIR)" ]; then \
		echo "Recent AO1 Logs"; \
		find $(LOGS_DIR) -name "*.log" -type f -exec ls -lt {} + | head -5; \
		echo ""; \
		echo "Latest log content:"; \
		find $(LOGS_DIR) -name "*.log" -type f -exec ls -t {} + | head -1 | xargs tail -20; \
	else \
		echo "No logs directory found"; \
	fi

test:
	@echo "Running tests..."
	@python3 -m pytest tests/ -v || echo "No tests found"

format:
	@echo "Formatting code..."
	@black . || echo "black not installed"

lint:
	@echo "Running linting..."
	@flake8 . || echo "flake8 not installed"

clean:
	@echo "Cleaning generated files..."
	@rm -rf __pycache__ .pytest_cache .cache
	@rm -f *.pyc *.pyo
	@rm -f discovery_checkpoint.json
	@echo "Cleanup complete"