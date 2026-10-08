import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from maize_gee import count_arrays, consolidate
import pipeline


class ArrayImage:
    def __init__(self,value): self.value=np.asarray(value)
    def arrayLength(self,axis):return self.value.shape[axis]
    def arrayCat(self,other,axis):return ArrayImage(np.concatenate([self.value,other.value],axis=axis))
    def arraySlice(self,axis,start,end):return ArrayImage(self.value[start:end])
    def And(self,other):return ArrayImage(np.logical_and(self.value,other.value))
    def Not(self):return ArrayImage(np.logical_not(self.value))
    def arrayReduce(self,reducer,axes):return ArrayImage([self.value.sum()])
    def arrayGet(self,index):return ArrayImage(self.value[tuple(index)])
    def rename(self,name):return self


class GEETests(unittest.TestCase):
    def test_run_arrays_against_local_reference(self):
        from datetime import date,timedelta
        ee=SimpleNamespace(Image=SimpleNamespace(constant=ArrayImage),Array=lambda x:x,
                           Reducer=SimpleNamespace(sum=lambda:None))
        # Exercise isolated hits, long runs, boundaries and missing days.
        rng=np.random.default_rng(42)
        for n in [1,2,3,8,50]:
            for minimum in [1,2,3]:
                for _ in range(10):
                    values=rng.integers(0,2,n).astype(float)
                    valid=rng.integers(0,2,n)
                    values[valid==0]=np.nan
                    dates=[date(2000,1,1)+timedelta(days=i) for i in range(n)]
                    expected=len(pipeline.runs(dates,values.tolist(),1,'>=',minimum))
                    hit=np.nan_to_num(values).tolist()
                    result,days=count_arrays(ee,ArrayImage(hit),ArrayImage(valid),minimum,'episodes')
                    self.assertEqual(int(result.value),expected)
                    self.assertEqual(int(days.value),int(valid.sum()))
                    result,_=count_arrays(ee,ArrayImage(hit),ArrayImage(valid),1,'days')
                    self.assertEqual(int(result.value),int(np.nansum(values)))

    def test_consolidation_keeps_zero_and_excludes_incomplete(self):
        import pandas as pd
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path=root/'batch.csv'
            rows=[dict(pixel_id=7,phase='EST',season_year=y,count_unit='episodes',quality=q,
                       mean_count_per_native_cell=c,evaluated_area_fraction_with_event=a)
                  for y,q,c,a in [(1981,'OK',0,0),(1982,'OK',2,0.5),(1983,'INCOMPLETE',100,1)]]
            pipeline.save_csv(path,rows)
            consolidate([path],root)
            result=pd.read_csv(root/'frecuencia_historica_GDHY.csv').iloc[0]
            self.assertEqual(result.complete_seasons,2)
            self.assertEqual(result.mean_annual_count_per_native_cell,1)
            self.assertEqual(len(pd.read_csv(root/'resumen_GDHY_anual.csv')),3)


if __name__=='__main__':unittest.main()
