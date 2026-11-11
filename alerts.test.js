const assert=require('node:assert/strict');const {changes}=require('./alerts');
const base={gapEGP:10,gapPercent:.5,fxGap:.1,fxPercent:.2,local24:7000,local21:6125,peak24:7100,peak21:6200,dd24:100/7100*100,dd21:75/6200*100};
assert.equal(changes(null,base).length,0);assert.equal(changes(base,base).length,0);
assert.ok(changes(base,{...base,gapEGP:85}).some(x=>x.includes('فجوة الذهب')));
assert.ok(changes(base,{...base,fxGap:1.1}).some(x=>x.includes('الدولار')));
assert.ok(changes(base,{...base,local24:7101}).some(x=>x.includes('قمة')));
assert.ok(changes(base,{...base,local24:6800}).some(x=>x.includes('الهبوط')));
console.log('Alert thresholds, quiet updates, new peaks and deeper drawdown passed.');
