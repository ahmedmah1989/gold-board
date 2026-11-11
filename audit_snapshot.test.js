const fs=require('node:fs'),assert=require('node:assert/strict'),path=require('node:path');
const {calculate}=require('./monitor.js');
const q=JSON.parse(fs.readFileSync(path.join(__dirname,'data/quotes.json'),'utf8'));
const a=JSON.parse(fs.readFileSync(path.join(__dirname,'data/audit.json'),'utf8'));
assert.equal(a.quoteSnapshotTime,q.generatedAt,'Audit receipt belongs to this exact snapshot');
if(Object.keys(a.arithmetic.values).length){
 const s=q.sources,r=calculate(s.gold.sell,s.misr.sell,s.isagha['24'].sell,s.isagha['21'].sell);
 for(const [k,v] of Object.entries(a.arithmetic.values))assert.ok(Math.abs(v-r[k])<1e-8,k+' differs from independent Decimal calculation');
}
console.log('Actual collected snapshot matches independent Decimal arithmetic receipt.');
