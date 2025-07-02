#!/usr/bin/env python3
"""
Example: Cell Rules CSV Generation

This example demonstrates how to use the new Cell Rules CSV generation functionality
to create PhysiCell-compatible rules CSV files.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_builder_modular import PhysiCellConfig

def create_cell_rules_example():
    """Create an example configuration with cell rules CSV generation."""
    
    print("=== PhysiCell Cell Rules CSV Generation Example ===\n")
    
    # 1. Create basic configuration
    config = PhysiCellConfig()
    
    # Add some cell types and substrates
    config.cell_types.add_cell_type("tumor")
    config.cell_types.add_cell_type("immune_cell")
    config.cell_types.add_cell_type("stromal_cell")
    
    config.substrates.add_substrate("oxygen", diffusion_coefficient=1000.0, decay_rate=0.1)
    config.substrates.add_substrate("glucose", diffusion_coefficient=500.0, decay_rate=0.05)
    config.substrates.add_substrate("growth_factor", diffusion_coefficient=100.0, decay_rate=0.01)
    
    # 2. Access the cell rules CSV module (auto-updates context)
    rules = config.cell_rules_csv
    
    # 3. Explore available options
    print("Current context after adding cell types and substrates:")
    rules.print_context()
    
    print("\n" + "="*60)
    print("AVAILABLE SIGNALS AND BEHAVIORS")
    print("="*60)
    
    # Show some example signal categories
    print("\n--- Contact-related Signals ---")
    rules.print_available_signals(filter_by_type="contact")
    
    print("\n--- Substrate-related Signals ---")
    rules.print_available_signals(filter_by_type="substrate")
    
    print("\n--- Death-related Behaviors ---")
    rules.print_available_behaviors(filter_by_type="death")
    
    print("\n--- Motility-related Behaviors ---")
    rules.print_available_behaviors(filter_by_type="motility")
    
    # 4. Add rules following the exact CSV format from the example
    print("\n" + "="*60)
    print("ADDING CELL RULES")
    print("="*60)
    
    # Tumor cell rules (based on the example CSV)
    print("\nAdding tumor cell rules...")
    
    # Oxygen affects cycle entry and necrosis
    rules.add_rule("tumor", "oxygen", "decreases", "necrosis", 0, 3.75, 8, 0)
    rules.add_rule("tumor", "oxygen", "increases", "cycle entry", 0.003333, 21.5, 4, 0)
    
    # Pressure affects cycle entry
    rules.add_rule("tumor", "pressure", "decreases", "cycle entry", 0, 1, 4, 0)
    
    # Oxygen affects migration
    rules.add_rule("tumor", "oxygen", "decreases", "migration speed", 0, 5, 4, 0)
    
    # Damage triggers apoptosis
    rules.add_rule("tumor", "damage", "increases", "apoptosis", 0.1, 5, 8, 0)
    
    # Immune cell rules
    print("Adding immune cell rules...")
    
    # Contact with tumor affects migration and attack
    rules.add_rule("immune_cell", "contact with tumor", "increases", "attack tumor", 0.01, 0.1, 10, 0)
    rules.add_rule("immune_cell", "contact with tumor", "decreases", "migration speed", 0.01, 0.1, 10, 0)
    
    # Growth factor affects migration
    rules.add_rule("immune_cell", "growth_factor", "increases", "migration speed", 1, 0.01, 4, 0)
    
    # Stromal cell rules  
    print("Adding stromal cell rules...")
    
    # Volume affects phagocytosis
    rules.add_rule("stromal_cell", "volume", "decreases", "phagocytose apoptotic cell", 0, 6000, 4, 0)
    rules.add_rule("stromal_cell", "volume", "decreases", "phagocytose necrotic cell", 0, 6000, 4, 0)
    
    # 5. Display current rules
    print("\n" + "="*60)
    print("CURRENT RULES SUMMARY")
    print("="*60)
    rules.print_rules()
    
    # 6. Validate rules
    print("\n" + "="*60)
    print("RULE VALIDATION")
    print("="*60)
    validation_messages = rules.validate_rules()
    if validation_messages:
        print("Validation warnings/errors:")
        for msg in validation_messages:
            print(f"  - {msg}")
    else:
        print("All rules validated successfully!")
    
    # 7. Generate CSV file
    print("\n" + "="*60)
    print("GENERATING CSV FILE")
    print("="*60)
    
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)
    csv_filename = os.path.join(output_dir, "generated_cell_rules.csv")
    
    try:
        generated_file = rules.generate_csv(csv_filename)
        print(f"✅ Successfully generated: {generated_file}")
        
        # Read and display the contents
        print(f"\nGenerated CSV contents:")
        print("-" * 40)
        with open(generated_file, 'r') as f:
            for i, line in enumerate(f, 1):
                print(f"{i:2}: {line.rstrip()}")
                
    except Exception as e:
        print(f"❌ Error generating CSV: {e}")
    
    print("\n" + "="*60)
    print("EXAMPLE COMPLETE")
    print("="*60)
    print("You can now:")
    print("1. Use the generated CSV file with PhysiCell")
    print("2. Add more rules using: config.cell_rules_csv.add_rule(...)")
    print("3. Explore signals/behaviors using: config.cell_rules_csv.print_available_signals()")
    print("4. Check context using: config.cell_rules_csv.print_context()")

if __name__ == "__main__":
    create_cell_rules_example()
