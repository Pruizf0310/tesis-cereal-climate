import unittest
import numpy as np
import pandas as pd
from piloto_pearson import episode_confirmation, pearson, welch_pair

class PilotTests(unittest.TestCase):
    def test_episode_crosses_month_without_duplication(self):
        dates=pd.date_range('2001-01-30',periods=7)
        hot=pd.DataFrame({'cell':[False,True,True,True,False,True,True]},index=dates)
        hits=episode_confirmation(hot).cell
        self.assertEqual(list(hits[hits].index),[pd.Timestamp('2001-02-01'),pd.Timestamp('2001-02-05')])

    def test_constant_not_zero_correlation(self):
        r,n=pearson(np.arange(36),np.zeros(36))
        self.assertTrue(np.isnan(r));self.assertEqual(n,36)

    def test_welch_known_period_and_gap(self):
        x=np.sin(2*np.pi*np.arange(4096)/64)
        f,p,c,n=welch_pair(x,x)
        self.assertEqual(1/f[np.argmax(p)],64)
        self.assertAlmostEqual(c[np.argmax(p)],1)
        x[1000:1600]=np.nan
        _,_,_,n_gap=welch_pair(x,x)
        self.assertLess(n_gap,n)

if __name__=='__main__':unittest.main()
