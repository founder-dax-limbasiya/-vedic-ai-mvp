import assert from "node:assert/strict";
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, resolve, sep } from "node:path";
import { chromium } from "playwright";

const root=resolve("web");
const mime={
  ".html":"text/html; charset=utf-8",
  ".js":"text/javascript; charset=utf-8",
  ".css":"text/css; charset=utf-8",
  ".json":"application/json; charset=utf-8",
  ".wasm":"application/wasm",
  ".svg":"image/svg+xml",
  ".png":"image/png"
};
const server=createServer(async(req,res)=>{
  try{
    const url=new URL(req.url,"http://127.0.0.1");
    if(url.pathname==="/engine-smoke.html"){
      res.writeHead(200,{"Content-Type":"text/html; charset=utf-8","Cache-Control":"no-store"});
      res.end("<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'></head><body>Jyoti engine smoke test</body></html>");
      return;
    }
    const pathname=decodeURIComponent(url.pathname==="/"?"/index.html":url.pathname);
    const file=resolve(root,`.${pathname}`);
    if(file!==root && !file.startsWith(root+sep)){res.writeHead(403).end();return;}
    const data=await readFile(file);
    res.writeHead(200,{"Content-Type":mime[extname(file)]||"application/octet-stream","Cache-Control":"no-store"});
    res.end(data);
  }catch{
    res.writeHead(404).end("Not found");
  }
});
await new Promise(resolveListen=>server.listen(0,"127.0.0.1",resolveListen));
const address=server.address();
const origin=`http://127.0.0.1:${address.port}`;
const browser=await chromium.launch({headless:true});
try{
  const page=await browser.newPage();
  const externalRequests=[];
  page.on("request",request=>{
    if(!request.url().startsWith(origin)) externalRequests.push(request.url());
  });
  await page.goto(`${origin}/engine-smoke.html`,{waitUntil:"domcontentloaded"});
  const result=await page.evaluate(async()=>{
    const engine=await import("./engine.bundle.js");
    const ready=await engine.isClientEngineReady();
    const jamnagarTimezone=engine.timezoneAt(22.4707,70.0577);
    const mumbaiTimezone=engine.timezoneAt(19.0760,72.8777);
    const chart=await engine.calculateBirthChart({
      birth_date:"1990-03-15",
      birth_time:"10:30",
      timezone:"Asia/Kolkata",
      latitude:19.0760,
      longitude:72.8777,
      ayanamsa:"lahiri"
    });
    const daily=await engine.calculateDailyPanchanga({
      calendar_date:"2026-03-08",
      timezone:"Asia/Kolkata",
      latitude:22.4707,
      longitude:70.0577,
      ayanamsa:"lahiri"
    });
    const transitions=await engine.calculatePanchangaTransitions({
      calendar_date:"2026-03-08",
      timezone:"Asia/Kolkata",
      latitude:22.4707,
      longitude:70.0577,
      ayanamsa:"lahiri"
    });
    return {
      ready,
      jamnagarTimezone,
      mumbaiTimezone,
      birth:chart.birth,
      ayanamsa:chart.ayanamsa_degrees,
      ascendant:chart.ascendant,
      planets:chart.planets,
      houses:chart.houses,
      dasha:chart.vimshottari_mahadashas,
      divisional:chart.divisional_charts,
      birthPanchanga:chart.birth_panchanga,
      daily,
      transitions
    };
  });
  const reference=JSON.parse(await readFile("tests/python_reference.json","utf8"));
  const pythonChart=reference.chart;
  const circularDifference=(a,b)=>{
    const diff=((a-b)%360+360)%360;
    return Math.min(diff,360-diff);
  };
  const localMillis=value=>{
    if(!value) return null;
    return Date.parse(/[zZ]|[+-][0-9]{2}:[0-9]{2}$/.test(value)?value:`${value}Z`);
  };
  const assertNearTime=(actual,expected,label,toleranceSeconds=180)=>{
    assert.ok(actual && expected, `${label}: missing timestamp`);
    const delta=Math.abs(localMillis(actual)-localMillis(expected))/1000;
    assert.ok(delta<=toleranceSeconds,`${label}: difference ${delta.toFixed(1)} seconds exceeds ${toleranceSeconds}`);
  };
  const referencePlanets=new Map(pythonChart.planets.map(p=>[p.planet,p]));
  for(const actual of result.planets){
    const expected=referencePlanets.get(actual.planet);
    assert.ok(expected,`Missing Python reference for ${actual.planet}`);
    assert.equal(actual.sign,expected.sign,`${actual.planet} sign parity`);
    assert.equal(actual.nakshatra,expected.nakshatra,`${actual.planet} nakshatra parity`);
    assert.equal(actual.pada,expected.pada,`${actual.planet} pada parity`);
    assert.equal(actual.retrograde,expected.retrograde,`${actual.planet} retrograde parity`);
    assert.ok(circularDifference(actual.longitude,expected.longitude)<=0.02,`${actual.planet} longitude parity`);
  }
  assert.equal(result.ascendant.sign,pythonChart.ascendant.sign,"Ascendant sign parity");
  assert.ok(circularDifference(result.ascendant.longitude,pythonChart.ascendant.longitude)<=0.02,"Ascendant longitude parity");
  assert.equal(result.houses.length,pythonChart.houses.length);
  assert.deepEqual(result.houses,pythonChart.houses,"Whole-sign house parity");
  assert.deepEqual(
    result.dasha.map(x=>x.lord),
    pythonChart.vimshottari_mahadashas.map(x=>x.lord),
    "Vimshottari sequence parity"
  );
  assert.equal(Object.keys(result.divisional).length,Object.keys(pythonChart.divisional_charts).length);
  for(const [code,actual] of Object.entries(result.divisional)){
    const expected=pythonChart.divisional_charts[code];
    assert.ok(expected,`${code} Python reference exists`);
    assert.equal(actual.ascendant_sign,expected.ascendant_sign,`${code} ascendant parity`);
    assert.deepEqual(
      actual.planets.map(x=>({planet:x.planet,sign:x.sign})),
      expected.planets,
      `${code} planetary sign parity`
    );
  }
  for(const key of ["vara","tithi_number","tithi_name","nakshatra","yoga_number","yoga_name","karana_number","karana_name"]){
    assert.equal(result.birthPanchanga[key],pythonChart.birth_panchanga[key],`Birth Panchanga ${key} parity`);
  }
  assertNearTime(result.birthPanchanga.sunrise_local,pythonChart.birth_panchanga.sunrise_local,"Birth sunrise");
  assertNearTime(result.birthPanchanga.sunset_local,pythonChart.birth_panchanga.sunset_local,"Birth sunset");
  const pythonDaily=reference.daily_panchanga;
  for(const key of ["vara","tithi_number","tithi_name","nakshatra","yoga_number","yoga_name","karana_number","karana_name"]){
    assert.equal(result.daily[key],pythonDaily[key],`Daily Panchanga ${key} parity`);
  }
  assertNearTime(result.daily.sunrise_local,pythonDaily.sunrise_local,"Daily sunrise");
  assertNearTime(result.daily.sunset_local,pythonDaily.sunset_local,"Daily sunset");
  const pythonTransitions=reference.transitions.transitions;
  assert.equal(result.transitions.transitions.length,pythonTransitions.length,"Transition count parity");
  for(let i=0;i<pythonTransitions.length;i++){
    const actual=result.transitions.transitions[i],expected=pythonTransitions[i];
    assert.equal(actual.element,expected.element,`Transition ${i} element`);
    assert.equal(actual.from_value,expected.from_value,`Transition ${i} from value`);
    assert.equal(actual.to_value,expected.to_value,`Transition ${i} to value`);
    assertNearTime(actual.transition_time_local,expected.transition_time_local,`Transition ${i} time`,180);
  }
  assert.equal(result.ready.ready,true);
  assert.equal(result.jamnagarTimezone,"Asia/Kolkata");
  assert.equal(result.mumbaiTimezone,"Asia/Kolkata");
  assert.ok(result.ready.version);
  assert.equal(result.birth.utc_datetime,"1990-03-15T05:00:00+00:00");
  assert.ok(result.ayanamsa>20 && result.ayanamsa<30);
  assert.equal(result.planets.length,9);
  assert.equal(result.houses.length,12);
  assert.equal(result.dasha.length,9);
  assert.equal(Object.keys(result.divisional).length,16);
  assert.ok(result.ascendant.sign);
  assert.ok(result.birthPanchanga.tithi_name);
  assert.ok(result.birthPanchanga.sunrise_local);
  assert.ok(result.daily.sunrise_local);
  assert.ok(result.daily.sunset_local);
  assert.ok(result.transitions.next_sunrise_local);
  assert.ok(Array.isArray(result.transitions.transitions));
  assert.ok(result.planets.every(p=>p.longitude>=0 && p.longitude<360));
  assert.deepEqual(externalRequests,[]);
  console.log(JSON.stringify({
    wasm:result.ready,
    coordinate_timezones:{jamnagar:result.jamnagarTimezone,mumbai:result.mumbaiTimezone},
    ayanamsa:result.ayanamsa,
    ascendant:result.ascendant,
    planets:result.planets.map(p=>({planet:p.planet,sign:p.sign,longitude:p.longitude})),
    birth_panchanga:result.birthPanchanga,
    daily_panchanga:result.daily,
    transition_count:result.transitions.transitions.length,
    outbound_requests:externalRequests.length,
    parity:"passed against pinned Python engine",
    python_ayanamsa:pythonChart.ayanamsa_degrees,
    client_ayanamsa:result.ayanamsa,
    python_daily_sunrise:pythonDaily.sunrise_local,
    client_daily_sunrise:result.daily.sunrise_local
  },null,2));
}finally{
  await browser.close();
  await new Promise(resolveClose=>server.close(resolveClose));
}
