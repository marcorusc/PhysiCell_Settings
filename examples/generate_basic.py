#!/usr/bin/env python3
"""
Generate basic PhysiCell configuration (PhysiCell_settings.xml reproduction)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from physicell_config import PhysiCellConfig

def create_basic_config():
    """Create basic template configuration."""
    config = PhysiCellConfig()
    
    # Domain settings
    config.domain.set_bounds(-500, 500, -500, 500, -10, 10)
    config.domain.set_mesh(20, 20, 20)
    config.domain.set_2D(True)
    
    # Overall settings
    config.options.set_max_time(7200)
    config.options.set_time_steps(dt_diffusion=0.01, dt_mechanics=0.1, dt_phenotype=6)
    config.options.set_parallel_threads(6)
    config.options.set_random_seed(0)
    config.options.set_legacy_random_points(False)
    config.options.set_virtual_wall(True)
    config.options.set_automated_spring_adhesions(False)
    
    # Save options
    config.save_options.set_output_folder('output')
    config.save_options.set_full_data_options(interval=60, enable=True)
    config.save_options.set_svg_options(interval=60, enable=True)
    config.save_options.set_svg_plot_substrate(enabled=False, limits=True, 
                                              substrate='substrate', colormap='YlOrRd', 
                                              min_conc=0, max_conc=1)
    config.save_options.set_legacy_data(False)
    
    # Add substrates
    config.substrates.add_substrate("substrate", "100000.0", 10, 0, False, 0)
    
    config.substrates.set_track_internalized_substrates(True)
    
    # Set boundary values for all boundaries
    for boundary in ['xmin', 'xmax', 'ymin', 'ymax', 'zmin', 'zmax']:
        config.substrates.set_dirichlet_boundary('substrate', boundary, False, 0)
    
    # Add cell type
    config.cell_types.add_cell_type(name='default')
    config.cell_types.set_cycle_model('default', 'flow_cytometry_separated')
    
    # Override to use phase_durations to match example
    config.cell_types.cell_types['default']['phenotype']['cycle']['phase_durations'] = [
        {'index': 0, 'duration': 300.0, 'fixed_duration': False},
        {'index': 1, 'duration': 480.0, 'fixed_duration': True},
        {'index': 2, 'duration': 240.0, 'fixed_duration': True},
        {'index': 3, 'duration': 60.0, 'fixed_duration': True}
    ]
    # Remove transition_rates if present
    if 'transition_rates' in config.cell_types.cell_types['default']['phenotype']['cycle']:
        del config.cell_types.cell_types['default']['phenotype']['cycle']['transition_rates']
    
    # Set custom data for default cell
    config.cell_types.cell_types['default']['custom_data']['sample'] = {
        'value': 1.0,
        'units': 'dimensionless',
        'description': '',
        'conserved': False
    }
    
    # Initial conditions - disabled by default
    config.initial_conditions.add_csv_file('cells.csv', './config', enabled=False)
    
    # Don't add any cell rules (will result in no cell_rules section)
    
    # User parameters
    config.add_user_parameter('number_of_cells', 5, 'none', 
                             'initial number of cells (for each cell type)', 'int')
    
    return config

if __name__ == "__main__":
    config = create_basic_config()
    config.save_xml('test_output/generated_basic.xml')
    print("Basic configuration saved to test_output/generated_basic.xml")
