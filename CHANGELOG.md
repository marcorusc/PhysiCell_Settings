# Changelog

All notable changes to the PhysiCell Configuration Builder will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.4] - 2025-07-02

### ✨ New Features

#### Added
- **Automatic Standard User Parameters**
  - `number_of_cells` parameter is now automatically included in all configurations
  - Default value: 5 (matching PhysiCell templates)
  - Type: int, Units: none
  - Description: "initial number of cells (for each cell type)"
  - Used by PhysiCell for initial cell placement when no custom cell.csv is provided

#### Enhanced
- **PhysiCellConfig Class**
  - Added `set_number_of_cells(count: int)` convenience method
  - Added `_add_standard_user_parameters()` for automatic parameter initialization
  - Improved template compatibility with standard PhysiCell projects

### 🔧 API Improvements
- **Standard Parameter Handling**
  - All new configurations now include PhysiCell-expected user parameters
  - Better alignment with PhysiCell template structure
  - Improved MCP tool compatibility for agent-driven model building

## [0.1.3] - 2025-07-02

### 🐛 Bug Fixes

#### Fixed
- **Basic Chemotaxis Substrate Requirement** in CellTypeModule
  - PhysiCell requires a substrate element in basic chemotaxis even when disabled
  - Now automatically sets the first available substrate as default when no specific chemotaxis is configured
  - Ensures XML compatibility with PhysiCell simulator requirements
  - Prevents runtime errors from missing substrate specifications

### 🔧 API Improvements
- **Enhanced XML Generation**
  - Basic chemotaxis section always includes substrate element
  - Automatically uses first available substrate when none specified
  - Better compliance with PhysiCell XML schema requirements

## [0.1.2] - 2025-07-02

### 🐛 Bug Fixes

#### Fixed
- **Chemotaxis Substrate Bug** in CellTypeModule
  - Fixed XML generation to exclude default placeholder 'substrate' value
  - Only include chemotaxis substrate in XML if it's a real substrate name
  - Prevents PhysiCell runtime errors from invalid substrate references
  
#### Added
- **New Chemotaxis Methods** in CellTypeModule
  - Added `set_chemotaxis()` method for simple chemotaxis configuration
  - Added `set_advanced_chemotaxis()` method for complex chemotaxis setup
  - Both methods validate substrate names and prevent placeholder issues
  - Enables proper programmatic chemotaxis configuration

### 🔧 API Improvements
- **Enhanced XML Generation**
  - Improved chemotaxis XML generation logic
  - Better handling of default vs. real substrate names
  - More robust substrate validation in advanced chemotaxis

## [0.1.1] - 2025-07-02

### 🔧 API Improvements

#### Added
- **Migration Bias Support** in CellTypeModule
  - Added `migration_bias` parameter to `set_motility()` method
  - Parameter accepts values between -1.0 and 1.0 (validated)
  - Enables proper chemotaxis configuration for realistic cell behavior
  
- **Enhanced Validation**
  - Added `_validate_number_in_range()` method to BaseModule
  - Provides range validation for parameters like migration_bias
  
#### Enhanced
- **Cell Motility Configuration** now supports all key PhysiCell motility parameters
- **MCP Tool Compatibility** - Improved support for Model Context Protocol tools

## [1.0.0] - 2025-06-26

### 🎉 Initial Release

#### Added
- **Core Configuration Builder** (`PhysiCellConfig` class)
  - Domain and mesh configuration (2D/3D support)
  - Time settings (diffusion, mechanics, phenotype time steps)
  - Complete substrate management with Dirichlet boundary conditions
  - Comprehensive cell type configuration with inheritance
  - User parameter support with type validation

- **Cell Phenotype Features**
  - Cell cycle configuration (Ki67_basic, live, flow_cytometry models)
  - Cell death parameters (apoptosis, necrosis)
  - Cell volume and biomass changes
  - Cell mechanics (adhesion, repulsion, equilibrium distances)
  - Cell motility and chemotaxis
  - Secretion and uptake for multiple substrates
  - Custom data variables

- **Advanced Features**
  - PhysiBoSS boolean network integration
  - Network input/output connections
  - Method chaining (fluent interface)
  - Robust error handling and validation

- **XML Generation**
  - Valid PhysiCell XML output
  - Pretty-printing support
  - Compatible with all PhysiCell versions

- **Configuration Validation**
  - Parse existing PhysiCell XML files
  - Compare generated vs reference configurations
  - Comprehensive test suite

- **Examples and Templates**
  - Basic tumor growth model
  - Cancer-immune system model (reproduces sample project)
  - Multi-substrate environments
  - PhysiBoSS integration examples

#### Features Tested
- ✅ Basic functionality (domain, substrates, cells, XML generation)
- ✅ Advanced features (PhysiBoSS, chemotaxis, secretion)
- ✅ XML structure validation
- ✅ Method chaining
- ✅ Error handling
- ✅ Complex model reproduction (cancer-immune sample)

#### Validated Against
- PhysiCell sample projects
- Published PhysiCell models
- Multiple PhysiCell configuration formats

### 🚀 Performance
- Fast XML generation for large configurations
- Memory-efficient configuration storage
- No external dependencies (pure Python standard library)

### 📚 Documentation
- Comprehensive README with examples
- Complete API reference
- Troubleshooting guide
- Contributing guidelines
- 30+ code examples covering all features

### 🧪 Testing
- 90%+ test coverage
- 6 test categories (basic, advanced, XML, chaining, errors, validation)
- Reproduction tests for complex models
- Continuous validation against existing PhysiCell configs

---

## Planned for Future Releases

### [1.1.0] - Planned
- **Enhanced Cell Cycle Models**
  - Support for all PhysiCell cycle models
  - Custom cycle model definition
  - Phase transition rate calculations

- **ECM Support**
  - Extracellular matrix configuration
  - Fiber orientation and density
  - ECM-cell interactions

- **Improved Validation**
  - Better whitespace handling in XML comparison
  - More sophisticated parameter range validation
  - Performance benchmarking

### [1.2.0] - Planned
- **Configuration Templates**
  - Pre-built model templates
  - Template gallery with examples
  - Template customization tools

- **Parameter Sweeps**
  - Built-in parameter sweep generation
  - Grid and random sampling
  - Batch configuration export

### [2.0.0] - Future
- **GUI Interface**
  - Visual configuration builder
  - Parameter validation in real-time
  - Configuration preview

- **Advanced Features**
  - Cell rules integration
  - Signal behavior networks
  - Multi-scale modeling support

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
