import re
from pathlib import Path

class SolidityVersionAnalyzer:
    
    def __init__(self):
        self._version_pattern = re.compile(
            r'pragma\s+solidity\s+(?P<operators>[^\d;]*)(?P<versions>[\d\.\s]+)\s*;',
            re.IGNORECASE
        )
    
    def get_min_version_from_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return self.get_min_version_from_code(content)
        except FileNotFoundError:
            return None, f"ERROR: {file_path} is not found."
        except Exception as e:
            return None, f"ERROR - {str(e)}"
    
    def get_min_version_from_code(self, solidity_code):
        version_declarations = self._extract_version_declarations(solidity_code)
        if not version_declarations:
            return None, "ERROR: No Solidity version declaration found"
        
        min_version = None
        
        for operators, version_numbers in version_declarations:
            version_parts = re.split(r'\s+', version_numbers)
            operator_parts = re.split(r'\s+', operators)
            
            if len(operator_parts) < len(version_parts):
                operator_parts += [''] * (len(version_parts) - len(operator_parts))
            
            for i, version in enumerate(version_parts):
                if not version:
                    continue
                    
                operator = operator_parts[i] if i < len(operator_parts) else ''
                
                if operator in ('>=', '^', '>', ''):
                    if min_version is None or self._compare_versions(version, min_version) < 0:
                        min_version = version
                elif operator == '<' and min_version is None:

                    pass
        
        if min_version is None:
            return None, "EEROR: Unable to determine minimum Solidity version"
        
        return min_version, None
    
    def get_all_version_declarations(self, solidity_code):
        matches = self._version_pattern.finditer(solidity_code)
        return [match.group(0) for match in matches]
    
    def _extract_version_declarations(self, solidity_code):
        matches = self._version_pattern.finditer(solidity_code)
        return [(m.group('operators').strip(), m.group('versions').strip()) for m in matches]
    
    @staticmethod
    def _compare_versions(v1, v2):
        v1_parts = list(map(int, v1.split('.')))
        v2_parts = list(map(int, v2.split('.')))
        
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts += [0] * (max_len - len(v1_parts))
        v2_parts += [0] * (max_len - len(v2_parts))
        
        for a, b in zip(v1_parts, v2_parts):
            if a < b:
                return -1
            elif a > b:
                return 1
        return 0


