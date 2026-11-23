import {
  SwissEphemeris,
  Planet,
  LunarPoint,
  HouseSystem,
  SiderealMode,
  CalculationFlag
} from "@swisseph/browser";
import {
  SIGNS, SIGN_LORDS, VARGA_DIVISIONS,
  buildDivisionalCharts, calculateMahadashas,
  findPanchangaTransitions, panchangaFromLongitudes,
  positionPayload, roundTo, wrap360
} from "./vedic-core.js";

const AYANAMSA_MODES = {
  lahiri: SiderealMode.Lahiri,
  raman: SiderealMode.Raman,
  kp: SiderealMode.Krishnamurti,
  true_chitrapaksha: SiderealMode.TrueCitra
};
const PLANETS = [
  ["Sun",Planet.Sun],
  ["Moon",Planet.Moon],
  ["Mars",Planet.Mars],
  ["Mercury",Planet.Mercury],
  ["Jupiter",Planet.Jupiter],
  ["Venus",Planet.Venus],
  ["Saturn",Planet.Saturn],
  ["Rahu",LunarPoint.MeanNode]
];
const MoshierFlags = CalculationFlag.MoshierEphemeris | CalculationFlag.Speed;
let enginePromise;

function getParts(epochMs,timeZone) {
  const fmt=new Intl.DateTimeFormat("en-GB",{
    timeZone,year:"numeric",month:"2-digit",day:"2-digit",
    hour:"2-digit",minute:"2-digit",second:"2-digit",hourCycle:"h23"
  });
  const parts=Object.fromEntries(fmt.formatToParts(new Date(epochMs))
    .filter(p=>p.type!=="literal").map(p=>[p.type,Number(p.value)]));
  return {year:parts.year,month:parts.month,day:parts.day,hour:parts.hour,minute:parts.minute,second:parts.second};
}
function sameParts(a,b) {
  return ["year","month","day","hour","minute","second"].every(k=>a[k]===b[k]);
}
function offsetAt(epochMs,timeZone) {
  const p=getParts(epochMs,timeZone);
  const utcAsLocal=Date.UTC(p.year,p.month-1,p.day,p.hour,p.minute,p.second);
  return (utcAsLocal-Math.floor(epochMs/1000)*1000)/3600000;
}
function resolveLocalTime(date,time,timeZone,fold=null) {
  if (!/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(date) || !/^([01][0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?$/.test(time)) {
    throw new Error("Enter a valid birth date and local time.");
  }
  const [year,month,day]=date.split("-").map(Number);
  const [hour,minute,second=0]=time.split(":").map(Number);
  const target={year,month,day,hour,minute,second};
  const wallMs=Date.UTC(year,month-1,day,hour,minute,second);
  const offsets=new Set();
  for(let h=-36;h<=36;h+=6) offsets.add(offsetAt(wallMs+h*3600000,timeZone));
  const candidates=[];
  for(const offset of offsets){
    const candidate=wallMs-offset*3600000;
    if(sameParts(getParts(candidate,timeZone),target)) candidates.push(candidate);
  }
  const unique=[...new Set(candidates)].sort((a,b)=>a-b);
  if(!unique.length) throw new Error("That local time did not occur because the clocks moved forward. Check the birth time.");
  if(unique.length>1 && fold===null) throw new Error("That local time occurred twice because the clocks moved backward. Choose the first or second occurrence.");
  const selected=unique[Math.min(Number(fold??0),unique.length-1)];
  return {epochMs:selected,offsetHours:offsetAt(selected,timeZone)};
}
function isoLocal(epochMs,timeZone) {
  const p=getParts(epochMs,timeZone);
  return `${String(p.year).padStart(4,"0")}-${String(p.month).padStart(2,"0")}-${String(p.day).padStart(2,"0")}T${String(p.hour).padStart(2,"0")}:${String(p.minute).padStart(2,"0")}:${String(p.second).padStart(2,"0")}`;
}
function dateOnly(epochMs,timeZone) {
  const p=getParts(epochMs,timeZone);
  return `${String(p.year).padStart(4,"0")}-${String(p.month).padStart(2,"0")}-${String(p.day).padStart(2,"0")}`;
}
function shiftDate(date,days) {
  const [y,m,d]=date.split("-").map(Number);
  const shifted=new Date(Date.UTC(y,m-1,d+days));
  return `${shifted.getUTCFullYear()}-${String(shifted.getUTCMonth()+1).padStart(2,"0")}-${String(shifted.getUTCDate()).padStart(2,"0")}`;
}
function julianDay(swe,epochMs) {
  return swe.dateToJulianDay(new Date(epochMs));
}
function epochFromJd(jd) {
  return (jd-2440587.5)*86400000;
}
function makeLongitudeReader(swe,ayanamsaDegrees) {
  return (jd,body) => {
    const raw=swe.calculatePosition(jd,body,MoshierFlags);
    return {
      longitude:wrap360(raw.longitude-ayanamsaDegrees),
      speed:raw.longitudeSpeed,
      latitude:raw.latitude,
      distance:raw.distance
    };
  };
}
function solarApparentAltitude(swe,epochMs,latitude,longitude) {
  const jd=julianDay(swe,epochMs);
  const sun=swe.calculatePosition(jd,Planet.Sun,MoshierFlags);
  return swe.horizontalCoordinates(
    jd,{longitude,latitude,altitude:0},
    [sun.longitude,sun.latitude,sun.distance],false
  ).apparentAltitude;
}
function findCrossing(swe,startMs,endMs,latitude,longitude,rising) {
  const target=-0.26667; // standard apparent centre altitude for upper-limb sunrise/sunset
  const step=5*60*1000;
  let previousMs=startMs;
  let previous=solarApparentAltitude(swe,previousMs,latitude,longitude)-target;
  let low=null,high=null;
  for(let ms=startMs+step;ms<=endMs+step;ms+=step){
    const currentMs=Math.min(ms,endMs);
    const current=solarApparentAltitude(swe,currentMs,latitude,longitude)-target;
    if((rising && previous<0 && current>=0)||(!rising && previous>=0 && current<0)){
      low=previousMs;high=currentMs;break;
    }
    previousMs=currentMs;previous=current;
    if(currentMs===endMs) break;
  }
  if(low===null) return null;
  while(high-low>1000){
    const mid=Math.floor((low+high)/2);
    const value=solarApparentAltitude(swe,mid,latitude,longitude)-target;
    if((rising && value>=0)||(!rising && value<0)) high=mid;
    else low=mid;
  }
  return high;
}
function solarEventsForLocalDate(swe,date,timeZone,latitude,longitude) {
  const start=resolveLocalTime(date,"00:00:00",timeZone).epochMs;
  const end=resolveLocalTime(shiftDate(date,1),"00:00:00",timeZone).epochMs;
  const sunrise=findCrossing(swe,start,end,latitude,longitude,true);
  const sunset=findCrossing(swe,start,end,latitude,longitude,false);
  return {
    sunriseMs:sunrise,
    sunsetMs:sunset,
    sunriseJd:sunrise===null?null:julianDay(swe,sunrise),
    sunsetJd:sunset===null?null:julianDay(swe,sunset)
  };
}
async function createEngine() {
  const swe=new SwissEphemeris();
  await swe.init(new URL("./swisseph.wasm",import.meta.url).href);
  return swe;
}
async function getEngine() {
  if(!enginePromise) enginePromise=createEngine().catch(error=>{enginePromise=null;throw error;});
  return enginePromise;
}
function astronomyFor(swe,epochMs,latitude,longitude,ayanamsa) {
  const jd=julianDay(swe,epochMs);
  swe.setSiderealMode(ayanamsa);
  const ayanamsaDegrees=swe.getAyanamsa(jd);
  const read=makeLongitudeReader(swe,ayanamsaDegrees);
  const positions={};
  for(const [name,body] of PLANETS){
    const result=read(jd,body);
    positions[name]=positionPayload(name,result.longitude,name==="Rahu"||result.speed<0);
  }
  positions.Ketu=positionPayload("Ketu",wrap360(positions.Rahu.longitude+180),true);
  const houses=swe.calculateHouses(jd,latitude,longitude,HouseSystem.WholeSign);
  const ascendant=positionPayload("Ascendant",wrap360(houses.ascendant-ayanamsaDegrees),false);
  const houseRows=Array.from({length:12},(_,i)=>{
    const signIndex=(Math.floor(ascendant.longitude/30)+i)%12;
    return {house:i+1,sign:SIGNS[signIndex],lord:SIGN_LORDS[signIndex]};
  });
  return {jd,ayanamsaDegrees,positions:Object.values(positions),ascendant,houses:houseRows,read};
}
function panchangaFor(swe,epochMs,latitude,longitude,timeZone,ayanamsa) {
  const day=dateOnly(epochMs,timeZone);
  const events=solarEventsForLocalDate(swe,day,timeZone,latitude,longitude);
  const calculationMs=events.sunriseMs??resolveLocalTime(day,"12:00:00",timeZone).epochMs;
  const jd=julianDay(swe,calculationMs);
  swe.setSiderealMode(ayanamsa);
  const aya=swe.getAyanamsa(jd);
  const read=makeLongitudeReader(swe,aya);
  const sun=read(jd,Planet.Sun).longitude;
  const moon=read(jd,Planet.Moon).longitude;
  return {
    date:day,
    ...panchangaFromLongitudes(sun,moon,day),
    sunrise_local:events.sunriseMs===null?null:isoLocal(events.sunriseMs,timeZone),
    sunset_local:events.sunsetMs===null?null:isoLocal(events.sunsetMs,timeZone),
    calculation_time:events.sunriseMs===null?"Local noon fallback":"Local sunrise",
    timezone:timeZone,latitude,longitude
  };
}

export async function calculateBirthChart(payload) {
  const swe=await getEngine();
  const timeZone=String(payload.timezone||"").trim();
  const birthDate=String(payload.birth_date||"");
  const birthTime=String(payload.birth_time||"");
  const location={latitude:Number(payload.latitude),longitude:Number(payload.longitude)};
  if(!Number.isFinite(location.latitude)||location.latitude < -90||location.latitude>90||
     !Number.isFinite(location.longitude)||location.longitude < -180||location.longitude>180) {
    throw new Error("Enter valid birthplace coordinates.");
  }
  const mode=AYANAMSA_MODES[payload.ayanamsa||"lahiri"];
  if(mode===undefined) throw new Error("Choose a supported ayanamsa.");
  const birth=resolveLocalTime(birthDate,birthTime,timeZone,payload.fold??null);
  const dateBirth=new Date(birth.epochMs);
  const todayLocal=dateOnly(Date.now(),timeZone);
  if(birthDate>todayLocal) throw new Error("Birth date cannot be in the future.");
  const astro=astronomyFor(swe,birth.epochMs,location.latitude,location.longitude,mode);
  const sunriseEvents=solarEventsForLocalDate(swe,birthDate,timeZone,location.latitude,location.longitude);
  const birthPanchanga=astro.read(astro.jd,Planet.Sun);
  const birthMoon=astro.read(astro.jd,Planet.Moon);
  const birthPanchangaValues=panchangaFromLongitudes(birthPanchanga.longitude,birthMoon.longitude,birthDate);
  return {
    calculation:{
      engine:"Swiss Ephemeris WebAssembly + Jyoti client engine",
      engine_commit:"browser-local-poc",
      ephemeris_by_planet:Object.fromEntries(PLANETS.map(([name])=>[name,"Moshier analytical ephemeris (WebAssembly)"])),
      retrograde_speed_flag:"SEFLG_SPEED",
      disclaimer:"All calculation runs on this device using the built-in Moshier ephemeris. Local-engine results must pass the project's parity suite before replacing the current API."
    },
    birth:{
      local_datetime:isoLocal(birth.epochMs,timeZone),
      utc_datetime:new Date(birth.epochMs).toISOString().replace(".000Z","+00:00").replace("Z","+00:00"),
      timezone:timeZone,
      utc_offset_hours:birth.offsetHours,
      latitude:location.latitude,
      longitude:location.longitude
    },
    settings:{ayanamsa:payload.ayanamsa||"lahiri",house_system:"Whole Sign"},
    ayanamsa_degrees:roundTo(astro.ayanamsaDegrees,6),
    ascendant:astro.ascendant,
    planets:astro.positions,
    houses:astro.houses,
    birth_panchanga:{
      ...birthPanchangaValues,
      sunrise_local:sunriseEvents.sunriseMs===null?null:isoLocal(sunriseEvents.sunriseMs,timeZone),
      sunset_local:sunriseEvents.sunsetMs===null?null:isoLocal(sunriseEvents.sunsetMs,timeZone),
      calculation_time:"Exact local birth time"
    },
    vimshottari_mahadashas:calculateMahadashas(astro.positions.find(p=>p.planet==="Moon").longitude,isoLocal(birth.epochMs,timeZone)),
    divisional_charts:buildDivisionalCharts(astro.positions,astro.ascendant)
  };
}

export async function calculateDailyPanchanga(payload) {
  const swe=await getEngine();
  const timeZone=String(payload.timezone||"").trim();
  const date=String(payload.calendar_date||"");
  const latitude=Number(payload.latitude),longitude=Number(payload.longitude);
  if(!Number.isFinite(latitude)||latitude < -90||latitude>90||!Number.isFinite(longitude)||longitude < -180||longitude>180) {
    throw new Error("Enter valid birthplace coordinates.");
  }
  const mode=AYANAMSA_MODES[payload.ayanamsa||"lahiri"];
  if(mode===undefined) throw new Error("Choose a supported ayanamsa.");
  const anchor=resolveLocalTime(date,"12:00:00",timeZone).epochMs;
  return panchangaFor(swe,anchor,latitude,longitude,timeZone,mode);
}

export async function calculatePanchangaTransitions(payload) {
  const swe=await getEngine();
  const timeZone=String(payload.timezone||"").trim();
  const date=String(payload.calendar_date||"");
  const latitude=Number(payload.latitude),longitude=Number(payload.longitude);
  const mode=AYANAMSA_MODES[payload.ayanamsa||"lahiri"];
  if(mode===undefined) throw new Error("Choose a supported ayanamsa.");
  const today=solarEventsForLocalDate(swe,date,timeZone,latitude,longitude);
  const tomorrow=solarEventsForLocalDate(swe,shiftDate(date,1),timeZone,latitude,longitude);
  if(today.sunriseJd===null||tomorrow.sunriseJd===null) {
    throw new Error("Sunrise-to-next-sunrise timings are unavailable at this location and date.");
  }
  swe.setSiderealMode(mode);
  const aya=swe.getAyanamsa(today.sunriseJd);
  const read=makeLongitudeReader(swe,aya);
  const transitions=findPanchangaTransitions(
    today.sunriseJd,tomorrow.sunriseJd,
    jd=>[read(jd,Planet.Sun).longitude,read(jd,Planet.Moon).longitude]
  ).map(item=>({
    element:item.element,
    from_value:item.from_value,
    to_value:item.to_value,
    from_name:item.from_name,
    to_name:item.to_name,
    transition_time_local:isoLocal(epochFromJd(item.transition_jd),timeZone)
  }));
  return {
    date,
    timezone:timeZone,
    latitude,longitude,
    sunrise_local:isoLocal(today.sunriseMs,timeZone),
    next_sunrise_local:isoLocal(tomorrow.sunriseMs,timeZone),
    ayanamsa:payload.ayanamsa||"lahiri",
    transitions,
    vara_note:"Vara changes at sunrise."
  };
}

export async function isClientEngineReady() {
  const swe=await getEngine();
  return {ready:true,version:swe.version()};
}
