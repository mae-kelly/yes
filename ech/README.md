# AO1 Log Visibility - Neural Threat Intelligence System

A comprehensive cybersecurity analytics platform for FISERV CSOC log visibility measurement.

## 🚀 Quick Setup (All files at root level)

### Prerequisites
- Python 3.8+
- Node.js 16+
- Your `universal_cmdb.db` DuckDB file

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies  
npm install
```

### 2. Place Your Database
Ensure your `universal_cmdb.db` file is in the same directory as all other files.

### 3. Start the Application

```bash
# Terminal 1: Start Backend
python app.py

# Terminal 2: Start Frontend
npm run dev
```

### 4. Access the Application
Open http://localhost:3000

## 📁 File Structure (All at Root Level)

```
├── package.json              # Node.js dependencies
├── vite.config.js            # Vite configuration
├── requirements.txt          # Python dependencies
├── index.html               # Main HTML file
├── main.js                  # Application entry point
├── app.css                  # Global styles
├── app.py                   # Flask backend
├── App.svelte               # Main Svelte component
├── MatrixBackground.svelte  # Matrix rain effect
├── SourceTables.svelte      # Source tables analysis
├── DomainMetrics.svelte     # 1DC vs FEAD analysis
├── InfrastructureType.svelte # Infrastructure analysis
├── RegionMetrics.svelte     # Regional distribution
├── CountryMetrics.svelte    # Country analysis
├── DataCenterMetrics.svelte # Data center mapping
├── CloudRegionMetrics.svelte # Cloud regions
├── ClassMetrics.svelte      # Class analysis
├── SystemClassification.svelte # System taxonomy
├── BusinessUnitMetrics.svelte # Business units
├── CioMetrics.svelte        # CIO analysis
├── TaniumCoverage.svelte    # Tanium deployment
├── CmdbPresence.svelte      # CMDB registration
├── universal_cmdb.db        # Your database file
└── README.md                # This file
```

## 🗄️ Database Requirements

Your `universal_cmdb.db` should contain a table named `universal_cmdb` with these columns:

- `host` - Hostname/server identifier
- `source_tables` - Comma-separated data sources
- `domain` - Domain information for 1DC/FEAD analysis
- `infrastructure_type` - Pipe-separated infrastructure types
- `region` - Geographic region
- `country` - Country location
- `data_center` - Data center identifier
- `cloud_region` - Cloud region identifier
- `class` - Classification data
- `system` - System types (pipe-separated)
- `business_unit` - Business unit info (comma/pipe-separated)
- `cio` - CIO information (words only)
- `tanium_coverage` - Tanium agent status
- `present_in_cmdb` - CMDB registration status

## 🎨 Features

### Neural Threat Intelligence Dashboard
- **Matrix Background**: Animated Matrix-style background effect
- **Real-time Analytics**: Live data visualization
- **Multiple Analysis Views**: 13 different analytical perspectives

### Analysis Modules
1. **SOURCE TABLES** - Comma-separated frequency analysis
2. **1DC vs FEAD** - Domain intelligence classification
3. **INFRASTRUCTURE** - Pipe-separated infrastructure types
4. **REGIONS** - Global regional distribution
5. **COUNTRIES** - Normalized country analysis
6. **DATA CENTERS** - Facility intelligence mapping
7. **CLOUD REGIONS** - Cloud infrastructure analysis
8. **CLASSES** - Class number extraction and analysis
9. **SYSTEMS** - System taxonomy classification
10. **BUSINESS UNITS** - Organizational structure analysis
11. **CIO ANALYSIS** - Chief Information Officer data
12. **TANIUM** - Security agent deployment tracking
13. **CMDB** - Configuration database compliance

## 🛠️ Troubleshooting

### Database Connection Issues
```bash
# Test database connection
python -c "
import duckdb
conn = duckdb.connect('universal_cmdb.db')
print('✅ Connected successfully')
tables = conn.execute('SHOW TABLES').fetchall()
print('Tables found:', tables)
conn.close()
"
```

### Port Conflicts
- Backend runs on port 5000
- Frontend runs on port 3000
- Change ports in `app.py` and `vite.config.js` if needed

### Import Errors
Ensure all `.svelte` files are in the same directory as `App.svelte`

## 🔧 API Endpoints

- `GET /api/database_status` - Database connection status
- `GET /api/source_tables` - Source table analysis
- `GET /api/domain_metrics` - Domain intelligence
- `GET /api/infrastructure_type` - Infrastructure analysis
- `GET /api/region_metrics` - Regional metrics
- `GET /api/country_metrics` - Country distribution
- `GET /api/data_center_metrics` - Data center analysis
- `GET /api/cloud_region_metrics` - Cloud regions
- `GET /api/class_metrics` - Classification analysis
- `GET /api/system_classification_metrics` - System taxonomy
- `GET /api/business_unit_metrics` - Business unit analysis
- `GET /api/cio_metrics` - CIO analysis
- `GET /api/tanium_coverage` - Tanium deployment status
- `GET /api/cmdb_presence` - CMDB registration status
- `GET /api/host_search?q=<term>` - Host search functionality

## 🎯 Usage

1. Start both backend and frontend servers
2. Navigate to http://localhost:3000
3. Use the navigation modules to switch between analysis views
4. Each module provides specific insights into your infrastructure
5. Data refreshes automatically when switching modules
6. Use the REFRESH button to reload current data

## 💻 Development

- Built with **Svelte** + **Vite** for frontend
- **Flask** + **DuckDB** for backend
- **Matrix-themed** cyberpunk UI design
- **Responsive** grid layouts
- **Real-time** data visualization

## 🔒 Security Features

- Read-only database connections
- CORS protection configured
- Input validation and sanitization
- Error handling and logging
- No mock or test data - works only with real databases

---

**CLASSIFICATION: TOP SECRET // NEURAL THREAT INTELLIGENCE PROTOCOL ACTIVE**