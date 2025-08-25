import logging
import re
from typing import List, Dict
from collections import Counter

logger = logging.getLogger(__name__)

class NLPDocumentProcessor:
    def __init__(self):
        self.processed_docs = []
        
        logger.info("NLP Document Processor initialized for automated documentation analysis")
    
    def process_documentation(self, documents: List[str]) -> List[Dict]:
        logger.info(f"Processing {len(documents)} documentation files with NLP")
        
        extracted_assets = []
        
        for doc_id, document in enumerate(documents):
            logger.info(f"  Processing document {doc_id + 1}")
            
            hostnames = self.extract_hostnames(document)
            ip_addresses = self.extract_ip_addresses(document)
            configurations = self.extract_configurations(document)
            
            for hostname in hostnames:
                extracted_assets.append({
                    'hostname': hostname,
                    'source': 'documentation',
                    'doc_id': doc_id,
                    'confidence': 0.8
                })
            
            for ip in ip_addresses:
                extracted_assets.append({
                    'ip': ip,
                    'source': 'documentation',
                    'doc_id': doc_id,
                    'confidence': 0.7
                })
        
        logger.info(f"    Extracted {len(extracted_assets)} potential assets from documentation")
        
        return extracted_assets
    
    def extract_hostnames(self, text: str) -> List[str]:
        hostname_patterns = [
            r'[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-]+\.[a-zA-Z]+',
            r'[a-zA-Z]+-[a-zA-Z0-9]+-\d{2,3}',
            r'srv-[a-zA-Z0-9]+-\d{2,3}',
            r'[a-zA-Z]{2,4}\d{2,4}[a-zA-Z]{2,4}'
        ]
        
        hostnames = []
        for pattern in hostname_patterns:
            matches = re.findall(pattern, text)
            hostnames.extend(matches)
        
        return list(set(hostnames))
    
    def extract_ip_addresses(self, text: str) -> List[str]:
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ips = re.findall(ip_pattern, text)
        
        valid_ips = []
        for ip in ips:
            parts = ip.split('.')
            if all(0 <= int(part) <= 255 for part in parts):
                valid_ips.append(ip)
        
        return valid_ips
    
    def extract_configurations(self, text: str) -> Dict:
        configs = {
            'servers': [],
            'databases': [],
            'applications': [],
            'network_devices': []
        }
        
        if 'server' in text.lower():
            configs['servers'] = re.findall(r'server[:\s]+([a-zA-Z0-9\-\.]+)', text.lower())
        
        if 'database' in text.lower() or 'db' in text.lower():
            configs['databases'] = re.findall(r'database[:\s]+([a-zA-Z0-9\-\.]+)', text.lower())
        
        return configs