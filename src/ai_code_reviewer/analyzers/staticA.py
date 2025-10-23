# ===============================
# staticA.py
# AI-Powered Code Reviewer: Style Analyzer
# ===============================
# This analyzer checks Python code for style violations.
# It uses flake8 and other static rules (Rule examples: line length, whitespace, tabs).
# It also assigns a score and letter grade to indicate overall code quality.
# ===============================

import subprocess
import tempfile
import json
import os
from typing import Dict, Any, List
import logging
from flask import Flask, request, jsonify

logger = logging.getLogger(__name__)

class StyleAnalyzer:
    """Style analyzer using flake8 and other linting tools"""
    
    def __init__(self):
        self.violations = []
        self.score = 100.0
    
    def analyze(self, code: str) -> Dict[str, Any]:
        """Analyze Python code style using flake8"""
        try:
            self.violations = []
            self.score = 100.0
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name
            
            try:
                flake8_result = self._run_flake8(temp_file_path)
                self._check_line_length(code)
                self._check_whitespace(code)
                self._calculate_score()
                
                return {
                    "success": True,
                    "style_score": self.score,
                    "violations": self.violations,
                    "flake8_results": flake8_result,
                    "summary": self._generate_summary()
                }
                
            finally:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"Error in style analysis: {str(e)}")
            return {
                "success": False,
                "style_score": 0,
                "violations": [],
                "error": f"Style analysis error: {str(e)}"
            }
    
    def _run_flake8(self, file_path: str) -> List[Dict[str, Any]]:
        """Run flake8 on the code file"""
        try:
            result = subprocess.run(
                ['flake8', '--format=json', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return []
            
            violations = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    try:
                        violation_data = json.loads(line)
                        for file_violations in violation_data.values():
                            for violation in file_violations:
                                violations.append({
                                    'line': violation['line_number'],
                                    'column': violation['column_number'],
                                    'code': violation['code'],
                                    'text': violation['text'],
                                    'severity': self._get_severity(violation['code'])
                                })
                    except json.JSONDecodeError:
                        parts = line.split(':')
                        if len(parts) >= 4:
                            violations.append({
                                'line': int(parts[1]),
                                'column': int(parts[2]),
                                'code': parts[3].split()[0],
                                'text': ':'.join(parts[3:]).strip(),
                                'severity': 'warning'
                            })
            
            return violations
            
        except subprocess.TimeoutExpired:
            logger.warning("Flake8 analysis timed out")
            return [{'error': 'Flake8 analysis timed out'}]
        except FileNotFoundError:
            logger.warning("Flake8 not found, skipping flake8 analysis")
            return [{'error': 'Flake8 not installed'}]
        except Exception as e:
            logger.error(f"Error running flake8: {str(e)}")
            return [{'error': f'Flake8 error: {str(e)}'}]
    
    def _get_severity(self, code: str) -> str:
        """Determine severity based on flake8 error code"""
        if code.startswith('E'):
            return 'error'
        elif code.startswith('W'):
            return 'warning'
        elif code.startswith('F'):
            return 'error'
        else:
            return 'info'
    
    def _check_line_length(self, code: str):
        """Check for line length violations"""
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            if len(line) > 79:
                self.violations.append({
                    'line': i,
                    'column': 80,
                    'code': 'E501',
                    'text': f'Line too long ({len(line)} > 79 characters)',
                    'severity': 'warning'
                })
    
    def _check_whitespace(self, code: str):
        """Check for whitespace issues"""
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            if line.rstrip() != line:
                self.violations.append({
                    'line': i,
                    'column': len(line.rstrip()) + 1,
                    'code': 'W291',
                    'text': 'Trailing whitespace',
                    'severity': 'warning'
                })
            
            if '\t' in line and ' ' in line:
                self.violations.append({
                    'line': i,
                    'column': 1,
                    'code': 'E101',
                    'text': 'Mixed tabs and spaces',
                    'severity': 'error'
                })
    
    def _calculate_score(self):
        """Calculate style score based on violations"""
        base_score = 100.0
        
        for violation in self.violations:
            if violation.get('severity') == 'error':
                base_score -= 10
            elif violation.get('severity') == 'warning':
                base_score -= 5
            else:
                base_score -= 2
        
        self.score = max(0.0, base_score)
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary of style analysis"""
        error_count = len([v for v in self.violations if v.get('severity') == 'error'])
        warning_count = len([v for v in self.violations if v.get('severity') == 'warning'])
        info_count = len([v for v in self.violations if v.get('severity') == 'info'])
        
        return {
            'total_violations': len(self.violations),
            'errors': error_count,
            'warnings': warning_count,
            'info': info_count,
            'grade': self._get_grade()
        }
    
    def _get_grade(self) -> str:
        """Get letter grade based on score"""
        if self.score >= 90:
            return 'A'
        elif self.score >= 80:
            return 'B'
        elif self.score >= 70:
            return 'C'
        elif self.score >= 60:
            return 'D'
        else:
            return 'F'

# Flask service
app = Flask(__name__)
analyzer = StyleAnalyzer()

@app.route('/style', methods=['POST'])
def analyze_style():
    """Flask endpoint for style analysis"""
    try:
        data = request.get_json()
        
        if not data or 'code' not in data:
            return jsonify({'success': False, 'error': 'Missing code in request'}), 400
        
        code = data['code']
        user_id = data.get('user_id', 'unknown')
        submission_id = data.get('submission_id', 'unknown')
        
        logger.info(f"Processing style analysis for submission {submission_id}")
        result = analyzer.analyze(code)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in style analysis endpoint: {str(e)}")
        return jsonify({'success': False, 'error': f'Internal server error: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'service': 'style-analyzer',
        'status': 'healthy',
        'version': '1.0.0'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
