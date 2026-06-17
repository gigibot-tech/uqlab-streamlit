# Python Dependency Analysis & Visualization Tool

A comprehensive tool for analyzing and visualizing Python dependencies in the uqlab-streamlit project.

## 🎯 Overview

This tool provides:
- **AST-based import parsing** - Accurate analysis of all Python imports
- **Dependency mapping** - Complete graph of import relationships
- **Interactive visualization** - Streamlit app with tables, graphs, and queries
- **Architecture insights** - Frontend/backend/shared module categorization
- **Circular dependency detection** - Identifies problematic import cycles

## 📁 Files

- `analyze_dependencies.py` - AST-based dependency analyzer (CLI tool)
- `dependency_visualizer.py` - Streamlit visualization app
- `dependencies.json` - Generated dependency data (created after running analyzer)

## 🚀 Quick Start

### 1. Run the Analyzer

```bash
cd uqlab-streamlit
python3 analyze_dependencies.py --directory . --output dependencies.json
```

This will:
- Scan all `.py` files in the project
- Parse imports using Python's AST module
- Build dependency graph
- Export results to `dependencies.json`

**Output:**
```
Scanning directory: /path/to/uqlab-streamlit
Found 274 local modules
Analyzed 260 Python files
Found 0 circular dependency chains

Total Python files: 260
Files by category:
  backend: 70
  frontend: 11
  notebooks: 16
  scripts: 13
  shared: 131
  tests: 19
```

### 2. Launch the Visualizer

```bash
streamlit run dependency_visualizer.py
```

This opens an interactive web app at `http://localhost:8501`

## 📊 Features

### 1. Files Table View
- **Searchable table** of all Python files
- **Filter by category** (frontend, backend, shared, scripts, tests, notebooks)
- **Sort by** import counts, dependencies
- **Export to CSV**

Columns:
- File path
- Module name
- Category
- Local imports count
- External imports count
- Imported by count
- Import lists (preview)

### 2. Imports Table View
- **Detailed import information** for every import statement
- **Filter by**:
  - Import type (local, external, stdlib)
  - Source category
  - Search term
- **Shows**:
  - Source file and module
  - Imported module
  - Line number
  - Relative vs absolute import
  - Import statement type

### 3. Graph Visualization
- **Interactive dependency graph** using Plotly
- **Node features**:
  - Size = how many files import it (importance)
  - Color = category (frontend/backend/shared/etc.)
  - Hover = detailed information
- **Edge features**:
  - Regular edges = normal dependencies
  - Dashed red edges = cross-boundary imports (frontend ↔ backend)
- **Filters**:
  - View by category
  - Highlight cross-boundary imports

### 4. Query Tool

#### Query: "Where is X imported?"
Find all files that import a specific module.

**Example:**
```
Query: "batch_experiments"
Results:
  - backend/app/api/routes/experiments.py (line 15)
  - scripts/run_experiments.py (line 8)
```

#### Query: "What does X import?"
Show all imports from a specific file.

**Example:**
```
File: streamlit_app.py
Results:
  Local imports: 5
    - ui_components (line 13)
    - uqlab.classification.config (line 14)
  External imports: 8
    - streamlit (line 1)
    - pandas (line 2)
```

#### Query: "Show import chain"
Display import chains starting from a file.

**Example:**
```
Starting file: streamlit_app.py
Chains:
  1. streamlit_app.py → ui_components → signal_visualization → signals
  2. streamlit_app.py → ui_components → dataset → data_loader
  3. streamlit_app.py → classification.config → validation_config
```

### 5. Statistics Dashboard
- **Import type distribution** (pie chart)
- **Files by category** (bar chart)
- **Most imported files** (top 10)
- **Files with most dependencies** (top 10)
- **Cross-boundary analysis** (frontend ↔ backend)
- **Circular dependencies** (if any detected)

## 🔍 Use Cases

### Architecture Review
```bash
# Analyze the codebase
python3 analyze_dependencies.py

# Open visualizer
streamlit run dependency_visualizer.py

# Navigate to "Graph Visualization" tab
# Filter by "backend" to see backend architecture
# Filter by "frontend" to see frontend architecture
# Enable "Highlight cross-boundary imports" to find coupling issues
```

### Find Import Locations
**Question:** "Where is `batch_experiments.py` imported?"

1. Open visualizer
2. Go to "Query Tool" tab
3. Select "Where is X imported?"
4. Enter: `batch_experiments`
5. View results showing all importing files

### Analyze Module Dependencies
**Question:** "What does `streamlit_app.py` import?"

1. Open visualizer
2. Go to "Query Tool" tab
3. Select "What does X import?"
4. Choose: `streamlit_app.py`
5. View categorized imports (local/external/stdlib)

### Detect Circular Dependencies
```bash
python3 analyze_dependencies.py

# Check output for:
# "Circular dependency chains: X"

# If X > 0, view details in visualizer:
# Statistics tab → Circular Dependencies section
```

### Export Data for Analysis
```python
import json

# Load dependency data
with open('dependencies.json', 'r') as f:
    data = json.load(f)

# Access file information
files = data['files']
for file_path, info in files.items():
    print(f"{file_path}: {len(info['imports'])} imports")

# Access graph data
graph = data['graph']
nodes = graph['nodes']
edges = graph['edges']

# Access statistics
stats = data['statistics']
print(f"Cross-boundary imports: {stats['cross_boundary_imports']}")
```

## 📋 Command-Line Options

### analyze_dependencies.py

```bash
python3 analyze_dependencies.py [OPTIONS]

Options:
  --directory, -d PATH    Root directory to analyze (default: current directory)
  --output, -o FILE       Output JSON file (default: dependencies.json)
  --help                  Show help message
```

**Examples:**
```bash
# Analyze current directory
python3 analyze_dependencies.py

# Analyze specific directory
python3 analyze_dependencies.py --directory ./src

# Custom output file
python3 analyze_dependencies.py --output my_deps.json

# Analyze subdirectory with custom output
python3 analyze_dependencies.py -d ./backend -o backend_deps.json
```

## 📊 Output Format

### dependencies.json Structure

```json
{
  "metadata": {
    "root_directory": "/path/to/uqlab-streamlit",
    "total_files": 260,
    "total_local_modules": 274,
    "circular_dependencies_count": 0
  },
  "files": {
    "streamlit_app.py": {
      "path": "/full/path/streamlit_app.py",
      "relative_path": "streamlit_app.py",
      "module_name": "streamlit_app",
      "category": "frontend",
      "imports": [
        {
          "module": "ui_components",
          "type": "local",
          "line": 13,
          "import_type": "from_import",
          "alias": null,
          "imported_names": ["SignalVisualization"],
          "is_relative": false
        }
      ],
      "imported_by": ["test_app.py"]
    }
  },
  "graph": {
    "nodes": [
      {
        "id": "node_0",
        "label": "streamlit_app.py",
        "module": "streamlit_app",
        "category": "frontend",
        "local_imports": 5,
        "external_imports": 8,
        "imported_by_count": 1
      }
    ],
    "edges": [
      {
        "source": "node_0",
        "target": "node_15",
        "module": "ui_components",
        "line": 13,
        "is_cross_boundary": false,
        "is_relative": false
      }
    ]
  },
  "circular_dependencies": [],
  "statistics": {
    "by_category": {
      "frontend": 11,
      "backend": 70,
      "shared": 131
    },
    "by_import_type": {
      "local": 86,
      "external": 912,
      "stdlib": 476
    },
    "most_imported": [
      ["src/metrics/mc_dropout_uq.py", 7]
    ],
    "most_dependencies": [
      ["src/uqlab/ui_components/__init__.py", 14]
    ],
    "cross_boundary_imports": 0
  }
}
```

## 🏗️ Architecture Insights

### File Categories

The analyzer automatically categorizes files:

- **frontend**: Streamlit apps, UI components
- **backend**: FastAPI routes, services, database
- **shared**: Core libraries, utilities, models
- **scripts**: Standalone scripts, CLI tools
- **tests**: Test files
- **notebooks**: Jupyter notebooks

### Import Types

- **local**: Imports from within the project
- **external**: Third-party packages (numpy, pandas, etc.)
- **stdlib**: Python standard library (os, sys, json, etc.)

### Cross-Boundary Detection

The tool identifies imports that cross architectural boundaries:
- Frontend → Backend
- Backend → Frontend

These are highlighted in red (dashed lines) in the graph visualization.

## 🔧 Technical Details

### AST-Based Parsing

The analyzer uses Python's `ast` module for accurate import detection:
- Handles both `import` and `from ... import` statements
- Resolves relative imports (e.g., `from ..utils import helper`)
- Extracts line numbers for each import
- Captures import aliases and imported names

### Graph Construction

- Uses NetworkX for graph algorithms
- Detects circular dependencies via DFS
- Calculates node importance (imported_by count)
- Supports filtering and subgraph extraction

### Visualization

- Plotly for interactive graphs
- Pandas for data tables
- Streamlit for web interface
- Spring layout algorithm for graph positioning

## 📈 Current Project Statistics

Based on the latest analysis of uqlab-streamlit:

```
Total Python files: 260
Total local modules: 274

Files by category:
  backend: 70
  frontend: 11
  notebooks: 16
  scripts: 13
  shared: 131
  tests: 19

Imports by type:
  external: 912
  local: 86
  stdlib: 476

Cross-boundary imports: 0
Circular dependencies: 0

Most imported files:
  1. src/metrics/mc_dropout_uq.py (7 imports)
  2. src/triage/dualxda_axioms.py (7 imports)
  3. src/data/cifar10n_loader.py (6 imports)
  4. src/uqlab/notebook_support/signals.py (5 imports)
  5. src/uqlab/notebook_support/constants.py (4 imports)

Files with most dependencies:
  1. src/uqlab/ui_components/__init__.py (14 local imports)
  2. src/uqlab/classification/__init__.py (9 local imports)
  3. src/metrics/acquisition_functions.py (6 local imports)
  4. src/uqlab/notebook_support/__init__.py (6 local imports)
  5. src/uqlab/classification/model_factory.py (4 local imports)
```

## 🐛 Troubleshooting

### "No dependency data found"
- Run `python3 analyze_dependencies.py` first
- Check that `dependencies.json` exists in the current directory
- Verify the file is valid JSON

### "Module not found" errors
- Ensure you're running from the project root
- Check that all required packages are installed
- For the visualizer: `pip install streamlit pandas plotly networkx`

### Graph visualization is slow
- Filter by category to reduce node count
- The tool handles up to ~500 files efficiently
- For larger projects, analyze subdirectories separately

### Import not detected
- The analyzer only detects static imports
- Dynamic imports (e.g., `__import__()`, `importlib`) are not captured
- Conditional imports are detected but not evaluated

## 🎓 Best Practices

1. **Run regularly**: Analyze dependencies after major refactoring
2. **Monitor cross-boundary imports**: Keep frontend/backend separation clean
3. **Check circular dependencies**: Fix any cycles that appear
4. **Review most-imported files**: These are critical to your architecture
5. **Export data**: Use JSON output for custom analysis and reporting

## 🔗 Integration

### CI/CD Pipeline
```yaml
# .github/workflows/dependency-check.yml
name: Dependency Analysis
on: [push, pull_request]
jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Analyze dependencies
        run: python3 analyze_dependencies.py
      - name: Check for circular dependencies
        run: |
          CYCLES=$(python3 -c "import json; print(json.load(open('dependencies.json'))['metadata']['circular_dependencies_count'])")
          if [ "$CYCLES" -gt 0 ]; then
            echo "Error: Circular dependencies detected!"
            exit 1
          fi
```

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit
python3 analyze_dependencies.py --output .deps.json
CYCLES=$(python3 -c "import json; print(json.load(open('.deps.json'))['metadata']['circular_dependencies_count'])")
if [ "$CYCLES" -gt 0 ]; then
    echo "Warning: Circular dependencies detected!"
fi
```

## 📚 Additional Resources

- [Python AST Documentation](https://docs.python.org/3/library/ast.html)
- [NetworkX Documentation](https://networkx.org/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Plotly Documentation](https://plotly.com/python/)

## 🤝 Contributing

To extend the tool:

1. **Add new queries**: Extend `DependencyVisualizer` class in `dependency_visualizer.py`
2. **Add new visualizations**: Add tabs in the Streamlit app
3. **Improve categorization**: Modify `categorize_file()` in `analyze_dependencies.py`
4. **Add export formats**: Extend `export_to_json()` to support CSV, GraphML, etc.

## 📝 License

Part of the uqlab-streamlit project.