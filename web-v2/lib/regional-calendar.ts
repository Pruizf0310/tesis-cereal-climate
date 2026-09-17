export interface CalendarZone {
 id:string;label:string;count:number;representative:string;candidates:string[];members:string[];
 cycle_range:number[];cycle_median:number;longitude_min:number;longitude_max:number;planting_regime:string;
}
export interface RegionalCalendar {
 version:string;crop:string;season_id:string;selection:string;
 bands:{id:string;label:string;latitude_min:number;latitude_max:number;zones:CalendarZone[]}[];
}
