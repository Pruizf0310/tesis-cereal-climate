import unittest
from unittest.mock import patch
import numpy as np
from fechas_ocurrencias_core import qualifying_runs,assemble

class DatesTests(unittest.TestCase):
    def test_runs_qualification_and_gaps(self):
        hits=[1,1,1,0,1,1,1,1];valid=[1,1,1,1,1,0,1,1]
        self.assertEqual(qualifying_runs(hits,valid,2),[(0,1,2),(6,7,7)])

    @patch('fechas_ocurrencias_core.windows')
    def test_dates_and_partial_week_not_lost(self,window):
        window.return_value=[{'start':'2000-01-01','end':'2000-01-10'}]
        rule=dict(phase='EST',variable='tmax_c',operator='>=',threshold=34,min_days=2,count_unit='episodes')
        rows=[dict(phase='EST',x=i,y=0,longitude=i,latitude=0,valid=[1]*10,
            hits=([0]*5+[1]*5) if i==0 else ([0]*7+[1]*2+[0])) for i in range(2)]
        weeks,days,events=assemble(rows,[rule],{'pixel_id':1},2000,{})
        self.assertEqual(len(days),10)
        self.assertEqual(days.mean_occurrences_qualified.sum(),1)
        self.assertEqual(weeks['count'].sum(),.5)
        self.assertEqual(list(events.qualification_date),['2000-01-07','2000-01-09'])
        self.assertEqual(events.iloc[0].event_start_within_phase,'2000-01-06')
        self.assertTrue(events.iloc[0].touches_phase_end)

if __name__=='__main__':unittest.main()
