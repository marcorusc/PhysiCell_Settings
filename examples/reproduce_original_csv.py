#!/usr/bin/env python3
"""
Example: Reproduce the exact cell_rules.csv file provided

This example reproduces the exact cell_rules.csv file that was provided as an example.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_builder_modular import PhysiCellConfig

def reproduce_original_csv():
    """Reproduce the original cell_rules.csv file exactly."""
    
    print("=== Reproducing Original cell_rules.csv ===\n")
    
    # 1. Create configuration with the cell types from the original CSV
    config = PhysiCellConfig()
    
    # Add cell types from the original CSV
    config.cell_types.add_cell_type("malignant epithelial cell")
    config.cell_types.add_cell_type("M0 macrophage")
    config.cell_types.add_cell_type("M1 macrophage")
    config.cell_types.add_cell_type("M2 macrophage")
    config.cell_types.add_cell_type("effector T cell")
    config.cell_types.add_cell_type("exhausted T cell")
    
    # Add substrates from the original CSV
    config.substrates.add_substrate("oxygen")
    config.substrates.add_substrate("apoptotic debris")
    config.substrates.add_substrate("necrotic debris")
    config.substrates.add_substrate("pro-inflammatory factor")
    config.substrates.add_substrate("anti-inflammatory factor")
    
    # 2. Get rules module
    rules = config.cell_rules_csv
    
    print("Context loaded with cell types and substrates from original CSV:")
    rules.print_context()
    
    # 3. Add all rules from the original CSV file exactly
    print("\nAdding rules from original CSV...")
    
    # malignant epithelial cell rules
    rules.add_rule("malignant epithelial cell", "oxygen", "decreases", "necrosis", 0, 3.75, 8, 0)
    rules.add_rule("malignant epithelial cell", "oxygen", "increases", "cycle entry", 0.003333, 21.5, 4, 0)
    rules.add_rule("malignant epithelial cell", "pressure", "decreases", "cycle entry", 0, 1, 4, 0)
    rules.add_rule("malignant epithelial cell", "apoptotic", "increases", "apoptotic debris secretion", 0.017, 0.1, 10, 1)
    rules.add_rule("malignant epithelial cell", "necrotic", "increases", "necrotic debris secretion", 0.017, 0.1, 10, 1)
    rules.add_rule("malignant epithelial cell", "oxygen", "decreases", "migration speed", 0, 5, 4, 0)
    rules.add_rule("malignant epithelial cell", "damage", "increases", "apoptosis", 0.1, 5, 8, 0)
    
    # M0 macrophage rules
    rules.add_rule("M0 macrophage", "necrotic debris", "increases", "transform to M1 macrophage", 0.05, 0.005, 4, 0)
    rules.add_rule("M0 macrophage", "apoptotic debris", "decreases", "migration speed", 0.1, 0.005, 4, 0)
    rules.add_rule("M0 macrophage", "necrotic debris", "decreases", "migration speed", 0.1, 0.005, 4, 0)
    rules.add_rule("M0 macrophage", "volume", "decreases", "phagocytose apoptotic cell", 0, 6000, 4, 0)
    rules.add_rule("M0 macrophage", "volume", "decreases", "phagocytose necrotic cell", 0, 6000, 4, 0)
    
    # M1 macrophage rules
    rules.add_rule("M1 macrophage", "oxygen", "decreases", "transform to M2 macrophage", 0.0001, 5, 8, 0)
    rules.add_rule("M1 macrophage", "apoptotic debris", "decreases", "migration speed", 0.1, 0.005, 4, 0)
    rules.add_rule("M1 macrophage", "necrotic debris", "decreases", "migration speed", 0.1, 0.005, 4, 0)
    rules.add_rule("M1 macrophage", "volume", "decreases", "phagocytose apoptotic cell", 0.0, 6000, 4, 0)
    rules.add_rule("M1 macrophage", "volume", "decreases", "phagocytose necrotic cell", 0.0, 6000, 4, 0)
    
    # M2 macrophage rules
    rules.add_rule("M2 macrophage", "apoptotic debris", "decreases", "migration speed", 0.1, 0.005, 4, 0)
    rules.add_rule("M2 macrophage", "necrotic debris", "decreases", "migration speed", 0.1, 0.005, 4, 0)
    rules.add_rule("M2 macrophage", "volume", "decreases", "phagocytose apoptotic cell", 0.0, 6000, 4, 0)
    rules.add_rule("M2 macrophage", "volume", "decreases", "phagocytose necrotic cell", 0.0, 6000, 4, 0)
    
    # effector T cell rules
    rules.add_rule("effector T cell", "pro-inflammatory factor", "increases", "attack malignant epithelial cell", 0.01, 1, 4, 0)
    rules.add_rule("effector T cell", "contact with malignant epithelial cell", "decreases", "migration speed", 0.01, 0.1, 10, 0)
    rules.add_rule("effector T cell", "pro-inflammatory factor", "increases", "migration speed", 1, 0.01, 4, 0)
    rules.add_rule("effector T cell", "anti-inflammatory factor", "increases", "transform to exhausted T cell", 0.001, 0.5, 4, 0)
    
    # exhausted T cell rules
    rules.add_rule("exhausted T cell", "anti-inflammatory factor", "decreases", "migration speed", 0.001, 0.5, 4, 0)
    rules.add_rule("exhausted T cell", "contact with malignant epithelial cell", "decreases", "migration speed", 0.01, 0.1, 10, 0)
    
    # 4. Display rules summary
    print(f"\nAdded {len(rules.get_rules())} rules total")
    rules.print_rules()
    
    # 5. Generate CSV file
    output_file = "test_output/reproduced_cell_rules.csv"
    generated_file = rules.generate_csv(output_file)
    
    print(f"\n✅ Generated CSV file: {generated_file}")
    
    # 6. Compare with original
    print("\nComparing with original file...")
    original_file = "examples/cell_rules.csv"
    
    if os.path.exists(original_file):
        with open(original_file, 'r') as f:
            original_lines = f.readlines()
        
        with open(generated_file, 'r') as f:
            generated_lines = f.readlines()
        
        print(f"Original file has {len(original_lines)} rules")
        print(f"Generated file has {len(generated_lines)} rules")
        
        if len(original_lines) == len(generated_lines):
            print("✅ Same number of rules")
        else:
            print("❌ Different number of rules")
        
        # Show first few lines for comparison
        print("\nFirst 5 lines comparison:")
        print("Original vs Generated:")
        for i in range(min(5, len(original_lines), len(generated_lines))):
            orig = original_lines[i].strip()
            gen = generated_lines[i].strip()
            match = "✅" if orig == gen else "❌"
            print(f"{match} {orig}")
            if orig != gen:
                print(f"   {gen}")
    else:
        print(f"Original file not found at {original_file}")

if __name__ == "__main__":
    reproduce_original_csv()
