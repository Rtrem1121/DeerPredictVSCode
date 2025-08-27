#!/usr/bin/env python3
"""
Documentation Analysis Tool for Deer Prediction App
Identifies duplicate content and creates consolidation recommendations
"""

import os
import re
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

def similarity(a, b):
    """Calculate similarity between two text strings"""
    return SequenceMatcher(None, a, b).ratio()

def extract_key_content(content):
    """Extract key content indicators for better matching"""
    # Remove common markdown formatting
    content = re.sub(r'[#*`-]', '', content)
    # Remove excessive whitespace
    content = re.sub(r'\s+', ' ', content)
    return content.lower().strip()

def analyze_markdown_files():
    """Analyze all markdown files for content and similarities"""
    md_files = []
    categories = {
        'validation': [],
        'deployment': [],
        'security': [],
        'refactoring': [],
        'architecture': [],
        'other': []
    }
    
    print("Scanning markdown files...")
    
    for file_path in Path('.').glob('*.md'):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            file_info = {
                'path': str(file_path),
                'name': file_path.name,
                'size': len(content),
                'lines': len(content.splitlines()),
                'content': content,
                'key_content': extract_key_content(content)
            }
            
            md_files.append(file_info)
            
            # Categorize files
            name_lower = file_path.name.lower()
            if any(word in name_lower for word in ['validation', 'test', 'accuracy']):
                categories['validation'].append(file_info)
            elif any(word in name_lower for word in ['deploy', 'setup', 'install']):
                categories['deployment'].append(file_info)
            elif 'security' in name_lower:
                categories['security'].append(file_info)
            elif any(word in name_lower for word in ['refactor', 'plan', 'implementation']):
                categories['refactoring'].append(file_info)
            elif any(word in name_lower for word in ['architecture', 'system', 'design']):
                categories['architecture'].append(file_info)
            else:
                categories['other'].append(file_info)
                
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    # Find similar files
    similar_pairs = []
    print("Analyzing content similarity...")
    
    for i, file1 in enumerate(md_files):
        for j, file2 in enumerate(md_files[i+1:], i+1):
            sim = similarity(file1['key_content'], file2['key_content'])
            if sim > 0.3:  # 30% similarity threshold
                similar_pairs.append((file1['name'], file2['name'], sim))
    
    return md_files, similar_pairs, categories

def generate_consolidation_plan(md_files, similar_pairs, categories):
    """Generate a consolidation plan based on analysis"""
    plan = {
        'total_files': len(md_files),
        'total_lines': sum(f['lines'] for f in md_files),
        'categories': {},
        'similar_files': similar_pairs,
        'recommendations': []
    }
    
    for cat_name, files in categories.items():
        if files:
            plan['categories'][cat_name] = {
                'count': len(files),
                'total_lines': sum(f['lines'] for f in files),
                'files': [f['name'] for f in files]
            }
    
    # Generate specific recommendations
    if plan['categories'].get('validation', {}).get('count', 0) > 3:
        plan['recommendations'].append({
            'action': 'CONSOLIDATE',
            'target': 'docs/TESTING.md',
            'sources': plan['categories']['validation']['files'],
            'reason': 'Multiple validation reports can be consolidated'
        })
    
    if plan['categories'].get('deployment', {}).get('count', 0) > 2:
        plan['recommendations'].append({
            'action': 'CONSOLIDATE',
            'target': 'docs/DEPLOYMENT.md',
            'sources': plan['categories']['deployment']['files'],
            'reason': 'Multiple deployment guides should be unified'
        })
    
    # Files that look like historical archives
    archive_candidates = []
    for f in md_files:
        name = f['name'].lower()
        if any(word in name for word in ['complete', 'success', 'summary', 'old', 'legacy']):
            archive_candidates.append(f['name'])
    
    if archive_candidates:
        plan['recommendations'].append({
            'action': 'ARCHIVE',
            'target': 'docs/archives/',
            'sources': archive_candidates,
            'reason': 'Historical documentation should be archived'
        })
    
    return plan

def main():
    print("=== DEER PREDICTION APP - DOCUMENTATION ANALYSIS ===")
    print()
    
    try:
        md_files, similar_pairs, categories = analyze_markdown_files()
        plan = generate_consolidation_plan(md_files, similar_pairs, categories)
        
        # Print analysis results
        print(f"📊 ANALYSIS RESULTS")
        print(f"Total markdown files: {plan['total_files']}")
        print(f"Total lines of documentation: {plan['total_lines']:,}")
        print()
        
        print("📂 FILES BY CATEGORY:")
        for cat_name, cat_info in plan['categories'].items():
            print(f"  {cat_name.upper()}: {cat_info['count']} files, {cat_info['total_lines']} lines")
            for file_name in cat_info['files'][:5]:  # Show first 5
                print(f"    - {file_name}")
            if len(cat_info['files']) > 5:
                print(f"    ... and {len(cat_info['files']) - 5} more")
            print()
        
        print("🔄 SIMILAR FILES (>30% content similarity):")
        for f1, f2, sim in sorted(similar_pairs, key=lambda x: x[2], reverse=True)[:10]:
            print(f"  {f1} ↔ {f2}: {sim:.1%} similar")
        print()
        
        print("💡 CONSOLIDATION RECOMMENDATIONS:")
        for i, rec in enumerate(plan['recommendations'], 1):
            print(f"  {i}. {rec['action']}: {rec['reason']}")
            print(f"     Target: {rec['target']}")
            print(f"     Sources: {', '.join(rec['sources'][:3])}")
            if len(rec['sources']) > 3:
                print(f"              ... and {len(rec['sources']) - 3} more")
            print()
        
        # Save analysis results
        with open('documentation_analysis_results.txt', 'w') as f:
            f.write("DEER PREDICTION APP - DOCUMENTATION ANALYSIS\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Total files: {plan['total_files']}\n")
            f.write(f"Total lines: {plan['total_lines']:,}\n\n")
            
            f.write("CATEGORIES:\n")
            for cat_name, cat_info in plan['categories'].items():
                f.write(f"{cat_name}: {cat_info['count']} files\n")
                for file_name in cat_info['files']:
                    f.write(f"  - {file_name}\n")
                f.write("\n")
            
            f.write("SIMILAR FILES:\n")
            for f1, f2, sim in similar_pairs:
                f.write(f"{f1} <-> {f2}: {sim:.2%}\n")
        
        print("✅ Analysis complete! Results saved to 'documentation_analysis_results.txt'")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
