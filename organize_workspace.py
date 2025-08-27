#!/usr/bin/env python3
"""
Workspace Organization Script
============================

Cleans up the cluttered explorer view by organizing files into logical directories.
Keeps only essential, active files in the root while archiving the rest.

Author: GitHub Copilot
Date: August 26, 2025
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import json

class WorkspaceOrganizer:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.organization_log = []
        
        # Create archive directories
        self.create_archive_structure()
    
    def create_archive_structure(self):
        """Create organized directory structure"""
        directories = [
            "archive",
            "archive/tests",
            "archive/documentation", 
            "archive/reports",
            "archive/scripts",
            "archive/debug_tools",
            "archive/deployment",
            "archive/analysis",
            "archive/old_configs"
        ]
        
        for dir_path in directories:
            (self.root_path / dir_path).mkdir(parents=True, exist_ok=True)
            
    def log_move(self, source: str, destination: str, reason: str):
        """Log file movements"""
        self.organization_log.append({
            "source": source,
            "destination": destination,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })
        print(f"📁 {source} → {destination} ({reason})")

    def organize_test_files(self):
        """Move all test files to archive/tests"""
        print("\n🧪 Organizing test files...")
        
        test_patterns = [
            "test_*.py",
            "*_test.py", 
            "comprehensive_*test*.py",
            "*validation*.py",
            "*diagnostic*.py",
            "check_*.py",
            "verify_*.py",
            "debug_*.py",
            "*_fix_*.py"
        ]
        
        for pattern in test_patterns:
            for file_path in self.root_path.glob(pattern):
                if file_path.is_file():
                    dest = self.root_path / "archive" / "tests" / file_path.name
                    shutil.move(str(file_path), str(dest))
                    self.log_move(file_path.name, f"archive/tests/{file_path.name}", "Test file")

    def organize_documentation(self):
        """Move documentation files to archive/documentation"""
        print("\n📚 Organizing documentation...")
        
        doc_files = [
            "*.md",
            "ACTIVATION_QUICK_REF.md", 
            "ADVANCED_MAP_POINTS_PLAN.md",
            "AGENTS.md",
            "ANALYTICS_README.md",
            "CLEANUP_SUMMARY_REPORT.md",
            "CLOUDFLARE_TUNNEL_OPTION.md",
            "CODEBASE_IMPROVEMENT_PLAN.md",
            "COLLABORATIVE_AI_PROMPT_TEMPLATE.md",
            "COMPREHENSIVE_TESTING_PLAN.md", 
            "CONFIGURATION_MANAGEMENT.md",
            "CORE_PLUS_SATELLITE_DEPLOYMENT.md",
            "DOCKER_DEPLOYMENT.md",
            "ENHANCED_FEATURES_EXPLAINED.md",
            "FINAL_STEP_GEE_REGISTRATION.md",
            "FRONTEND_BACKEND_VERIFIED.md",
            "GEE_AUTHORIZATION_GUIDE.md",
            "GEE_SETUP_CHECKLIST.md",
            "GOOGLE_EARTH_ENGINE_*.md",
            "MATURE_BUCK_*.md",
            "RAILWAY_DEPLOYMENT_INSTRUCTIONS.md",
            "READY_TO_PROCEED.md",
            "REFACTORING_PLAN*.md",
            "RELEASE_NOTES_*.md",
            "SATELLITE_SETUP_SIMPLIFIED.md",
            "SECURITY_CLEANUP_COMPLETION_REPORT.md",
            "SYSTEM_STATUS.md",
            "VERMONT_ENHANCEMENTS.md"
        ]
        
        # Keep only README.md in root
        for file_path in self.root_path.glob("*.md"):
            if file_path.name != "README.md" and file_path.is_file():
                dest = self.root_path / "archive" / "documentation" / file_path.name
                shutil.move(str(file_path), str(dest))
                self.log_move(file_path.name, f"archive/documentation/{file_path.name}", "Documentation")

    def organize_reports_and_analysis(self):
        """Move analysis reports and results"""
        print("\n📊 Organizing reports and analysis files...")
        
        report_patterns = [
            "*_report*.txt",
            "*_report*.json", 
            "*_results*.json",
            "code_analysis*.json",
            "codebase_analysis*",
            "comprehensive_test_report*",
            "documentation_analysis*",
            "enhanced_prediction_validation*",
            "prediction_validation*",
            "quick_validation*",
            "vulture_report*",
            "pylint_*_report.txt",
            "cleanup_report.json"
        ]
        
        for pattern in report_patterns:
            for file_path in self.root_path.glob(pattern):
                if file_path.is_file():
                    dest = self.root_path / "archive" / "reports" / file_path.name
                    shutil.move(str(file_path), str(dest))
                    self.log_move(file_path.name, f"archive/reports/{file_path.name}", "Analysis report")

    def organize_scripts_and_tools(self):
        """Move utility scripts and tools"""
        print("\n🔧 Organizing scripts and tools...")
        
        script_files = [
            "analyze_*.py",
            "camera_api_integration.py",
            "camera_demo_server.py", 
            "demo_*.py",
            "dev.py",
            "feature_generation_diagnostic.py",
            "find_encoding_errors.py",
            "fix_*.py",
            "integrate_*.py",
            "inspect_*.py",
            "marker_*_test.py",
            "metadata_fix_verification.py",
            "oregon_adaptations.py",
            "run_*.py",
            "safe_*.py",
            "setup_*.py",
            "single_debug_test.py",
            "start_*.py",
            "status_check.py",
            "system_assessment.py",
            "terrain_scores_*.py",
            "user_management.py",
            "validate_*.py",
            "comprehensive_codebase_analysis.py",
            "safe_cleanup_tool.py"
        ]
        
        for pattern in script_files:
            for file_path in self.root_path.glob(pattern):
                if file_path.is_file():
                    dest = self.root_path / "archive" / "scripts" / file_path.name
                    shutil.move(str(file_path), str(dest))
                    self.log_move(file_path.name, f"archive/scripts/{file_path.name}", "Utility script")

    def organize_deployment_files(self):
        """Move deployment-related files"""
        print("\n🚀 Organizing deployment files...")
        
        deployment_files = [
            "deploy.*",
            "railway_deployment_setup.py",
            "setup_cloudflare_access.py",
            "gee_docker_setup.py",
            "cloudflare-*",
            "setup-cloudflare-tunnel.ps1",
            "Dockerfile.new",
            "Dockerfile.railway", 
            "docker-compose.cloudflare.yml",
            "docker-compose.monitoring.yml",
            "railway.json",
            "streamlit_deployment_guide.md"
        ]
        
        for pattern in deployment_files:
            for file_path in self.root_path.glob(pattern):
                if file_path.is_file():
                    dest = self.root_path / "archive" / "deployment" / file_path.name
                    shutil.move(str(file_path), str(dest))
                    self.log_move(file_path.name, f"archive/deployment/{file_path.name}", "Deployment file")

    def organize_batch_files(self):
        """Move Windows batch files"""
        print("\n🪟 Organizing batch files...")
        
        for file_path in self.root_path.glob("*.bat"):
            if file_path.is_file():
                dest = self.root_path / "archive" / "scripts" / file_path.name
                shutil.move(str(file_path), str(dest))
                self.log_move(file_path.name, f"archive/scripts/{file_path.name}", "Batch script")

        for file_path in self.root_path.glob("*.ps1"):
            if file_path.is_file():
                dest = self.root_path / "archive" / "scripts" / file_path.name
                shutil.move(str(file_path), str(dest))
                self.log_move(file_path.name, f"archive/scripts/{file_path.name}", "PowerShell script")

    def organize_config_files(self):
        """Move old config files"""
        print("\n⚙️ Organizing configuration files...")
        
        config_files = [
            "pyproject.toml",
            "nginx.conf",
            "requirements-test.txt",
            "requirements_phase2.txt",
            "analytics_requirements.txt"
        ]
        
        for file_name in config_files:
            file_path = self.root_path / file_name
            if file_path.exists():
                dest = self.root_path / "archive" / "old_configs" / file_name
                shutil.move(str(file_path), str(dest))
                self.log_move(file_name, f"archive/old_configs/{file_name}", "Old config")

    def clean_temporary_files(self):
        """Remove temporary and generated files"""
        print("\n🧹 Cleaning temporary files...")
        
        temp_patterns = [
            "*.pyc",
            "__pycache__",
            ".coverage",
            "*.log"
        ]
        
        for pattern in temp_patterns:
            for file_path in self.root_path.glob(pattern):
                if file_path.is_file():
                    file_path.unlink()
                    self.log_move(file_path.name, "DELETED", "Temporary file")
                elif file_path.is_dir() and pattern == "__pycache__":
                    shutil.rmtree(file_path)
                    self.log_move(file_path.name, "DELETED", "Cache directory")

    def create_essential_files_list(self):
        """Create a list of files that should remain in root"""
        essential_files = [
            # Core application files
            "requirements.txt",
            "README.md",
            ".env",
            ".env.example", 
            ".gitignore",
            "Dockerfile",
            "docker-compose.yml",
            "docker-compose.prod.yml",
            "Procfile",
            "Makefile",
            
            # Core directories
            "backend/",
            "frontend/", 
            "config/",
            "credentials/",
            "data/",
            "logs/",
            "tests/",
            "docs/",
            
            # Archive directories (newly created)
            "archive/",
            "dead_code_backups/",
            
            # Active development files
            "password_protection.py",  # If still actively used
            "hunting-waypoints.gpx"    # Sample data
        ]
        
        return essential_files

    def generate_organization_report(self):
        """Generate a report of the organization process"""
        report = {
            "organization_date": datetime.now().isoformat(),
            "total_files_moved": len(self.organization_log),
            "files_by_category": {},
            "movements": self.organization_log
        }
        
        # Count by category
        for entry in self.organization_log:
            reason = entry["reason"]
            if reason not in report["files_by_category"]:
                report["files_by_category"][reason] = 0
            report["files_by_category"][reason] += 1
        
        # Save report
        with open(self.root_path / "archive" / "organization_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        return report

    def run_organization(self):
        """Run the complete organization process"""
        print("🎯 STARTING WORKSPACE ORGANIZATION")
        print("=" * 50)
        
        # Organize different file types
        self.organize_test_files()
        self.organize_documentation() 
        self.organize_reports_and_analysis()
        self.organize_scripts_and_tools()
        self.organize_deployment_files()
        self.organize_batch_files()
        self.organize_config_files()
        self.clean_temporary_files()
        
        # Generate report
        report = self.generate_organization_report()
        
        print("\n" + "=" * 50)
        print("✅ ORGANIZATION COMPLETE!")
        print("=" * 50)
        print(f"📁 Total files organized: {report['total_files_moved']}")
        print("\n📊 Files by category:")
        for category, count in report["files_by_category"].items():
            print(f"   {category}: {count} files")
        
        print(f"\n📄 Detailed report: archive/organization_report.json")
        
        # Show what remains in root
        print(f"\n🏠 Essential files remaining in root:")
        remaining_files = []
        for item in self.root_path.iterdir():
            if item.is_file() and not item.name.startswith('.'):
                remaining_files.append(item.name)
        
        for file_name in sorted(remaining_files):
            print(f"   ✅ {file_name}")
        
        return report

def main():
    """Main organization function"""
    organizer = WorkspaceOrganizer(".")
    return organizer.run_organization()

if __name__ == "__main__":
    main()
