#!/usr/bin/env python3
"""
Comprehensive Python Dependency Analysis Tool for uqlab-streamlit project.

This script scans all Python files in a directory, parses imports using AST,
maps import relationships, builds a dependency graph, and exports data to JSON.

Usage:
    python analyze_dependencies.py [--directory DIR] [--output FILE]
"""

import ast
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import argparse


@dataclass
class ImportInfo:
    """Information about a single import statement."""
    module: str
    type: str  # 'local', 'external', 'stdlib'
    line: int
    import_type: str  # 'import', 'from_import'
    alias: Optional[str] = None
    imported_names: Optional[List[str]] = None
    is_relative: bool = False
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'module': self.module,
            'type': self.type,
            'line': self.line,
            'import_type': self.import_type,
            'alias': self.alias,
            'imported_names': self.imported_names or [],
            'is_relative': self.is_relative
        }


@dataclass
class FileInfo:
    """Information about a Python file and its dependencies."""
    path: str
    relative_path: str
    imports: List[ImportInfo]
    imported_by: List[str]
    module_name: str
    category: str  # 'frontend', 'backend', 'shared', 'scripts', 'tests'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'path': self.path,
            'relative_path': self.relative_path,
            'imports': [imp.to_dict() for imp in self.imports],
            'imported_by': self.imported_by,
            'module_name': self.module_name,
            'category': self.category
        }


class DependencyAnalyzer:
    """Analyzes Python dependencies in a project."""
    
    # Standard library modules (partial list - common ones)
    STDLIB_MODULES = {
        'abc', 'argparse', 'ast', 'asyncio', 'base64', 'collections', 'copy',
        'csv', 'dataclasses', 'datetime', 'decimal', 'enum', 'functools',
        'glob', 'hashlib', 'io', 'itertools', 'json', 'logging', 'math',
        'os', 'pathlib', 'pickle', 're', 'shutil', 'socket', 'sqlite3',
        'string', 'subprocess', 'sys', 'tempfile', 'threading', 'time',
        'typing', 'unittest', 'urllib', 'uuid', 'warnings', 'weakref', 'xml'
    }
    
    def __init__(self, root_dir: str):
        """Initialize analyzer with root directory."""
        self.root_dir = Path(root_dir).resolve()
        self.files: Dict[str, FileInfo] = {}
        self.local_modules: Set[str] = set()
        self.circular_deps: List[List[str]] = []
        
    def categorize_file(self, file_path: Path) -> str:
        """Categorize file based on its location."""
        rel_path = str(file_path.relative_to(self.root_dir))
        
        if 'backend' in rel_path:
            return 'backend'
        elif 'frontend' in rel_path or 'streamlit' in rel_path:
            return 'frontend'
        elif 'test' in rel_path.lower():
            return 'tests'
        elif 'script' in rel_path.lower():
            return 'scripts'
        elif 'notebook' in rel_path.lower():
            return 'notebooks'
        else:
            return 'shared'
    
    def get_module_name(self, file_path: Path) -> str:
        """Convert file path to Python module name."""
        rel_path = file_path.relative_to(self.root_dir)
        parts = list(rel_path.parts)
        
        # Remove .py extension
        if parts[-1].endswith('.py'):
            parts[-1] = parts[-1][:-3]
        
        # Remove __init__
        if parts[-1] == '__init__':
            parts = parts[:-1]
        
        return '.'.join(parts) if parts else ''
    
    def scan_directory(self) -> None:
        """Scan directory for all Python files."""
        print(f"Scanning directory: {self.root_dir}")
        
        for py_file in self.root_dir.rglob('*.py'):
            # Skip virtual environments and hidden directories
            if any(part.startswith('.') or part == '__pycache__' for part in py_file.parts):
                continue
            
            rel_path = str(py_file.relative_to(self.root_dir))
            module_name = self.get_module_name(py_file)
            
            if module_name:
                self.local_modules.add(module_name)
                # Also add parent packages
                parts = module_name.split('.')
                for i in range(1, len(parts)):
                    self.local_modules.add('.'.join(parts[:i]))
        
        print(f"Found {len(self.local_modules)} local modules")
    
    def parse_imports(self, file_path: Path) -> List[ImportInfo]:
        """Parse imports from a Python file using AST."""
        imports = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        import_info = self._classify_import(
                            alias.name, node.lineno, 'import', alias.asname
                        )
                        imports.append(import_info)
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    level = node.level
                    
                    # Handle relative imports
                    if level > 0:
                        module = self._resolve_relative_import(
                            file_path, module, level
                        )
                    
                    imported_names = [alias.name for alias in node.names]
                    import_info = self._classify_import(
                        module, node.lineno, 'from_import',
                        imported_names=imported_names,
                        is_relative=(level > 0)
                    )
                    imports.append(import_info)
        
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
        
        return imports
    
    def _resolve_relative_import(self, file_path: Path, module: str, level: int) -> str:
        """Resolve relative import to absolute module name."""
        # Get the package path
        rel_path = file_path.relative_to(self.root_dir)
        parts = list(rel_path.parts[:-1])  # Remove filename
        
        # Go up 'level' directories
        for _ in range(level - 1):
            if parts:
                parts.pop()
        
        # Add the module if specified
        if module:
            parts.append(module)
        
        return '.'.join(parts) if parts else module
    
    def _classify_import(self, module: str, line: int, import_type: str,
                        alias: Optional[str] = None,
                        imported_names: Optional[List[str]] = None,
                        is_relative: bool = False) -> ImportInfo:
        """Classify an import as local, external, or stdlib."""
        # Get the base module name
        base_module = module.split('.')[0] if module else ''
        
        # Determine type
        if base_module in self.STDLIB_MODULES:
            imp_type = 'stdlib'
        elif any(module.startswith(local) for local in self.local_modules):
            imp_type = 'local'
        elif module in self.local_modules:
            imp_type = 'local'
        else:
            imp_type = 'external'
        
        return ImportInfo(
            module=module,
            type=imp_type,
            line=line,
            import_type=import_type,
            alias=alias,
            imported_names=imported_names,
            is_relative=is_relative
        )
    
    def analyze(self) -> None:
        """Analyze all Python files in the directory."""
        print("Analyzing dependencies...")
        
        # First pass: scan directory
        self.scan_directory()
        
        # Second pass: parse imports
        for py_file in self.root_dir.rglob('*.py'):
            # Skip virtual environments and hidden directories
            if any(part.startswith('.') or part == '__pycache__' for part in py_file.parts):
                continue
            
            rel_path = str(py_file.relative_to(self.root_dir))
            module_name = self.get_module_name(py_file)
            
            imports = self.parse_imports(py_file)
            
            file_info = FileInfo(
                path=str(py_file),
                relative_path=rel_path,
                imports=imports,
                imported_by=[],
                module_name=module_name,
                category=self.categorize_file(py_file)
            )
            
            self.files[rel_path] = file_info
        
        # Third pass: build reverse dependencies
        self._build_reverse_dependencies()
        
        # Fourth pass: detect circular dependencies
        self._detect_circular_dependencies()
        
        print(f"Analyzed {len(self.files)} Python files")
        print(f"Found {len(self.circular_deps)} circular dependency chains")
    
    def _build_reverse_dependencies(self) -> None:
        """Build reverse dependency mapping (who imports this file)."""
        for file_path, file_info in self.files.items():
            for imp in file_info.imports:
                if imp.type == 'local':
                    # Find the file that corresponds to this import
                    target_files = self._find_files_for_module(imp.module)
                    for target_file in target_files:
                        if target_file in self.files:
                            self.files[target_file].imported_by.append(file_path)
    
    def _find_files_for_module(self, module: str) -> List[str]:
        """Find file paths that correspond to a module name."""
        matching_files = []
        
        for file_path, file_info in self.files.items():
            if file_info.module_name == module:
                matching_files.append(file_path)
            # Also check if module is a parent package
            elif file_info.module_name.startswith(module + '.'):
                matching_files.append(file_path)
        
        return matching_files
    
    def _detect_circular_dependencies(self) -> None:
        """Detect circular dependencies using DFS."""
        visited = set()
        rec_stack = set()
        
        def dfs(file_path: str, path: List[str]) -> None:
            visited.add(file_path)
            rec_stack.add(file_path)
            path.append(file_path)
            
            if file_path in self.files:
                for imp in self.files[file_path].imports:
                    if imp.type == 'local':
                        target_files = self._find_files_for_module(imp.module)
                        for target_file in target_files:
                            if target_file not in visited:
                                dfs(target_file, path.copy())
                            elif target_file in rec_stack:
                                # Found a cycle
                                cycle_start = path.index(target_file)
                                cycle = path[cycle_start:] + [target_file]
                                if cycle not in self.circular_deps:
                                    self.circular_deps.append(cycle)
            
            rec_stack.remove(file_path)
        
        for file_path in self.files:
            if file_path not in visited:
                dfs(file_path, [])
    
    def build_graph_data(self) -> Dict:
        """Build graph data structure for visualization."""
        nodes = []
        edges = []
        node_ids = {}
        
        # Create nodes
        for idx, (file_path, file_info) in enumerate(self.files.items()):
            node_id = f"node_{idx}"
            node_ids[file_path] = node_id
            
            # Count imports by type
            local_imports = sum(1 for imp in file_info.imports if imp.type == 'local')
            external_imports = sum(1 for imp in file_info.imports if imp.type == 'external')
            
            nodes.append({
                'id': node_id,
                'label': file_path,
                'module': file_info.module_name,
                'category': file_info.category,
                'local_imports': local_imports,
                'external_imports': external_imports,
                'imported_by_count': len(file_info.imported_by)
            })
        
        # Create edges
        for file_path, file_info in self.files.items():
            source_id = node_ids[file_path]
            
            for imp in file_info.imports:
                if imp.type == 'local':
                    target_files = self._find_files_for_module(imp.module)
                    for target_file in target_files:
                        if target_file in node_ids:
                            target_id = node_ids[target_file]
                            
                            # Determine if this is a cross-boundary import
                            source_cat = file_info.category
                            target_cat = self.files[target_file].category
                            is_cross_boundary = (
                                (source_cat == 'frontend' and target_cat == 'backend') or
                                (source_cat == 'backend' and target_cat == 'frontend')
                            )
                            
                            edges.append({
                                'source': source_id,
                                'target': target_id,
                                'module': imp.module,
                                'line': imp.line,
                                'is_cross_boundary': is_cross_boundary,
                                'is_relative': imp.is_relative
                            })
        
        return {'nodes': nodes, 'edges': edges}
    
    def export_to_json(self, output_file: str) -> None:
        """Export analysis results to JSON file."""
        print(f"Exporting to {output_file}...")
        
        data = {
            'metadata': {
                'root_directory': str(self.root_dir),
                'total_files': len(self.files),
                'total_local_modules': len(self.local_modules),
                'circular_dependencies_count': len(self.circular_deps)
            },
            'files': {
                path: info.to_dict() 
                for path, info in self.files.items()
            },
            'graph': self.build_graph_data(),
            'circular_dependencies': self.circular_deps,
            'statistics': self._compute_statistics()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"Export complete: {output_file}")
    
    def _compute_statistics(self) -> Dict:
        """Compute various statistics about the codebase."""
        stats = {
            'by_category': defaultdict(int),
            'by_import_type': defaultdict(int),
            'most_imported': [],
            'most_dependencies': [],
            'cross_boundary_imports': 0
        }
        
        # Count by category
        for file_info in self.files.values():
            stats['by_category'][file_info.category] += 1
            
            # Count import types
            for imp in file_info.imports:
                stats['by_import_type'][imp.type] += 1
        
        # Find most imported files
        imported_counts = [
            (path, len(info.imported_by))
            for path, info in self.files.items()
        ]
        stats['most_imported'] = sorted(
            imported_counts, key=lambda x: x[1], reverse=True
        )[:10]
        
        # Find files with most dependencies
        dependency_counts = [
            (path, len([imp for imp in info.imports if imp.type == 'local']))
            for path, info in self.files.items()
        ]
        stats['most_dependencies'] = sorted(
            dependency_counts, key=lambda x: x[1], reverse=True
        )[:10]
        
        # Count cross-boundary imports
        for file_info in self.files.values():
            for imp in file_info.imports:
                if imp.type == 'local':
                    target_files = self._find_files_for_module(imp.module)
                    for target_file in target_files:
                        if target_file in self.files:
                            source_cat = file_info.category
                            target_cat = self.files[target_file].category
                            if ((source_cat == 'frontend' and target_cat == 'backend') or
                                (source_cat == 'backend' and target_cat == 'frontend')):
                                stats['cross_boundary_imports'] += 1
        
        # Convert defaultdicts to regular dicts
        stats['by_category'] = dict(stats['by_category'])
        stats['by_import_type'] = dict(stats['by_import_type'])
        
        return stats
    
    def print_summary(self) -> None:
        """Print a summary of the analysis."""
        print("\n" + "="*60)
        print("DEPENDENCY ANALYSIS SUMMARY")
        print("="*60)
        
        stats = self._compute_statistics()
        
        print(f"\nTotal Python files: {len(self.files)}")
        print(f"Total local modules: {len(self.local_modules)}")
        
        print("\nFiles by category:")
        for category, count in sorted(stats['by_category'].items()):
            print(f"  {category}: {count}")
        
        print("\nImports by type:")
        for imp_type, count in sorted(stats['by_import_type'].items()):
            print(f"  {imp_type}: {count}")
        
        print(f"\nCross-boundary imports (frontend ↔ backend): {stats['cross_boundary_imports']}")
        print(f"Circular dependency chains: {len(self.circular_deps)}")
        
        print("\nMost imported files:")
        for path, count in stats['most_imported'][:5]:
            print(f"  {path}: {count} imports")
        
        print("\nFiles with most dependencies:")
        for path, count in stats['most_dependencies'][:5]:
            print(f"  {path}: {count} local imports")
        
        if self.circular_deps:
            print("\nCircular dependencies detected:")
            for idx, cycle in enumerate(self.circular_deps[:3], 1):
                print(f"  {idx}. {' → '.join(cycle)}")
            if len(self.circular_deps) > 3:
                print(f"  ... and {len(self.circular_deps) - 3} more")
        
        print("\n" + "="*60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Analyze Python dependencies in a project'
    )
    parser.add_argument(
        '--directory', '-d',
        default='.',
        help='Root directory to analyze (default: current directory)'
    )
    parser.add_argument(
        '--output', '-o',
        default='dependencies.json',
        help='Output JSON file (default: dependencies.json)'
    )
    
    args = parser.parse_args()
    
    # Create analyzer
    analyzer = DependencyAnalyzer(args.directory)
    
    # Run analysis
    analyzer.analyze()
    
    # Print summary
    analyzer.print_summary()
    
    # Export results
    analyzer.export_to_json(args.output)
    
    print(f"\n✓ Analysis complete! Results saved to {args.output}")
    print(f"  Run the visualizer: streamlit run dependency_visualizer.py")


if __name__ == '__main__':
    main()

# Made with Bob
