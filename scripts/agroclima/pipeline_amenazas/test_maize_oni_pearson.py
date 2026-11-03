import unittest
import numpy as np
from maize_oni_pearson import pearson_rows, condition_summary

class PearsonTests(unittest.TestCase):
    def test_pairwise_missing_keeps_zero_occurrences(self):
        x=np.arange(36,dtype=float)[None,:];y=x.copy()
        x[0,4]=np.nan;y[0,9]=np.nan
        a,b,n,r,status=pearson_rows(x,y)
        self.assertEqual(n[0],34)
        self.assertEqual(a[0,0],0)
        self.assertTrue(np.isnan(a[0,9]))
        self.assertTrue(np.isnan(b[0,4]))
        self.assertAlmostEqual(r[0],1)
        self.assertEqual(status[0],'OK')

    def test_constant_is_undefined(self):
        _,_,_,r,status=pearson_rows(np.arange(36)[None,:],np.zeros((1,36)))
        self.assertTrue(np.isnan(r[0]))
        self.assertEqual(status[0],'CONSTANT_OCCURRENCES')

    def test_condition_denominators_and_missing(self):
        x=np.array([[1,2,-1,-2,0,np.nan]])
        y=np.array([[2,0,1,3,0,10]])
        d=condition_summary(x,y)
        self.assertEqual(d['years_ONI_positive'][0],2)
        self.assertEqual(d['percent_years_with_occurrences_ONI_positive'][0],50)
        self.assertEqual(d['percent_years_with_occurrences_ONI_negative'][0],100)
        self.assertEqual(d['mean_count_ONI_negative'][0],2)
        self.assertEqual(d['years_ONI_zero'][0],1)

if __name__=='__main__':unittest.main()
