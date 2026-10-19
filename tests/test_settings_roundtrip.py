"""Offline public-API regressions; also runnable with unittest alone."""
import copy
import tempfile
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

from physicell_config import PhysiCellConfig
from physicell_config.xml_loader import XMLLoadingError


class SettingsRoundtripTests(unittest.TestCase):
    def config(self):
        cfg = PhysiCellConfig()
        cfg.cell_types.add_cell_type('test')
        return cfg

    def phenotype(self, cfg):
        return cfg.cell_types.cell_types['test']['phenotype']

    def roundtrip(self, cfg):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'settings.xml'
            cfg.save_xml(str(path))
            loaded = PhysiCellConfig()
            loaded.load_xml(path)
        return loaded

    def test_zero_death_and_disabled_motility(self):
        for imported in (False, True):
            with self.subTest(imported=imported):
                cfg = self.config()
                if imported:
                    cfg = self.roundtrip(cfg)
                for death in ('apoptosis', 'necrosis'):
                    cfg.cell_types.set_death_rate('test', death, 0)
                cfg.cell_types.set_motility('test', speed=0, enabled=False)
                for _ in range(2):
                    root = ET.fromstring(cfg.generate_xml())
                    self.assertEqual([float(e.text) for e in root.findall('.//death/model/death_rate')], [0, 0])
                    self.assertEqual(root.findtext('.//motility/options/enabled'), 'false')
                    cfg = self.roundtrip(cfg)
                    self.assertEqual(self.phenotype(cfg)['death']['apoptosis']['default_rate'], 0)
                    self.assertEqual(self.phenotype(cfg)['death']['necrosis']['default_rate'], 0)
                    self.assertIs(self.phenotype(cfg)['motility']['enabled'], False)

    def test_death_xml_primary_and_legacy_rate(self):
        for rates, expected in (('<death_rate>0</death_rate><rate>0.7</rate>', 0),
                                ('<rate>0.25</rate>', 0.25),
                                ('<death_rate>0.125</death_rate>', 0.125)):
            cfg = self.config()
            root = ET.fromstring(cfg.generate_xml())
            model = root.find('.//death/model')
            model.remove(model.find('death_rate'))
            for child in ET.fromstring('<rates>' + rates + '</rates>'):
                model.append(child)
            cfg.load_xml_string(ET.tostring(root, encoding='unicode'))
            self.assertEqual(self.phenotype(cfg)['death']['apoptosis']['default_rate'], expected)

    def test_cycle_fixed_duration_roundtrip_and_rate_only_update(self):
        cfg = self.config()
        cfg.cell_types.set_cycle_model('test', 'Ki67_basic')
        cfg.cell_types.set_cycle_transition_rate('test', 1, 0, 0, fixed_duration=False)
        cfg.cell_types.set_cycle_transition_rate('test', 0, 1, 0.25, fixed_duration=True)
        for _ in range(2):
            cfg = self.roundtrip(cfg)
            cfg.cell_types.set_cycle_transition_rate('test', 1, 0, 0)
            cycle = ET.fromstring(cfg.generate_xml()).find('.//cycle')
            self.assertEqual(cycle.get('code'), '1')
            rates = cycle.findall('./phase_transition_rates/rate')
            self.assertEqual([(r.get('start_index'), r.get('end_index'), float(r.text), r.get('fixed_duration')) for r in rates],
                             [('0', '1', 0.25, 'true'), ('1', '0', 0, 'false')])

    def test_imported_cycle_attributes_override_templates(self):
        cfg = self.config()
        root = ET.fromstring(cfg.generate_xml())
        cycle = root.find('.//cycle')
        cycle.set('code', '1')
        cycle.set('name', 'Ki67 (basic)')
        cycle.find('phase_transition_rates').clear()
        ET.SubElement(cycle.find('phase_transition_rates'), 'rate', start_index='1', end_index='0', fixed_duration='false').text = '0'
        cfg.load_xml_string(ET.tostring(root, encoding='unicode'))
        result = ET.fromstring(self.roundtrip(cfg).generate_xml()).find('.//cycle')
        self.assertEqual(result.get('code'), '1')
        self.assertEqual(len(result.findall('.//rate')), 1)
        self.assertEqual(result.find('.//rate').get('fixed_duration'), 'false')
        self.assertEqual(float(result.findtext('.//rate')), 0)

    def test_imported_cycle_metadata_survives_roundtrips(self):
        for code, name in (('1', 'Imported Ki67 label'),
                           ('99', 'live'),
                           ('99', 'Custom cycle')):
            with self.subTest(code=code, name=name):
                cfg = self.config()
                root = ET.fromstring(cfg.generate_xml())
                cycle = root.find('.//cycle')
                cycle.set('code', code)
                cycle.set('name', name)
                cfg.load_xml_string(ET.tostring(root, encoding='unicode'))
                for _ in range(2):
                    result = ET.fromstring(cfg.generate_xml()).find('.//cycle')
                    self.assertEqual(result.get('code'), code)
                    self.assertEqual(result.get('name'), name)
                    copied = ET.fromstring(cfg.copy().generate_xml()).find('.//cycle')
                    self.assertEqual(copied.attrib, result.attrib)
                    cfg = self.roundtrip(cfg)
                result = ET.fromstring(cfg.generate_xml()).find('.//cycle')
                self.assertEqual(result.get('code'), code)
                self.assertEqual(result.get('name'), name)

    def test_legacy_cycle_defaults(self):
        cfg = self.config()
        cfg.cell_types.set_cycle_model('test', 'Ki67_basic')
        cfg.cell_types.set_cycle_transition_rate('test', 1, 0, 0.1)
        rate = ET.fromstring(cfg.generate_xml()).find('.//cycle/phase_transition_rates/rate[@start_index="1"]')
        self.assertEqual(rate.get('fixed_duration'), 'true')

    def test_physiboss_roundtrip(self):
        for stochasticity in (0, 0.125, 2):
            for steepness in (None, 0, 2.5, 10):
                with self.subTest(stochasticity=stochasticity, steepness=steepness):
                    cfg = self.config()
                    cfg.physiboss.add_intracellular_model('test')
                    cfg.physiboss.set_intracellular_settings('test', time_stochasticity=stochasticity, inheritance_global=False)
                    kwargs = {} if steepness is None else {'steepness': steepness}
                    cfg.physiboss.add_intracellular_output('test', 'migration speed', 'Move', 'activation', 0, 0, 0, **kwargs)
                    for _ in range(2):
                        cfg = self.roundtrip(cfg)
                        intra = self.phenotype(cfg)['intracellular']
                        self.assertEqual(intra['settings']['time_stochasticity'], stochasticity)
                        self.assertIs(intra['settings']['inheritance']['global'], False)
                        output = intra['mapping']['outputs'][0]['settings']
                        for key in ('value', 'base_value', 'smoothing'):
                            self.assertEqual(output[key], 0)
                        self.assertEqual(output.get('steepness', 10), 10 if steepness is None else steepness)
                        if steepness is None:
                            self.assertNotIn('steepness', output)

    def test_all_cycle_models_retain_defaults(self):
        for model in ('Ki67_basic', 'Ki67_advanced', 'live', 'cycling_quiescent',
                      'flow_cytometry', 'flow_cytometry_separated'):
            with self.subTest(model=model):
                cfg = self.config()
                cfg.cell_types.set_cycle_model('test', model)
                before = ET.fromstring(cfg.generate_xml()).find('.//cycle')
                after = ET.fromstring(cfg.copy().generate_xml()).find('.//cycle')
                self.assertEqual(before.attrib, after.attrib)
                self.assertEqual([(r.attrib, float(r.text)) for r in before.findall('.//rate')],
                                 [(r.attrib, float(r.text)) for r in after.findall('.//rate')])

    def test_old_config_omissions_and_copy(self):
        cfg = self.config()
        default_death = copy.deepcopy(self.phenotype(cfg)['death'])
        cfg.physiboss.add_intracellular_model('test')
        cfg.physiboss.add_intracellular_output('test', 'migration speed', 'Move')
        cfg = cfg.copy()
        self.assertEqual(self.phenotype(cfg)['death'], default_death)
        intra = self.phenotype(cfg)['intracellular']
        self.assertNotIn('time_stochasticity', intra['settings'])
        self.assertNotIn('steepness', intra['mapping']['outputs'][0]['settings'])
        root = ET.fromstring(cfg.generate_xml())
        self.assertIsNone(root.find('.//time_stochasticity'))
        self.assertIsNone(root.find('.//steepness'))

    def test_xml_imported_steepness_and_fraction(self):
        cfg = self.config()
        cfg.physiboss.add_intracellular_model('test')
        cfg.physiboss.add_intracellular_output('test', 'migration speed', 'Move')
        root = ET.fromstring(cfg.generate_xml())
        ET.SubElement(root.find('.//intracellular/settings'), 'time_stochasticity').text = '0.375'
        ET.SubElement(root.find('.//output/settings'), 'steepness').text = '0'
        cfg.load_xml_string(ET.tostring(root, encoding='unicode'))
        result = ET.fromstring(cfg.copy().generate_xml())
        self.assertEqual(float(result.findtext('.//time_stochasticity')), 0.375)
        self.assertEqual(float(result.findtext('.//steepness')), 0)

    def test_invalid_physiboss_xml_and_direct_export(self):
        for field in ('steepness', 'time_stochasticity'):
            for bad in ('-0.5', 'nan', 'inf', 'invalid', ''):
                with self.subTest(field=field, bad=bad):
                    cfg = self.config()
                    cfg.physiboss.add_intracellular_model('test')
                    cfg.physiboss.add_intracellular_output('test', 'migration speed', 'Move')
                    root = ET.fromstring(cfg.generate_xml())
                    path = './/output/settings' if field == 'steepness' else './/intracellular/settings'
                    ET.SubElement(root.find(path), field).text = bad
                    with self.assertRaisesRegex(XMLLoadingError, field):
                        PhysiCellConfig.from_xml_string(ET.tostring(root, encoding='unicode'))
                    intra = self.phenotype(cfg)['intracellular']
                    settings = intra['mapping']['outputs'][0]['settings'] if field == 'steepness' else intra['settings']
                    settings[field] = bad
                    with self.assertRaisesRegex(ValueError, field):
                        cfg.generate_xml()
                    with tempfile.TemporaryDirectory() as directory:
                        with self.assertRaisesRegex(ValueError, field):
                            cfg.save_xml(str(Path(directory) / 'invalid.xml'))

    def test_cycle_phase_durations_and_new_transition(self):
        cfg = self.config()
        cfg.cell_types.set_cycle_model('test', 'live')
        cfg.cell_types.set_cycle_phase_durations('test', [
            {'index': 0, 'duration': 0, 'fixed_duration': False}])
        cfg = self.roundtrip(cfg)
        cycle = ET.fromstring(cfg.generate_xml()).find('.//cycle')
        self.assertIsNone(cycle.find('phase_transition_rates'))
        self.assertEqual(cycle.find('.//duration').get('fixed_duration'), 'false')
        self.assertEqual(float(cycle.findtext('.//duration')), 0)
        cfg.cell_types.set_cycle_transition_rate('test', 0, 0, 0, True)
        rate = ET.fromstring(cfg.copy().generate_xml()).find('.//cycle/phase_transition_rates/rate')
        self.assertEqual(float(rate.text), 0)
        self.assertEqual(rate.get('fixed_duration'), 'true')

    def test_invalid_setters_do_not_mutate(self):
        cfg = self.config()
        cfg.physiboss.add_intracellular_model('test')
        for bad in (-1, float('nan'), float('inf'), 'invalid', [], True):
            for setter in (
                lambda: cfg.physiboss.set_intracellular_settings('test', intracellular_dt=5, time_stochasticity=bad),
                lambda: cfg.physiboss.add_intracellular_output('test', 'speed', 'Move', steepness=bad),
            ):
                before = copy.deepcopy(self.phenotype(cfg))
                with self.assertRaises(ValueError):
                    setter()
                self.assertEqual(self.phenotype(cfg), before)
        for bad in ('false', 0, 1, [], 'true'):
            with self.assertRaises(ValueError):
                cfg.cell_types.set_cycle_transition_rate('test', 0, 0, 0, fixed_duration=bad)
        for setter in (lambda: cfg.cell_types.set_death_rate('test', 'apoptosis', -1),
                       lambda: cfg.cell_types.set_cycle_transition_rate('test', 0, 0, -1)):
            with self.assertRaises(ValueError):
                setter()


if __name__ == '__main__':
    unittest.main()
