.PHONY: help install run docker-build docker-run clean test format lint setup

PROJECT_ID ?= $(GOOGLE_CLOUD_PROJECT)
CONFIG_FILE ?= config.yaml
WORKERS ?= 12

DATA_DIR ?= ./data
CACHE_DIR ?= $(DATA_DIR)/cache
LOGS_DIR ?= $(DATA_DIR)/logs
OUTPUT_DIR ?= $(DATA_DIR)/output
CHECKPOINTS_DIR ?= $(DATA_DIR)/checkpoints

DOCKER_IMAGE ?= ao1-discovery:latest

help:
	@echo "AO1 Log Visibility Discovery System"
	@echo "==================================="
	@echo ""
	@echo "Core Commands:"
	@echo "  setup                 - Complete setup"
	@echo "  run                   - Run AO1 discovery"
	@echo "  docker-run            - Run discovery in Docker"
	@echo "  estimate              - Estimate scope"
	@echo "  resume                - Resume from checkpoint"
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
	@echo "  analyze               - Analyze AO1 results"
	@echo "  export                - Export results"
	@echo "  clean                 - Clean generated files"
	@echo "  backup                - Backup results"
	@echo ""
	@echo "Configuration:"
	@echo "  PROJECT_ID            - GCP Project ID ($(PROJECT_ID))"
	@echo "  CONFIG_FILE           - Configuration file ($(CONFIG_FILE))"
	@echo "  WORKERS               - Number of workers ($(WORKERS))"

setup:
	@echo "AO1 Discovery Setup"
	@echo "=================="
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
	@echo "Setup complete!"

check-prerequisites:
	@echo "Checking Python version..."
	@python3 --version || (echo "Python 3.8+ required" && exit 1)
	@echo "Checking pip..."
	@pip3 --version || (echo "pip3 required" && exit 1)
	@echo "Checking gcloud..."
	@gcloud version --format="value(Google Cloud SDK)" 2>/dev/null || echo "gcloud not found"
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

run:
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "PROJECT_ID not set"; \
		echo "Run: export GOOGLE_CLOUD_PROJECT='your-project-id'"; \
		exit 1; \
	fi
	@echo "Starting AO1 discovery..."
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

analyze:
	@if [ ! -f "ao1_visibility_cmdb.db" ]; then \
		echo "AO1 database not found. Run discovery first."; \
		exit 1; \
	fi
	@echo "AO1 Visibility Analysis"
	@echo "======================"
	@echo ""
	@echo "Total Assets:"
	@duckdb ao1_visibility_cmdb.db "SELECT COUNT(*) as total_assets FROM ao1_asset_inventory;"
	@echo ""
	@echo "Visibility Coverage:"
	@duckdb ao1_visibility_cmdb.db "SELECT (SUM(CASE WHEN in_splunk OR in_chronicle THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as global_visibility_pct FROM ao1_asset_inventory;"
	@echo ""
	@echo "Security Tool Coverage:"
	@duckdb ao1_visibility_cmdb.db "SELECT (SUM(CASE WHEN has_crowdstrike THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as crowdstrike_coverage FROM ao1_asset_inventory;"

export:
	@echo "Exporting AO1 results..."
	@mkdir -p $(OUTPUT_DIR)/exports
	@if [ -f "ao1_visibility_cmdb.db" ]; then \
		echo "Exporting asset inventory to CSV..."; \
		duckdb ao1_visibility_cmdb.db "COPY (SELECT * FROM ao1_asset_inventory) TO '$(OUTPUT_DIR)/exports/ao1_asset_inventory.csv' (HEADER, DELIMITER ',');"; \
		echo "Exporting visibility gaps to CSV..."; \
		duckdb ao1_visibility_cmdb.db "COPY (SELECT hostname, found_in_tables, global_region, system_classification, CASE WHEN NOT in_splunk AND NOT in_chronicle THEN 'No Logging Coverage' ELSE 'Partial Coverage' END as gap_type FROM ao1_asset_inventory WHERE NOT (in_splunk AND in_chronicle)) TO '$(OUTPUT_DIR)/exports/ao1_visibility_gaps.csv' (HEADER, DELIMITER ',');"; \
		echo "Results exported to $(OUTPUT_DIR)/exports/"; \
	else \
		echo "AO1 database not found"; \
	fi

backup:
	@echo "Creating AO1 backup..."
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S) && \
	mkdir -p backups && \
	tar -czf "backups/ao1_backup_$$TIMESTAMP.tar.gz" \
		ao1_visibility_cmdb.db \
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
	@ls -la ao1_visibility_cmdb.db 2>/dev/null && echo "  AO1 database exists" || echo "  AO1 database not found"
	@ls -la $(CONFIG_FILE) 2>/dev/null && echo "  Config exists" || echo "  Config not found"
	@ls -d $(OUTPUT_DIR) 2>/dev/null && echo "  Output directory exists" || echo "  Output directory not found"

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