const assert=require('node:assert/strict');
const {validOffer}=require('./services.js');
const now=Date.parse('2026-11-11T12:00:00Z');
const offer={status:'observed',inStock:true,manufacturingIncluded:true,taxIncluded:true,stampIncluded:true,listedPrice:50000,sourceTime:'2026-11-11T11:59:00Z'};
assert.equal(validOffer(offer,now),true);
assert.equal(validOffer({...offer,stampIncluded:null},now),false);
assert.equal(validOffer({...offer,sourceTime:null},now),false);
assert.equal(validOffer({...offer,sourceTime:'2026-11-11T11:00:00Z'},now),false);
console.log('Final offer fee, timestamp and freshness gates passed.');
