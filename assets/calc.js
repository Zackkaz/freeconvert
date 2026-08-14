// Simple client-side calculators for FreeConvert.
function fmt(x){
  if(!isFinite(x)) return '—';
  var s=(Math.abs(x)>=1e12||(Math.abs(x)<1e-6&&x!==0))?x.toExponential(4):x.toFixed(4);
  s=s.replace(/0+$/,'').replace(/\.$/,'');
  var p=s.split('.'); if(p[0]) p[0]=p[0].replace(/\B(?=(\d{3})+(?!\d))/g,',');
  return p.join('.');
}
function pct(){ var p=parseFloat(document.getElementById('p').value), n=parseFloat(document.getElementById('n').value);
  if(isNaN(p)||isNaN(n)) return '';
  var r=p/100*n; return fmt(r)+'  (remaining: '+fmt(n-r)+')'; }
function tip(){ var b=parseFloat(document.getElementById('b').value), tp=parseFloat(document.getElementById('tp').value), pe=parseInt(document.getElementById('pe').value)||1;
  if(isNaN(b)) return '';
  var t=b*tp/100; return 'Tip: '+fmt(t)+'  •  Total: '+fmt(b+t)+'  •  Per person: '+fmt((b+t)/pe); }
function loan(){ var a=parseFloat(document.getElementById('a').value), r=parseFloat(document.getElementById('r').value), y=parseFloat(document.getElementById('y').value);
  if(isNaN(a)||isNaN(r)||isNaN(y)) return '';
  var m=r/100/12, n=y*12, emi=a*m*Math.pow(1+m,n)/(Math.pow(1+m,n)-1);
  if(!isFinite(emi)||emi<=0) emi=a/n;
  return 'Monthly EMI: '+fmt(emi)+'  •  Total paid: '+fmt(emi*n)+'  •  Interest: '+fmt(emi*n-a); }
function ddiff(){ var d1=new Date(document.getElementById('d1').value), d2=new Date(document.getElementById('d2').value);
  if(isNaN(d1)||isNaN(d2)) return '';
  var days=Math.round((d2-d1)/86400000); return Math.abs(days)+' days  ('+fmt(Math.abs(days)/365.25)+' years)'; }
function wtp(){ var w=parseFloat(document.getElementById('w').value), pp=parseFloat(document.getElementById('pp').value)||500;
  if(isNaN(w)) return '';
  return fmt(Math.ceil(w/pp))+' page(s) at ~'+pp+' words/page'; }
function age(){ var d=new Date(document.getElementById('dob').value);
  if(isNaN(d)) return '';
  var days=(Date.now()-d.getTime())/86400000, y=days/365.25; return fmt(y)+' years  ('+fmt(days)+' days)'; }
function runCalc(fn, out){ document.getElementById(out).textContent = fn(); }
