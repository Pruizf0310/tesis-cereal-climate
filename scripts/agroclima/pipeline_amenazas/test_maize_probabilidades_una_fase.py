"""Offline tests: no GEE calls, no thesis outputs."""
import unittest
from unittest.mock import patch
import numpy as np
from maize_probabilidades_una_fase import daily_frame

class TestDailyExposure(unittest.TestCase):
    def setUp(self):
        self.pixel={'pixel_id':1,'lat':0,'lon':0}
        self.rule={'phase':'EST','count_unit':'episodes','min_days':2}
        self.cells=[dict(x=0,y=0,latitude=0,hits=[0,1,1,1,0,1],valid=[1]*6),
                    dict(x=1,y=0,latitude=0,hits=[0]*6,valid=[1]*6)]

    @patch('maize_probabilidades_una_fase.windows',return_value=[{'start':'1981-01-01','end':'1981-01-06'}])
    def test_days_and_episodes_are_distinct(self,_):
        d=daily_frame(self.cells,self.rule,self.pixel,1981,{})
        np.testing.assert_allclose(d.affected,[0,.5,.5,.5,0,0])
        np.testing.assert_allclose(d.mean_occurrences_qualified,[0,0,.5,0,0,0])
        self.assertEqual(len(d),6)

    @patch('maize_probabilidades_una_fase.windows',return_value=[{'start':'1981-01-01','end':'1981-01-06'}])
    def test_missing_is_not_zero(self,_):
        self.cells[1]['valid'][0]=0
        d=daily_frame(self.cells,self.rule,self.pixel,1981,{})
        self.assertTrue(d.affected.isna().all())
        self.assertTrue(d.mean_occurrences_qualified.isna().all())

    @patch('maize_probabilidades_una_fase.windows',return_value=[{'start':'1981-01-01','end':'1981-01-06'}])
    def test_rain_days_are_individual_occurrences(self,_):
        rule={'phase':'MAT','count_unit':'days','min_days':1}
        d=daily_frame(self.cells,rule,self.pixel,1981,{})
        np.testing.assert_allclose(d.affected,d.mean_occurrences_qualified)

if __name__=='__main__':unittest.main()
