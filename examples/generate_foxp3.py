#!/usr/bin/env python3
"""
Generate PhysiBoSS PhysiCell configuration (PhysiCell_settings_FOXP3_2_mutant.xml reproduction)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_builder_modular import PhysiCellConfig

def create_foxp3_config():
    """Create PhysiBoSS configuration with FOXP3 mutation."""
    config = PhysiCellConfig()
    
    # Cell rules first (should be at top of XML)
    config.cell_rules.add_ruleset('differentiation', 
                                 folder='config/differentiation', 
                                 filename='rules.csv', 
                                 enabled=True)
    
    # Domain settings
    config.domain.set_bounds(-300, 300, -300, 300, -10, 10)
    config.domain.set_mesh(20, 20, 20)
    config.domain.set_2D(True)
    
    # Overall settings
    config.options.set_max_time(5000.0)
    config.options.set_time_steps(dt_diffusion=0.01, dt_mechanics=0.1, dt_phenotype=6.0)
    config.options.set_parallel_threads(10)
    config.options.set_legacy_random_points(False)
    config.options.set_virtual_wall(True)
    config.options.set_automated_spring_adhesions(False)
    
    # Save options
    config.save_options.set_output_folder('output')
    config.save_options.set_full_data_options(interval=30.0, enable=True)
    config.save_options.set_svg_options(interval=30.0, enable=True)
    config.save_options.set_svg_legend(enabled=True, cell_phase=False, cell_type=True)
    config.save_options.set_svg_plot_substrate(enabled=True, limits=False, 
                                              substrate='CCL21', colormap='original', 
                                              min_conc=0.0, max_conc=0.1)
    config.save_options.set_legacy_data(True)
    
    # Add CCL21 substrate
    config.substrates.add_substrate(
        name='CCL21',
        diffusion_coefficient=1000.0,
        decay_rate=0.005,
        initial_condition=0.0,
        dirichlet_enabled=False,
        dirichlet_value=0.0,
        units='dimensionless',
        initial_units='mmHg'
    )
    
    # Set track internalized substrates to true
    config.substrates.set_track_internalized_substrates(True)
    
    # Set all boundary values to disabled, 0.0
    for boundary in ['xmin', 'xmax', 'ymin', 'ymax', 'zmin', 'zmax']:
        config.substrates.set_dirichlet_boundary('CCL21', boundary, False, 0.0)
    
    # Add cell types
    cell_types_data = [
        ('T0', 0),
        ('Treg', 1),
        ('Th1', 2),
        ('Th17', 3),
        ('dendritic_cell', 4),
        ('endothelial_cell', 5)
    ]
    
    for name, cell_id in cell_types_data:
        config.cell_types.add_cell_type(name, template="live_cell")  # Use live_cell template
        # Set explicit ID
        config.cell_types.cell_types[name]['id'] = cell_id
        
        # Set basic phenotype matching the canonical file
        # Live cycle should already be set by template, but ensure it's correct
        config.cell_types.cell_types[name]['phenotype']['cycle']['code'] = '5'
        config.cell_types.cell_types[name]['phenotype']['cycle']['name'] = 'live'
        config.cell_types.set_death_rate(name, 'apoptosis', 0.0)
        config.cell_types.set_death_rate(name, 'necrosis', 0.0)
        
        # Volume parameters (same for all cell types)
        config.cell_types.set_volume_parameters(name, total=2494, nuclear=540, fluid_fraction=0.75)
        
        # Mechanics parameters
        config.cell_types.cell_types[name]['phenotype']['mechanics'].update({
            'cell_cell_adhesion_strength': 0.4,
            'cell_cell_repulsion_strength': 10.0,
            'relative_maximum_adhesion_distance': 1.25,
            'attachment_elastic_constant': 0.0,
            'attachment_rate': 0.0,
            'detachment_rate': 0.0
        })
        
        # Custom data
        config.cell_types.cell_types[name]['custom_data'] = {
            'somedata': {
                'value': 1.0 if name != 'endothelial_cell' else 0.0,
                'conserved': False,
                'units': 'dimensionless',
                'description': ''
            }
        }
    
    # Configure specific cell type properties
    # T0 cell (ID=0) - has detailed configuration and intracellular model
    config.cell_types.set_motility('T0', speed=0.8, persistence_time=0, enabled=True)
    config.cell_types.cell_types['T0']['phenotype']['motility']['migration_bias'] = 0.0
    config.cell_types.cell_types['T0']['phenotype']['motility']['use_2D'] = True
    
    # Add phase transition rate for T0
    config.cell_types.cell_types['T0']['phenotype']['cycle']['phase_transition_rates'] = {
        'rate_0_0': {
            'start_index': 0,
            'end_index': 0,
            'fixed_duration': False,
            'rate': 0
        }
    }
    
    # Add cell adhesion affinities for T0
    config.cell_types.cell_types['T0']['phenotype']['mechanics']['cell_adhesion_affinities'] = {
        'Th1': 1.0,
        'Th17': 1.0,
        'dendritic_cell': 1.0,
        'T0': 1.0,
        'Treg': 1.0,
        'endothelial_cell': 1.0
    }
    
    # Add T0 intracellular model
    config.cell_types.add_intracellular_model('T0', 'maboss',
                                             'config/differentiation/boolean_network/tcell_corral.bnd',
                                             'config/differentiation/boolean_network/tcell_corral.cfg')
    
    config.cell_types.set_intracellular_settings('T0', intracellular_dt=6.0, time_stochasticity=0, 
                                                 scaling=1.0, start_time=0.0, inheritance_global=False)
    
    # Add mutation for FOXP3_2
    config.cell_types.add_intracellular_mutation('T0', 'FOXP3_2', 0)
    
    # Add input mappings for T0
    inputs = [
        ('contact with dendritic_cell', 'IL1_In'),
        ('contact with dendritic_cell', 'MHCII_b1'),
        ('contact with dendritic_cell', 'MHCII_b2'),
        ('contact with dendritic_cell', 'IL12_In'),
        ('contact with dendritic_cell', 'IL6_In'),
        ('contact with dendritic_cell', 'CD80'),
        ('contact with dendritic_cell', 'CD4'),
        ('contact with dendritic_cell', 'IL23_In'),
        ('contact with dendritic_cell', 'PIP2')
    ]
    
    for physicell_name, intracellular_name in inputs:
        config.cell_types.add_intracellular_input('T0', physicell_name, intracellular_name)
    
    # Add output mappings for T0
    outputs = [
        ('transform to Treg', 'Treg'),
        ('transform to Th1', 'Th1'),
        ('transform to Th17', 'Th17')
    ]
    
    for physicell_name, intracellular_name in outputs:
        config.cell_types.add_intracellular_output('T0', physicell_name, intracellular_name)
    
    # Configure other cell types with simpler parameters
    for name in ['Treg', 'Th1', 'Th17']:
        config.cell_types.set_motility(name, speed=0.5, persistence_time=1, enabled=None)
        config.cell_types.cell_types[name]['phenotype']['motility']['migration_bias'] = 0.5
    
    # Dendritic cell - stationary but with intracellular model
    config.cell_types.set_motility('dendritic_cell', speed=0, persistence_time=1, enabled=None)
    config.cell_types.cell_types['dendritic_cell']['phenotype']['motility']['migration_bias'] = 0.8
    
    # Add dendritic cell intracellular model
    config.cell_types.add_intracellular_model('dendritic_cell', 'maboss',
                                             'config/differentiation/boolean_network/dendritic_cells.bnd',
                                             'config/differentiation/boolean_network/dendritic_cells.cfg')
    
    config.cell_types.set_intracellular_settings('dendritic_cell', intracellular_dt=6.0, 
                                                 time_stochasticity=0, scaling=30.0, 
                                                 start_time=0.0, inheritance_global=False)
    
    # Add initial value for dendritic cell
    config.cell_types.add_intracellular_initial_value('dendritic_cell', 'Maturation', 1.0)
    
    # Add input mappings for dendritic cell
    dc_inputs = [
        ('CCL21', 'CCL21', 1.0, 0),
        ('contact with T0', 'Contact', 0.5, 0)
    ]
    
    for physicell_name, intracellular_name, threshold, smoothing in dc_inputs:
        config.cell_types.add_intracellular_input('dendritic_cell', physicell_name, intracellular_name,
                                                 threshold=threshold, smoothing=smoothing)
    
    # Add output mappings for dendritic cell
    dc_outputs = [
        ('chemotactic response to CCL21', 'Migration', 1, 0),
        ('migration speed', 'Migration', 1.0, 0.0)
    ]
    
    for physicell_name, intracellular_name, value, base_value in dc_outputs:
        config.cell_types.add_intracellular_output('dendritic_cell', physicell_name, intracellular_name,
                                                  value=value, base_value=base_value)
    
    # Endothelial cell - different attachment properties
    config.cell_types.set_motility('endothelial_cell', speed=1.0, persistence_time=1.0, enabled=None)
    config.cell_types.cell_types['endothelial_cell']['phenotype']['motility']['migration_bias'] = 0.0
    config.cell_types.cell_types['endothelial_cell']['phenotype']['mechanics']['attachment_elastic_constant'] = 0.01
    config.cell_types.cell_types['endothelial_cell']['phenotype']['volume']['calcified_fraction'] = 0.0
    config.cell_types.cell_types['endothelial_cell']['phenotype']['volume']['calcification_rate'] = 0.0
    config.cell_types.cell_types['endothelial_cell']['phenotype']['volume']['relative_rupture_volume'] = 2  # no .0
    
    # Update all cell types for substrates
    config.cell_types.update_all_cell_types_for_substrates()
    
    # Initial conditions from CSV file
    config.initial_conditions.add_csv_file('cells.csv', './config/differentiation', enabled=True)
    
    # User parameters
    config.add_user_parameter('random_seed', 0, 'dimensionless', '', 'int')
    config.add_user_parameter('number_of_cells', 0, 'none', 
                             'initial number of cells (for each cell type)', 'int')
    
    return config

if __name__ == "__main__":
    config = create_foxp3_config()
    config.save_xml('test_output/generated_foxp3.xml')
    print("FOXP3 configuration saved to test_output/generated_foxp3.xml")
