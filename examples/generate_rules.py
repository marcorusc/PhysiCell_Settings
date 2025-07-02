#!/usr/bin/env python3
"""
Generate cell rules PhysiCell configuration (PhysiCell_settings_rules.xml reproduction)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_builder_modular import PhysiCellConfig

def create_rules_config():
    """Create configuration with cell rules."""
    config = PhysiCellConfig()
    
    # Domain settings
    config.domain.set_bounds(-500, 500, -500, 500, -10, 10)
    config.domain.set_mesh(20, 20, 20)
    config.domain.set_2D(True)
    
    # Overall settings  
    config.options.set_max_time(1.0)
    config.options.set_time_steps(dt_diffusion=0.01, dt_mechanics=0.1, dt_phenotype=6.0)
    config.options.set_parallel_threads(1)
    config.options.set_random_seed(0)
    config.options.set_legacy_random_points(False)
    config.options.set_virtual_wall(True)
    config.options.set_automated_spring_adhesions(False)
    
    # Save options
    config.save_options.set_output_folder('output')
    config.save_options.set_full_data_options(interval=60.0, enable=True)
    config.save_options.set_svg_options(interval=60.0, enable=True)
    config.save_options.set_svg_plot_substrate(enabled=False, limits=False, 
                                              substrate='oxygen', colormap='', 
                                              min_conc=0, max_conc=0)
    config.save_options.set_legacy_data(False)
    
    # Add substrates
    substrates_data = [
        ('oxygen', 100000.0, 0.1, 38, True, 38),
        ('apoptotic debris', 1.0, 0.0, 0.0, False, 0.0),
        ('necrotic debris', 1.0, 0.0, 0.0, False, 0.0),
        ('pro-inflammatory factor', 10000.0, 1.0, 0.0, False, 0.0),
        ('anti-inflammatory factor', 10000.0, 1.0, 0.0, False, 0.0)
    ]
    
    for name, diff_coeff, decay_rate, init_cond, dirichlet_enabled, dirichlet_val in substrates_data:
        units = 'dimensionless'
        init_units = 'mmHg' if name == 'oxygen' else 'dimensionless'
        
        config.substrates.add_substrate(
            name=name,
            diffusion_coefficient=diff_coeff,
            decay_rate=decay_rate,
            initial_condition=init_cond,
            dirichlet_enabled=dirichlet_enabled,
            dirichlet_value=dirichlet_val,
            units=units,
            initial_units=init_units
        )
        
        # Set specific boundary conditions for oxygen
        if name == 'oxygen':
            for boundary in ['xmin', 'xmax', 'ymin', 'ymax']:
                config.substrates.set_dirichlet_boundary(name, boundary, True, 20)
            for boundary in ['zmin', 'zmax']:
                config.substrates.set_dirichlet_boundary(name, boundary, False, 38)
    
    # Add cell types
    cell_types = [
        'malignant epithelial cell',
        'M0 macrophage', 
        'M1 macrophage',
        'M2 macrophage',
        'effector T cell',
        'exhausted T cell'
    ]
    
    for i, cell_type in enumerate(cell_types):
        config.cell_types.add_cell_type(cell_type)
    
    # Update all cell types to include secretion for all substrates
    config.cell_types.update_all_cell_types_for_substrates()
    
    # Initial conditions - enabled
    config.initial_conditions.add_csv_file('cells.csv', './config', enabled=True)
    
    # Cell rules - add ruleset with proper folder and filename
    config.cell_rules.add_ruleset('main', folder='./config', filename='cell_rules.csv', enabled=True)
    
    # User parameters
    config.add_user_parameter('number_of_cells', 0, 'none', 
                             'initial number of cells (for each cell type)', 'int')
    
    return config

if __name__ == "__main__":
    config = create_rules_config()
    config.save_xml('test_output/generated_rules.xml')
    print("Rules configuration saved to test_output/generated_rules.xml")
