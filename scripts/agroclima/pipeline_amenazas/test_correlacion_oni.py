import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from correlacion_oni_amenazas import read_oni,window_oni,correlations,block_permutations,permutation_p,fdr_bh,SEASONS


class ONITests(unittest.TestCase):
    def test_center_month_weighting_and_cross_year(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'oni.txt'
            pd.DataFrame([dict(Year=2000,**dict(zip(SEASONS,np.arange(1,13)/10))),
                          dict(Year=2001,**dict(zip(SEASONS,np.arange(13,25)/10)))]).to_csv(path,sep='\t',index=False)
            _,origin,sums,missing=read_oni(path)
            result=window_oni(pd.Series(['2000-01-31','2000-12-31','2000-02-28']),
                              pd.Series(['2000-02-02','2001-01-02','2000-03-01']),origin,sums,missing)
            self.assertAlmostEqual(result[0],(1+2+2)/30)
            self.assertAlmostEqual(result[1],(12+13+13)/30)
            self.assertAlmostEqual(result[2],(2+2+3)/30) # leap day belongs to February

    def test_rank_linear_and_constant_series(self):
        x=np.tile(np.arange(36,dtype=float),(3,1))
        y=np.array([np.arange(36),-np.arange(36),np.zeros(36)],dtype=float)
        result=correlations(x,y,20)
        self.assertAlmostEqual(result['pearson'][0],1)
        self.assertAlmostEqual(result['spearman'][1],-1)
        self.assertTrue(np.isnan(result['pearson'][2]))
        self.assertEqual(result['status'][2],'CONSTANT_HAZARD')

    def test_blocks_permutation_p_and_fdr(self):
        p=block_permutations(36,99,3,42)
        for perm in p:
            self.assertEqual(sorted(perm.tolist()),list(range(36)))
            self.assertTrue(np.all(np.diff(perm.reshape(-1,3),axis=1)==1))
        x=np.arange(36,dtype=float)[None,:];result=correlations(x,x,20)
        stats=permutation_p(result,p)
        self.assertLessEqual(stats['spearman'][0],.02)
        q=fdr_bh(np.array([.01,.04,np.nan,.03]))
        np.testing.assert_allclose(q[[0,1,3]],[.03,.04,.04])

    def test_missing_oni_month_is_not_filled_from_previous(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'oni.txt'
            row=dict(Year=2000,**dict(zip(SEASONS,range(12))));row['JFM']=np.nan
            pd.DataFrame([row]).to_csv(path,sep='\t',index=False)
            _,origin,sums,missing=read_oni(path)
            result=window_oni(pd.Series(['2000-02-01']),pd.Series(['2000-02-03']),origin,sums,missing)
            self.assertTrue(np.isnan(result[0]))


if __name__=='__main__':unittest.main()
