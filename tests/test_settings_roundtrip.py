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


if __name__ == "__main__":
    unittest.main()
