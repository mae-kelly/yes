#!/usr/bin/env python3
"""
Script to parse manual_labeled_columns.json and separate into individual JSON files by column type
"""

import json
import logging
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LabeledDataSeparator:
    def __init__(self, input_file: str = 'manual_labeled_columns.json', output_dir: str = 'separated_labels'):
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        
        # Mapping of numbers to column types and filenames
        self.column_type_mapping = {
            1: ('host', 'one_hosts.json'),
            2: ('infrastructure_type', 'two_infrastructure_types.json'),
            3: ('region', 'three_regions.json'),
            4: ('country', 'four_countries.json'),
            5: ('data_center', 'five_data_centers.json'),
            6: ('cloud_region', 'six_cloud_regions.json'),
            7: ('business_unit', 'seven_business_units.json'),
            8: ('cio', 'eight_cios.json'),
            9: ('apm', 'nine_apms.json'),
            10: ('app_class', 'ten_app_classes.json'),
            11: ('system_classification', 'eleven_system_classifications.json'),
            12: ('edr_coverage', 'twelve_edr_coverages.json'),
            13: ('tanium_coverage', 'thirteen_tanium_coverages.json'),
            14: ('dlp_agent_coverage', 'fourteen_dlp_agent_coverages.json'),
            15: ('logging_in_splunk', 'fifteen_logging_in_splunks.json'),
            16: ('logging_in_gso', 'sixteen_logging_in_gsos.json'),
            17: ('domain', 'seventeen_domains.json'),
            18: ('skip', 'eighteen_skips.json')
        }
        
        # Initialize data structures for each type
        self.separated_data = {
            num: {
                'column_type': type_info[0],
                'column_type_number': num,
                'description': f'All columns labeled as {type_info[0]} (type {num})',
                'tables': {},
                'columns': [],
                'statistics': {
                    'total_columns': 0,
                    'total_tables': 0,
                    'unique_column_names': set(),
                    'column_name_frequency': defaultdict(int)
                },
                'examples': [],
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'source_file': str(self.input_file)
                }
            }
            for num, type_info in self.column_type_mapping.items()
        }
        
    def load_labeled_data(self) -> Dict[str, Any]:
        """Load the manual labeled columns JSON file"""
        if not self.input_file.exists():
            logger.error(f"Input file {self.input_file} not found!")
            return {}
        
        try:
            with open(self.input_file, 'r') as f:
                data = json.load(f)
                logger.info(f"Successfully loaded {self.input_file}")
                return data
        except Exception as e:
            logger.error(f"Failed to load {self.input_file}: {e}")
            return {}
    
    def separate_by_column_type(self, labeled_data: Dict[str, Any]):
        """Separate the labeled data by column type"""
        
        # Process columns from each table
        columns_data = labeled_data.get('columns', {})
        
        for table_path, table_labels in columns_data.items():
            logger.info(f"Processing table: {table_path}")
            
            for column_name, label in table_labels.items():
                # Find the corresponding number for this label
                type_number = None
                for num, (type_name, _) in self.column_type_mapping.items():
                    if type_name == label:
                        type_number = num
                        break
                
                if type_number is None:
                    logger.warning(f"Unknown label '{label}' for column '{column_name}' in table '{table_path}'")
                    continue
                
                # Add to the appropriate separated data structure
                self._add_column_to_type(type_number, table_path, column_name, label)
        
        # Process patterns if they exist
        patterns_data = labeled_data.get('patterns', {})
        for label, pattern_list in patterns_data.items():
            type_number = None
            for num, (type_name, _) in self.column_type_mapping.items():
                if type_name == label:
                    type_number = num
                    break
            
            if type_number:
                self.separated_data[type_number]['examples'].extend(pattern_list[:10])
        
        # Add labeling history if it exists
        labeling_history = labeled_data.get('labeling_history', [])
        for entry in labeling_history:
            table_path = entry.get('table', '')
            labels = entry.get('labels', {})
            timestamp = entry.get('timestamp', '')
            rows = entry.get('rows', 0)
            
            for column_name, label in labels.items():
                type_number = None
                for num, (type_name, _) in self.column_type_mapping.items():
                    if type_name == label:
                        type_number = num
                        break
                
                if type_number:
                    if 'labeling_history' not in self.separated_data[type_number]:
                        self.separated_data[type_number]['labeling_history'] = []
                    
                    self.separated_data[type_number]['labeling_history'].append({
                        'table': table_path,
                        'column': column_name,
                        'timestamp': timestamp,
                        'table_rows': rows
                    })
        
        # Copy over global statistics if they exist
        if 'statistics' in labeled_data:
            for type_number in self.separated_data:
                self.separated_data[type_number]['global_statistics'] = labeled_data['statistics']
    
    def _add_column_to_type(self, type_number: int, table_path: str, column_name: str, label: str):
        """Add a column to the appropriate type's data structure"""
        
        # Add to tables dictionary
        if table_path not in self.separated_data[type_number]['tables']:
            self.separated_data[type_number]['tables'][table_path] = []
        
        self.separated_data[type_number]['tables'][table_path].append(column_name)
        
        # Add to columns list
        self.separated_data[type_number]['columns'].append({
            'table': table_path,
            'column': column_name,
            'project': table_path.split('.')[0] if '.' in table_path else 'unknown',
            'dataset': table_path.split('.')[1] if '.' in table_path else 'unknown',
            'table_name': table_path.split('.')[-1] if '.' in table_path else table_path
        })
        
        # Update statistics
        self.separated_data[type_number]['statistics']['total_columns'] += 1
        self.separated_data[type_number]['statistics']['unique_column_names'].add(column_name)
        self.separated_data[type_number]['statistics']['column_name_frequency'][column_name] += 1
    
    def calculate_final_statistics(self):
        """Calculate final statistics for each type"""
        for type_number, data in self.separated_data.items():
            # Convert set to list for JSON serialization
            data['statistics']['unique_column_names'] = list(data['statistics']['unique_column_names'])
            data['statistics']['total_tables'] = len(data['tables'])
            
            # Convert defaultdict to regular dict
            data['statistics']['column_name_frequency'] = dict(data['statistics']['column_name_frequency'])
            
            # Add most common column names
            if data['statistics']['column_name_frequency']:
                sorted_columns = sorted(
                    data['statistics']['column_name_frequency'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                data['statistics']['most_common_column_names'] = sorted_columns[:10]
            
            # Add summary
            data['summary'] = {
                'column_type': data['column_type'],
                'type_number': type_number,
                'total_columns': data['statistics']['total_columns'],
                'total_tables': data['statistics']['total_tables'],
                'unique_column_names': len(data['statistics']['unique_column_names'])
            }
    
    def save_separated_files(self):
        """Save each type's data to a separate JSON file"""
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(exist_ok=True)
        
        saved_files = []
        
        for type_number, (type_name, filename) in self.column_type_mapping.items():
            data = self.separated_data[type_number]
            
            # Only save if there's actual data
            if data['statistics']['total_columns'] > 0:
                output_file = self.output_dir / filename
                
                try:
                    with open(output_file, 'w') as f:
                        json.dump(data, f, indent=2, default=str)
                    
                    logger.info(f"✅ Saved {data['statistics']['total_columns']} columns to {output_file}")
                    saved_files.append({
                        'file': str(output_file),
                        'type': type_name,
                        'number': type_number,
                        'columns': data['statistics']['total_columns'],
                        'tables': data['statistics']['total_tables']
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to save {output_file}: {e}")
            else:
                logger.info(f"⏭️  Skipping {type_name} (type {type_number}) - no columns found")
        
        # Create a master index file
        index_file = self.output_dir / 'index.json'
        index_data = {
            'generated_at': datetime.now().isoformat(),
            'source_file': str(self.input_file),
            'total_files_created': len(saved_files),
            'files': saved_files,
            'column_type_mapping': {
                num: type_info[0] 
                for num, type_info in self.column_type_mapping.items()
            }
        }
        
        with open(index_file, 'w') as f:
            json.dump(index_data, f, indent=2)
        
        logger.info(f"📋 Created index file: {index_file}")
        
        return saved_files
    
    def generate_summary_report(self):
        """Generate a summary report of the separation"""
        
        report_file = self.output_dir / 'separation_report.txt'
        
        with open(report_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("LABELED COLUMNS SEPARATION REPORT\n")
            f.write("="*80 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Source: {self.input_file}\n\n")
            
            f.write("SUMMARY BY COLUMN TYPE\n")
            f.write("-"*80 + "\n\n")
            
            total_columns = 0
            total_tables = 0
            
            for type_number in sorted(self.separated_data.keys()):
                data = self.separated_data[type_number]
                if data['statistics']['total_columns'] > 0:
                    f.write(f"{type_number:2}. {data['column_type']:25} ")
                    f.write(f"Columns: {data['statistics']['total_columns']:5} ")
                    f.write(f"Tables: {data['statistics']['total_tables']:5}\n")
                    
                    # Show top 3 most common column names
                    if data['statistics'].get('most_common_column_names'):
                        f.write("    Most common column names:\n")
                        for col_name, count in data['statistics']['most_common_column_names'][:3]:
                            f.write(f"      - {col_name}: {count} occurrences\n")
                    f.write("\n")
                    
                    total_columns += data['statistics']['total_columns']
                    total_tables += len(data['tables'])
            
            f.write("-"*80 + "\n")
            f.write(f"TOTAL: {total_columns} columns across {total_tables} unique tables\n")
            f.write("="*80 + "\n")
        
        logger.info(f"📊 Generated summary report: {report_file}")
    
    def run(self):
        """Main execution method"""
        logger.info("Starting labeled data separation...")
        logger.info(f"Input file: {self.input_file}")
        logger.info(f"Output directory: {self.output_dir}")
        
        # Load the labeled data
        labeled_data = self.load_labeled_data()
        if not labeled_data:
            logger.error("No data to process!")
            return
        
        # Separate by column type
        self.separate_by_column_type(labeled_data)
        
        # Calculate final statistics
        self.calculate_final_statistics()
        
        # Save separated files
        saved_files = self.save_separated_files()
        
        # Generate summary report
        self.generate_summary_report()
        
        # Print summary
        print("\n" + "="*60)
        print("SEPARATION COMPLETE")
        print("="*60)
        print(f"Created {len(saved_files)} files in {self.output_dir}/")
        print("\nFiles created:")
        for file_info in saved_files:
            print(f"  {file_info['number']:2}. {file_info['type']:25} → {Path(file_info['file']).name}")
            print(f"      {file_info['columns']} columns from {file_info['tables']} tables")
        print("\nAdditional files:")
        print(f"  - index.json (master index)")
        print(f"  - separation_report.txt (detailed report)")
        print("="*60)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Separate manual labeled columns by type')
    parser.add_argument(
        '--input',
        default='manual_labeled_columns.json',
        help='Input JSON file (default: manual_labeled_columns.json)'
    )
    parser.add_argument(
        '--output',
        default='separated_labels',
        help='Output directory (default: separated_labels)'
    )
    
    args = parser.parse_args()
    
    separator = LabeledDataSeparator(input_file=args.input, output_dir=args.output)
    separator.run()

if __name__ == "__main__":
    main()