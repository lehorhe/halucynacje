/* jezyki.js — gra „Halucynacje” (dawniej „Języki”): nazwa pisze się po kolei we wszystkich językach (jak „hello” w iPhonie), zapis na wiadomość o resecie.
   Tekst z serwera trafia do DOM wyłącznie przez textContent. Czyste funkcje eksportowane do testów pod node. */
(function(root){
'use strict';
var J={};
/* Nazwa języka `kod` wyrażona w języku `w` (domyślnie po polsku) z przeglądarki (Intl), a gdy jej nie zna — kod. */
J.nazwa=function(kod,Intl_,w){try{var n=new (Intl_||(typeof Intl!=='undefined'?Intl:root.Intl)).DisplayNames([w||'pl'],{type:'language'}).of(kod);return n&&n!==kod?n:kod;}catch(e){return kod;}};
/* Polski i najpopularniejsze języki świata (liczba mówiących) — na początku listy wyboru. */
J.POPULARNE=['pl','en','zh','hi','es','fr','ar','bn','pt','ru','ur','id','de','ja','uk','it','tr','ko','vi','nl','cs','sv','el','he'];
/* Opcje listy: {kod, wlasna (nazwa w tym języku), tu (nazwa w języku `w`), pop}; najpierw popularne w stałej kolejności, reszta alfabetycznie
   wg nazwy własnej. Tylko języki, dla których przeglądarka ma nazwy (supportedLocalesOf) — inaczej Intl po cichu podałby angielski. */
J.opcje=function(kody,w,Intl_){var I=Intl_||(typeof Intl!=='undefined'?Intl:root.Intl),wid={},out=[],reszta=[];
  var ma=function(k){try{return I.DisplayNames.supportedLocalesOf([k]).length>0;}catch(e){return false;}};
  J.POPULARNE.concat(kody||[]).forEach(function(k){k=String(k||'').split('-')[0].toLowerCase();if(!k||wid[k]||!/^[a-z]{2,3}$/.test(k)||!ma(k))return;wid[k]=1;
    var o={kod:k,wlasna:J.nazwa(k,I,k),tu:J.nazwa(k,I,w||'pl'),pop:J.POPULARNE.indexOf(k)>=0};if(o.wlasna===k)return;(o.pop?out:reszta).push(o);});
  reszta.sort(function(a,b){return a.wlasna.localeCompare(b.wlasna,w||'pl');});return out.concat(reszta);};
/* Kolejność pokazu: polski pierwszy, potem pozostałe bez dwóch identycznych słów pod rząd. */
J.kolejka=function(slowa){var out=[],ost=null;(slowa||[]).forEach(function(s){if(!s||!s.slowo)return;if(ost&&ost.slowo===s.slowo)return;out.push(s);ost=s;});return out;};
/* Adres e-mail tak jak sprawdza serwer. */
J.email=function(e){return /^[A-Za-z0-9._%+\-]{1,64}@[A-Za-z0-9.\-]{1,190}\.[A-Za-z]{2,24}$/.test(String(e||'').trim());};
/* Klauzula informacyjna (art. 13 RODO) — treść do akceptacji IOD; dane administratora i IOD z serwera (/api/stan). */
J.klauzula=function(s){return 'Administratorem Twoich danych jest '+String(s.administrator||'').replace(/\.$/,'')+'. Kontakt z inspektorem ochrony danych: '+s.iod+'. '+
  'Cel: jedna wiadomość e-mail o resecie świata gry „Halucynacje” dla nowych graczy. Podstawa: Twoja zgoda (art. 6 ust. 1 lit. a RODO). '+
  'Przetwarzamy tylko adres e-mail, czas zapisu i język przeglądarki — bez adresu IP. Przechowujemy je do wysłania tej wiadomości albo do wycofania zgody. '+
  'Zgodę wycofasz w każdej chwili formularzem „Wypisz mnie” poniżej albo pisząc do inspektora; wycofanie nie wpływa na zgodność z prawem przetwarzania sprzed wycofania. '+
  'Masz prawo dostępu do danych, ich sprostowania, usunięcia, ograniczenia przetwarzania i przenoszenia oraz prawo skargi do Prezesa Urzędu Ochrony Danych Osobowych. '+
  'Nie profilujemy i nie podejmujemy decyzji automatycznie. Stronę udostępnia sieć Cloudflare (przekazuje ruch). Podanie adresu jest dobrowolne. Wersja klauzuli: '+s.klauzula+'.';};
if(typeof module!=='undefined'){module.exports=J;return;}
if(!root.document)return;
var doc=root.document,q=function(id){return doc.getElementById(id);};
var W='pl';try{W=root.localStorage.getItem('jezyki_nazwy')||'pl';}catch(e){}
var T=q('slowo'),KOL=[],I=0,BIEZ=null,cicho=root.matchMedia&&root.matchMedia('(prefers-reduced-motion: reduce)').matches;

function dopasuj(){T.style.fontSize='150px';var w;try{w=T.getComputedTextLength();}catch(e){w=0;}
  if(w>940)T.style.fontSize=Math.max(40,Math.floor(150*940/w))+'px';
  var dl=0;try{dl=Math.ceil(T.getComputedTextLength()*4.2)+400;}catch(e){dl=3000;}
  T.style.setProperty('--dl',dl);T.style.strokeDasharray=dl;T.style.strokeDashoffset=dl;}
function podpis(s){if(!s)return;q('jez').textContent=(s.kod==='pl'&&W==='pl')?'po polsku':J.nazwa(s.kod,null,W);}
function pokaz(){var s=KOL[I%KOL.length];I++;BIEZ=s;
  T.classList.remove('pisze','znika');T.textContent=s.slowo;
  dopasuj();void T.getBBox();T.classList.add('pisze');
  podpis(s);q('licz').textContent=((I-1)%KOL.length+1)+' z '+KOL.length;
  root.setTimeout(function(){T.classList.remove('pisze');T.classList.add('znika');root.setTimeout(pokaz,cicho?50:470);},cicho?2600:3300);}
/* lista wyboru języka nazw: popularne w grupie na górze, reszta alfabetycznie; etykieta „nazwa własna · nazwa w wybranym” */
var SEL=q('jezyk-nazw');
function lista(kody){SEL.textContent='';var o=J.opcje(kody,W),g1=doc.createElement('optgroup'),g2=doc.createElement('optgroup');
  g1.label=J.nazwa('pl',null,W)==='polski'?'Najpopularniejsze':'★';g2.label=J.nazwa('pl',null,W)==='polski'?'Wszystkie (A–Ż)':'A–Z';
  o.forEach(function(x){var op=doc.createElement('option');op.value=x.kod;op.textContent=x.wlasna+(x.tu&&x.tu.toLowerCase()!==x.wlasna.toLowerCase()?' · '+x.tu:'');
    if(x.kod===W)op.selected=true;(x.pop?g1:g2).appendChild(op);});SEL.appendChild(g1);if(g2.children.length)SEL.appendChild(g2);
  q('ile-nazw').textContent=o.length;}
var KODY=[];
SEL.addEventListener('change',function(){W=SEL.value;try{root.localStorage.setItem('jezyki_nazwy',W);}catch(e){}lista(KODY);podpis(BIEZ);});
fetch('/api/slowa').then(function(r){return r.json();}).then(function(d){KOL=J.kolejka(d.slowa);KODY=KOL.map(function(s){return s.kod;});lista(KODY);if(KOL.length)pokaz();}).catch(function(){KOL=[{kod:'pl',slowo:'Halucynacje'}];pokaz();});

/* zapis */
var f=q('zapis'),kom=q('kom'),btn=q('wyslij');
function komunikat(t,ok){kom.textContent=t;kom.className='kom '+(ok?'ok':'bl');}
fetch('/api/stan').then(function(r){return r.json();}).then(function(s){
  if(s.zapisy_otwarte){q('adm').textContent='Administrator danych: '+s.administrator+' · inspektor ochrony danych: '+s.iod+'.';
    q('klauzula-tekst').textContent=J.klauzula(s);q('klauzula').hidden=false;q('wypis').hidden=false;}
  else{q('adm').textContent='Zapisy ruszą, gdy wskażemy administratora danych — wtedy ten formularz się odblokuje.';btn.disabled=true;q('email').disabled=true;}}).catch(function(){});
var fw=q('wypis');fw.addEventListener('submit',function(ev){ev.preventDefault();var e=q('email-wypis').value,k=q('kom-wypis');
  if(!J.email(e)){k.textContent='To nie wygląda na adres e-mail.';k.className='kom bl';return;}
  fetch('/api/wypisz',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:e})}).then(function(r){return r.json();})
    .then(function(j){k.textContent=j.komunikat||'Gotowe.';k.className='kom '+(j.ok?'ok':'bl');if(j.ok)fw.reset();}).catch(function(){k.textContent='Brak połączenia — spróbuj za chwilę.';k.className='kom bl';});});
f.addEventListener('submit',function(ev){ev.preventDefault();var e=q('email').value;
  if(!J.email(e)){komunikat('To nie wygląda na adres e-mail.');return;}
  if(!q('zgoda').checked){komunikat('Zaznacz zgodę na jedną wiadomość o resecie świata gry.');return;}
  btn.disabled=true;
  fetch('/api/zapis',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:e,zgoda:true,www:q('www').value})})
    .then(function(r){return r.json().then(function(j){return {ok:r.ok,j:j};});})
    .then(function(x){komunikat(x.j.komunikat||(x.ok?'Zapisane.':'Nie udało się.'),x.ok);if(x.ok)f.reset();btn.disabled=false;})
    .catch(function(){komunikat('Brak połączenia — spróbuj za chwilę.');btn.disabled=false;});});
})(typeof window!=='undefined'?window:this);
