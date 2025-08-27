#!/usr/bin/env python3
"""
Simple test script to verify MCP integration is working.
This script creates test scenarios that MCP tools should be able to help with.
"""

import os
import json
from datetime import datetime

def test_file_operations():
    """Test basic file operations that MCP filesystem tools should detect."""
    print("🔍 Testing file operations...")
    
    # Create a test directory
    test_dir = "mcp_test_data"
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
        print(f"✅ Created directory: {test_dir}")
    
    # Create test files
    test_files = [
        "config.json",
        "data.txt", 
        "README.md"
    ]
    
    for filename in test_files:
        filepath = os.path.join(test_dir, filename)
        with open(filepath, 'w') as f:
            if filename.endswith('.json'):
                json.dump({"test": True, "timestamp": str(datetime.now())}, f, indent=2)
            elif filename.endswith('.md'):
                f.write("# Test MCP Integration\n\nThis is a test file for MCP tools.\n")
            else:
                f.write(f"Test content for {filename}\nCreated at: {datetime.now()}\n")
        print(f"✅ Created file: {filepath}")
    
    return test_dir

def test_data_analysis():
    """Create sample data that MCP tools might analyze."""
    print("📊 Creating sample data for analysis...")
    
    sample_data = {
        "users": [
            {"id": 1, "name": "Alice", "age": 30, "role": "developer"},
            {"id": 2, "name": "Bob", "age": 25, "role": "designer"},
            {"id": 3, "name": "Charlie", "age": 35, "role": "manager"}
        ],
        "metrics": {
            "total_users": 3,
            "avg_age": 30,
            "roles": ["developer", "designer", "manager"]
        }
    }
    
    with open("mcp_test_data/sample_data.json", 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    print("✅ Created sample data file")
    return sample_data

def main():
    """Main test function."""
    print("🚀 Starting MCP Integration Test")
    print("=" * 50)
    
    # Test 1: File operations
    test_dir = test_file_operations()
    
    # Test 2: Data creation
    data = test_data_analysis()
    
    print("\n🎯 MCP Test Summary:")
    print(f"📁 Test directory created: {test_dir}")
    print(f"📝 Files created: {len(os.listdir(test_dir))}")
    print(f"💾 Sample data records: {len(data['users'])}")
    
    print("\n✨ Test completed!")
    print("Now try asking GitHub Copilot to:")
    print("  • Analyze the files in mcp_test_data/")
    print("  • Summarize the sample_data.json")
    print("  • List all .json files in this workspace")
    print("  • Count lines in the test files")

if __name__ == "__main__":
    main()
