import unittest
import numpy as np
import pandas as pd
from maize_mjo_diario import accumulate_daily

class DailyPairTests(unittest.TestCase):
    def test_exact_dates_zero_days_and_last_day(self):
        dates=pd.date_range('2000-01-01',periods=8)
        x=np.arange(8,dtype=float)
        index=pd.DataFrame({'component1':x,'component2':-x},index=dates)
        daily=pd.DataFrame({'date':dates,'phase':'EST','pixel_id':1,'quality':'OK',
            'mean_occurrences_qualified':[0,0,1,0,0,0,0,2]})
        stats=np.zeros((2,6,1,6));accumulate_daily(stats,daily,index,{1:0})
        self.assertEqual(stats[0,0,0,0],8)
        self.assertEqual(stats[0,0,0,2],3)
        self.assertEqual(stats[0,0,0,5],16)  # day 3: 2*1; day 8: 7*2
        self.assertEqual(stats[1,0,0,5],-16)

    def test_incomplete_and_missing_dates_excluded(self):
        dates=pd.date_range('2000-01-01',periods=4)
        index=pd.DataFrame({'component1':[1,2,np.nan,4],'component2':[1,2,3,4]},index=dates)
        daily=pd.DataFrame({'date':dates,'phase':'EST','pixel_id':1,
            'quality':['OK','INCOMPLETE','OK','OK'],'mean_occurrences_qualified':[0,99,1,1]})
        stats=np.zeros((2,6,1,6));accumulate_daily(stats,daily,index,{1:0})
        self.assertEqual(stats[0,0,0,0],2)
        self.assertEqual(stats[1,0,0,0],3)
        self.assertEqual(stats[0,0,0,2],1)

if __name__=='__main__':unittest.main()
