import csv
import tempfile
import unittest
from pathlib import Path
import pandas as pd
import pipeline
from maize_seis_fases import windows, aggregate


class SixPhaseTests(unittest.TestCase):
    def test_source_subphase_and_cross_year(self):
        codes=['VE','V1_V6','V7_VT','R1','R2','R3','R4_R5','R6']
        data={'templates':[{'code':x} for x in codes],
              'pixels':{'1.25,2.25':[350,100,10,0,7,28,50,56,63,72,90,100]}}
        p=dict(pixel_id=1,lat=1.25,lon=2.25)
        veg=windows(data,p,'VEG',2000,2000)[0]
        self.assertEqual(veg['technical_stages'],'V7_VT')
        self.assertEqual(veg['start'],'2001-01-13')
        flo=windows(data,p,'FLO',2000,2000)[0]
        rep=windows(data,p,'REP',2000,2000)[0]
        self.assertLess(flo['end'],rep['start'])

    def test_precipitation_strict_threshold_counts_days(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder); cache=out/'clima'; cache.mkdir()
            pipeline.save_csv(out/'windows_candidate.csv',[
                dict(pixel_id=7,season_year=2000,phase='MAT',start='2000-01-01',end='2000-01-04')])
            pd.DataFrame([dict(pixel_id=7,date=f'2000-01-0{i}',x=1,y=1,latitude=5,
                               longitude=2,precip_mm=v) for i,v in enumerate([10,11,12,0],1)]).to_csv(
                                   cache/'era5_precip_UTC_7_2000_01.csv',index=False)
            # Temperature cache must not enter the precipitation analysis.
            (cache/'era5_UTC_7_2000_01.csv').write_text('invalid temperature file')
            c=dict(calendar_selection_confirmed=True,crop='maize',phase='MAT',variable='precip_mm',
                   threshold=10,operator='>',min_days=1,count_unit='days',source='SYNTHETIC')
            pipeline.analyze(c,out)
            result=pd.read_csv(out/'frecuencia_por_celda_fase.csv')
            self.assertEqual(result.event_count.iloc[0],2)
            self.assertEqual(len(pd.read_csv(out/'eventos.csv')),2)

    def test_aggregation_ignores_unfinished_partitions(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for pid,done in [(1,True),(2,False)]:
                out=root/f'pixel_{pid}'/'EST';out.mkdir(parents=True)
                for name in ['resumen_GDHY.csv','frecuencia_historica.csv','eventos.csv']:
                    pipeline.save_csv(out/name,[dict(pixel_id=pid,value=0)])
                if done:(out/'COMPLETED.json').write_text('{}')
            aggregate(root,root/'consolidado')
            result=pd.read_csv(root/'consolidado/resumen_GDHY.csv')
            self.assertEqual(result.pixel_id.tolist(),[1])


if __name__=='__main__':unittest.main()
