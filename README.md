# PhysiCell Configuration Builder

A powerful, modular Python package for generating PhysiCell XML configuration files with comprehensive parameter coverage, intuitive API design, and maintainable architecture.

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

## 🚀 Overview

The PhysiCell Configuration Builder provides a powerful yet simple API for creating complex PhysiCell simulations. Built with a modern modular architecture, it handles all aspects of PhysiCell configuration with a focus on ease of use, maintainability, and compatibility with existing PhysiCell standards.

### ✨ Key Features

- **🏗️ Modular Architecture** - Well-organized, maintainable codebase with focused modules
- **🎯 Simple & Intuitive** - Clean API with sensible defaults and method chaining
- **🔧 Comprehensive Coverage** - All PhysiCell features: domain, substrates, cells, rules, PhysiBoSS
- **✅ Built-in Validation** - Configuration validation with detailed error reporting
- **🔄 Full Compatibility** - Generates standard PhysiCell XML, reproduces existing configs
- **🧬 Advanced Features** - Cell rules, PhysiBoSS integration, initial conditions, enhanced visualization
- **📊 Cell Rules CSV** - Context-aware generation of rules.csv files with signal/behavior validation
- **📚 Well Documented** - Extensive examples and clear modular documentation

### 🎯 Perfect For

- **Researchers** building new PhysiCell models with complex requirements
- **Developers** programmatically generating parameter sweeps and batch simulations
- **Teams** collaborating on large simulation projects with maintainable code
- **Educators** teaching computational biology with clear, reproducible examples

## 🏗️ Modular Architecture

The configuration builder uses a modular composition pattern that provides:

- **Clean Separation**: Each module handles one aspect of configuration
- **Easy Maintenance**: Small, focused files instead of monolithic code
- **Team Development**: Multiple developers can work on different modules
- **Extensibility**: Easy to add new modules without affecting existing code

### Module Structure

```
├── config_builder_modular.py       # Main configuration class
└── modules/
    ├── domain.py                # Simulation domain and mesh
    ├── substrates.py            # Microenvironment substrates  
    ├── cell_types.py            # Cell definitions and phenotypes
    ├── cell_rules.py            # Cell behavior rules
    ├── cell_rules_csv.py        # rules.csv generation with context awareness
    ├── physiboss.py             # PhysiBoSS boolean networks
    ├── initial_conditions.py    # Initial cell placement
    ├── save_options.py          # Output and visualization
    └── options.py               # Simulation parameters
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/marcorusc/PhysiCell_Settings.git
cd PhysiCell_Settings

# Install dependencies (if needed)
pip install -r requirements.txt
```

### Basic Usage

```python
from config_builder_modular import PhysiCellConfig

# Create configuration
config = PhysiCellConfig()

# Quick setup with convenience method
config.setup_basic_simulation(
    x_range=(-400, 400),
    y_range=(-400, 400),
    mesh_spacing=20.0,
    max_time=1440.0  # 24 hours
)

# Add substrates and cell types
config.add_simple_substrate("oxygen", diffusion_coeff=100000.0)
config.add_simple_cell_type("cancer_cell", motile=True)

# Save configuration
config.save_xml("my_simulation.xml")
```

### Advanced Modular Usage

```python
# Direct module access for advanced features
config.domain.set_bounds(-500, 500, -500, 500)
config.substrates.add_substrate("glucose", diffusion_coefficient=50000.0)

config.cell_types.add_cell_type("immune_cell")
config.cell_types.set_motility("immune_cell", speed=2.0, enabled=True)
config.cell_types.add_secretion("immune_cell", "oxygen", uptake_rate=5.0)

config.cell_rules.add_rule("oxygen", "proliferation", "cancer_cell")
config.physiboss.enable_physiboss("boolean_model.bnd")
config.initial_conditions.add_cell_cluster("cancer_cell", x=0, y=0, radius=100)
```

## 📖 Examples

### Complete Tumor-Immune Simulation

```python
from config_builder_modular import PhysiCellConfig

# Create configuration
config = PhysiCellConfig()

# Setup domain  
config.domain.set_bounds(-600, 600, -600, 600)
config.domain.set_mesh(20.0, 20.0)

# Add substrates
config.substrates.add_substrate("oxygen", 
    diffusion_coefficient=100000.0,
    decay_rate=0.1, 
    initial_condition=38.0)

config.substrates.add_substrate("glucose",
    diffusion_coefficient=50000.0,
    decay_rate=0.01,
    initial_condition=10.0)

# Add cell types
config.cell_types.add_cell_type("cancer_cell")
config.cell_types.set_motility("cancer_cell", speed=0.5, enabled=True)
config.cell_types.add_secretion("cancer_cell", "oxygen", uptake_rate=10.0)

config.cell_types.add_cell_type("immune_cell")  
config.cell_types.set_motility("immune_cell", speed=2.0, enabled=True)

# Add initial conditions
config.initial_conditions.add_cell_cluster("cancer_cell", x=0, y=0, radius=150, num_cells=100)
config.initial_conditions.add_cell_cluster("immune_cell", x=300, y=300, radius=50, num_cells=20)

# Add cell rules to XML
config.cell_rules.add_rule(
    signal="oxygen",
    behavior="proliferation",
    cell_type="cancer_cell",
    min_signal=0.0,
    max_signal=38.0,
    min_behavior=0.0,
    max_behavior=0.05
)

# Configure visualization
config.save_options.set_svg_options(
    interval=120.0,
    plot_substrate=True,
    substrate_to_plot="oxygen",
    cell_color_by="cell_type"
)

# Save configuration
config.save_xml("tumor_immune_simulation.xml")
```

### Loading Cell Rules from CSV

```python
# Create rules CSV file
import csv

rules = [
    {"signal": "oxygen", "behavior": "proliferation", "cell_type": "cancer_cell", 
     "min_signal": 0.0, "max_signal": 38.0, "min_behavior": 0.0, "max_behavior": 0.05},
    {"signal": "pressure", "behavior": "apoptosis", "cell_type": "cancer_cell",
     "min_signal": 0.0, "max_signal": 1.0, "min_behavior": 0.0, "max_behavior": 0.1}
]

with open("cell_rules.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rules[0].keys())
    writer.writeheader()
    writer.writerows(rules)

# Load rules in configuration
config.cell_rules.load_rules_from_csv("cell_rules.csv")
```

## 🧪 Testing and Validation

### Run Demo
```bash
python demo_modular.py
```

### Configuration Validation
```python
# Built-in validation
issues = config.validate()
if issues:
    for issue in issues:
        print(f"⚠️  {issue}")
else:
    print("✅ Configuration is valid!")

# Get configuration summary
summary = config.get_summary()
print(f"Substrates: {summary['substrates']}")
print(f"Cell types: {summary['cell_types']}")
```

## 📁 Project Structure

```
physicell_config/
├── README.md                          # This file
├── config_builder.py                  # Main configuration class
├── demo_modular.py                    # Demonstration script
├── modules/                           # Modular components
│   ├── __init__.py
│   ├── base.py                        # Common utilities
│   ├── domain.py                      # Domain configuration
│   ├── substrates.py                  # Substrate management
│   ├── cell_types.py                  # Cell type definitions
│   ├── cell_rules.py                  # Cell behavior rules
│   ├── physiboss.py                   # PhysiBoSS integration
│   ├── initial_conditions.py          # Initial cell placement
│   ├── save_options.py                # Output configuration
│   └── options.py                     # Simulation options
├── examples/                          # Example configurations
│   ├── PhysiCell_settings.xml         # Reference PhysiCell config
│   ├── basic_tumor.py                 # Basic tumor example
│   ├── cancer_immune.py               # Cancer-immune interaction
│   └── physiboss_integration.py       # PhysiBoSS example
├── MODULAR_ARCHITECTURE.md            # Detailed architecture docs
├── MODULARIZATION_COMPLETE.md         # Project completion summary
└── setup.py                          # Package setup
```

## 🔧 Advanced Features

### PhysiBoSS Integration
```python
# Enable PhysiBoSS boolean networks
config.physiboss.enable_physiboss("boolean_model.bnd")
config.physiboss.add_mutation("mutant_cell", "p53", False)
config.physiboss.add_initial_value("EGFR", True)
```

### Complex Initial Conditions
```python
# Multiple initial condition types
config.initial_conditions.add_cell_cluster("cancer", 0, 0, radius=100)
config.initial_conditions.add_single_cell("stem_cell", 200, 200)
config.initial_conditions.add_rectangular_region("stromal", -300, 300, -300, 300, density=0.3)
```

### Enhanced Visualization
```python
# Advanced SVG options
config.save_options.set_svg_options(
    plot_substrate=True,
    substrate_to_plot="oxygen", 
    cell_color_by="cell_type",
    interval=60.0
)
```

### Cell Rules CSV Generation
```python
# Create cell rules CSV with context awareness
rules = config.cell_rules_csv

# Explore available signals and behaviors
rules.print_available_signals(filter_by_type="contact")
rules.print_available_behaviors(filter_by_type="motility")
rules.print_context()  # Shows current cell types and substrates

# Add rules following PhysiCell CSV format
rules.add_rule("tumor", "oxygen", "decreases", "necrosis", 0, 3.75, 8, 0)
rules.add_rule("tumor", "contact with immune_cell", "increases", "apoptosis", 0.1, 0.5, 4, 0)

# Generate PhysiCell-compatible CSV file
rules.generate_csv("config/differentiation/rules.csv")
```

### PhysiBoSS Integration
```python
# Add intracellular models to cell types
config.cell_types.add_intracellular_model("T_cell", "maboss")
config.cell_types.set_intracellular_settings("T_cell", 
    bnd_filename="tcell.bnd",
    cfg_filename="tcell.cfg")
config.cell_types.add_intracellular_mutation("T_cell", "FOXP3", 0)
```

## 🤝 Contributing

We welcome contributions! The modular architecture makes it easy to:

- Add new modules for additional PhysiCell features
- Enhance existing modules with new functionality  
- Improve documentation and examples
- Add comprehensive test suites

See `CONTRIBUTING.md` for guidelines.

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the `LICENSE` file for details.

**What this means for you:**
- ✅ **Free to use** for research, education, and commercial purposes
- ✅ **Modify and distribute** - but derivative works must also be GPL v3
- ✅ **Strong attribution** - your contributions are protected and credited
- ✅ **Patent protection** - includes explicit patent grant
- 🔒 **Copyleft protection** - prevents proprietary forks that don't give back to the community

**For scientific use:** Please cite this work in publications. For commercial use: derivative works must remain open source.

## 🙏 Acknowledgments

- PhysiCell development team for the excellent simulation platform
- Contributors to this configuration builder
- The computational biology community for feedback and suggestions

---

**Note**: This is the modular version of the PhysiCell Configuration Builder, designed for maintainability and extensibility. The architecture supports easy addition of new features and collaborative development.
