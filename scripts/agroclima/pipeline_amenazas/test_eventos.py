import unittest
from datetime import date, timedelta
from pipeline import runs, phase_date, absolute_reference_date, pixel_phase_windows

class EventTests(unittest.TestCase):
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

if __name__ == '__main__': unittest.main()
