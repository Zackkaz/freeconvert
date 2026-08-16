// Shared client-side converter for FreeConvert static pages.
// Each page sets window.__PAGE__ = {cat, from, to, preset?}
// Controls: swap, copy, reset, precision. None of these alter the underlying
// calculation — they only affect which units are shown or how the number is
// displayed.
(function(){
  var PRESET = 1;                 // default input value
  var DEFAULT_PRECISION = 'auto'; // matches the HTML <select> default
  var prevFrom = null, prevTo = null; // remembered across a swap

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
  function fmtPrec(x, prec){
    if(!isFinite(x)) return '—';
    if(x===0) return '0';
    // fixed precision mode: force the requested number of decimals
    if(prec !== 'auto'){
      var d = parseInt(prec,10);
      var s = x.toFixed(d);
      // keep thousands separators; do NOT strip trailing zeros in fixed mode
      var p = s.split('.');
      if(p[0]) p[0] = p[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
      return p.join('.');
    }
    // auto mode: 6 sig decimals, then drop unnecessary trailing zeros
    var a = (Math.abs(x)>=1e12 || (Math.abs(x)<1e-6 && x!==0)) ? x.toExponential(4) : x.toFixed(6);
    a = a.replace(/0+$/,'').replace(/\.$/,'');
    var q = a.split('.'); if(q[0]) q[0] = q[0].replace(/\B(?=(\d{3})+(?!\d))/g,',');
    return q.join('.');
  }
  function unitSym(c,slug){ var u=c.units.find(function(x){return x.s===slug;}); return u?u.y:''; }

  function init(){
    var P = window.__PAGE__; if(!P) return;
    var c = window.CATS[P.cat];
    var fromSel = document.getElementById('from'), toSel = document.getElementById('to'),
        valIn = document.getElementById('val'), resEl = document.getElementById('res'),
        precSel = document.getElementById('prec'), copyBtn = document.getElementById('copy'),
        swapBtn = document.getElementById('swap'), resetBtn = document.getElementById('reset'),
        copyStat = document.getElementById('copystat');
    if(!fromSel||!toSel||!valIn||!resEl) return;

    // build unit options once
    c.units.forEach(function(u){
      [fromSel,toSel].forEach(function(sel){
        var o=document.createElement('option'); o.value=u.s; o.textContent=u.n+' ('+u.y+')'; sel.appendChild(o);
      });
    });
    // initial state
    fromSel.value = P.from; toSel.value = P.to;
    prevFrom = P.from; prevTo = P.to;
    valIn.value = (P.preset!=null?P.preset:PRESET);
    var precision = (precSel && precSel.value) ? precSel.value : DEFAULT_PRECISION;

    function run(){
      var v = parseFloat(valIn.value);
      if(isNaN(v)){ resEl.textContent='—'; return; }
      var r = convert(P.cat, fromSel.value, toSel.value, v);
      resEl.textContent = fmtPrec(r, precision) + ' ' + unitSym(c, toSel.value);
    }

    fromSel.onchange = run;
    toSel.onchange = run;
    valIn.oninput = run;
    if(precSel) precSel.onchange = function(){ precision = precSel.value; run(); };

    // Swap: reverse units, keep input, recalc. Never produce same-unit.
    if(swapBtn) swapBtn.onclick = function(){
      prevFrom = fromSel.value; prevTo = toSel.value;
      var f = toSel.value, t = fromSel.value;
      if(f === t){ // edge case: if equal, restore the previous distinct pair
        f = prevTo; t = prevFrom;
        if(f === t){ // last resort: pick any unit != current
          f = c.units[0].s; t = c.units.find(function(u){return u.s!==f;}).s;
        }
      }
      fromSel.value = f; toSel.value = t; run();
    };

    // Copy result (numeric only). Graceful failure feedback.
    if(copyBtn) copyBtn.onclick = function(){
      var txt = (resEl.textContent||'').replace(/[^\d.,eE+\-]/g,'').trim();
      if(!txt){ if(copyStat) copyStat.textContent='Nothing to copy'; return; }
      function ok(){ if(copyStat){ copyStat.textContent='Copied ✓'; setTimeout(function(){ if(copyStat) copyStat.textContent=''; },1500); } }
      function fail(){ if(copyStat){ copyStat.textContent='Copy failed — select and copy manually'; } }
      if(navigator.clipboard && navigator.clipboard.writeText){
        navigator.clipboard.writeText(txt).then(ok, function(){ // some browsers block without focus/permission
          try { var r=document.createRange(); r.selectNodeContents(resEl); var s=getSelection(); s.removeAllRanges(); s.addRange(r); document.execCommand('copy'); s.removeAllRanges(); ok(); }
          catch(e){ fail(); }
        });
      } else {
        try { var r=document.createRange(); r.selectNodeContents(resEl); var s=getSelection(); s.removeAllRanges(); s.addRange(r); document.execCommand('copy'); s.removeAllRanges(); ok(); }
        catch(e){ fail(); }
      }
    };

    // Reset: sensible defaults (initial units + default value + auto precision).
    if(resetBtn) resetBtn.onclick = function(){
      fromSel.value = P.from; toSel.value = P.to;
      prevFrom = P.from; prevTo = P.to;
      valIn.value = (P.preset!=null?P.preset:PRESET);
      if(precSel){ precSel.value = DEFAULT_PRECISION; precision = DEFAULT_PRECISION; }
      run();
    };

    run();
  }
  if(document.readyState!=='loading') init(); else document.addEventListener('DOMContentLoaded',init);
})();
