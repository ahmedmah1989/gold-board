const assert=require('node:assert/strict');
const {validOffer,displayable,productRows}=require('./services.js');
const now=Date.parse('2026-11-11T12:00:00Z');
const offer={status:'observed',identityVerified:true,inStock:true,manufacturingIncluded:true,taxIncluded:true,stampIncluded:true,listedPrice:50000,sourceTime:'2026-11-11T11:59:00Z',checkedAt:'2026-11-11T12:00:00Z'};
assert.equal(validOffer(offer,now),true);
assert.equal(validOffer({...offer,stampIncluded:null},now),false);
assert.equal(validOffer({...offer,sourceTime:null},now),false);
assert.equal(validOffer({...offer,sourceTime:'2026-11-11T11:00:00Z'},now),false);
assert.equal(validOffer({...offer,sourceTime:'2026-11-11T12:00:00'},now),false);
assert.equal(displayable({...offer,identityVerified:false},now),false);
assert.equal(displayable(offer,now+25*3600000),false);
assert.equal(displayable({...offer,inStock:false},now),true); // A historical listed price is distinct from availability.
assert.equal(productRows({offers:[{...offer,productId:'quarter'},{...offer,productId:'bar100'}]},'quarter').length,1);
console.log('Final offer fee, timestamp and freshness gates passed.');
