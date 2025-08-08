# Bidirectional XML Support for PhysiCell Configurations

## Overview

This update adds comprehensive bidirectional XML support to the physicell-settings package, enabling users to load existing PhysiCell XML configuration files, modify them programmatically, and save them back to XML format with perfect data preservation.

## New Features

### 🔄 Complete XML Loading System
- **Load existing PhysiCell configurations** from XML files
- **Modify loaded configurations** using the full physicell-settings API
- **Save modified configurations** back to XML format
- **Perfect data preservation** through round-trip loading and saving

### 🛡️ Robust XML Validation
- **Content-based validation** ensures files are valid PhysiCell configurations
- **Clear error messages** for invalid files (e.g., wrong root element, missing required sections)
- **Automatic validation** during loading prevents cryptic parsing errors
- **Standalone validation** method for checking files before loading

### 🧬 Complete PhysiBOSS/Intracellular Support
- **Full intracellular model parsing** including MaBoSS boolean networks
- **Input/output mapping** between PhysiCell and intracellular variables
- **Settings preservation** (time steps, mutations, inheritance, etc.)
- **Automatic PhysiBOSS detection** when intracellular models are present

### 📋 Enhanced Cell Rules Integration
- **XML ruleset loading** preserves existing rule configurations
- **Context-aware CSV generation** automatically syncs with loaded cell types and substrates
- **Complete workflow support** for the cell rules system

## Usage Examples

### Basic XML Loading and Modification
```python
from physicell_config import PhysiCellConfig

# Load existing configuration
config = PhysiCellConfig()
config.load_xml("existing_simulation.xml")

# Modify as needed
config.domain.set_bounds(-600, 600, -400, 400)
config.substrates.add_substrate("my_drug", 1.0)

# Save modified version
config.save_xml("modified_simulation.xml")
```

### Cell Rules Workflow
```python
# Load existing XML file
config = PhysiCellConfig()
config.load_xml("existing_simulation.xml")

# Rules context automatically syncs with loaded cell types & substrates
rules = config.cell_rules_csv

# Add new rules
rules.add_rule("tumor_cell", "oxygen", "decreases", "necrosis", 0, 3.75, 8, 0)

# Generate CSV and enable in XML
csv_file = rules.generate_csv("./config/my_rules.csv")
config.cell_rules.add_ruleset("my_rules", folder="./config", 
                             filename="my_rules.csv", enabled=True)

# Save updated configuration
config.save_xml("updated_simulation.xml")
```

### XML Validation
```python
# Method 1: Validate before loading
config = PhysiCellConfig()
is_valid, error_msg = config.validate_xml_file("unknown_file.xml")

if is_valid:
    config.load_xml("unknown_file.xml")
else:
    print(f"Invalid PhysiCell file: {error_msg}")

# Method 2: Automatic validation during load
try:
    config = PhysiCellConfig()
    config.load_xml("suspicious_file.xml")  # Automatically validates
except XMLValidationError as e:
    print(f"File validation failed: {e}")
```

## Technical Implementation

### Core Components
- **XMLLoader**: Core XML parsing engine with validation
- **BaseModule**: Abstract base class with `load_from_xml()` method
- **Module Implementations**: All 6 core modules support bidirectional XML

### Supported Modules
1. **Domain Module** - Simulation bounds, mesh, dimensions
2. **Substrates Module** - Microenvironment variables and properties
3. **Options Module** - Simulation settings and parameters
4. **Cell Types Module** - Cell phenotype definitions (most complex)
5. **Initial Conditions Module** - Cell placement configurations
6. **Save Options Module** - Output formats and intervals

### XML Validation Checks
- Root element must be `<PhysiCell_settings>`
- Required `version` attribute in root element
- Presence of essential sections: `domain`, `microenvironment_setup`, `cell_definitions`
- Valid domain structure with required elements
- Valid microenvironment and cell definition structures

### PhysiBOSS/Intracellular Support
- Complete parsing of `<intracellular>` sections within cell phenotypes
- Support for MaBoSS boolean network configurations
- Input/output mapping between PhysiCell and intracellular variables
- Settings parsing (time steps, mutations, initial values, inheritance)
- Automatic PhysiBOSS enabled flag detection

## Exception Handling

The system includes comprehensive exception handling with custom exception types:

- `XMLLoadingError`: Base exception for XML loading errors
- `XMLParseError`: XML parsing or structure errors
- `XMLValidationError`: XML validation errors (e.g., wrong file type)

## Testing and Validation

The implementation has been thoroughly tested with:
- **Basic PhysiCell configurations** (single cell type, basic substrates)
- **Complex configurations** (FOXP3 example with 6 cell types, intracellular models)
- **Round-trip testing** to ensure perfect data preservation
- **Invalid file handling** to verify robust error reporting
- **Edge cases** and malformed XML files

## Backward Compatibility

All existing functionality remains unchanged. The new XML loading features are additive and do not affect existing workflows for creating configurations from scratch.

## Performance Considerations

- XML validation occurs before expensive parsing operations
- Fast failure for invalid files prevents wasted processing time
- Efficient parsing using Python's built-in ElementTree library
- Memory-efficient handling of large configuration files

## Future Enhancements

The bidirectional XML support provides a foundation for future enhancements such as:
- Configuration file versioning and migration
- Partial configuration loading/merging
- Configuration comparison and diff tools
- Automated configuration validation in CI/CD pipelines
