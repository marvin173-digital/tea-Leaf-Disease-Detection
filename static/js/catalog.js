const $ = i => document.getElementById(i);
let flt = "all";
const FILTERS = [["all","Semua"],["ok","Sehat"],["fungus","Jamur"],["pest","Hama"],["other","Lainnya"]];

function renderCat() {
  $('fl').innerHTML = FILTERS.map(([k,l]) => `<button data-k="${k}" class="${k===flt?'on':''}">${l}</button>`).join('');
  $('cats').innerHTML = D.filter(x => flt==='all' || x.t===flt || (flt==='other' && x.t==='alga')).map(x => {
    const t = T[x.t];
    return `<div class="dc"><div class="top" style="background:${x.bg}">${x.e}</div><div class="bd">
      <span class="chip" style="background:${t[1]};color:${t[2]}">${t[0]}</span><h3>${x.n}</h3><p>${x.d}</p>
      <span class="hint">Lihat penyebab &amp; pencegahan ▾</span>
      <div class="more"><b>Penyebab:</b> ${x.c}<br><br><b>Cara mencegah:</b><ul>${x.p.map(i=>`<li>${i}</li>`).join('')}</ul></div></div></div>`;
  }).join('');
  document.querySelectorAll('.dc').forEach(c => c.onclick = () => c.classList.toggle('open'));
}
$('fl').onclick = e => { if (e.target.dataset.k) { flt = e.target.dataset.k; renderCat(); } };
renderCat();
