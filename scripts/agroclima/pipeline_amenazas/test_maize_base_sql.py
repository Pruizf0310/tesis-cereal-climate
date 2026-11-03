import unittest
import pandas as pd
from maize_base_sql import exposure


class ExposureTests(unittest.TestCase):
    def test_inclusive_missing_and_joint(self):
        d = pd.DataFrame({'date':pd.date_range('2000-12-30',periods=4),
                          'oni':[1.,1.,float('nan'),-.8],
                          'oni_state':['Nino','Nino','Missing','Nina'],
                          'mjo':[2.,0.,float('nan'),8.]})
        w = pd.DataFrame({'start':['2000-12-30','2001-01-01'], 'end':['2000-12-31','2001-01-02']})
        r = exposure(w,d)
        self.assertEqual(r.window_days.tolist(),[2,2])
        self.assertEqual(r.oni_state.tolist(),['Nino','Incomplete'])
        self.assertEqual(r.mjo_valid_days.tolist(),[2,1])
        self.assertEqual(r.mjo_0_days.tolist(),[1,0])
        self.assertIn('Nino_2',r.joint_days_json.iloc[0])
        self.assertEqual(r.Nina_days.tolist(),[0,1])

    def test_outside_coverage_fails(self):
        d = pd.DataFrame({'date':pd.date_range('2000-01-01',periods=2)})
        w = pd.DataFrame({'start':['1999-12-31'],'end':['2000-01-01']})
        with self.assertRaises(ValueError): exposure(w,d)


if __name__=='__main__': unittest.main()
