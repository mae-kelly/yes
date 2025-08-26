# README.md
# AO1 Log Visibility - Neural Threat Intelligence System

A comprehensive cybersecurity analytics platform for FISERV CSOC log visibility measurement.

## Installation

1. Backend setup:
```bash
pip install -r requirements.txt
```

2. Frontend setup:
```bash
npm install
```

## Running the Application

1. Start the Python backend:
```bash
python app.py
```

2. Start the frontend development server:
```bash
npm run dev
```

3. Access the application at http://localhost:3000

## Database Requirements

Ensure your `universal_cmdb.db` file is in the root directory with the `universal_cmdb` table containing the required columns.

## Features

- Source Tables Analysis
- Domain Intelligence (1DC vs FEAD)
- Infrastructure Type Distribution
- Regional and Country Analysis
- Data Center Mapping
- Cloud Region Analysis
- Class and System Classification
- Business Unit Analysis
- CIO Analysis
- Tanium Coverage Tracking
- CMDB Presence Monitoring