/**
 * Pure Vedic calculation rules ported from the pinned vedic-calc AGPL-3.0
 * implementation. Astronomical longitudes are supplied by the WASM adapter.
 * Keep this file free of browser APIs so it can be tested with Node.
 */
export const SIGNS = [
  "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
  "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
];

export const SIGN_LORDS = [
  "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
  "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"
];

export const NAKSHATRAS = [
  "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
  "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
  "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
  "Anuradha", "Jyeshtha", "Moola", "Purva Ashadha", "Uttara Ashadha",
  "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
  "Uttara Bhadrapada", "Revati"
];

export const VIMSOTTARI_ORDER = [
  "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"
];
export const VIMSOTTARI_YEARS = {
  Ketu: 7, Venus: 20, Sun: 6, Moon: 10, Mars: 7,
  Rahu: 18, Jupiter: 16, Saturn: 19, Mercury: 17
};
export const VARGA_DIVISIONS = [2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60];
export const VARGA_NAMES = {
  1:"Rasi", 2:"Hora", 3:"Drekkana", 4:"Chaturthamsa", 7:"Saptamsa",
  9:"Navamsa", 10:"Dasamsa", 12:"Dwadasamsa", 16:"Shodasamsa",
  20:"Vimsamsa", 24:"Chaturvimsamsa", 27:"Bhamsa", 30:"Trimsamsa",
  40:"Khavedamsa", 45:"Akshavedamsa", 60:"Shashtiamsa"
};

export const TITHI_NAMES = [
  "Shukla Pratipada","Shukla Dwitiya","Shukla Tritiya","Shukla Chaturthi",
  "Shukla Panchami","Shukla Shashthi","Shukla Saptami","Shukla Ashtami",
  "Shukla Navami","Shukla Dashami","Shukla Ekadashi","Shukla Dwadashi",
  "Shukla Trayodashi","Shukla Chaturdashi","Purnima","Krishna Pratipada",
  "Krishna Dwitiya","Krishna Tritiya","Krishna Chaturthi","Krishna Panchami",
  "Krishna Shashthi","Krishna Saptami","Krishna Ashtami","Krishna Navami",
  "Krishna Dashami","Krishna Ekadashi","Krishna Dwadashi","Krishna Trayodashi",
  "Krishna Chaturdashi","Amavasya"
];
export const YOGA_NAMES = [
  "Vishkambha","Priti","Ayushman","Saubhagya","Shobhana","Atiganda",
  "Sukarma","Dhriti","Shoola","Ganda","Vriddhi","Dhruva","Vyaghata",
  "Harshana","Vajra","Siddhi","Vyatipata","Variyan","Parigha","Shiva",
  "Siddha","Sadhya","Shubha","Shukla","Brahma","Indra","Vaidhriti"
];
const REPEATING_KARANAS = ["Bava","Balava","Kaulava","Taitila","Garaja","Vanija","Vishti"];
export const KARANA_NAMES = Array.from({length:60},(_,i) => {
  const n=i+1;
  if (n===1) return "Kimstughna";
  if (n>=58) return ({58:"Shakuni",59:"Chatushpada",60:"Nagava"})[n];
  return REPEATING_KARANAS[(n-2)%7];
});
export const VARA_NAMES = [
  "Monday (Somavara)", "Tuesday (Mangalavara)", "Wednesday (Budhavara)",
  "Thursday (Guruvara)", "Friday (Shukravara)", "Saturday (Shanivara)",
  "Sunday (Ravivara)"
];

export const NAKSHATRA_LORDS = Array.from({length:27},(_,i)=>VIMSOTTARI_ORDER[i%9]);
export const NAKSHATRA_SPAN = 360/27;
export const PADA_SPAN = 360/108;

export function wrap360(value) {
  return ((value % 360) + 360) % 360;
}
export function roundTo(value, places=4) {
  const factor=10**places;
  return Math.round((value + Number.EPSILON)*factor)/factor;
}
export function signIndex(longitude) {
  return Math.min(11,Math.floor(wrap360(longitude)/30));
}
export function nakshatraInfo(longitude) {
  const lon=wrap360(longitude);
  const index=Math.min(26,Math.floor(lon/NAKSHATRA_SPAN));
  const within=lon%NAKSHATRA_SPAN;
  return {
    nakshatra: NAKSHATRAS[index],
    pada: Math.min(4,Math.floor(within/PADA_SPAN)+1),
    nakshatra_lord: NAKSHATRA_LORDS[index],
    degree_in_nakshatra: roundTo(within,4)
  };
}
export function positionPayload(name, longitude, retrograde=false) {
  const lon=wrap360(longitude);
  const index=signIndex(lon);
  const nak=nakshatraInfo(lon);
  return {
    planet:name,
    longitude:roundTo(lon,6),
    sign:SIGNS[index],
    degree_in_sign:roundTo(lon%30,4),
    nakshatra:nak.nakshatra,
    pada:nak.pada,
    nakshatra_lord:nak.nakshatra_lord,
    retrograde:Boolean(retrograde)
  };
}
function countSigns(start,count) { return ((start+count)%12+12)%12; }
function isOdd(signIndexZeroBased) { return ((signIndexZeroBased+1)%2)===1; }
function signElement(signIndexZeroBased) { return ["fire","earth","air","water"][signIndexZeroBased%4]; }
function signModality(signIndexZeroBased) { return ["movable","fixed","dual"][signIndexZeroBased%3]; }

const ELEMENT_STARTS = {
  9:{fire:0,earth:9,air:6,water:3},
  27:{fire:0,earth:3,air:6,water:9}
};
const MODALITY_STARTS = {
  16:{movable:0,fixed:4,dual:8},
  20:{movable:0,fixed:8,dual:4},
  45:{movable:0,fixed:4,dual:8}
};
const ODD_EVEN_STARTS = {
  24:[4,3],
  40:[0,6]
};
export function divisionalSign(signIndexZeroBased, degree, division) {
  if (!Number.isInteger(division) || division<1 || division>60) {
    throw new RangeError("Division must be an integer from 1 to 60");
  }
  if (division===1) return signIndexZeroBased;
  if (division===2) {
    const first=degree<15;
    return isOdd(signIndexZeroBased) ? (first?4:3) : (first?3:4);
  }
  if (division===3) return countSigns(signIndexZeroBased,[0,4,8][Math.min(2,Math.floor(degree/10))]);
  if (division===30) {
    const odd=isOdd(signIndexZeroBased);
    const limits=odd?[5,10,18,25]:[5,12,20,25];
    const signs=odd?[0,10,8,2,6]:[1,5,11,9,7];
    const i=limits.findIndex(limit=>degree<limit);
    return signs[i<0?4:i];
  }
  const part=Math.min(division-1,Math.floor(degree/(30/division)));
  if (division===4) return countSigns(signIndexZeroBased,part*3);
  if (division===7) return countSigns(signIndexZeroBased,(isOdd(signIndexZeroBased)?0:6)+part);
  if (ELEMENT_STARTS[division]) return countSigns(ELEMENT_STARTS[division][signElement(signIndexZeroBased)],part);
  if (division===10) return countSigns(signIndexZeroBased,(isOdd(signIndexZeroBased)?0:8)+part);
  if (division===12) return countSigns(signIndexZeroBased,part);
  if (MODALITY_STARTS[division]) return countSigns(MODALITY_STARTS[division][signModality(signIndexZeroBased)],part);
  if (ODD_EVEN_STARTS[division]) return countSigns(isOdd(signIndexZeroBased)?ODD_EVEN_STARTS[division][0]:ODD_EVEN_STARTS[division][1],part);
  return countSigns(signIndexZeroBased,part);
}
export function buildDivisionalCharts(planets, ascendant) {
  const charts={};
  const divisions=[1,...VARGA_DIVISIONS];
  for (const division of divisions) {
    const planetRows=planets.map(planet=>({
      planet:planet.planet,
      sign:SIGNS[divisionalSign(signIndex(planet.longitude),planet.degree_in_sign,division)]
    }));
    charts[`D${division}`]={
      division,
      name:VARGA_NAMES[division] || `D${division}`,
      ascendant_sign:SIGNS[divisionalSign(signIndex(ascendant.longitude),ascendant.degree_in_sign,division)],
      planets:planetRows
    };
  }
  return charts;
}
export function panchangaFromLongitudes(sunLongitude, moonLongitude, calendarDate) {
  const diff=wrap360(moonLongitude-sunLongitude);
  const tithi=Math.min(30,Math.floor(diff/12)+1);
  const nak=Math.min(27,Math.floor(wrap360(moonLongitude)/NAKSHATRA_SPAN)+1);
  const yoga=Math.min(27,Math.floor(wrap360(moonLongitude+sunLongitude)/NAKSHATRA_SPAN)+1);
  const karana=Math.min(60,Math.floor(diff/6)+1);
  const [year,month,day]=calendarDate.split("-").map(Number);
  const weekday=(new Date(Date.UTC(year,month-1,day)).getUTCDay()+6)%7;
  return {
    vara:VARA_NAMES[weekday],
    tithi_number:tithi,
    tithi_name:TITHI_NAMES[tithi-1],
    nakshatra:NAKSHATRAS[nak-1],
    yoga_number:yoga,
    yoga_name:YOGA_NAMES[yoga-1],
    karana_number:karana,
    karana_name:KARANA_NAMES[karana-1]
  };
}
export function calculateMahadashas(moonLongitude,birthLocalIso) {
  const nak=nakshatraInfo(moonLongitude);
  const startIndex=VIMSOTTARI_ORDER.indexOf(nak.nakshatra_lord);
  const sequence=[...VIMSOTTARI_ORDER.slice(startIndex),...VIMSOTTARI_ORDER.slice(0,startIndex)];
  const [datePart,timePart="00:00:00"]=birthLocalIso.split("T");
  const [y,m,d]=datePart.split("-").map(Number);
  const [hh=0,mm=0,ss=0]=timePart.split(":").map(Number);
  const birthMs=Date.UTC(y,m-1,d,hh,mm,ss);
  const elapsedYears=VIMSOTTARI_YEARS[nak.nakshatra_lord]*(nak.degree_in_nakshatra/NAKSHATRA_SPAN);
  let currentMs=birthMs-elapsedYears*365.25*86400000;
  return sequence.map(lord=>{
    const startMs=currentMs;
    currentMs+=VIMSOTTARI_YEARS[lord]*365.25*86400000;
    return {
      lord,
      start_local:new Date(startMs).toISOString().replace(/\.000Z$/,"").replace(/Z$/,""),
      end_local:new Date(currentMs).toISOString().replace(/\.000Z$/,"").replace(/Z$/,""),
      duration_years:VIMSOTTARI_YEARS[lord]
    };
  });
}
export function panchangaIndexValues(sunLongitude,moonLongitude) {
  const diff=wrap360(moonLongitude-sunLongitude);
  return {
    tithi:Math.min(30,Math.floor(diff/12)+1),
    nakshatra:Math.min(27,Math.floor(wrap360(moonLongitude)/NAKSHATRA_SPAN)+1),
    yoga:Math.min(27,Math.floor(wrap360(moonLongitude+sunLongitude)/NAKSHATRA_SPAN)+1),
    karana:Math.min(60,Math.floor(diff/6)+1)
  };
}
export function findPanchangaTransitions(sunriseJd,nextSunriseJd,getLongitudes,stepDays=0.02083,precisionDays=1e-6) {
  const config=[
    ["tithi",v=>v.tithi,TITHI_NAMES],
    ["nakshatra",v=>v.nakshatra,NAKSHATRAS],
    ["yoga",v=>v.yoga,YOGA_NAMES],
    ["karana",v=>v.karana,KARANA_NAMES]
  ];
  const transitions=[];
  for (const [element,selector,names] of config) {
    let jd=sunriseJd;
    let previous=selector(panchangaIndexValues(...getLongitudes(jd)));
    while (jd<nextSunriseJd) {
      const next=Math.min(jd+stepDays,nextSunriseJd);
      const current=selector(panchangaIndexValues(...getLongitudes(next)));
      if (current!==previous) {
        let low=jd,high=next;
        while (high-low>precisionDays) {
          const mid=(low+high)/2;
          if (selector(panchangaIndexValues(...getLongitudes(mid)))===previous) low=mid;
          else high=mid;
        }
        transitions.push({element,from_value:previous,to_value:current,from_name:names[previous-1],to_name:names[current-1],transition_jd:high});
        previous=current;
      }
      jd=next;
    }
  }
  return transitions.sort((a,b)=>a.transition_jd-b.transition_jd);
}
