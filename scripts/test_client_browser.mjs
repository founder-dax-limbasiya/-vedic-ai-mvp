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
  await page.goto(origin,{waitUntil:"domcontentloaded"});
  const result=await page.evaluate(async()=>{
    const engine=await import("./engine.bundle.js");
    const ready=await engine.isClientEngineReady();
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
  assert.equal(result.ready.ready,true);
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
    ayanamsa:result.ayanamsa,
    ascendant:result.ascendant,
    planets:result.planets.map(p=>({planet:p.planet,sign:p.sign,longitude:p.longitude})),
    birth_panchanga:result.birthPanchanga,
    daily_panchanga:result.daily,
    transition_count:result.transitions.transitions.length,
    outbound_requests:externalRequests.length
  },null,2));
}finally{
  await browser.close();
  await new Promise(resolveClose=>server.close(resolveClose));
}
