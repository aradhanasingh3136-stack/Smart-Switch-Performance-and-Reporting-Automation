import assert from 'node:assert/strict';
import fs from 'node:fs';
import {summarize,dailyCsv} from '../web/model.mjs';
const data=JSON.parse(fs.readFileSync(new URL('../web/data.json',import.meta.url),'utf8'));
const cases=JSON.parse(fs.readFileSync(0,'utf8'));
for(const {filters,expected} of cases){
  const result=summarize(data,filters),actual=result.total;
  for(const [key,value] of Object.entries(expected)){
    const description=`${JSON.stringify(filters)}: ${key}`;
    if(value===null)assert.equal(actual[key],null,description);
    else assert.ok(Math.abs(actual[key]-value)<=1e-5,`${description}: ${actual[key]} != ${value}`);
  }
  assert.equal(result.daily.reduce((n,d)=>n+d.commands,0),actual.commands,'Daily command counts reconcile');
  assert.equal(result.devices.reduce((n,d)=>n+d.commands,0),actual.commands,'Device counts reconcile');
  assert.equal(actual.failures.reduce((a,b)=>a+b,0),actual.commands-actual.successes,'Failure reasons reconcile');
  const csv=dailyCsv(result).trim().split('\r\n');
  assert.equal(csv.length,result.daily.length+1,'CSV exports every visible day');
}
console.log(`PASS: browser metrics match raw SQL facts for ${cases.length} selections, including incident, firmware, one-day and empty cases.`);
