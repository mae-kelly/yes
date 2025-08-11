# CMDB Discovery System

Enterprise-grade CMDB discovery and gap analysis system with parallel processing, intelligent caching, graceful failure handling, and comprehensive cost controls.

## Features

- Parallel processing with configurable worker pools
- Real-time BigQuery cost estimation and limits
- Checkpoint/resume capability for graceful interruption handling
- Content-based detection analyzing actual column data
- Multi-level caching with TTL and compression
- Graceful failure handling continuing despite individual table failures
- Real-time monitoring with progress tracking and performance metrics
- Production-grade logging with rotation

## Quick Start

### Prerequisites
- Python 3.8+
- 8GB+ RAM recommended
- 10GB+ free disk space
- Google Cloud SDK (optional)
- Docker (optional)

### Setup
```bash
# Clone repository
git clone <repository>
cd cmdb-discovery

# Install dependencies
make install

# Set your GCP project
export GOOGLE_CLOUD_PROJECT='your-project-id'

# Authenticate
gcloud auth application-default login

# Or place service account key as gcp_prod_key.json
```

### Run Discovery
```bash
# Estimate scope and cost first
make estimate

# Run full discovery
make run

# With custom settings
python main.py --project your-project-id --workers 64 --cost-limit 500
```

## Configuration

Edit `config.yaml` to customize:

```yaml
max_workers: 32
max_cost_per_query: 2.0
max_total_cost: 200.0
batch_size: 1000
cache_ttl_hours: 48
```

## Docker Usage

```bash
# Build and run with Docker
make docker-build
make docker-run

# With Docker Compose
docker-compose up discovery
```

## Available Commands

```bash
make help              # Show all commands
make setup             # Complete setup
make run               # Run discovery
make estimate          # Estimate scope/cost
make resume            # Resume from checkpoint
make analyze           # Quick analysis
make export            # Export to CSV
make status            # Check system status
make logs              # View recent logs
```

## Output

The system generates:
- `universal_cmdb.db` - Complete endpoint database
- `output/discovery_stats_*.json` - Discovery statistics
- `output/queries_*/` - Analysis SQL queries
- `logs/` - Detailed logs

## Analysis Queries

```sql
-- View all endpoints
SELECT * FROM universal_endpoint ORDER BY confidence_score DESC;

-- Coverage summary
SELECT 
    SUM(CASE WHEN original_cmdb THEN 1 ELSE 0 END) as cmdb,
    SUM(CASE WHEN original_splunk THEN 1 ELSE 0 END) as splunk,
    SUM(CASE WHEN original_crowdstrike THEN 1 ELSE 0 END) as crowdstrike
FROM universal_endpoint;

-- Missing from CMDB
SELECT * FROM universal_endpoint 
WHERE NOT original_cmdb 
ORDER BY confidence_score DESC;
```

## Performance

- Small Project (< 100 datasets): 5-10 minutes
- Medium Project (< 1000 datasets): 30-60 minutes
- Large Project (> 1000 datasets): 2-4 hours
- Enterprise Project (> 5000 datasets): 4-8 hours

## Cost Management

- Real-time BigQuery cost estimation
- Progressive per-query and total cost limits
- Smart sampling to limit data size
- Automatic table filtering for expensive operations
- Free tier usage tracking

## Error Handling

- Table-level failures continue processing other tables
- Dataset-level failures continue with other datasets
- Network timeouts with automatic retry and backoff
- Permission errors logged and skipped
- Cost limit exceeded triggers graceful shutdown with checkpoint

## Authentication

The system uses this authentication priority:
1. Service account key: `gcp_prod_key.json`
2. `GOOGLE_APPLICATION_CREDENTIALS` environment variable
3. Default gcloud credentials

## Files Structure

```
cmdb-discovery/
├── main.py                 # Main entry point
├── discovery_engine.py     # Core discovery engine
├── gcp_client.py          # BigQuery client with auth
├── content_matcher.py     # Content-based column detection
├── cache_manager.py       # Caching system
├── progress_tracker.py    # Progress monitoring
├── checkpoint_manager.py  # Checkpoint/resume
├── cost_estimator.py      # Cost calculation
├── signal_handler.py      # Signal handling
├── config_loader.py       # Configuration loading
├── config.yaml           # Main configuration
├── requirements.txt      # Dependencies
├── Dockerfile           # Container definition
├── docker-compose.yml   # Container orchestration
├── Makefile            # Build automation
└── README.md          # This file
```

## Troubleshooting

**No endpoints discovered:**
- Check GCP permissions
- Verify project has data
- Review authentication setup

**Cost limit exceeded:**
- Increase limits or use cost-conscious mode
- Reduce workers and batch size

**Memory issues:**
- Reduce workers: `--workers 8`
- Use low memory config

**BigQuery quota exceeded:**
- Add delays between queries
- Reduce parallelism

## Required GCP Permissions

```json
{
  "bigquery.datasets.get",
  "bigquery.tables.get", 
  "bigquery.tables.list",
  "bigquery.jobs.create",
  "bigquery.jobs.get"
}
```