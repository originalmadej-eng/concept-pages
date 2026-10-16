/* ink-worker.js — paints the six backdrops off the main thread, so the carousel never stutters while a painting is being made.
   The page sends {cmd:'gen'} (size, scene order, epoch) and, once its brush font is loaded, {cmd:'seals'} (glyph masks, because a worker has no page fonts). */
import {createPainter,sealMask} from './ink.js?v=4';
const SEALS={},waiting={};let epochNow=0,chain=Promise.resolve();
const getMask=(S,text)=>{const k=S+':'+text;if(SEALS[k])return SEALS[k];
  return new Promise(res=>{(waiting[k]=waiting[k]||[]).push(res);setTimeout(()=>res(SEALS[k]||sealMask(S,text)),3000);});};   // no mask in 3 s: fall back to a serif seal
self.onmessage=e=>{const m=e.data;
  if(m.cmd==='seals'){Object.assign(SEALS,m.seals);for(const k in m.seals)(waiting[k]||[]).splice(0).forEach(r=>r(SEALS[k]));return;}
  if(m.cmd==='gen'){epochNow=m.epoch;chain=chain.then(()=>run(m));}};
async function run(m){
  if(m.epoch!==epochNow)return;
  const P=createPainter(m.pw,m.ph,m.seed,{sealMask:getMask});
  for(const idx of m.order){
    if(m.epoch!==epochNow)return;
    try{const sc=await P.scene(idx);if(m.epoch!==epochNow)return;
      self.postMessage({type:'scene',epoch:m.epoch,idx,W:sc.W,H:sc.H,layers:sc.layers,times:sc.times},[...sc.layers.map(l=>l.buffer),sc.times.buffer]);}
    catch(err){self.postMessage({type:'error',epoch:m.epoch,msg:String(err&&err.stack||err)});}
  }
}
