import tempfile
import unittest
from pathlib import Path
from maize_mjo_semanal import read_index

class IndexTests(unittest.TestCase):
    def test_rmm_and_missing_values(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'rmm.txt'
            p.write_text('header\n2000 1 1 0.2 -0.4 3 0.447\n2000 1 2 9999 9999 0 9999\n')
            s=read_index(p,'RMM')
            self.assertEqual(s.iloc[0,0],.2);self.assertEqual(s.iloc[0,1],-.4)
            self.assertTrue(s.iloc[1].isna().all())

    def test_romi_not_silently_rmm(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'romi.txt';p.write_text('2000 1 1 0 0.2 -0.4 0.447\n')
            with self.assertRaises(ValueError):read_index(p,'RMM')
            s=read_index(p,'ROMI');self.assertEqual(s.iloc[0,0],.2)

if __name__=='__main__':unittest.main()
