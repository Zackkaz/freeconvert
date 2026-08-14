// Shared client-side converter for FreeConvert static pages.
// Each page sets window.__PAGE__ = {cat, from, to, preset?}
(function(){
  function convert(cat, from, to, v){
    var c = window.CATS[cat];
    if(!c) return NaN;
    if(c.type === 'f'){ return v * c.factors[from] / c.factors[to]; }
    if(c.type === 't'){
      var cv = from==='celsius' ? v : from==='fahrenheit' ? (v-32)*5/9 : v-273.15;
      return to==='celsius' ? cv : to==='fahrenheit' ? cv*9/5+32 : cv+273.15;
    }
    return NaN;
  }
  function fmt(x){
    if(!isFinite(x)) return '—';
    if(x===0) return '0';
    var s = (Math.abs(x)>=1e12 || (Math.abs(x)<1e-6 && x!==0)) ? x.toExponential(4) : x.toFixed(6);
    s = s.replace(/0+$/,'').replace(/\.$/,'');
    var p = s.split('.'); if(p[0]) p[0] = p[0].replace(/\B(?=(\d{3})+(?!\d))/g,',');
    return p.join('.');
  }
  function unitSym(c,slug){ var u=c.units.find(function(x){return x.s===slug;}); return u?u.y:''; }
  function init(){
    var P = window.__PAGE__; if(!P) return;
    var c = window.CATS[P.cat];
    var fromSel = document.getElementById('from'), toSel = document.getElementById('to'), valIn = document.getElementById('val'), resEl = document.getElementById('res');
    if(!fromSel||!toSel||!valIn||!resEl) return;
    c.units.forEach(function(u){ [fromSel,toSel].forEach(function(sel){ var o=document.createElement('option'); o.value=u.s; o.textContent=u.n+' ('+u.y+')'; sel.appendChild(o); }); });
    fromSel.value = P.from; toSel.value = P.to; valIn.value = (P.preset!=null?P.preset:1);
    function run(){ var v=parseFloat(valIn.value); if(isNaN(v)){resEl.textContent='—';return;} var r=convert(P.cat,fromSel.value,toSel.value,v); resEl.textContent=fmt(r)+' '+unitSym(c,toSel.value); }
    fromSel.onchange=run; toSel.onchange=run; valIn.oninput=run; run();
  }
  if(document.readyState!=='loading') init(); else document.addEventListener('DOMContentLoaded',init);
})();
