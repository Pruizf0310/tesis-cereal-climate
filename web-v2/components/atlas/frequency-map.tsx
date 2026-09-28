'use client';
import {useEffect,useRef,useState} from 'react';
import maplibregl from 'maplibre-gl';
import {Globe2,LocateFixed} from 'lucide-react';

export interface MapCell {cell:string;color:string;opacity:number;label:string;}
export function FrequencyMap({cells,onSelect,onBounds,compact=false,coverageBounds}:{cells:MapCell[];onSelect:(cell:string)=>void;onBounds:(bounds:number[])=>void;compact?:boolean;coverageBounds?:[number,number,number,number]}) {
  const host=useRef<HTMLDivElement>(null),map=useRef<maplibregl.Map|null>(null);
  const callbacks=useRef({onSelect,onBounds});callbacks.current={onSelect,onBounds};
  const [ready,setReady]=useState(false),[error,setError]=useState('');
  useEffect(()=>{
    if(!host.current)return;
    let instance:maplibregl.Map;
    try {
      instance=new maplibregl.Map({container:host.current,center:[0,12],zoom:compact?0:1.25,minZoom:-2,maxZoom:10,interactive:!compact,
        style:{version:8,sources:{world:{type:'geojson',data:'/data/world_outline.geojson'}},layers:[
          {id:'ocean',type:'background',paint:{'background-color':'#e8eef0'}},
          {id:'land',type:'fill',source:'world',paint:{'fill-color':'#fafbf9'}},
          {id:'borders',type:'line',source:'world',paint:{'line-color':'#b5c1c1','line-width':0.65}}
        ]}});
    }catch {setError('The map could not start. Results remain available in the table.');return;}
    map.current=instance;
    if(!compact)instance.addControl(new maplibregl.NavigationControl({showCompass:false}),'top-right');
    const bounds=()=>{const b=instance.getBounds();callbacks.current.onBounds([b.getWest(),b.getSouth(),b.getEast(),b.getNorth()]);};
    instance.on('load',()=>{
      instance.addSource('cells',{type:'geojson',data:{type:'FeatureCollection',features:[]}});
      instance.addLayer({id:'cells',type:'fill',source:'cells',paint:{'fill-color':['get','color'],'fill-opacity':['get','opacity']}});
      instance.addLayer({id:'cell-borders',type:'line',source:'cells',minzoom:4,paint:{'line-color':'#ffffff','line-width':1,'line-opacity':.7}});
      const popup=new maplibregl.Popup({closeButton:false,closeOnClick:false});
      instance.on('click','cells',e=>{const key=e.features?.[0]?.properties?.cell;if(key)callbacks.current.onSelect(key);});
      instance.on('mousemove','cells',e=>{
        const properties=e.features?.[0]?.properties;
        if(properties)popup.setLngLat(e.lngLat).setText(`${properties.cell}: ${properties.label}`).addTo(instance);
      });
      instance.on('mouseenter','cells',()=>{instance.getCanvas().style.cursor='pointer';});
      instance.on('mouseleave','cells',()=>{instance.getCanvas().style.cursor='';popup.remove();});
      instance.fitBounds([[-180,-60],[180,80]],{padding:12,maxZoom:1.25,duration:0});
      setReady(true);bounds();
    });
    instance.on('moveend',bounds);
    instance.on('error',()=>setError('A map layer could not be loaded.'));
    const observer=new ResizeObserver(()=>instance.resize());observer.observe(host.current);
    return()=>{observer.disconnect();instance.remove();map.current=null;};
  },[]);
  useEffect(()=>{
    if(!ready||!map.current)return;
    const source=map.current.getSource('cells') as maplibregl.GeoJSONSource;
    source.setData({type:'FeatureCollection',features:cells.map(c=>{
      const [lat,lon]=c.cell.split(',').map(Number);
      return {type:'Feature' as const,properties:{cell:c.cell,color:c.color,opacity:c.opacity,label:c.label},geometry:{type:'Polygon' as const,coordinates:[[[lon-.25,lat-.25],[lon+.25,lat-.25],[lon+.25,lat+.25],[lon-.25,lat+.25],[lon-.25,lat-.25]]]}};
    })});
  },[cells,ready]);
  function fitCoverage(){
    if(coverageBounds)map.current?.fitBounds([[coverageBounds[0],coverageBounds[1]],[coverageBounds[2],coverageBounds[3]]],{padding:45,maxZoom:7,duration:0});
  }
  useEffect(()=>{if(ready)fitCoverage();},[ready,coverageBounds]);
  return <div className="atlas-map"><div ref={host} className="atlas-map-canvas" aria-label="Crop cells and historical event frequencies"/>
    {!compact&&<button className="atlas-home" title="World view" aria-label="World view" onClick={()=>map.current?.fitBounds([[-180,-60],[180,80]],{padding:12,maxZoom:1.25})}><Globe2 size={19}/></button>}
    {!compact&&coverageBounds&&<button className="atlas-coverage-button" title="Calculated coverage" aria-label="Calculated coverage" onClick={fitCoverage}><LocateFixed size={19}/></button>}
    {error&&<p className="atlas-map-error" role="alert">{error}</p>}
    <span className="atlas-map-caption">0.5° cells · Crop inventory</span>
  </div>;
}
