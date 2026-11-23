import test from "node:test";
import assert from "node:assert/strict";
import {
  wrap360, signIndex, nakshatraInfo, divisionalSign,
  panchangaFromLongitudes, calculateMahadashas,
  buildDivisionalCharts, positionPayload
} from "../web/engine/vedic-core.js";

test("wrap360 normalizes negative and overflowing longitudes",()=>{
  assert.equal(wrap360(-1),359);
  assert.equal(wrap360(361),1);
  assert.equal(wrap360(720),0);
});

test("sign and nakshatra boundaries are stable",()=>{
  assert.equal(signIndex(0),0);
  assert.equal(signIndex(30),1);
  assert.equal(signIndex(359.999),11);
  assert.equal(nakshatraInfo(0).nakshatra,"Ashwini");
  assert.equal(nakshatraInfo(0).pada,1);
  assert.equal(nakshatraInfo(13.34).nakshatra,"Bharani");
  assert.equal(nakshatraInfo(40).nakshatra,"Rohini");
  assert.equal(nakshatraInfo(40).pada,1);
});

test("Parashari special varga rules match the source implementation",()=>{
  // Odd Aries: first/second Hora are Leo/Cancer.
  assert.equal(divisionalSign(0,14.999,2),4);
  assert.equal(divisionalSign(0,15,2),3);
  // Even Taurus: first/second Hora are Cancer/Leo.
  assert.equal(divisionalSign(1,14.999,2),3);
  assert.equal(divisionalSign(1,15,2),4);
  // Drekkana: same, fifth, ninth.
  assert.deepEqual([0,10,20].map(d=>divisionalSign(0,d,3)),[0,4,8]);
  // Odd-sign D30 unequal segments.
  assert.deepEqual([0,5,10,18,25].map(d=>divisionalSign(0,d,30)),[0,10,8,2,6]);
});

test("Panchanga formulas return the expected index names",()=>{
  const result=panchangaFromLongitudes(0,180,"1990-03-15");
  assert.equal(result.tithi_number,16);
  assert.equal(result.tithi_name,"Krishna Pratipada");
  assert.equal(result.nakshatra,"Chitra");
  assert.equal(result.yoga_name,"Harshana");
  assert.equal(result.karana_number,31);
  assert.equal(result.karana_name,"Balava");
  assert.equal(result.vara,"Thursday (Guruvara)");
});

test("Vimshottari starts from Moon's nakshatra lord and returns nine major periods",()=>{
  const result=calculateMahadashas(45,"1990-03-15T10:30:00");
  assert.equal(result.length,9);
  assert.equal(result[0].lord,"Moon");
  assert.equal(result[1].lord,"Mars");
  assert.equal(result[8].lord,"Sun");
  assert.ok(Date.parse(result[0].start_local)<Date.parse("1990-03-15T10:30:00"));
  assert.equal(result[0].duration_years,10);
});

test("the requested sixteen vargas contain all nine planets",()=>{
  const planets=["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]
    .map((name,i)=>positionPayload(name,i*31.1,i>5));
  const asc=positionPayload("ASCENDANT",91.2345,false);
  const charts=buildDivisionalCharts(planets,asc);
  assert.equal(Object.keys(charts).length,16);
  assert.equal(charts.D1.planets.length,9);
  assert.equal(charts.D9.division,9);
  assert.equal(charts.D60.division,60);
  assert.equal(charts.D1.ascendant_sign,"Cancer");
});
