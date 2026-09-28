import {referenceDate,type PixelPhaseWindow} from './pixel-phenology';

export const REFERENCE_MONTHS=Array.from({length:24},(_,index)=>{
  const year=Math.floor(index/12),month=index%12;
  const start=year*365+(Date.UTC(2001,month,1)-Date.UTC(2001,0,1))/86400000;
  const days=(Date.UTC(2001,month+1,1)-Date.UTC(2001,month,1))/86400000;
  return {label:new Intl.DateTimeFormat('en-US',{month:'short',timeZone:'UTC'}).format(new Date(Date.UTC(2001,month,1))),year:year+1,start,days};
});

export function calendarPosition(window:PixelPhaseWindow){
  const start=window.start_year_offset*365+window.start_doy-1;
  const end=window.end_year_offset*365+window.end_doy;
  return {left:100*start/730,width:100*(end-start)/730};
}

export function calendarDate(doy:number,yearOffset:number){
  const date=new Intl.DateTimeFormat('en-GB',{day:'numeric',month:'short',timeZone:'UTC'}).format(referenceDate(2001,doy));
  return `${date} (Year ${yearOffset+1})`;
}
