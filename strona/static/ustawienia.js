/* ustawienia.js — panel operatora gry „Języki”: dostawcy tłumaczeń i klucze (maskowane). Tekst z serwera tylko przez textContent. */
(function(){
'use strict';
var q=function(id){return document.getElementById(id);};
var OPIS={wikidata:'Wikidane — etykiety CC0, bez klucza (podstawa)',mymemory:'MyMemory — bezpłatny, bez klucza, limit dzienny',deepl:'DeepL — z kluczem API',libre:'LibreTranslate — własna instancja albo publiczna z kluczem'};
var KOL=['wikidata','mymemory','deepl','libre'];
function kom(t,ok){q('kom').textContent=t;q('kom').className='kom '+(ok?'ok':'bl');}
function rysuj(u){var box=q('dost');box.textContent='';var wl=u.dostawcy||[];
  KOL.slice().sort(function(a,b){var ia=wl.indexOf(a),ib=wl.indexOf(b);return (ia<0?99:ia)-(ib<0?99:ib);}).forEach(function(k){
    var l=document.createElement('label');l.className='zg';var c=document.createElement('input');c.type='checkbox';c.value=k;c.checked=wl.indexOf(k)>=0;
    l.appendChild(c);l.appendChild(document.createTextNode(' '+OPIS[k]+(k==='deepl'&&u.deepl_klucz?' · klucz '+u.deepl_klucz:'')+(k==='libre'&&u.libre_klucz?' · klucz '+u.libre_klucz:'')));box.appendChild(l);});
  q('libre_url').value=u.libre_url||'';}
fetch('/api/ustawienia').then(function(r){return r.json();}).then(rysuj).catch(function(){kom('Brak dostępu (tylko przy ZBooku).');});
q('f').addEventListener('submit',function(ev){ev.preventDefault();
  var d={dostawcy:[].slice.call(document.querySelectorAll('#dost input:checked')).map(function(c){return c.value;}),deepl_klucz:q('deepl').value,libre_url:q('libre_url').value,libre_klucz:q('libre').value};
  fetch('/api/ustawienia',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)}).then(function(r){return r.json();})
    .then(function(u){if(u.blad){kom(u.blad);return;}q('deepl').value='';q('libre').value='';rysuj(u);kom('Zapisane (poza gitem).',true);});});
q('przebuduj').addEventListener('click',function(){q('przebuduj').disabled=true;kom('Buduję słownik — to może potrwać minutę…',true);
  fetch('/api/przebuduj',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}).then(function(r){return r.json();})
    .then(function(x){q('wynik').textContent=x.wynik||'';kom(x.rc===0?'Gotowe.':'Błąd budowy (rc '+x.rc+').',x.rc===0);q('przebuduj').disabled=false;});});
})();
