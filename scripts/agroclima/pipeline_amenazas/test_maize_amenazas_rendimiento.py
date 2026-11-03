import unittest
import numpy as np
from maize_amenazas_rendimiento import estimate,ols

class TestAssociations(unittest.TestCase):
    def test_known_coefficients_and_centered_decomposition(self):
        rng=np.random.default_rng(12)
        x=rng.uniform(0,4,(36,6));beta=np.array([-1,-2,0,.4,-.2,.1])
        y=5+x@beta
        summary,rows,fitted,cv,terms=estimate(x,y,np.arange(1981,2017))
        np.testing.assert_allclose([r['coefficient'] for r in rows],beta,atol=1e-10)
        np.testing.assert_allclose(terms.sum(axis=1),fitted-y.mean(),atol=1e-10)
        np.testing.assert_allclose(cv,y,atol=1e-10)
        self.assertAlmostEqual(summary['blocked_cv_r2'],1)

    def test_aliased_phases_are_not_assigned(self):
        rng=np.random.default_rng(1);x=rng.random((36,6));x[:,4]=x[:,3]
        summary,rows,*_=estimate(x,rng.random(36),np.arange(1981,2017))
        self.assertEqual(summary['status'],'PHASES_NOT_SEPARABLE')
        self.assertTrue(all(np.isnan(r['coefficient']) for r in rows))

    def test_real_zero_retained_missing_excluded(self):
        rng=np.random.default_rng(9);x=rng.random((36,6));x[0]=0;x[1,2]=np.nan
        y=rng.random(36);y[2]=np.nan
        summary,*_=estimate(x,y,np.arange(1981,2017))
        self.assertEqual(summary['n_valid_years'],34)
        self.assertEqual(summary['n_years_without_events'],1)

    def test_constant_phase_has_no_estimated_coefficient(self):
        rng=np.random.default_rng(3);x=rng.random((36,6));x[:,0]=0
        summary,rows,*_=estimate(x,rng.random(36),np.arange(1981,2017))
        self.assertEqual(rows[0]['status'],'CONSTANT_PHASE')
        self.assertTrue(np.isnan(rows[0]['coefficient']))

if __name__=='__main__':unittest.main()
