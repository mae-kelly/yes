# AO1 Log Visibility Measurement Dashboard

A comprehensive cybersecurity operations center (CSOC) dashboard for measuring log visibility and security control coverage across enterprise infrastructure.

## Features

- **Global View**: Overall coverage metrics across all platforms
- **Infrastructure Analysis**: Detailed breakdown by infrastructure types
- **Regional & Country Coverage**: Geographic distribution analysis
- **Business Unit Analysis**: Coverage by organizational units
- **System Classification**: Analysis by system types and classes
- **Security Control Coverage**: Agent deployment and overlap analysis
- **Domain Visibility**: 1DC vs FEAD domain analysis
- **Logging Compliance**: Platform compliance tracking
- **Log Type Priority**: Critical log source priority matrix

## Technology Stack

- **Backend**: Python Flask with DuckDB
- **Frontend**: Svelte with Vite
- **Database**: DuckDB (universal_cmdb.db)
- **Styling**: Custom CSS framework optimized for cybersecurity dashboards

## Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- npm
- DuckDB database file (`universal_cmdb.db`) in project root

## Quick Start

1. **Clone and setup the project:**
   ```bash
   git clone <repository-url>
   cd ao1-log-visibility-dashboard
   ```

2. **Place your database file:**
   - Ensure `universal_cmdb.db` is in the project root directory

3. **Start the server (Terminal 1):**
   ```bash
   chmod +x server.sh
   ./server.sh
   ```

4. **Start the client (Terminal 2):**
   ```bash
   chmod +x client.sh
   ./client.sh
   ```

5. **Access the dashboard:**
   - Open http://localhost:3000 in your browser

## Project Structure

```
ao1-log-visibility-dashboard/
├── README.md
├── server.sh                 # Server startup script
├── client.sh                 # Client startup script
├── universal_cmdb.db         # Your database file (not included)
├── server/
│   ├── app.py               # Flask application
│   ├── requirements.txt     # Python dependencies
│   └── venv/               # Virtual environment (auto-created)
└── client/
    ├── package.json         # Node.js dependencies
    ├── vite.config.js       # Vite configuration
    ├── index.html           # Main HTML file
    ├── src/
    │   ├── main.js         # Entry point
    │   ├── App.svelte      # Main application component
    │   ├── styles/
    │   │   └── global.css  # Cybersecurity-themed CSS framework
    │   └── components/
    │       ├── GlobalView.svelte
    │       ├── InfrastructureType.svelte
    │       ├── RegionalCountryView.svelte
    │       ├── BUandApplicationView.svelte
    │       ├── SystemClassification.svelte
    │       ├── SecurityControlCoverage.svelte
    │       ├── DomainVisibility.svelte
    │       ├── LoggingComplianceInGSOandSplunk.svelte
    │       └── LogTypePriority.svelte
    └── node_modules/       # Dependencies (auto-created)
```

## API Endpoints

The Flask server provides the following API endpoints:

- `/api/global-view` - Overall coverage statistics
- `/api/infrastructure-type` - Infrastructure type analysis
- `/api/regional-country-view` - Geographic coverage breakdown
- `/api/bu-application-view` - Business unit analysis
- `/api/system-classification` - System classification metrics
- `/api/security-control-coverage` - Security agent coverage
- `/api/domain-visibility` - Domain-specific analysis
- `/api/logging-compliance-gso-splunk` - Platform compliance
- `/api/log-type-priority` - Log source prioritization

## Database Schema Requirements

The system expects a DuckDB database with a table named `universal_cmdb` containing the following columns:

- `host` - Hostname
- `domain` - Domain information
- `infrastructure_type` - Infrastructure classification
- `region` - Geographic region
- `country` - Country information
- `business_unit` - Business unit assignment
- `cio` - CIO assignment
- `system_classification` - System type classification
- `class` - System class information
- `logging_in_splunk` - Splunk logging status
- `logging_in_chronicle` - Chronicle logging status
- `present_in_cmdb` - CMDB presence indicator
- `edr_coverage` - EDR agent coverage
- `tanium_coverage` - Tanium agent coverage
- `dlp_agent_coverage` - DLP agent coverage
- `apm` - APM monitoring status

## Customization

### Adding New Components

1. Create a new Svelte component in `client/src/components/`
2. Add the route to the `routes` object in `App.svelte`
3. Create corresponding API endpoint in `server/app.py`

### Modifying Threat Levels

Adjust the `getThreatLevel()` function in components to change color coding thresholds:
- 90%+ = Optimal (Green)
- 75-89% = Good (Cyan)
- 50-74% = Moderate (Yellow)
- 25-49% = Poor (Magenta)
- <25% = Critical (Red)

## Troubleshooting

### Server Issues

- **Database not found**: Ensure `universal_cmdb.db` is in the project root
- **Python dependencies**: Run `pip install -r server/requirements.txt`
- **Port conflicts**: Change the port in `server/app.py` if 5000 is in use

### Client Issues

- **Node modules**: Delete `client/node_modules` and run `npm install`
- **Port conflicts**: Change the port in `client/vite.config.js` if 3000 is in use
- **API connection**: Ensure the server is running before starting the client

### Common Database Issues

- **Missing columns**: Verify your database schema matches the expected structure
- **Data format**: Ensure multi-value fields use `|` or `,` as separators
- **Case sensitivity**: The system handles case-insensitive matching for status fields

## Performance Optimization

- The dashboard handles up to 2M+ database records efficiently
- Queries are optimized for real-time dashboard updates
- Multi-value field parsing is cached for better performance

## Security Considerations

- The dashboard runs on localhost by default
- No authentication is implemented - add security layers for production use
- Database connections are read-only for safety

## Support

For issues related to:
- Database connectivity: Check your DuckDB installation
- Frontend errors: Check browser console for JavaScript errors
- Performance issues: Monitor database query execution times