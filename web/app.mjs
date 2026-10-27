import {summarize,dailyCsv} from './model.mjs';

const $=id=>document.getElementById(id);
const number=new Intl.NumberFormat('en-IN');
const num=(v,digits=0)=>v===null?'—':Number(v).toLocaleString('en-IN',{maximumFractionDigits:digits,minimumFractionDigits:digits});
const percent=v=>v===null?'—':`${(v*100).toFixed(2)}%`;
const shortDate=date=>new Date(date+'T12:00:00').toLocaleDateString('en-GB',{day:'numeric',month:'short'});
const safe=text=>String(text).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let data,result,page=0,sort='successRate',direction=1;
let filters={home:'',firmware:'',start:'',end:''};

function graph(series,{energy=false}={}) {
  if(!series.length)return '<p class="empty">No data in this selection. Try another date range or reset the filters.</p>';
  const w=720,h=230,l=42,r=15,t=18,b=36,plotW=w-l-r,plotH=h-t-b;
  const values=series.map(d=>energy?d.energy:d.successRate*100);
  const lo=energy?0:Math.max(0,Math.floor(Math.min(94,...values)-2));
  const hi=energy?Math.max(1,...series.map(d=>Math.max(d.energy,d.baseline)))*1.18:100;
  const x=i=>l+(series.length===1?plotW/2:i*plotW/(series.length-1));
  const y=v=>t+plotH*(1-(v-lo)/(hi-lo));
  let svg=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${energy?'Daily estimated consumption and assumed baseline':'Daily command success percentage'}"><title>${energy?'Daily estimated energy in kWh':'Daily command success with a 98% target'}</title>`;
  for(let i=0;i<5;i++){
    const value=lo+(hi-lo)*i/4,yy=y(value);
    svg+=`<line x1="${l}" y1="${yy}" x2="${w-r}" y2="${yy}" stroke="#edf0f4" stroke-dasharray="3 5"/><text x="${l-10}" y="${yy+3}" text-anchor="end" fill="#a0adbb" font-size="9">${energy?value.toFixed(0):value.toFixed(0)+'%'}</text>`;
  }
  const points=values.map((v,i)=>`${x(i)},${y(v)}`).join(' ');
  if(energy){
    svg+=`<polygon points="${x(0)},${y(0)} ${points} ${x(series.length-1)},${y(0)}" fill="#e8f5f0"/>`;
    svg+=`<polyline points="${series.map((d,i)=>`${x(i)},${y(d.baseline)}`).join(' ')}" fill="none" stroke="#b6c2cf" stroke-width="1.6" stroke-dasharray="5 5"/>`;
  }else if(lo<98){
    svg+=`<line x1="${l}" y1="${y(98)}" x2="${w-r}" y2="${y(98)}" stroke="#c6cfd8" stroke-dasharray="5 5"/>`;
  }
  svg+=`<polyline points="${points}" fill="none" stroke="#159883" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round"/>`;
  if(series.length===1)svg+=`<circle cx="${x(0)}" cy="${y(values[0])}" r="4" fill="#159883"/>`;
  const labels=[...new Set([0,Math.floor((series.length-1)/3),Math.floor(2*(series.length-1)/3),series.length-1])];
  for(const i of labels)svg+=`<text x="${x(i)}" y="${h-9}" text-anchor="middle" fill="#9aa8b6" font-size="9">${shortDate(series[i].date)}</text>`;
  svg+='</svg>';
  return svg;
}

function renderTable(){
  const query=$('search').value.trim().toLowerCase();
  const rows=result.devices.filter(d=>`${d.device_id} ${d.home_id} ${d.room} ${d.load_type}`.toLowerCase().includes(query));
  rows.sort((a,b)=>direction*(typeof a[sort]==='string'?a[sort].localeCompare(b[sort]):(a[sort]??-1)-(b[sort]??-1))||a.device_id.localeCompare(b.device_id));
  const pages=Math.max(1,Math.ceil(rows.length/8));page=Math.min(page,pages-1);
  $('device-rows').innerHTML=rows.slice(page*8,page*8+8).map(d=>`<tr><td>${safe(d.device_id)}</td><td>${safe(d.home_id)}<br><small>${safe(d.room)}</small></td><td>${num(d.commands)}</td><td><span class="rate ${d.successRate<data.targets.success?'low':''}">${percent(d.successRate)}</span></td><td>${percent(d.heartbeatRate)}</td><td>${num(d.energy,2)} <small>kWh</small></td></tr>`).join('')||'<tr><td colspan="6" class="empty">No devices match this selection.</td></tr>';
  $('table-count').textContent=rows.length?`${page*8+1}–${Math.min(page*8+8,rows.length)} of ${rows.length} devices`:'0 devices';
  $('page-number').textContent=`${page+1} / ${pages}`;
  $('previous').disabled=page===0;$('next').disabled=page>=pages-1;
  for(const button of document.querySelectorAll('[data-sort]')){
    const active=button.dataset.sort===sort;
    button.parentElement.setAttribute('aria-sort',active?(direction===1?'ascending':'descending'):'none');
    button.textContent=button.textContent.replace(/[↕↑↓]/g,'').trim()+' '+(active?(direction===1?'↑':'↓'):'↕');
  }
}

function update(){
  $('chart-tooltip').hidden=true;
  filters={home:$('home').value,firmware:$('firmware').value,start:$('start').value||data.dates[0],end:$('end').value||data.dates.at(-1)};
  const invalid=filters.start>filters.end;
  $('filter-error').hidden=!invalid;$('filter-error').textContent='Choose a start date that is on or before the end date.';
  result=summarize(data,filters);page=0;
  const s=result.total;
  const allHomes=filters.home||'All homes',allVersions=filters.firmware?`Firmware ${filters.firmware}`:'All firmware';
  $('selection').textContent=`${allHomes} · ${allVersions} · ${shortDate(filters.start)} – ${shortDate(filters.end)} 2026 · ${result.devices.length} devices`;
  $('success').textContent=percent(s.successRate);
  $('command-count').textContent=`${num(s.commands)} commands · ${num(s.successes)} successful`;
  $('success-status').textContent=s.successRate===null?'No commands':s.successRate>=data.targets.success?'✓ Target met · 98%':'↓ Below 98% target';
  $('success-status').classList.toggle('warning',s.successRate!==null&&s.successRate<data.targets.success);
  $('success-track').style.width=`${(s.successRate||0)*100}%`;
  $('latency').innerHTML=s.p95===null?'—':`${num(s.p95,1)} <small>ms</small>`;
  $('heartbeat').textContent=percent(s.heartbeatRate);
  $('heartbeat-count').textContent=`${num(s.received)} / ${num(s.expected)} heartbeats`;
  $('energy-value').innerHTML=s.hours?`${num(s.energy,1)} <small>kWh</small>`:'—';
  $('trend').innerHTML=graph(result.daily);
  $('energy-chart').innerHTML=graph(result.daily,{energy:true});
  $('firmware-bars').innerHTML=result.firmware.map(f=>`<button class="firmware-option ${f.successRate<data.targets.success?'warn':''}" data-firmware="${safe(f.version)}" aria-label="Filter to firmware ${safe(f.version)}"><div><span>${safe(f.version)}</span><strong>${percent(f.successRate)}</strong></div><div class="bar"><i style="width:${(f.successRate||0)*100}%"></i></div><small>${num(f.commands)} commands</small></button>`).join('')||'<p class="empty">No firmware data for this selection.</p>';
  const failed=s.commands-s.successes;
  $('failure-total').textContent=`${num(failed)} failures`;
  const failures=data.failure_reasons.map((name,i)=>({name,count:s.failures[i]})).sort((a,b)=>b.count-a.count);
  const max=Math.max(1,...failures.map(f=>f.count));
  $('failure-bars').innerHTML=failures.map(f=>`<div class="failure-row"><span>${safe(f.name.toLowerCase().replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase()))}</span><div class="bar"><i style="width:${f.count/max*100}%"></i></div><strong>${num(f.count)}<small>${failed?Math.round(f.count/failed*100):0}%</small></strong></div>`).join('');
  $('insight').textContent=failed?`${failures[0].name.toLowerCase().replaceAll('_',' ')} accounts for ${(failures[0].count/failed*100).toFixed(1)}% of failures in this selection. Explore firmware and home filters to investigate.`:'No failed commands in this selection.';
  $('duplicates').textContent=num(data.quality.duplicates);$('rejected').textContent=num(data.quality.rejected);
  $('baseline').textContent=s.hours?`${num(s.baseline,1)} kWh`:'—';
  $('consumption').textContent=s.hours?`${num(s.energy,1)} kWh`:'—';
  $('difference').textContent=s.hours?`${num(s.difference,1)} kWh`:'—';
  $('cost').textContent=s.hours?`₹${num(s.difference*data.tariff_inr_per_kwh,0)} at assumed ₹${data.tariff_inr_per_kwh}/kWh`:'';
  $('export').disabled=!result.daily.length;
  renderTable();
  const url=new URL(location.href);url.search='';
  for(const [key,value] of Object.entries(filters))if(value&&!(key==='start'&&value===data.dates[0])&&!(key==='end'&&value===data.dates.at(-1)))url.searchParams.set(key,value);
  history.replaceState(null,'',url);
}

function applyPreset(preset){
  $('home').value='';$('firmware').value='';$('start').value=data.dates[0];$('end').value=data.dates.at(-1);
  if(preset==='firmware'){$('firmware').value='1.1.0';$('start').value=data.dates[Math.min(37,data.dates.length-1)];$('end').value=data.dates[Math.min(50,data.dates.length-1)];}
  if(preset==='connectivity'){$('home').value='HOME003';$('start').value=data.dates[Math.min(29,data.dates.length-1)];$('end').value=data.dates[Math.min(33,data.dates.length-1)];}
  update();
}

async function main(){
  try{
    const response=await fetch('./data.json');if(!response.ok)throw new Error(`HTTP ${response.status}`);
    data=await response.json();if(data.schema_version!==1)throw new Error('Unsupported reporting schema');
    const homes=[...new Set(data.devices.map(d=>d.home_id))].sort();
    $('home').innerHTML='<option value="">All homes</option>'+homes.map(h=>`<option>${safe(h)}</option>`).join('');
    $('firmware').innerHTML='<option value="">All versions</option>'+data.firmware.map(f=>`<option>${safe(f)}</option>`).join('');
    const params=new URLSearchParams(location.search);
    $('home').value=homes.includes(params.get('home'))?params.get('home'):'';
    $('firmware').value=data.firmware.includes(params.get('firmware'))?params.get('firmware'):'';
    for(const key of ['start','end']){
      const input=$(key);input.min=data.dates[0];input.max=data.dates.at(-1);
      input.value=data.dates.includes(params.get(key))?params.get(key):(key==='start'?data.dates[0]:data.dates.at(-1));
      input.disabled=false;
    }
    for(const key of ['home','firmware','reset'])$(key).disabled=false;
    for(const key of ['home','firmware','start','end'])$(key).addEventListener('change',update);
    $('reset').addEventListener('click',()=>{$('search').value='';applyPreset('all');});
    document.querySelectorAll('[data-preset]').forEach(b=>b.addEventListener('click',()=>applyPreset(b.dataset.preset)));
    $('firmware-bars').addEventListener('click',event=>{const b=event.target.closest('[data-firmware]');if(b){$('firmware').value=b.dataset.firmware;update();}});
    $('search').addEventListener('input',()=>{page=0;renderTable();});
    document.querySelectorAll('[data-sort]').forEach(b=>b.addEventListener('click',()=>{if(sort===b.dataset.sort)direction*=-1;else{sort=b.dataset.sort;direction=1;}page=0;renderTable();}));
    $('previous').addEventListener('click',()=>{page--;renderTable();});$('next').addEventListener('click',()=>{page++;renderTable();});
    $('export').addEventListener('click',()=>{const blob=new Blob([dailyCsv(result)],{type:'text/csv;charset=utf-8'});const link=document.createElement('a');link.href=URL.createObjectURL(blob);link.download=`smartswitch-${filters.home||'all-homes'}-${filters.start}-${filters.end}.csv`;link.click();setTimeout(()=>URL.revokeObjectURL(link.href),1000);});
    $('trend').addEventListener('pointermove',event=>{
      if(!result.daily.length)return;
      const bounds=$('trend').getBoundingClientRect(),x=(event.clientX-bounds.left)/bounds.width*720;
      const index=Math.max(0,Math.min(result.daily.length-1,Math.round((x-42)/(720-42-15)*(result.daily.length-1))));
      const d=result.daily[index],tooltip=$('chart-tooltip');tooltip.hidden=false;
      tooltip.textContent=`${shortDate(d.date)} · ${percent(d.successRate)} · ${num(d.commands)} commands`;
      tooltip.style.left=`${Math.max(0,Math.min(bounds.width-210,event.clientX-bounds.left-90))}px`;
      tooltip.style.top='10px';
    });
    $('trend').addEventListener('pointerleave',()=>$('chart-tooltip').hidden=true);
    document.querySelectorAll('.sidebar nav a').forEach(a=>a.addEventListener('click',()=>{document.querySelectorAll('.sidebar nav a').forEach(n=>n.classList.remove('active'));a.classList.add('active');}));
    update();
  }catch(error){$('load-error').hidden=false;$('selection').textContent='The reporting dataset is unavailable.';console.error(error);}
}
main();
