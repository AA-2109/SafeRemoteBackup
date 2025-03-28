import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from tests.test_data_generator import TestDataGenerator

class TestDataManager:
    def __init__(self, export_dir="test_data_exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(exist_ok=True)
        self.generator = TestDataGenerator()
    
    def export_test_data(self, count=100, name=None):
        """Export test data to a JSON file."""
        if name is None:
            name = f"test_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        export_path = self.export_dir / f"{name}.json"
        files = self.generator.generate_file_set(count=count)
        
        export_data = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'file_count': len(files),
                'name': name
            },
            'files': []
        }
        
        for file_data in files:
            file_info = {
                'path': str(file_data['path']),
                'metadata': file_data['metadata'],
                'content': self._read_file_content(file_data['path'])
            }
            export_data['files'].append(file_info)
        
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return export_path
    
    def import_test_data(self, import_path):
        """Import test data from a JSON file."""
        import_path = Path(import_path)
        if not import_path.exists():
            raise FileNotFoundError(f"Import file not found: {import_path}")
        
        with open(import_path, 'r') as f:
            import_data = json.load(f)
        
        imported_files = []
        for file_info in import_data['files']:
            file_path = Path(file_info['path'])
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w') as f:
                f.write(file_info['content'])
            
            imported_files.append({
                'path': file_path,
                'metadata': file_info['metadata']
            })
        
        return imported_files
    
    def _read_file_content(self, file_path):
        """Read file content as string."""
        with open(file_path, 'r') as f:
            return f.read()
    
    def cleanup_export(self, name):
        """Clean up an exported test data file."""
        export_path = self.export_dir / f"{name}.json"
        if export_path.exists():
            export_path.unlink()
    
    def list_exports(self):
        """List all exported test data files."""
        return [f.stem for f in self.export_dir.glob("*.json")]
    
    def get_export_info(self, name):
        """Get information about a specific export."""
        export_path = self.export_dir / f"{name}.json"
        if not export_path.exists():
            raise FileNotFoundError(f"Export not found: {name}")
        
        with open(export_path, 'r') as f:
            data = json.load(f)
        
        return data['metadata']
    
    def compare_exports(self, name1, name2):
        """Compare two test data exports."""
        info1 = self.get_export_info(name1)
        info2 = self.get_export_info(name2)
        
        comparison = {
            'file_count_diff': info2['file_count'] - info1['file_count'],
            'time_diff': datetime.fromisoformat(info2['created_at']) - datetime.fromisoformat(info1['created_at']),
            'export1': info1,
            'export2': info2
        }
        
        return comparison
    
    def merge_exports(self, names, output_name=None):
        """Merge multiple test data exports."""
        if output_name is None:
            output_name = f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        merged_data = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'source_exports': names,
                'name': output_name
            },
            'files': []
        }
        
        for name in names:
            export_path = self.export_dir / f"{name}.json"
            with open(export_path, 'r') as f:
                data = json.load(f)
                merged_data['files'].extend(data['files'])
        
        merged_data['metadata']['file_count'] = len(merged_data['files'])
        
        output_path = self.export_dir / f"{output_name}.json"
        with open(output_path, 'w') as f:
            json.dump(merged_data, f, indent=2)
        
        return output_path
    
    def cleanup_all(self):
        """Clean up all exported test data files."""
        for file in self.export_dir.glob("*.json"):
            file.unlink()
        self.export_dir.rmdir()
        self.export_dir.mkdir(exist_ok=True)

def test_data_manager():
    """Test the TestDataManager functionality."""
    manager = TestDataManager()
    
    try:
        # Export test data
        export_path = manager.export_test_data(count=50, name="test_export")
        assert export_path.exists()
        
        # Import test data
        imported_files = manager.import_test_data(export_path)
        assert len(imported_files) == 50
        
        # List exports
        exports = manager.list_exports()
        assert "test_export" in exports
        
        # Get export info
        info = manager.get_export_info("test_export")
        assert info['file_count'] == 50
        
        # Create another export
        export_path2 = manager.export_test_data(count=30, name="test_export2")
        
        # Compare exports
        comparison = manager.compare_exports("test_export", "test_export2")
        assert comparison['file_count_diff'] == -20
        
        # Merge exports
        merged_path = manager.merge_exports(["test_export", "test_export2"], "merged_export")
        assert merged_path.exists()
        
        merged_info = manager.get_export_info("merged_export")
        assert merged_info['file_count'] == 80
        
    finally:
        # Clean up
        manager.cleanup_all()
        assert not manager.export_dir.exists()

if __name__ == "__main__":
    test_data_manager() 