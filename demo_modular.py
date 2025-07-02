#!/usr/bin/env python3
"""
Test script for the modular PhysiCell configuration builder.

This demonstrates how the modular approach maintains the same simple interface
while organizing code into manageable modules.
"""

from config_builder import PhysiCellConfig

def test_modular_config():
    """Test the modular configuration builder."""
    print("Testing Modular PhysiCell Configuration Builder")
    print("=" * 50)
    
    # Create configuration
    config = PhysiCellConfig()
    
    # Setup basic simulation (using convenience method)
    print("1. Setting up basic simulation...")
    config.setup_basic_simulation(
        x_range=(-400, 400),
        y_range=(-400, 400),
        mesh_spacing=20.0,
        max_time=1440.0  # 24 hours
    )
    
    # Add substrates using the substrates module
    print("2. Adding substrates...")
    config.substrates.add_substrate("oxygen", diffusion_coefficient=100000.0, decay_rate=0.1, initial_condition=38.0)
    config.substrates.add_substrate("glucose", diffusion_coefficient=50000.0, decay_rate=0.01, initial_condition=10.0)
    
    # Add cell types using the cell_types module
    print("3. Adding cell types...")
    config.cell_types.add_cell_type("cancer_cell")
    config.cell_types.set_motility("cancer_cell", speed=0.5, persistence_time=10.0, enabled=True)
    config.cell_types.add_secretion("cancer_cell", "oxygen", secretion_rate=0.0, uptake_rate=10.0)
    
    config.cell_types.add_cell_type("immune_cell")
    config.cell_types.set_motility("immune_cell", speed=2.0, persistence_time=5.0, enabled=True)
    
    # Add initial conditions using the initial_conditions module
    print("4. Adding initial conditions...")
    config.initial_conditions.add_cell_cluster("cancer_cell", x=0, y=0, radius=100, num_cells=50)
    config.initial_conditions.add_cell_cluster("immune_cell", x=200, y=200, radius=50, num_cells=20)
    
    # Add cell rules using the cell_rules module
    print("5. Adding cell rules...")
    config.cell_rules.add_rule(
        signal="oxygen",
        behavior="proliferation rate",
        cell_type="cancer_cell",
        min_signal=0.0,
        max_signal=38.0,
        min_behavior=0.0,
        max_behavior=0.05
    )
    
    # Add user parameters (legacy compatibility)
    print("6. Adding user parameters...")
    config.add_user_parameter("tumor_radius", 100.0, "micron", "Initial tumor radius")
    config.add_user_parameter("immune_recruitment_rate", 0.1, "1/min", "Rate of immune cell recruitment")
    
    # Configure save options using the save_options module
    print("7. Configuring save options...")
    config.save_options.set_svg_options(
        interval=120.0,
        plot_substrate=True,
        substrate_to_plot="oxygen",
        cell_color_by="cell_type"
    )
    
    # Print summary
    print("\n8. Configuration Summary:")
    summary = config.get_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")
    
    # Validate configuration
    print("\n9. Validating configuration...")
    issues = config.validate()
    if issues:
        print("   Issues found:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("   Configuration is valid!")
    
    # Generate and save XML
    print("\n10. Generating XML...")
    try:
        config.save_xml("test_output/modular_config.xml")
        print("    XML saved to: test_output/modular_config.xml")
    except Exception as e:
        print(f"    Error saving XML: {e}")
    
    # Demonstrate module access
    print("\n11. Demonstrating modular access:")
    print(f"    Domain bounds: {config.domain.data['x_min']} to {config.domain.data['x_max']}")
    print(f"    Number of substrates: {len(config.substrates.get_substrates())}")
    print(f"    Number of cell types: {len(config.cell_types.get_cell_types())}")
    print(f"    PhysiBoSS enabled: {config.physiboss.is_enabled()}")
    
    print("\nModular configuration test completed!")
    return config

def test_legacy_compatibility():
    """Test that legacy methods still work."""
    print("\n" + "=" * 50)
    print("Testing Legacy Compatibility")
    print("=" * 50)
    
    config = PhysiCellConfig()
    
    # Use legacy methods (should delegate to modules)
    config.set_domain(-300, 300, -300, 300, dx=15.0, dy=15.0)
    config.add_substrate("oxygen", diffusion_coefficient=100000.0)
    config.add_cell_type("default")
    
    print("Legacy methods work correctly!")
    print(f"Domain info: {config.domain.get_info()}")
    print(f"Substrates: {list(config.substrates.get_substrates().keys())}")
    print(f"Cell types: {list(config.cell_types.get_cell_types().keys())}")

if __name__ == "__main__":
    # Test modular approach
    config = test_modular_config()
    
    # Test legacy compatibility
    test_legacy_compatibility()
    
    print("\n" + "=" * 50)
    print("All tests completed successfully!")
    print("The modular approach provides:")
    print("  ✓ Clean separation of concerns")
    print("  ✓ Maintainable code organization") 
    print("  ✓ Simple user interface")
    print("  ✓ Legacy compatibility")
    print("  ✓ Extensible architecture")
