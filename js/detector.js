import { Client, handle_file } from "https://cdn.jsdelivr.net/npm/@gradio/client/dist/index.min.js";

/* ISI dengan alamat Space Hugging Face-mu, format "username/nama-space" */
const SPACE = "kryptosX/Backend-Tea-Leaf";

const $ = i => document.getElementById(i);
let file = null, mode = "visitor", hist = [];
try { hist = JSON.parse(localStorage.getItem("teaHist") || "[]"); } catch (e) {}
const LV = {
  ok:   ["#16a34a","Sehat","#dcfce7","#166534"],
  warn: ["#f59e0b","Waspada","#fef3c7","#92400e"],
  bad:  ["#ef4444","Terinfeksi","#fee2e2","#991b1b"]
};

/* mode pengunjung / staf */
function applyMode() {
  const shown = $('res').style.display !== 'none';
  $('rS').style.display = shown && mode === 'staff' ? 'block' : 'none';
  $('rF').style.display = shown && mode === 'visitor' ? 'block' : 'none';
}
$('mode').onclick = e => {
  const m = e.target.dataset.m; if (!m) return;
  mode = m;
  [...$('mode').children].forEach(b => b.classList.toggle('on', b.dataset.m === m));
  applyMode();
};

/* upload */
function setFile(f) {
  if (!f || !f.type.startsWith('image/')) return;
  file = f;
  $('img').src = URL.createObjectURL(f);
  $('pv').style.display = 'block'; $('drop').style.display = 'none'; $('go').disabled = false;
}
$('file').onchange = e => setFile(e.target.files[0]);
$('drop').ondragover = e => { e.preventDefault(); $('drop').classList.add('over'); };
$('drop').ondragleave = () => $('drop').classList.remove('over');
$('drop').ondrop = e => { e.preventDefault(); $('drop').classList.remove('over'); setFile(e.dataTransfer.files[0]); };
$('clr').onclick = () => {
  file = null; $('file').value = '';
  $('pv').style.display = 'none'; $('drop').style.display = 'block'; $('go').disabled = true;
  $('res').style.display = 'none'; $('empty').style.display = 'block';
};

/* panggil backend Gradio di Hugging Face Space */
let client = null;
async function predictRemote(f) {
  if (SPACE.startsWith("USERNAME")) {   // Space belum diisi -> mode demo (acak)
    const r = D.map(() => Math.random() ** 4), s = r.reduce((x, y) => x + y);
    return { demo: true, probs: Object.fromEntries(D.map((d, i) => [d.n, r[i] / s])) };
  }
  client = client || await Client.connect(SPACE);
  const res = await client.predict("/predict", [handle_file(f)]);
  return { demo: false, probs: res.data[0] };
}
$('go').onclick = async () => {
  $('go').disabled = true; $('go').textContent = 'Menganalisis…';
  try {
    const { demo, probs } = await predictRemote(file);
    $('demo').style.display = demo ? 'block' : 'none';
    show(probs);
  } catch (e) { alert('Deteksi gagal: ' + (e.message || e)); }
  $('go').textContent = 'Detect Disease'; $('go').disabled = false;
};

function show(pr) {
  const o = Object.entries(pr).sort((a, b) => b[1] - a[1]);
  const [name, cf] = o[0], x = D.find(d => d.n === name);
  if (!x) throw new Error('Nama kelas "' + name + '" tidak ada di diseases.js');
  const l = LV[x.lv], t = T[x.t];
  $('empty').style.display = 'none'; $('res').style.display = 'block';
  $('rI').textContent = x.e; $('rI').style.background = x.bg; $('rN').textContent = x.n;
  $('rT').textContent = t[0]; $('rT').style.cssText = `background:${t[1]};color:${t[2]}`;
  $('rC').textContent = (cf * 100).toFixed(1) + '%';
  $('rB').style.width = (cf * 100) + '%'; $('rB').style.background = l[0];
  $('rA').style.borderColor = l[0];
  $('rAh').textContent = x.lv === 'ok' ? 'Kondisi daun baik' : 'Penjelasan & Pencegahan';
  $('rAd').textContent = x.d + (cf < 0.6 ? ' (Keyakinan rendah, coba foto ulang dengan cahaya lebih baik.)' : '');
  $('rAl').innerHTML = x.p.map(i => `<li>${i}</li>`).join('');
  $('rSd').textContent = x.s; $('rFd').textContent = x.f;
  $('rP').innerHTML = o.map(([n, v], k) =>
    `<div class="pr ${k ? '' : 'top'}"><span>${n}</span><div class="bar"><i style="width:${v*100}%;background:${k ? '#cbd5c4' : '#16a34a'}"></i></div><em>${(v*100).toFixed(1)}%</em></div>`).join('');
  applyMode();
  hist.unshift({ t: new Date().toLocaleString('id-ID'), n: x.n, c: (cf * 100).toFixed(1), lv: x.lv });
  hist = hist.slice(0, 5);
  try { localStorage.setItem("teaHist", JSON.stringify(hist)); } catch (e) {}
  renderHist();
  if (innerWidth < 760) $('res').scrollIntoView({ behavior: 'smooth' });
}

function renderHist() {
  $('hb').innerHTML = hist.length ? hist.map(h => {
    const l = LV[h.lv];
    return `<tr><td>${h.t}</td><td><b>${h.n}</b></td><td style="color:${l[0]};font-weight:700">${h.c}%</td><td><span class="chip" style="background:${l[2]};color:${l[3]}">${l[1]}</span></td></tr>`;
  }).join('') : '<tr><td colspan="4" style="color:#667561">Belum ada riwayat.</td></tr>';
}
renderHist();
