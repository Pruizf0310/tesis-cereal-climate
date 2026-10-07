import unittest
from datetime import date, timedelta
from pipeline import runs, phase_date, absolute_reference_date, pixel_phase_windows, fetch_pages, authenticate_gee
from unittest.mock import Mock, patch
from types import SimpleNamespace
import csv
import tempfile
from pathlib import Path
from pipeline import analyze

class EventTests(unittest.TestCase):
    def test_authentication_cloud_only(self):
        fake=SimpleNamespace(Authenticate=Mock())
        with patch.dict('sys.modules',{'ee':fake}), patch('shutil.which',return_value='gcloud.cmd'):
            authenticate_gee(force=True)
        fake.Authenticate.assert_called_once_with(auth_mode='gcloud',
            scopes=['https://www.googleapis.com/auth/cloud-platform'], force=True)
    def test_duration_and_threshold_equality(self):
        ds = [date(2000,1,1)+timedelta(days=i) for i in range(7)]
        es = runs(ds,[34,34,34,20,34,20,34],34,'>=',2)
        self.assertEqual([len(e) for e in es],[3])
    def test_missing_breaks_event(self):
        ds = [date(2000,1,1)+timedelta(days=i) for i in range(3)]
        self.assertEqual(runs(ds,[35,float('nan'),35],34,'>=',2),[])
    def test_calendar_gap_breaks_event(self):
        self.assertEqual(runs([date(2000,1,1),date(2000,1,3)],[35,35],34,'>=',2),[])
    def test_leap_calendar(self):
        self.assertEqual(phase_date(2000,60),date(2000,3,1))
    def test_half_open_boundary_includes_leap_day(self):
        end=absolute_reference_date(2000,59)-timedelta(days=1)
        self.assertEqual(end,date(2000,2,29))
    def test_merged_native_blocks(self):
        data={'pixels':{'1.25,2.25':[100,10,14,0,2,6,10]},'templates':[
            {'code':'a','macro_phases':['EST']},{'code':'b','macro_phases':['VEG']},
            {'code':'c','macro_phases':['VEG']}]}
        result=pixel_phase_windows(data,1.25,2.25)
        self.assertEqual(result[1][1]['start'],2)
        self.assertEqual(result[1][1]['end'],10)
    def test_download_pagination(self):
        calls=[]
        def compute(params):
            calls.append(dict(params))
            if 'pageToken' not in params:
                return {'features':[{'properties':{'date':'2000-01-01'}}], 'nextPageToken':'second'}
            return {'features':[{'properties':{'date':'2000-01-02'}}]}
        ee=SimpleNamespace(data=SimpleNamespace(computeFeatures=compute))
        self.assertEqual(len(fetch_pages(ee,'expression')),2)
        self.assertEqual(calls[1]['pageToken'],'second')
    def test_analysis_zero_and_missing_seasons(self):
        import pandas as pd
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder);cache=out/'clima';cache.mkdir()
            with (out/'windows_candidate.csv').open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=['pixel_id','season_year','phase','start','end']);w.writeheader()
                w.writerow(dict(pixel_id=7,season_year=2000,phase='EST',start='2000-01-01',end='2000-01-05'))
            rows=[]
            for x,values in [(1,[35,35,35,20,20]),(2,[20,20,20,20,20]),(3,[35,None,35,35,35])]:
                for day,value in enumerate(values,1):
                    rows.append(dict(pixel_id=7,date=f'2000-01-{day:02d}',x=x,y=1,latitude=5.25,longitude=2.25,tmax_c=value))
            pd.DataFrame(rows).to_csv(cache/'era5_UTC_7_2000_01.csv',index=False)
            c=dict(calendar_selection_confirmed=True,crop='maize',phase='EST',variable='tmax_c',
                   threshold=34,operator='>=',min_days=2,source='SYNTHETIC_TEST_ONLY')
            analyze(c,out)
            annual=pd.read_csv(out/'frecuencia_por_celda_fase.csv').set_index('x')
            self.assertEqual(annual.loc[1,'event_count'],1)
            self.assertEqual(annual.loc[2,'event_count'],0)
            self.assertTrue(pd.isna(annual.loc[3,'event_count']))
            agg=pd.read_csv(out/'resumen_GDHY.csv')
            self.assertEqual(agg.iloc[0].evaluated_area_fraction_with_event,0.5)
            self.assertTrue((out/'frecuencia_anual.png').exists())
            self.assertTrue((out/'distribucion_frecuencias.png').exists())

if __name__ == '__main__': unittest.main()
