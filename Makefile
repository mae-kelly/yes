.PHONY: help install run docker-build docker-run clean test format lint setup

PROJECT_ID ?= $(GOOGLE_CLOUD_PROJECT)
CONFIG_FILE ?= config.yaml
MAX_COST ?= 100
WORKERS ?= 32
LOG_LEVEL ?= INFO

DATA_DIR ?= ./data
CACHE_DIR ?= $(DATA_DIR)/cache
LOGS_DIR ?= $(DATA_DIR)/logs
OUTPUT_DIR ?= $(DATA_DIR)/output
CHECKPOINTS_DIR ?= $(DATA_DIR)/checkpoints

DOCKER_IMAGE ?= cmdb-discovery:latest

RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m

help:
	@echo "$(BLUE)CMDB Discovery System$(NC)"
	@echo "$(BLUE)=====================$(NC)"
	@echo ""
	@echo "$(GREEN)Core Commands:$(NC)"
	@echo "  $(YELLOW)setup$(NC)                 - Complete setup"
	@echo "  $(YELLOW)run$(NC)                   - Run discovery locally"
	@echo "  $(YELLOW)docker-run$(NC)            - Run discovery in Docker"
	@echo "  $(YELLOW)estimate$(NC)              - Estimate scope and cost"
	@echo "  $(YELLOW)resume$(NC)                - Resume from checkpoint"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  $(YELLOW)install$(NC)               - Install dependencies"
	@echo "  $(YELLOW)test$(NC)                  - Run tests"
	@echo "  $(YELLOW)format$(NC)                - Format code"
	@echo "  $(YELLOW)lint$(NC)                  - Run linting"
	@echo ""
	@echo "$(GREEN)Docker:$(NC)"
	@echo "  $(YELLOW)docker-build$(NC)          - Build Docker image"
	@echo "  $(YELLOW)docker-dev$(NC)            - Run development container"
	@echo ""
	@echo "$(GREEN)Data Management:$(NC)"
	@echo "  $(YELLOW)analyze$(NC)               - Analyze results"
	@echo "  $(YELLOW)export$(NC)                - Export results"
	@echo "  $(YELLOW)clean$(NC)                 - Clean generated files"
	@echo "  $(YELLOW)backup$(NC)                - Backup results"
	@echo ""
	@echo "$(GREEN)Configuration:$(NC)"
	@echo "  $(YELLOW)PROJECT_ID$(NC)            - GCP Project ID ($(PROJECT_ID))"
	@echo "  $(YELLOW)CONFIG_FILE$(NC)           - Configuration file ($(CONFIG_FILE))"
	@echo "  $(YELLOW)MAX_COST$(NC)              - Maximum cost in USD ($(MAX_COST))"
	@echo "  $(YELLOW)WORKERS$(NC)               - Number of workers ($(WORKERS))"

setup:
	@echo "$(BLUE)CMDB Discovery Setup$(NC)"
	@echo "$(BLUE)====================$(NC)"
	@echo ""
	@echo "$(GREEN)1. Checking prerequisites...$(NC)"
	@$(MAKE) check-prerequisites
	@echo ""
	@echo "$(GREEN)2. Creating directory structure...$(NC)"
	@$(MAKE) create-dirs
	@echo ""
	@echo "$(GREEN)3. Installing dependencies...$(NC)"
	@$(MAKE) install
	@echo ""
	@echo "$(GREEN)4. Validating configuration...$(NC)"
	@$(MAKE) validate-config
	@echo ""
	@echo "$(GREEN)Setup complete!$(NC)"

check-prerequisites:
	@echo "$(BLUE)Checking Python version...$(NC)"
	@python3 --version || (echo "$(RED)Python 3.8+ required$(NC)" && exit 1)
	@echo "$(BLUE)Checking pip...$(NC)"
	@pip3 --version || (echo "$(RED)pip3 required$(NC)" && exit 1)
	@echo "$(BLUE)Checking gcloud...$(NC)"
	@gcloud version --format="value(Google Cloud SDK)" 2>/dev/null || echo "$(YELLOW)gcloud not found$(NC)"
	@echo "$(BLUE)Checking Docker...$(NC)"
	@docker --version 2>/dev/null || echo "$(YELLOW)Docker not found$(NC)"
	@echo "$(GREEN)Prerequisites checked$(NC)"

create-dirs:
	@mkdir -p $(DATA_DIR) $(CACHE_DIR) $(LOGS_DIR) $(OUTPUT_DIR) $(CHECKPOINTS_DIR)
	@mkdir -p config
	@echo "$(GREEN)Directory structure created$(NC)"

install:
	@echo "$(BLUE)Installing Python dependencies...$(NC)"
	@pip3 install -r requirements.txt
	@echo "$(GREEN)Dependencies installed$(NC)"

validate-config:
	@if [ -f "$(CONFIG_FILE)" ]; then \
		echo "$(GREEN)Configuration file found: $(CONFIG_FILE)$(NC)"; \
		python3 -c "import yaml; yaml.safe_load(open('$(CONFIG_FILE)'))" || \
		(echo "$(RED)Invalid YAML configuration$(NC)" && exit 1); \
	else \
		echo "$(YELLOW)Configuration file not found: $(CONFIG_FILE)$(NC)"; \
	fi

run:
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "$(RED)PROJECT_ID not set$(NC)"; \
		echo "Run: export GOOGLE_CLOUD_PROJECT='your-project-id'"; \
		exit 1; \
	fi
	@echo "$(BLUE)Starting discovery...$(NC)"
	@echo "$(BLUE)Project: $(PROJECT_ID)$(NC)"
	@echo "$(BLUE)Workers: $(WORKERS)$(NC)"
	@echo "$(BLUE)Cost limit: $$(MAX_COST)$(NC)"
	@python3 main.py \
		--project $(PROJECT_ID) \
		--config $(CONFIG_FILE) \
		--workers $(WORKERS) \
		--cost-limit $(MAX_COST) \
		--log-level $(LOG_LEVEL) \
		--output-dir $(OUTPUT_DIR)

estimate:
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "$(RED)PROJECT_ID not set$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Estimating discovery scope...$(NC)"
	@python3 main.py \
		--project $(PROJECT_ID) \
		--config $(CONFIG_FILE) \
		--dry-run \
		--output-dir $(OUTPUT_DIR)

resume:
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "$(RED)PROJECT_ID not set$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Resuming from checkpoint...$(NC)"
	@python3 main.py \
		--project $(PROJECT_ID) \
		--config $(CONFIG_FILE) \
		--resume \
		--workers $(WORKERS) \
		--cost-limit $(MAX_COST) \
		--output-dir $(OUTPUT_DIR)

docker-build:
	@echo "$(BLUE)Building Docker image...$(NC)"
	@docker build -f Dockerfile -t $(DOCKER_IMAGE) .
	@echo "$(GREEN)Docker image built: $(DOCKER_IMAGE)$(NC)"

docker-run: docker-build
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "$(RED)PROJECT_ID not set$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Running discovery in Docker...$(NC)"
	@mkdir -p $(DATA_DIR) $(CACHE_DIR) $(LOGS_DIR) $(OUTPUT_DIR) $(CHECKPOINTS_DIR)
	@GOOGLE_CLOUD_PROJECT=$(PROJECT_ID) \
	 DATA_DIR=$(DATA_DIR) \
	 CACHE_DIR=$(CACHE_DIR) \
	 LOGS_DIR=$(LOGS_DIR) \
	 docker-compose up --build discovery

docker-dev: docker-build
	@echo "$(BLUE)Starting development container...$(NC)"
	@docker-compose run --rm discovery-dev

analyze:
	@if [ ! -f "universal_cmdb.db" ]; then \
		echo "$(RED)Database not found. Run discovery first.$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Quick Analysis$(NC)"
	@echo "$(BLUE)==============$(NC)"
	@echo ""
	@echo "$(GREEN)Total Endpoints:$(NC)"
	@duckdb universal_cmdb.db "SELECT COUNT(*) as total_endpoints FROM universal_endpoint;"
	@echo ""
	@echo "$(GREEN)Core System Coverage:$(NC)"
	@duckdb universal_cmdb.db "SELECT SUM(CASE WHEN original_cmdb THEN 1 ELSE 0 END) as cmdb, SUM(CASE WHEN original_splunk THEN 1 ELSE 0 END) as splunk, SUM(CASE WHEN original_crowdstrike THEN 1 ELSE 0 END) as crowdstrike FROM universal_endpoint;"

export:
	@echo "$(BLUE)Exporting results...$(NC)"
	@mkdir -p $(OUTPUT_DIR)/exports
	@if [ -f "universal_cmdb.db" ]; then \
		echo "$(BLUE)Exporting endpoints to CSV...$(NC)"; \
		duckdb universal_cmdb.db "COPY (SELECT * FROM universal_endpoint) TO '$(OUTPUT_DIR)/exports/endpoints.csv' (HEADER, DELIMITER ',');"; \
		echo "$(BLUE)Exporting tables to CSV...$(NC)"; \
		duckdb universal_cmdb.db "COPY (SELECT * FROM discovered_table) TO '$(OUTPUT_DIR)/exports/discovered_tables.csv' (HEADER, DELIMITER ',');"; \
		echo "$(GREEN)Results exported to $(OUTPUT_DIR)/exports/$(NC)"; \
	else \
		echo "$(RED)Database not found$(NC)"; \
	fi

backup:
	@echo "$(BLUE)Creating backup...$(NC)"
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S) && \
	mkdir -p backups && \
	tar -czf "backups/discovery_backup_$$TIMESTAMP.tar.gz" \
		universal_cmdb.db \
		$(OUTPUT_DIR) \
		$(LOGS_DIR) \
		$(CHECKPOINTS_DIR) \
		2>/dev/null || true
	@echo "$(GREEN)Backup created in backups/$(NC)"

status:
	@echo "$(BLUE)System Status$(NC)"
	@echo "$(BLUE)==============$(NC)"
	@echo ""
	@echo "$(GREEN)Environment:$(NC)"
	@echo "  Project ID: $(or $(PROJECT_ID),Not set)"
	@echo "  Config file: $(CONFIG_FILE)"
	@echo "  Max cost: $$(MAX_COST)"
	@echo "  Workers: $(WORKERS)"
	@echo ""
	@echo "$(GREEN)Files:$(NC)"
	@ls -la universal_cmdb.db 2>/dev/null && echo "  Database exists" || echo "  Database not found"
	@ls -la $(CONFIG_FILE) 2>/dev/null && echo "  Config exists" || echo "  Config not found"
	@ls -d $(OUTPUT_DIR) 2>/dev/null && echo "  Output directory exists" || echo "  Output directory not found"

logs:
	@if [ -d "$(LOGS_DIR)" ]; then \
		echo "$(BLUE)Recent Logs$(NC)"; \
		find $(LOGS_DIR) -name "*.log" -type f -exec ls -lt {} + | head -5; \
		echo ""; \
		echo "$(GREEN)Latest log content:$(NC)"; \
		find $(LOGS_DIR) -name "*.log" -type f -exec ls -t {} + | head -1 | xargs tail -20; \
	else \
		echo "$(RED)No logs directory found$(NC)"; \
	fi

test:
	@echo "$(BLUE)Running tests...$(NC)"
	@python3 -m pytest tests/ -v || echo "$(YELLOW)No tests found$(NC)"

format:
	@echo "$(BLUE)Formatting code...$(NC)"
	@black . || echo "$(YELLOW)black not installed$(NC)"

lint:
	@echo "$(BLUE)Running linting...$(NC)"
	@flake8 . || echo "$(YELLOW)flake8 not installed$(NC)"

clean:
	@echo "$(BLUE)Cleaning generated files...$(NC)"
	@rm -rf __pycache__ .pytest_cache .cache
	@rm -f *.pyc *.pyo
	@rm -f discovery_checkpoint.json
	@echo "$(GREEN)Cleanup complete$(NC)"