// Pure reporting functions, shared by the browser and SQL reconciliation checks.
const bucket = () => ({commands:0, successes:0, latencies:[], failures:[0,0,0],
  expected:0, received:0, energy:0, baseline:0, rssi:0, hours:0});
const add = (b, row) => {
  b.commands += row[3]; b.successes += row[4];
  for (const value of row[5]) b.latencies.push(value);
  row[6].forEach((value, i) => b.failures[i] += value);
  b.expected += row[7]; b.received += row[8]; b.energy += row[9];
  b.baseline += row[10]; b.rssi += row[11]; b.hours += row[12];
};
const finish = b => {
  b.latencies.sort((a,b) => a-b);
  return {...b, successRate: b.commands ? b.successes/b.commands : null,
    heartbeatRate: b.expected ? b.received/b.expected : null,
    p95: b.latencies.length ? b.latencies[Math.ceil(.95*b.latencies.length)-1]/10 : null,
    avgLatency: b.latencies.length ? b.latencies.reduce((a,b)=>a+b,0)/b.latencies.length/10 : null,
    avgRssi: b.hours ? b.rssi/b.hours : null, difference: b.baseline-b.energy};
};

export function summarize(data, filters={}) {
  const total=bucket(), daily=new Map(), firmware=new Map(), devices=new Map();
  for (const row of data.rows) {
    const date=data.dates[row[0]], device=data.devices[row[1]], version=data.firmware[row[2]];
    if ((filters.home && device.home_id!==filters.home) ||
        (filters.firmware && version!==filters.firmware) ||
        (filters.start && date<filters.start) || (filters.end && date>filters.end)) continue;
    add(total,row);
    for (const [map,key] of [[daily,date],[firmware,version],[devices,row[1]]]) {
      if (!map.has(key)) map.set(key,bucket());
      add(map.get(key),row);
    }
  }
  return {total:finish(total),
    daily:[...daily].sort(([a],[b])=>a.localeCompare(b)).map(([date,b])=>({date,...finish(b)})),
    firmware:[...firmware].sort(([a],[b])=>a.localeCompare(b)).map(([version,b])=>({version,...finish(b)})),
    devices:[...devices].map(([id,b])=>({...data.devices[id],...finish(b)}))};
}

export function dailyCsv(result) {
  const head=['date','commands','successes','command_success_rate','p95_latency_ms',
    'heartbeat_delivery_rate','estimated_kwh','assumed_baseline_kwh','modeled_difference_kwh'];
  const rows=result.daily.map(d=>[d.date,d.commands,d.successes,d.successRate,d.p95,
    d.heartbeatRate,d.energy,d.baseline,d.difference].map(v=>v??'').join(','));
  return [head.join(','),...rows].join('\r\n')+'\r\n';
}
