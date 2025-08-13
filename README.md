# Smart Discovery System

Ultra-intelligent asset discovery with advanced AI and visibility analysis.

## Features

- **Neural Field Classification**: Deep learning for field type detection
- **Semantic Content Analysis**: Advanced pattern recognition
- **AO1 Visibility Engine**: Comprehensive visibility analysis
- **Intelligent Caching**: Adaptive memory and disk management
- **Graph Analysis**: Asset relationship discovery
- **Anomaly Detection**: Automated visibility gap identification
- **Predictive Intelligence**: Smart strategy recommendation

## Quick Start

```bash
pip install -r requirements.txt
python main.py --project your-gcp-project
```

## Configuration

Edit `config.yaml` for advanced settings:

```yaml
max_memory_mb: 4096
max_disk_gb: 50
enable_machine_learning: true
intelligence_level: "expert"
```

## Usage

### Standard Discovery
```bash
python main.py --project prj-fisv --memory 4096 --workers 32
```

### Dry Run
```bash
python main.py --project prj-fisv --dry-run
```

### Debug Mode
```bash
python main.py --project prj-fisv --debug
```

## Architecture

```
├── core/           # Core types and data structures
├── ai/             # Neural networks and intelligence
├── cache/          # Intelligent caching system
├── discovery/      # Discovery engines
├── storage/        # Database management
├── gcp/            # BigQuery client
└── main.py         # Entry point
```

## Engines

1. **Intelligent Discovery**: Primary schema-aware discovery
2. **Content-Based Discovery**: Universal table scanning
3. **AO1 Enhanced Discovery**: Visibility-focused analysis

## Database Schema

### Assets Table
- Comprehensive asset attributes
- Intelligence scores and quality metrics
- Source tracking and confidence scoring

### Discovery Metadata
- Processing statistics
- AI insights and recommendations
- Performance metrics

## Authentication

Place GCP service account key as `gcp_prod_key.json` or use:
```bash
gcloud auth application-default login
```

## Output

- `discovery_results_YYYYMMDD_HHMMSS.json`: Complete results
- `discovery_report_YYYYMMDD_HHMMSS.json`: Executive summary
- `smart_cmdb.db`: Main asset database
- `content_cmdb.db`: Content-based discoveries

## Performance

- Processes 50,000+ assets in minutes
- Intelligent caching reduces BigQuery costs
- Adaptive strategies optimize for dataset size
- Memory-efficient processing with compression

## Requirements

- Python 3.8+
- GCP BigQuery access
- 4GB+ RAM recommended
- Neural network libraries (PyTorch)

## License

Internal use only.