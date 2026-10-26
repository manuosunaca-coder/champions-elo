/* Pronósticos Champions Elo — widget para Blogger.
   Uso: <div class="uce-app" data-view="all"></div>
        <script src="https://manuosunaca-coder.github.io/champions-elo/widget.js"></script>
   data-view:    all | picks | cards | table | title | elo | results | stats
   data-max:     número máximo de filas/tarjetas
   data-country: código de país (es, gb-eng, de…) para filtrar equipos de un país
   data-scope:   en la vista elo, "cl" (equipos de la Champions) o "europe" (top europeo)
   data-md:      en picks, "next" para mostrar solo la próxima jornada */
(function () {
  var SCRIPT = document.currentScript;
  var BASE = SCRIPT && SCRIPT.src ? SCRIPT.src.replace(/[^\/]*$/, "") : "";
  if (window.__uceLoaded) { return; }
  window.__uceLoaded = true;

  var CSS = "\
.uce{--bg:#0b1030;--panel:#121a46;--panel2:#18225a;--line:rgba(160,180,255,.16);--ink:#eef1ff;--mut:#9aa6d6;--acc:#7cc4ff;--acc2:#b69cff;--gold:#f6c85f;--ok:#4ade80;--bad:#f87171;--warn:#fbbf24;\
font:15px/1.5 Manrope,system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif;color:var(--ink);max-width:100%;text-align:left;-webkit-font-smoothing:antialiased}\
.uce *{box-sizing:border-box}.uce a{color:var(--acc);text-decoration:none}.uce img{border:0;max-width:none}\
.uce h3{font:700 18px/1.25 Unbounded,Manrope,sans-serif;margin:0 0 10px;color:var(--ink);letter-spacing:-.01em}\
.uce-muted{color:var(--mut);font-size:13px}\
.uce-load{padding:28px;text-align:center;color:var(--mut)}\
.uce-tabs{display:flex;gap:6px;margin:0 0 14px;overflow-x:auto;padding-bottom:4px;scrollbar-width:none}.uce-tabs::-webkit-scrollbar{display:none}\
.uce-tab{border:1px solid var(--line);background:transparent;color:var(--mut);padding:9px 16px;border-radius:999px;cursor:pointer;font:600 14px Manrope,sans-serif;white-space:nowrap;min-height:40px}\
.uce-tab:hover{color:var(--ink)}.uce-tab.on{background:linear-gradient(135deg,var(--acc),var(--acc2));color:#0b1030;border-color:transparent}\
.uce-tools{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 12px}\
.uce-search{flex:1 1 200px;min-width:0;max-width:320px;padding:10px 14px;border-radius:10px;border:1px solid var(--line);background:var(--panel);color:var(--ink);font:14px Manrope,sans-serif}\
.uce-search::placeholder{color:var(--mut)}\
.uce-pill{border:1px solid var(--line);background:var(--panel);color:var(--ink);padding:8px 12px;border-radius:10px;font:600 13px Manrope,sans-serif;cursor:pointer;min-height:38px}\
.uce-pill.on{border-color:var(--acc);color:var(--acc)}\
.uce-stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:0 0 16px}\
.uce-stat{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:12px 14px}\
.uce-stat b{display:block;font:700 24px/1.1 Unbounded,sans-serif;font-variant-numeric:tabular-nums;color:var(--ink)}\
.uce-stat span{font-size:12px;color:var(--mut)}\
.uce-day{font:700 12px Manrope,sans-serif;text-transform:uppercase;letter-spacing:.08em;color:var(--acc);margin:18px 0 8px}\
.uce-match{display:grid;grid-template-columns:62px minmax(0,1fr) 210px 120px;gap:12px;align-items:center;background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:12px 14px;margin:0 0 8px}\
.uce-time{font:700 15px Unbounded,sans-serif;color:var(--ink)}.uce-time small{display:block;font:500 11px Manrope,sans-serif;color:var(--mut)}\
.uce-teams{min-width:0}.uce-tm{display:flex;align-items:center;gap:8px;min-width:0;font-weight:700;line-height:1.35}\
.uce-tm span.n{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}\
.uce-logo{width:22px;height:22px;object-fit:contain;flex:none}\
.uce-flag{width:16px;height:11px;border-radius:2px;flex:none;opacity:.9}\
.uce-elo{font:600 11px Manrope,sans-serif;color:var(--mut);margin-left:auto;padding-left:6px;white-space:nowrap}\
.uce-up{color:var(--ok)}.uce-down{color:var(--bad)}\
.uce-bar{display:flex;height:26px;border-radius:8px;overflow:hidden;font:700 11px Manrope,sans-serif}\
.uce-bar i{display:flex;align-items:center;justify-content:center;font-style:normal;color:#0b1030;min-width:0;overflow:hidden;white-space:nowrap}\
.uce-b1{background:var(--acc)}.uce-bx{background:#c7cdea}.uce-b2{background:var(--acc2)}\
.uce-barlab{display:flex;justify-content:space-between;font-size:11px;color:var(--mut);margin-top:3px}\
.uce-pick{text-align:center}.uce-pick b{display:inline-block;font:700 15px Unbounded,sans-serif;padding:5px 12px;border-radius:9px;background:rgba(124,196,255,.14);color:var(--acc)}\
.uce-pick small{display:block;font-size:11px;color:var(--mut);margin-top:4px}\
.uce-conf{display:inline-flex;gap:2px;margin-top:4px}.uce-conf i{width:7px;height:7px;border-radius:2px;background:rgba(160,180,255,.18)}.uce-conf i.on{background:var(--gold)}\
.uce-extra{grid-column:2 / -1;display:flex;flex-wrap:wrap;gap:6px 14px;font-size:12px;color:var(--mut);border-top:1px dashed var(--line);padding-top:8px}\
.uce-extra b{color:var(--ink)}\
.uce-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}\
.uce-card{position:relative;background:radial-gradient(120% 90% at 100% 0,rgba(182,156,255,.20),transparent 60%),var(--panel);border:1px solid var(--line);border-radius:18px;padding:16px;overflow:hidden}\
.uce-card.hot{border-color:rgba(246,200,95,.55)}\
.uce-card .uce-when{font-size:12px;color:var(--mut);display:flex;justify-content:space-between;gap:8px;margin-bottom:10px}\
.uce-vs{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:8px;text-align:center;margin-bottom:12px}\
.uce-vs .t{display:flex;flex-direction:column;align-items:center;gap:6px;font-weight:700;font-size:14px;line-height:1.2;min-width:0}\
.uce-vs .t img{width:44px;height:44px;object-fit:contain}\
.uce-vs .sc{font:700 22px Unbounded,sans-serif;color:var(--gold)}\
.uce-vs .sc small{display:block;font:500 10px Manrope,sans-serif;color:var(--mut);letter-spacing:.06em;text-transform:uppercase}\
.uce-card .uce-pk{display:flex;justify-content:space-between;align-items:center;margin-top:10px;font-size:13px}\
.uce-tbl{width:100%;border-collapse:collapse;font-size:14px;margin:0;border:0;background:none}\
.uce-scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid var(--line);border-radius:14px;background:var(--panel)}\
.uce-tbl th{font:700 11px Manrope,sans-serif;text-transform:uppercase;letter-spacing:.06em;color:var(--mut);text-align:left;padding:10px 8px;border:0;border-bottom:1px solid var(--line);background:none;white-space:nowrap}\
.uce-tbl td{padding:9px 8px;border:0;border-top:1px solid var(--line);background:none;color:var(--ink);white-space:nowrap;font-variant-numeric:tabular-nums}\
.uce-tbl tr:first-child td{border-top:0}\
.uce-tbl .r{text-align:right}.uce-tbl .c{text-align:center}\
.uce-tbl td.tn{min-width:160px}\
.uce-z1 td:first-child{box-shadow:inset 3px 0 0 var(--ok)}.uce-z2 td:first-child{box-shadow:inset 3px 0 0 var(--warn)}.uce-z3 td:first-child{box-shadow:inset 3px 0 0 var(--bad)}\
.uce-pct{display:inline-block;min-width:46px;text-align:right;padding:2px 6px;border-radius:6px}\
.uce-form{display:inline-flex;gap:3px}.uce-form i{width:18px;height:18px;border-radius:5px;font:700 10px/18px Manrope,sans-serif;text-align:center;font-style:normal;color:#0b1030}\
.uce-form .V{background:var(--ok)}.uce-form .E{background:#c7cdea}.uce-form .D{background:var(--bad)}\
.uce-legend{display:flex;flex-wrap:wrap;gap:14px;font-size:12px;color:var(--mut);margin:10px 2px 0}\
.uce-legend i{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;vertical-align:-1px}\
.uce-fav{display:grid;grid-template-columns:28px minmax(0,1fr) 64px;gap:10px;align-items:center;padding:9px 0;border-top:1px solid var(--line)}\
.uce-fav:first-child{border-top:0}.uce-fav .pos{font:700 13px Unbounded,sans-serif;color:var(--mut)}\
.uce-fav .bar{height:8px;border-radius:99px;background:rgba(160,180,255,.12);margin-top:6px;overflow:hidden}\
.uce-fav .bar i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,var(--acc),var(--gold))}\
.uce-fav .v{font:700 16px Unbounded,sans-serif;text-align:right;color:var(--gold)}\
.uce-box{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:14px 16px}\
.uce-res{display:grid;grid-template-columns:70px minmax(0,1fr) 54px 56px 30px;gap:10px;align-items:center;padding:9px 0;border-top:1px solid var(--line);font-size:14px}\
.uce-res:first-child{border-top:0}\
.uce-ok,.uce-ko{display:inline-flex;width:24px;height:24px;border-radius:7px;align-items:center;justify-content:center;font-weight:800}\
.uce-ok{background:rgba(74,222,128,.16);color:var(--ok)}.uce-ko{background:rgba(248,113,113,.14);color:var(--bad)}\
.uce-spark{vertical-align:middle}\
.uce-note{font-size:12px;color:var(--mut);margin-top:10px}\
.uce-empty{padding:22px;text-align:center;color:var(--mut);background:var(--panel);border:1px dashed var(--line);border-radius:14px}\
.uce-more{display:block;margin:12px auto 0;border:1px solid var(--line);background:transparent;color:var(--acc);padding:10px 18px;border-radius:999px;cursor:pointer;font:700 13px Manrope,sans-serif}\
@media (max-width:820px){.uce-match{grid-template-columns:48px minmax(0,1fr) 96px;gap:10px}.uce-match .uce-probs{grid-column:1 / -1;order:4}.uce-extra{grid-column:1 / -1;order:5}.uce-match .uce-elo,.uce-match .uce-flag{display:none}.uce-stats{grid-template-columns:repeat(2,minmax(0,1fr))}}\
@media (max-width:480px){.uce{font-size:14px}.uce-stat b{font-size:20px}.uce-res{grid-template-columns:52px minmax(0,1fr) 46px 26px}.uce-res .pk{display:none}.uce-cards{grid-template-columns:1fr}}\
";

  function el(html) { var d = document.createElement("div"); d.innerHTML = html; return d.firstChild; }
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function pct(x) { return (x == null ? "—" : (Math.round(x * 10) / 10).toString().replace(".", ",") + " %"); }
  function pct0(x) { if (x == null) return "—"; if (x > 0 && x < 1) return "<1 %"; if (x < 100 && x > 99) return ">99 %"; return Math.round(x) + " %"; }
  var TZ = "Europe/Madrid";
  function fmt(d, o) { try { return new Intl.DateTimeFormat("es-ES", Object.assign({ timeZone: TZ }, o)).format(d); } catch (e) { return d.toLocaleString("es-ES"); } }
  function dayKey(iso) { return fmt(new Date(iso), { year: "numeric", month: "2-digit", day: "2-digit" }); }
  function dayLabel(iso) {
    var d = new Date(iso), t = new Date();
    var k = dayKey(iso), kt = dayKey(t.toISOString()), km = dayKey(new Date(t.getTime() + 864e5).toISOString());
    var s = fmt(d, { weekday: "long", day: "numeric", month: "long" });
    if (k === kt) return "Hoy · " + s; if (k === km) return "Mañana · " + s; return s;
  }
  function hour(iso) { return fmt(new Date(iso), { hour: "2-digit", minute: "2-digit" }); }
  function shortDate(iso) { return fmt(new Date(iso), { day: "numeric", month: "short" }); }
  function flag(c) { return c ? '<img class="uce-flag" loading="lazy" alt="" src="https://flagcdn.com/w20/' + esc(c) + '.png">' : ""; }
  function logo(src, cls) { return src ? '<img class="' + (cls || "uce-logo") + '" loading="lazy" alt="" src="' + esc(src) + '">' : ""; }
  function tr(t) { return t > 0 ? '<span class="uce-up" title="En racha">▲</span>' : (t < 0 ? '<span class="uce-down" title="A la baja">▼</span>' : ""); }
  function conf(n) { var s = '<span class="uce-conf" title="Confianza ' + n + '/10">'; for (var i = 1; i <= 10; i++) s += '<i class="' + (i <= n ? "on" : "") + '"></i>'; return s + "</span>"; }
  function pickName(m) { return m.pick === "1" ? m.h.n : (m.pick === "2" ? m.a.n : "Empate"); }
  function pickLabel(p) { return p === "1" ? "Gana local" : (p === "2" ? "Gana visitante" : "Empate"); }
  function matchesCountry(m, c) { return !c || m.h.c === c || m.a.c === c; }
  function heat(v) { var a = Math.min(1, (v || 0) / 100); return "background:rgba(124,196,255," + (0.08 + a * 0.42).toFixed(2) + ")"; }

  function statsBox(d) {
    var s = d.stats.season, st = d.stats.season_strong, ph = d.phase;
    var fase = ph.lp_total ? (ph.lp_done >= ph.lp_total ? (ph.ko_started ? "Eliminatorias" : "Fase liga terminada") : "Jornada " + (ph.md_done || 0) + " de 8") : "Pendiente del sorteo";
    return '<div class="uce-stats">' +
      '<div class="uce-stat"><b>' + (s.n ? pct0(s.rate) : "—") + '</b><span>Aciertos 1X2 esta temporada (' + s.hits + "/" + s.n + ')</span></div>' +
      '<div class="uce-stat"><b>' + (st.n ? pct0(st.rate) : "—") + '</b><span>Aciertos con confianza 7+ (' + st.hits + "/" + st.n + ')</span></div>' +
      '<div class="uce-stat"><b>' + (s.n ? pct0(s.dc_rate) : "—") + '</b><span>Aciertos en doble oportunidad</span></div>' +
      '<div class="uce-stat"><b>' + esc(fase) + '</b><span>Champions ' + esc(d.season) + '</span></div></div>';
  }

  function probBar(p) {
    return '<div class="uce-bar"><i class="uce-b1" style="width:' + p[0] + '%">' + (p[0] >= 14 ? Math.round(p[0]) + "%" : "") + '</i>' +
      '<i class="uce-bx" style="width:' + p[1] + '%">' + (p[1] >= 14 ? Math.round(p[1]) + "%" : "") + '</i>' +
      '<i class="uce-b2" style="width:' + p[2] + '%">' + (p[2] >= 14 ? Math.round(p[2]) + "%" : "") + '</i></div>' +
      '<div class="uce-barlab"><span>1</span><span>X</span><span>2</span></div>';
  }

  function matchRow(m) {
    var tag = m.md ? "J" + m.md : esc(m.round);
    return '<div class="uce-match"><div class="uce-time">' + (m.live ? '<span style="color:var(--bad)">●</span>' : hour(m.date)) + '<small>' + tag + '</small></div>' +
      '<div class="uce-teams"><div class="uce-tm">' + logo(m.h.logo) + '<span class="n">' + esc(m.h.n) + '</span>' + flag(m.h.c) + '<span class="uce-elo">' + m.h.elo + " " + tr(m.h.tr) + '</span></div>' +
      '<div class="uce-tm">' + logo(m.a.logo) + '<span class="n">' + esc(m.a.n) + '</span>' + flag(m.a.c) + '<span class="uce-elo">' + m.a.elo + " " + tr(m.a.tr) + '</span></div></div>' +
      '<div class="uce-probs">' + probBar(m.prob) + '</div>' +
      '<div class="uce-pick"><b>' + m.pick + '</b><small>' + esc(pickLabel(m.pick)) + " · " + pct0(m.pick_prob) + '</small>' + conf(m.conf) + '</div>' +
      '<div class="uce-extra"><span>Marcador más probable <b>' + esc(m.score) + '</b></span><span>Doble oportunidad <b>' + m.dc + "</b> (" + pct0(m.dc_prob) + ')</span>' +
      '<span>Ambos marcan <b>' + pct0(m.btts) + '</b></span><span>Más de 2,5 goles <b>' + pct0(m.over25) + '</b></span>' +
      (m.venue ? '<span>Estadio <b>' + esc(m.venue) + "</b></span>" : "") + "</div></div>";
  }

  function viewPicks(root, d, o) {
    var list = d.upcoming.filter(function (m) { return matchesCountry(m, o.country); });
    if (o.md === "next" && list.length) {
      var first = list[0].md; list = list.filter(function (m) { return m.md === first; });
    }
    var state = { q: "", strong: false };
    root.innerHTML = '<div class="uce-tools"><input class="uce-search" type="search" placeholder="Buscar equipo…" aria-label="Buscar equipo">' +
      '<button class="uce-pill" type="button" data-f="strong">Solo confianza 7+</button></div><div class="uce-list"></div>';
    var box = root.querySelector(".uce-list");
    function draw() {
      var q = state.q.toLowerCase();
      var rows = list.filter(function (m) {
        return (!state.strong || m.conf >= 7) && (!q || (m.h.n + " " + m.a.n).toLowerCase().indexOf(q) >= 0);
      });
      if (o.max) rows = rows.slice(0, o.max);
      if (!rows.length) { box.innerHTML = '<div class="uce-empty">' + (list.length ? "No hay partidos con ese filtro." : "No hay partidos de Champions en los próximos días. Los pronósticos aparecen en cuanto se acerca la siguiente jornada.") + "</div>"; return; }
      var h = "", last = "";
      rows.forEach(function (m) { var k = dayKey(m.date); if (k !== last) { h += '<div class="uce-day">' + esc(dayLabel(m.date)) + "</div>"; last = k; } h += matchRow(m); });
      box.innerHTML = h;
    }
    root.querySelector(".uce-search").addEventListener("input", function (e) { state.q = e.target.value; draw(); });
    root.querySelector('[data-f="strong"]').addEventListener("click", function (e) { state.strong = !state.strong; e.currentTarget.classList.toggle("on", state.strong); draw(); });
    draw();
  }

  function viewCards(root, d, o) {
    var list = d.upcoming.filter(function (m) { return matchesCountry(m, o.country); }).slice();
    list.sort(function (a, b) { return b.pick_prob - a.pick_prob; });
    list = list.slice(0, o.max || 6);
    if (!list.length) { root.innerHTML = '<div class="uce-empty">Las tarjetas destacadas aparecen cuando se acerca la próxima jornada de Champions.</div>'; return; }
    root.innerHTML = '<div class="uce-cards">' + list.map(function (m) {
      return '<article class="uce-card' + (m.conf >= 8 ? " hot" : "") + '"><div class="uce-when"><span>' + esc(dayLabel(m.date)).replace(/^(\w)/, function (c) { return c.toUpperCase(); }) + " · " + hour(m.date) + "</span><span>" + (m.md ? "Jornada " + m.md : esc(m.round)) + '</span></div>' +
        '<div class="uce-vs"><div class="t">' + logo(m.h.logo) + '<span>' + esc(m.h.n) + '</span></div><div class="sc">' + esc(m.score) + '<small>marcador</small></div><div class="t">' + logo(m.a.logo) + '<span>' + esc(m.a.n) + "</span></div></div>" +
        probBar(m.prob) +
        '<div class="uce-pk"><span>Pronóstico: <b>' + esc(pickName(m)) + "</b> (" + pct0(m.pick_prob) + ")</span>" + conf(m.conf) + "</div></article>";
    }).join("") + "</div>";
  }

  function viewTable(root, d, o) {
    var t = d.table.filter(function (r) { return !o.country || r.c === o.country; });
    if (!t.length) { root.innerHTML = '<div class="uce-empty">La clasificación aparece cuando se sortea la fase liga.</div>'; return; }
    var lpDone = d.phase.lp_done >= d.phase.lp_total;
    var h = '<div class="uce-scroll"><table class="uce-tbl"><thead><tr><th class="c">#</th><th>Equipo</th><th class="c">PJ</th><th class="c">G</th><th class="c">E</th><th class="c">P</th><th class="c">DG</th><th class="c">Pts</th>' +
      (lpDone ? "" : '<th class="r" title="Puntos esperados al final de la fase liga">Pts esp.</th><th class="r">Top 8</th><th class="r">Playoff</th><th class="r">Fuera</th>') +
      '<th class="r">Octavos</th><th class="r">Gana</th><th>Forma</th><th>Próximo</th></tr></thead><tbody>';
    t.forEach(function (r) {
      var z = r.pos <= 8 ? "uce-z1" : (r.pos <= 24 ? "uce-z2" : "uce-z3");
      h += '<tr class="' + z + '"><td class="c">' + r.pos + '</td><td class="tn"><span class="uce-tm">' + logo(r.logo) + '<span class="n">' + esc(r.n) + "</span>" + flag(r.c) + "</span></td>" +
        '<td class="c">' + r.pj + '</td><td class="c">' + r.g + '</td><td class="c">' + r.e + '</td><td class="c">' + r.p + '</td><td class="c">' + (r.dg > 0 ? "+" : "") + r.dg + '</td><td class="c"><b>' + r.pts + "</b></td>" +
        (lpDone ? "" : '<td class="r">' + String(r.sim.xpts).replace(".", ",") + '</td><td class="r"><span class="uce-pct" style="' + heat(r.sim.top8) + '">' + pct0(r.sim.top8) + '</span></td><td class="r"><span class="uce-pct" style="' + heat(r.sim.po) + '">' + pct0(r.sim.po) + '</span></td><td class="r"><span class="uce-pct" style="' + heat(r.sim.out) + '">' + pct0(r.sim.out) + "</span></td>") +
        '<td class="r"><span class="uce-pct" style="' + heat(r.sim.r16) + '">' + pct0(r.sim.r16) + '</span></td><td class="r"><span class="uce-pct" style="' + heat(r.sim.win * 3) + '">' + pct0(r.sim.win) + "</span></td>" +
        '<td><span class="uce-form">' + (r.form || []).map(function (f) { return '<i class="' + f + '">' + f + "</i>"; }).join("") + "</span></td>" +
        "<td>" + (r.next ? esc(r.next.vs) + ' <span class="uce-muted">' + (r.next.home ? "(casa)" : "(fuera)") + "</span>" : "—") + "</td></tr>";
    });
    h += "</tbody></table></div>" +
      '<div class="uce-legend"><span><i style="background:var(--ok)"></i>1-8: octavos directos</span><span><i style="background:var(--warn)"></i>9-24: playoff</span><span><i style="background:var(--bad)"></i>25-36: eliminado</span></div>' +
      '<p class="uce-note">Probabilidades calculadas simulando ' + (d.model.sims || 10000).toLocaleString("es-ES") + " veces el resto de la Champions con el rating Elo de cada equipo. El cuadro de eliminatorias es aproximado.</p>";
    root.innerHTML = h;
  }

  function viewTitle(root, d, o) {
    var t = d.title.filter(function (r) { return !o.country || r.c === o.country; }).slice(0, o.max || 16);
    if (!t.length) { root.innerHTML = '<div class="uce-empty">Los favoritos aparecen cuando se sortea la fase liga.</div>'; return; }
    var mx = Math.max.apply(null, t.map(function (r) { return r.win; })) || 1;
    root.innerHTML = '<div class="uce-box">' + t.map(function (r, i) {
      return '<div class="uce-fav"><span class="pos">' + (i + 1) + '</span><div><span class="uce-tm">' + logo(r.logo) + '<span class="n">' + esc(r.n) + "</span>" + flag(r.c) + '<span class="uce-elo">Elo ' + r.elo + "</span></span>" +
        '<div class="bar"><i style="width:' + (100 * r.win / mx).toFixed(1) + '%"></i></div><div class="uce-muted" style="margin-top:4px">Final ' + pct0(r.final) + " · Semis " + pct0(r.sf) + " · Cuartos " + pct0(r.qf) + '</div></div><span class="v">' + pct0(r.win) + "</span></div>";
    }).join("") + '</div><p class="uce-note">Probabilidad de ganar la Champions según ' + (d.model.sims || 10000).toLocaleString("es-ES") + " simulaciones del torneo.</p>";
  }

  function spark(v) {
    if (!v || v.length < 2) return "";
    var mn = Math.min.apply(null, v), mx = Math.max.apply(null, v), w = 70, h = 20, r = mx - mn || 1;
    var pts = v.map(function (x, i) { return (i * w / (v.length - 1)).toFixed(1) + "," + (h - 2 - (x - mn) / r * (h - 4)).toFixed(1); }).join(" ");
    var col = v[v.length - 1] >= v[0] ? "#4ade80" : "#f87171";
    return '<svg class="uce-spark" width="' + w + '" height="' + h + '" viewBox="0 0 ' + w + " " + h + '" aria-hidden="true"><polyline fill="none" stroke="' + col + '" stroke-width="1.6" points="' + pts + '"/></svg>';
  }

  function viewElo(root, d, o) {
    var src = o.scope === "europe" ? d.elo_europe : d.elo_cl;
    var t = src.filter(function (r) { return !o.country || r.c === o.country; }).slice(0, o.max || 60);
    if (!t.length) { root.innerHTML = '<div class="uce-empty">Sin datos todavía.</div>'; return; }
    root.innerHTML = '<div class="uce-scroll"><table class="uce-tbl"><thead><tr><th class="c">#</th><th>Equipo</th><th class="r">Elo</th><th class="r">30 días</th><th>Tendencia</th></tr></thead><tbody>' +
      t.map(function (r, i) {
        return '<tr><td class="c">' + (i + 1) + '</td><td class="tn"><span class="uce-tm">' + logo(r.logo) + '<span class="n">' + esc(r.n) + "</span>" + flag(r.c) + '</span></td><td class="r"><b>' + r.elo + '</b></td><td class="r ' + (r.d30 > 0 ? "uce-up" : (r.d30 < 0 ? "uce-down" : "")) + '">' + (r.d30 > 0 ? "+" : "") + r.d30 + "</td><td>" + spark(r.spark) + "</td></tr>";
      }).join("") + "</tbody></table></div>";
  }

  function viewResults(root, d, o) {
    var list = d.recent;
    if (!list.length) { root.innerHTML = '<div class="uce-empty">Aún no hay pronósticos liquidados.</div>'; return; }
    var n = o.max || 30;
    function draw() {
      root.innerHTML = statsBox(d) + '<div class="uce-box">' + list.slice(0, n).map(function (p) {
        return '<div class="uce-res"><span class="uce-muted">' + shortDate(p.date) + "<br>" + (p.md ? "J" + p.md : esc(p.round)) + "</span>" +
          '<span><span class="uce-tm">' + logo(p.hl) + '<span class="n">' + esc(p.h) + '</span></span><span class="uce-tm">' + logo(p.al) + '<span class="n">' + esc(p.a) + "</span></span></span>" +
          '<b style="font-family:Unbounded,sans-serif">' + esc(p.final) + '</b><span class="pk uce-muted">Pron. <b style="color:var(--ink)">' + p.pick + "</b><br>" + pct0(p.pick_prob) + "</span>" +
          '<span class="' + (p.win ? "uce-ok" : "uce-ko") + '">' + (p.win ? "✓" : "✗") + "</span></div>";
      }).join("") + "</div>" + (list.length > n ? '<button class="uce-more" type="button">Ver más</button>' : "") +
        (d.retro ? '<p class="uce-note">Los partidos jugados antes de abrir la web se han pronosticado después, con el Elo que tenía cada equipo justo antes del partido.</p>' : "");
      var b = root.querySelector(".uce-more"); if (b) b.addEventListener("click", function () { n += 30; draw(); });
    }
    draw();
  }

  function updated(d) {
    return '<p class="uce-note">Actualizado: ' + esc(fmt(new Date(d.generated), { day: "numeric", month: "long", hour: "2-digit", minute: "2-digit" })) + " (hora peninsular) · " + (d.model.matches || 0).toLocaleString("es-ES") + " partidos analizados</p>";
  }

  function viewAll(root, d, o) {
    var tabs = [["picks", "Pronósticos"], ["table", "Clasificación"], ["title", "Favoritos"], ["elo", "Ranking Elo"], ["results", "Aciertos"]];
    root.innerHTML = '<div class="uce-tabs" role="tablist">' + tabs.map(function (t, i) { return '<button class="uce-tab' + (i ? "" : " on") + '" type="button" role="tab" data-t="' + t[0] + '">' + t[1] + "</button>"; }).join("") + '</div><div class="uce-pane"></div>' + updated(d);
    var pane = root.querySelector(".uce-pane");
    function show(v) { pane.innerHTML = ""; var inner = document.createElement("div"); pane.appendChild(inner); VIEWS[v](inner, d, { country: o.country, scope: "cl" }); }
    [].forEach.call(root.querySelectorAll(".uce-tab"), function (b) {
      b.addEventListener("click", function () { [].forEach.call(root.querySelectorAll(".uce-tab"), function (x) { x.classList.toggle("on", x === b); }); show(b.getAttribute("data-t")); });
    });
    show("picks");
  }

  var VIEWS = {
    all: viewAll, picks: viewPicks, cards: viewCards, table: viewTable, title: viewTitle, elo: viewElo, results: viewResults,
    stats: function (root, d) { root.innerHTML = statsBox(d); }
  };

  function render(node, d) {
    var o = { view: node.getAttribute("data-view") || "all", max: parseInt(node.getAttribute("data-max") || "0", 10) || 0,
      country: node.getAttribute("data-country") || "", scope: node.getAttribute("data-scope") || "cl", md: node.getAttribute("data-md") || "" };
    node.classList.add("uce");
    var fn = VIEWS[o.view] || viewAll;
    try { fn(node, d, o); } catch (e) { node.innerHTML = '<div class="uce-empty">No se han podido mostrar los datos.</div>'; if (window.console) console.error(e); }
    // cifras sueltas para la cabecera de la portada: <span data-uce="rate|strong|season|matches|next"></span>
  }

  function fillFigures(d) {
    var nxt = d.upcoming[0];
    var map = {
      rate: d.stats.season.n ? pct0(d.stats.season.rate) : "—",
      strong: d.stats.season_strong.n ? pct0(d.stats.season_strong.rate) : "—",
      season: d.season, matches: (d.model.matches || 0).toLocaleString("es-ES"),
      fav: d.title[0] ? d.title[0].n + " (" + pct0(d.title[0].win) + ")" : "—",
      next: nxt ? nxt.h.n + " – " + nxt.a.n : "—",
      md: d.phase.lp_total ? (d.phase.lp_done >= d.phase.lp_total ? "Eliminatorias" : "Jornada " + Math.min(8, (d.phase.md_done || 0) + 1)) : "—"
    };
    [].forEach.call(document.querySelectorAll("[data-uce]"), function (n) { var k = n.getAttribute("data-uce"); if (map[k] != null) n.textContent = map[k]; });
  }

  function boot() {
    var nodes = document.querySelectorAll(".uce-app, #uce-app");
    var figs = document.querySelectorAll("[data-uce]");
    if (!nodes.length && !figs.length) return;
    if (!document.getElementById("uce-css")) {
      var st = document.createElement("style"); st.id = "uce-css"; st.textContent = CSS; document.head.appendChild(st);
    }
    [].forEach.call(nodes, function (n) { n.classList.add("uce"); n.innerHTML = '<div class="uce-load">Cargando pronósticos…</div>'; });
    var url = BASE + "data.json?v=" + Math.floor(Date.now() / 600000);
    fetch(url).then(function (r) { return r.json(); }).then(function (d) {
      [].forEach.call(nodes, function (n) { render(n, d); });
      fillFigures(d);
    }).catch(function () {
      [].forEach.call(nodes, function (n) { n.innerHTML = '<div class="uce-empty">No se han podido cargar los datos. Prueba a recargar la página.</div>'; });
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();
