
const API = "/api";

function $(id) { return document.getElementById(id); }

function showSkeleton(elId, count) {
  const el = $(elId);
  if (!el) return;
  el.innerHTML = '<div class="skeleton skeleton-card"></div>'.repeat(count || 4);
}

function fadeIn(el) {
  if (!el) return;
  el.classList.remove('section-fade-in');
  void el.offsetWidth;
  el.classList.add('section-fade-in');
}

function setActiveTab(btn) {
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  if (btn) btn.classList.add("active");
}

function goHome() {
  $("results").innerHTML = "";
  $("homeGrid").style.display = "grid";
  window.__currentSection = "";
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
  document.querySelector(".nav-item:first-child")?.classList.add("active");
}

function closeModal() {
  $("modal").classList.remove("active");
}

function showModal(html) {
  $("modalContent").innerHTML = html;
  $("modal").classList.add("active");
}

$("modal")?.addEventListener("click", function(e) {
  if (e.target === this) closeModal();
});

// ─── BÚSQUEDA GLOBAL ─────────────────────────────────────────

async function globalSearchFn() {
  const q = document.getElementById("globalSearch").value.trim();
  if (!q) return;
  const resultsDiv = document.getElementById("results");
  let html = "<h3 style='margin-bottom:12px;font-size:16px'>🔍 Resultados</h3>";

  // Buscar protocolos
  try {
    const protos = await (await fetch(`${API}/protocols?q=${q}`)).json();
    if (protos.length > 0) {
      html += "<div class='section'><div class='section-header'>Protocolos</div><div class='section-body'>";
      protos.forEach(p => {
        html += `<div class='cmd-item'><div class='cmd'>${p.name}</div><div class='desc'>${p.description}</div></div>`;
      });
      html += "</div></div>";
    }
  } catch(e) {}

  // Buscar puertos
  try {
    const ports = await (await fetch(`${API}/ports?q=${q}`)).json();
    if (Object.keys(ports).length > 0) {
      html += "<div class='section'><div class='section-header'>Puertos</div><div class='section-body'>";
      for (const [port, svc] of Object.entries(ports)) {
        html += `<div class='cmd-item'><div class='cmd'>${port}</div><div class='desc'>${svc}</div></div>`;
      }
      html += "</div></div>";
    }
  } catch(e) {}

  // Buscar comandos
  for (const vendor of ["cisco","mikrotik","fortinet","linux","windows","cctv"]) {
    try {
      const cmds = await (await fetch(`${API}/commands?vendor=${vendor}&q=${q}`)).json();
      const entries = Object.entries(cmds);
      if (entries.length > 0) {
        html += `<div class='section'><div class='section-header'>${vendor.toUpperCase()}</div><div class='section-body'>`;
        entries.forEach(([cat, subcats]) => {
          if (Array.isArray(subcats)) {
            subcats.forEach(({cmd, desc}) => {
              html += `<div class='cmd-item'><div class='cmd'>${cmd}</div><div class='desc'>${desc}</div></div>`;
            });
          } else {
            Object.entries(subcats).forEach(([subcat, items]) => {
              items.forEach(({cmd, desc}) => {
                html += `<div class='cmd-item'><div class='cmd'>${cmd}</div><div class='desc'>${desc}</div></div>`;
              });
            });
          }
        });
        html += "</div></div>";
      }
    } catch(e) {}
  }

  if (html === "<h3 style='margin-bottom:12px;font-size:16px'>🔍 Resultados</h3>") {
    html += '<div class="empty-state"><div class="empty-text text-muted">Sin resultados</div></div>';
  }
  resultsDiv.innerHTML = html;
  fadeIn(resultsDiv);
}

// ─── SECCIONES ───────────────────────────────────────────────

window.__sectionCache = {};
window.__currentSection = "";

async function openSection(name) {
  const resultsDiv = $("results");
  $("homeGrid").style.display = "none";
  if (window.__currentSection) {
    window.__sectionCache[window.__currentSection] = resultsDiv.innerHTML;
  }
  window.__currentSection = name;
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
  const navMap = {scanner:1, tools:2, commands:3, speedtest:4};
  const idx = navMap[name];
  if (idx !== undefined) document.querySelectorAll(".nav-item")[idx]?.classList.add("active");
  if (window.__sectionCache[name]) {
    resultsDiv.innerHTML = window.__sectionCache[name];
    fadeIn(resultsDiv);
    return;
  }
  showSkeleton("results", 6);
  if (name === "protocols") {
    const protos = await (await fetch(`${API}/protocols`)).json();
    let html = '<h3 class="section-title">🌐 Protocolos de Red</h3>';
    html += "<div class='input-group'><input type='text' placeholder='Filtrar protocolos...' oninput='filterProtos(this.value)'></div>";
    html += "<div id='protoList'>";
    protos.forEach(p => {
      html += `<div class='card' style='text-align:left;margin-bottom:6px;padding:10px 14px' onclick='showProto("${p}")'>
        <div style='font-weight:600;font-size:14px'>${p}</div>
      </div>`;
    });
    html += "</div>";
    resultsDiv.innerHTML = html;
    fadeIn(resultsDiv);
  }
  else if (name === "ports") {
    const ports = await (await fetch(`${API}/ports`)).json();
    let html = '<h3 class="section-title">🔌 Puertos Comunes</h3>';
    html += "<div class='input-group'><input type='text' placeholder='Buscar puerto (ej: 443 o HTTP)...' oninput='searchPorts(this.value)'></div>";
    html += "<div id='portsList'>";
    for (const [port, svc] of Object.entries(ports)) {
      html += `<div class='cmd-item'><span class='badge badge-accent'>${port}</span> <span style='margin-left:8px'>${svc}</span></div>`;
    }
    html += "</div>";
    resultsDiv.innerHTML = html;
    fadeIn(resultsDiv);
  }
  else if (name === "commands") {
    resultsDiv.innerHTML = `
      <h3 class="section-title">⌨️ Comandos por Fabricante</h3>
      <div class='tabs'>
        <button class='tab active' onclick='loadCommands("cisco",this)'>Cisco</button>
        <button class='tab' onclick='loadCommands("mikrotik",this)'>MikroTik</button>
        <button class='tab' onclick='loadCommands("fortinet",this)'>Fortinet</button>
        <button class='tab' onclick='loadCommands("linux",this)'>Linux</button>
        <button class='tab' onclick='loadCommands("windows",this)'>Windows</button>
        <button class='tab' onclick='loadCommands("cctv",this)'>CCTV</button>
      </div>
      <div class='input-group'><input type='text' id='cmdSearch' placeholder='Buscar comando...' oninput='filterCommands(this.value)'></div>
      <div id='cmdList'></div>
    `;
    loadCommands("cisco", document.querySelector(".tab"));
  }
  else if (name === "calculators") {
    resultsDiv.innerHTML = `
      <h3 style='margin-bottom:12px'>🧮 Calculadoras Técnicas</h3>
      <div class='tabs'>
        <button class='tab active' onclick='showCalcs(\"network\",this)'>Redes</button>
        <button class='tab' onclick='showCalcs(\"conversions\",this)'>Conversión</button>
        <button class='tab' onclick='showCalcs(\"electrical\",this)'>Electrónica</button>
        <button class='tab' onclick='showCalcs(\"cctv\",this)'>CCTV</button>
      </div>
      <div id='calcList'></div>
    `;
    showCalcs("network", document.querySelector(".tab"));
  }
  else if (name === "cctv") {
    resultsDiv.innerHTML = `
      <h3 style='margin-bottom:12px'>📷 APIs CCTV - Conexión en Vivo</h3>
      <div class='tabs'>
        <button class='tab active' onclick='showCCTVForm(\"hikvision\",this)'>Hikvision</button>
        <button class='tab' onclick='showCCTVForm(\"dahua\",this)'>Dahua</button>
        <button class='tab' onclick='showCCTVForm(\"zkteco\",this)'>ZKTeco</button>
      </div>
      <div id='cctvForm'></div>
      <div id='cctvResult'></div>
    `;
    showCCTVForm("hikvision", document.querySelector(".tab"));
  }
  else if (name === "diagnostics") {
    const diags = await (await fetch(`${API}/diagnostics`)).json();
    let html = '<h3 class="section-title">🔍 Procedimientos de Diagnóstico</h3>';
    html += "<div class='input-group'><input type='text' placeholder='Filtrar diagnósticos...' oninput='filterDiagnostics(this.value)'></div>";
    html += "<div id='diagList'>";
    diags.forEach(d => {
      const safeId = d.replace(/[^a-zA-Z0-9]/g, "_");
      html += `<div class='card diag-card' style='text-align:left;margin-bottom:6px;padding:12px 14px' id='diag_${safeId}' onclick='showDiagnostic("${d.replace(/"/g, "&quot;")}")'>
        <div style='font-weight:600'>${d}</div>
      </div>`;
    });
    html += "</div>";
    resultsDiv.innerHTML = html;
    fadeIn(resultsDiv);
  }
  else if (name === "scanner") { showScanner(); }
  else if (name === "speedtest") { showSpeedtest(); }
  else if (name === "mac") { showMAC(); }
  else if (name === "tools") { showTools(); }
  else if (name === "snmp") { showSNMP(); }
  else if (name === "ipam") { showIPAM(); }
  else if (name === "topology") { showTopology(); }
  else if (name === "access-control") {
    resultsDiv.innerHTML = `
      <h3 style='margin-bottom:12px'>🚪 Control de Acceso</h3>
      <div class='tabs'>
        <button class='tab active' onclick='showACForm("hikvision",this)'>Hikvision</button>
        <button class='tab' onclick='showACForm("dahua",this)'>Dahua</button>
        <button class='tab' onclick='showACForm("zkteco",this)'>ZKTeco</button>
        <button class='tab' onclick='showACForm("lenel",this)'>Lenel</button>
        <button class='tab' onclick='showACForm("paxton",this)'>Paxton</button>
        <button class='tab' onclick='showACForm("hid",this)'>HID</button>
        <button class='tab' onclick='showACForm("gallagher",this)'>Gallagher</button>
        <button class='tab' onclick='showACForm("avigilon",this)'>Avigilon</button>
        <button class='tab' onclick='showACForm("aperio",this)'>Aperio</button>
        <button class='tab' onclick='showACForm("salto",this)'>SALTO</button>
        <button class='tab' onclick='showACForm("nedap",this)'>Nedap</button>
        <button class='tab' onclick='showACForm("2n",this)'>2N</button>
        <button class='tab' onclick='showACForm("kantech",this)'>Kantech</button>
        <button class='tab' onclick='showACForm("dormakaba",this)'>Dormakaba</button>
        <button class='tab' onclick='showACForm("bosch",this)'>Bosch</button>
        <button class='tab' onclick='showACForm("siemens",this)'>Siemens</button>
        <button class='tab' onclick='showACForm("cdvi",this)'>CDVI</button>
        <button class='tab' onclick='showACForm("schneider",this)'>Schneider</button>
        <button class='tab' onclick='showACForm("johnson",this)'>Johnson</button>
        <button class='tab' onclick='showACForm("stanley",this)'>Stanley</button>
        <button class='tab' onclick='showACForm("wiegand",this)'>Wiegand</button>
      </div>
      <div id='acForm'></div>
      <div id='acResult'></div>
    `;
    showACForm("hikvision", document.querySelector(".tab"));
  }
  else if (name === "scripts") {
    resultsDiv.innerHTML = `
      <h3 style='margin-bottom:12px'>🐍 Scripts Python</h3>
      <div class='tabs'>
        <button class='tab active' onclick='showScripts(\"network\",this)'>Network</button>
        <button class='tab' onclick='showScripts(\"dhcp\",this)'>DHCP</button>
        <button class='tab' onclick='showScripts(\"dns\",this)'>DNS</button>
        <button class='tab' onclick='showScripts(\"security\",this)'>Seguridad</button>
        <button class='tab' onclick='showScripts(\"system\",this)'>System</button>
      </div>
      <div id='scriptsList'></div>
    `;
    showScripts("network", document.querySelector(".tab"));
  }
  else if (name === "ups") {
    resultsDiv.innerHTML = `
      <h3 style='margin-bottom:12px'>🔋 UPS - Monitoreo y Gestión</h3>

        <div class='section-header'>🌐 Zabbix Server (conexión remota)</div>
        <div style='margin:6px 0;padding:6px;background:#1e1e2e;border-radius:6px'>
          <div class='input-group'><label>URL API</label><input type='text' id='zabbix_api_url' value='http://localhost:8080/api_jsonrpc.php'></div>
          <div class='input-group'><label>Usuario</label><input type='text' id='zabbix_user' value='Admin'></div>
          <div class='input-group'><label>Password</label><input type='password' id='zabbix_pass' value='zabbix'></div>
          <button class='btn' onclick='zabbixConnect()'>🔌 Conectar y listar UPS</button>
          <button class='btn btn-outline' style='margin-left:6px' onclick='zabbixAlerts()'>🚨 Alertas activas</button>
        </div>
        <div id='zabbixHosts' style='margin:4px 0'></div>

        <div class='section-header'>🔋 Estimación de Vida de Batería</div>
        <div style='margin:6px 0;padding:6px;background:#1e1e2e;border-radius:6px'>
          <div class='input-group'><label>Fecha de Fabricación</label><input type='date' id='ups_bat_date'></div>
          <div class='input-group'><label>Tipo</label><select id='ups_bat_type'>
            <option value='VRLA'>VRLA (Plomo-Ácido, 5 años)</option>
            <option value='LI-ION'>Li-Ion (Litio, 10 años)</option>
            <option value='NICD'>NiCd (Níquel-Cadmio, 15 años)</option>
          </select></div>
          <button class='btn btn-outline' onclick='upsBatteryLife()'>🔋 Estimar Vida</button>
        </div>

        <div class='section-header'>🔧 Diagnóstico de UPS</div>
        <div style='margin:6px 0;padding:6px;background:#1e1e2e;border-radius:6px'>
          <button class='btn btn-outline' onclick='upsDiagnostics()'>📋 Ver procedimiento</button>
        </div>

      <div id='upsResult'></div>
    `;
    zabbixCheckSession();
  }
  else if (name === "wifi") { showWiFi(); }
  else if (name === "bandwidth") { showBandwidth(); }
}

// ─── PROTOCOLOS ──────────────────────────────────────────────

async function showProto(name) {
  const p = await (await fetch(`${API}/protocols/${name}`)).json();
  showModal(`
    <button class='modal-close' onclick='closeModal()'>&times;</button>
    <h2>${p.name}</h2>
    <div class='result-box'>
Puerto: ${p.port}
Transporte: ${p.transport}
Capa: ${p.layer}
${p.description}
    </div>
  `);
}

function filterProtos(q) {
  document.querySelectorAll("#protoList .card").forEach(c => {
    c.style.display = c.textContent.toLowerCase().includes(q.toLowerCase()) ? "block" : "none";
  });
}

// ─── PUERTOS ─────────────────────────────────────────────────

async function searchPorts(q) {
  if (!q) return;
  const ports = await (await fetch(`${API}/ports?q=${q}`)).json();
  let html = "";
  for (const [port, svc] of Object.entries(ports)) {
    html += `<div class='cmd-item'><span class='badge badge-accent'>${port}</span> <span style='margin-left:8px'>${svc}</span></div>`;
  }
  document.getElementById("portsList").innerHTML = html || "<p style='color:var(--text2)'>Sin resultados</p>";
}

// ─── COMANDOS ────────────────────────────────────────────────

let allCmdsData = {};

async function loadCommands(vendor, btn) {
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  btn.classList.add("active");
  window._cmdVendor = vendor;
  try {
    allCmdsData = await (await fetch(`${API}/commands?vendor=${vendor}`)).json();
  } catch(e) { allCmdsData = {}; }
  renderCommands("");
}

function renderCommands(q) {
  const div = document.getElementById("cmdList");
  if (!div) return;
  let html = "";
  q = q.toLowerCase();
  const flat = window._cmdVendor === "windows";
  if (flat) {
    for (const [, subcats] of Object.entries(allCmdsData)) {
      if (Array.isArray(subcats)) {
        subcats.forEach(({cmd, desc}) => {
          if (!q || cmd.toLowerCase().includes(q) || desc.toLowerCase().includes(q)) {
            html += `<div class='cmd-item'><div class='cmd'>${cmd}</div><div class='desc'>${desc}</div></div>`;
          }
        });
      } else {
        for (const items of Object.values(subcats)) {
          items.forEach(({cmd, desc}) => {
            if (!q || cmd.toLowerCase().includes(q) || desc.toLowerCase().includes(q)) {
              html += `<div class='cmd-item'><div class='cmd'>${cmd}</div><div class='desc'>${desc}</div></div>`;
            }
          });
        }
      }
    }
    div.innerHTML = html || "<p style='color:var(--text2)'>Sin resultados</p>";
    return;
  }
  for (const [cat, subcats] of Object.entries(allCmdsData)) {
    let catHtml = "";
    if (Array.isArray(subcats)) {
      subcats.forEach(({cmd, desc}) => {
        if (!q || cmd.toLowerCase().includes(q) || desc.toLowerCase().includes(q)) {
          catHtml += `<div class='cmd-item'><div class='cmd'>${cmd}</div><div class='desc'>${desc}</div></div>`;
        }
      });
    } else {
      for (const [subcat, items] of Object.entries(subcats)) {
        let subHtml = "";
        items.forEach(({cmd, desc}) => {
          if (!q || cmd.toLowerCase().includes(q) || desc.toLowerCase().includes(q)) {
            subHtml += `<div class='cmd-item'><div class='cmd'>${cmd}</div><div class='desc'>${desc}</div></div>`;
          }
        });
        if (subHtml) {
           catHtml += `<div class='text-accent2 text-sm fw-600' style='margin-top:8px;margin-bottom:4px'>${subcat}</div>${subHtml}`;
        }
      }
    }
    if (catHtml) {
      html += `<div class='section'><div class='section-header'>${cat}</div><div class='section-body'>${catHtml}</div></div>`;
    }
  }
  div.innerHTML = html || "<p style='color:var(--text2)'>Sin resultados</p>";
}

function filterCommands(q) { renderCommands(q); }

// ─── CALCULADORAS ────────────────────────────────────────────

async function showCalcs(cat, btn) {
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  if (btn) btn.classList.add("active");
  const data = await (await fetch(`${API}/calculators?cat=${cat}`)).json();
  let html = "";
  for (const [name, info] of Object.entries(data)) {
    html += `<div class='card' style='text-align:left;margin-bottom:6px;padding:12px 14px' onclick='runCalc("${name}","${cat}",${JSON.stringify(info.params)})'>
      <div style='font-weight:600;font-size:14px'>${name}</div>
      <div style='font-size:11px;color:var(--text2)'>${info.params.join(", ")}</div>
    </div>`;
  }
  if (cat === "cctv") {
    // Replace generic cards with dedicated CCTV calculator
    renderCCTCCalculator(data);
    return;
  }
  document.getElementById("calcList").innerHTML = html;
}

function runCalc(name, cat, params) {
  let inputs = params.map(p => {
    let pname = p.replace("[","").replace("]","");
    return `<div class='input-group'><label>${pname}</label><input type='text' id='calc_${pname}' placeholder='${pname}'></div>`;
  }).join("");
  showModal(`
    <button class='modal-close' onclick='closeModal()'>&times;</button>
    <h2>${name}</h2>
    ${inputs}
    <button class='btn' onclick='execCalc("${name}","${cat}","${JSON.stringify(params)}")'>Calcular</button>
    <div id='calcResult'></div>
  `);
}

async function execCalc(name, cat, paramsStr) {
  const params = JSON.parse(paramsStr);
  const queryParams = new URLSearchParams();
  queryParams.set("calc", name);
  params.forEach(p => {
    const pname = p.replace("[","").replace("]","");
    const val = document.getElementById(`calc_${pname}`)?.value;
    if (val) {
      if (p.endsWith("[]")) {
        val.split(",").forEach(v => queryParams.append(p.replace("[]",""), v.trim()));
      } else {
        queryParams.set(p, val);
      }
    }
  });
  try {
    const resp = await (await fetch(`${API}/calculators/run?${queryParams}`)).json();
    const resultDiv = document.getElementById("calcResult");
    if (resp.error) {
      resultDiv.innerHTML = `<div class='result-box' style='color:var(--danger)'>Error: ${resp.error}</div>`;
    } else {
      resultDiv.innerHTML = `<div class='result-box'>${JSON.stringify(resp.result, null, 2)}</div>`;
    }
  } catch(e) {
    document.getElementById("calcResult").innerHTML = `<div class='result-box' style='color:var(--danger)'>Error: ${e.message}</div>`;
  }
}

// ─── CCTV CALCULATOR ────────────────────────────────────────────

async function renderCCTCCalculator(data) {
  const opts = data.cctv_calc.options;
  const resOptions = opts.resolutions.map(r =>
    `<option value="${r}">${r} (${opts.res_info[r]})</option>`
  ).join("");
  const codecOptions = opts.codecs.map(c =>
    `<option value="${c}">${c}</option>`
  ).join("");
  const smartOptions = opts.smart_codecs.map(s =>
    `<option value="${s}">${s}</option>`
  ).join("");
  const sceneOptions = opts.scenes.map(s =>
    `<option value="${s}">${s}</option>`
  ).join("");
  const poeOptions = Object.entries(opts.poe_profiles || {Genérico: 7.5}).map(([name, watts]) =>
    `<option value="${name}" data-watts="${watts}">${name} (${watts}W)</option>`
  ).join("");
  const nvrOptions = Object.entries(opts.nvr_channels || {}).map(([label, channels]) =>
    `<option value="${channels}">${label} (${channels} canales)</option>`
  ).join("");

  let groupRow = (idx, qty = 4) => `
    <div class='cctv-group-row' id='cg_${idx}'>
      <div class='cctv-group-head'>
        <div class='cctv-group-title'>Grupo ${idx + 1}</div>
        <button class='btn btn-outline cctv-remove-btn' onclick='removeCCTVGroup(${idx})'>✕</button>
      </div>
      <div class='cctv-mini-grid'>
        <div class='cctv-mini-field'>
          <label>Cant.</label>
          <input type='number' id='cg_${idx}_qty' value='${qty}' min='1' max='999'>
        </div>
        <div class='cctv-mini-field wide'>
          <label>Resolución</label>
          <select id='cg_${idx}_res'>${resOptions}</select>
        </div>
        <div class='cctv-mini-field'>
          <label>Codec</label>
          <select id='cg_${idx}_codec'>${codecOptions}</select>
        </div>
        <div class='cctv-mini-field'>
          <label>FPS</label>
          <input type='number' id='cg_${idx}_fps' value='15' min='1' max='60'>
        </div>
        <div class='cctv-mini-field wide'>
          <label>Smart Codec</label>
          <select id='cg_${idx}_smart'>${smartOptions}</select>
        </div>
        <div class='cctv-mini-field'>
          <label>Escena</label>
          <select id='cg_${idx}_scene'>${sceneOptions}</select>
        </div>
        <div class='cctv-mini-field wide'>
          <label>PoE</label>
          <select id='cg_${idx}_poe' onchange='syncCCTVPoeWatts(${idx})'>${poeOptions}</select>
        </div>
        <div class='cctv-mini-field'>
          <label>W</label>
          <input type='number' id='cg_${idx}_poe_w' value='7.5' min='0' step='0.1'>
        </div>
      </div>
    </div>`;

  let rowHtml = groupRow(0);

  document.getElementById("calcList").innerHTML = `
    <div class='section'>
      <div class='section-header'>📷 Grupos de Cámaras
        <button class='btn btn-outline cctv-add-btn' onclick='addCCTVGroup()'>+ Agregar grupo</button>
      </div>
      <div class='section-body'>
        <div class='cctv-group-list' id='cctvGroupBody'>
          ${rowHtml}
        </div>
      </div>
    </div>
    <div class='section'>
      <div class='section-header'>⚙️ Configuración Global</div>
      <div class='section-body'>
        <div style='display:flex;flex-wrap:wrap;gap:12px'>
          <div class='input-group' style='flex:1;min-width:120px'><label>Grabación (h/día)</label><input type='number' id='cc_hours' value='24' min='1' max='24'></div>
          <div class='input-group' style='flex:1;min-width:120px'><label>Movimiento (%)</label><input type='number' id='cc_motion' value='100' min='1' max='100'></div>
          <div class='input-group' style='flex:1;min-width:120px'><label>Retención (días)</label><input type='number' id='cc_days' value='30' min='1' max='9999'></div>
          <div class='input-group' style='flex:1;min-width:120px'><label>Disco disponible (GB)</label><input type='number' id='cc_storage' value='2000' min='1'></div>
          <div class='input-group' style='flex:1;min-width:120px'><label>Canales NVR</label><select id='cc_nvr'><option value=''>Sin límite</option>${nvrOptions}</select></div>
        </div>
      </div>
    </div>
    <div style='display:flex;gap:8px;flex-wrap:wrap;margin:12px 0'>
      <button class='btn' onclick='execCCTCCalc()'>📊 Calcular Todo</button>
    </div>
    <div id='groupCount' style='font-size:12px;color:var(--text2);margin-bottom:8px;display:none'></div>
    <div id='cctcCalcResult'></div>
  `;

  window._cctvGroupCount = 1;
  updateBitratePreview(0);
}

function addCCTVGroup() {
  const idx = window._cctvGroupCount;
  const opts = null; // will be fetched from DOM
  const resOptions = document.querySelector('#cg_0_res')?.innerHTML || "";
  const codecOptions = document.querySelector('#cg_0_codec')?.innerHTML || "";
  const smartOptions = document.querySelector('#cg_0_smart')?.innerHTML || "";
  const sceneOptions = document.querySelector('#cg_0_scene')?.innerHTML || "";
  const poeOptions = document.querySelector('#cg_0_poe')?.innerHTML || "";
  const row = `
    <div class='cctv-group-row' id='cg_${idx}'>
      <div class='cctv-group-head'>
        <div class='cctv-group-title'>Grupo ${idx + 1}</div>
        <button class='btn btn-outline cctv-remove-btn' onclick='removeCCTVGroup(${idx})'>✕</button>
      </div>
      <div class='cctv-mini-grid'>
        <div class='cctv-mini-field'>
          <label>Cant.</label>
          <input type='number' id='cg_${idx}_qty' value='1' min='1' max='999'>
        </div>
        <div class='cctv-mini-field wide'>
          <label>Resolución</label>
          <select id='cg_${idx}_res'>${resOptions}</select>
        </div>
        <div class='cctv-mini-field'>
          <label>Codec</label>
          <select id='cg_${idx}_codec'>${codecOptions}</select>
        </div>
        <div class='cctv-mini-field'>
          <label>FPS</label>
          <input type='number' id='cg_${idx}_fps' value='15' min='1' max='60'>
        </div>
        <div class='cctv-mini-field wide'>
          <label>Smart Codec</label>
          <select id='cg_${idx}_smart'>${smartOptions}</select>
        </div>
        <div class='cctv-mini-field'>
          <label>Escena</label>
          <select id='cg_${idx}_scene'>${sceneOptions}</select>
        </div>
        <div class='cctv-mini-field wide'>
          <label>PoE</label>
          <select id='cg_${idx}_poe' onchange='syncCCTVPoeWatts(${idx})'>${poeOptions}</select>
        </div>
        <div class='cctv-mini-field'>
          <label>W</label>
          <input type='number' id='cg_${idx}_poe_w' value='7.5' min='0' step='0.1'>
        </div>
      </div>
    </div>`;
  document.getElementById("cctvGroupBody").insertAdjacentHTML("beforeend", row);
  window._cctvGroupCount++;
  updateGroupCount();
}

function removeCCTVGroup(idx) {
  const el = document.getElementById(`cg_${idx}`);
  if (el) el.remove();
  updateGroupCount();
}

function updateGroupCount() {
  const rows = document.querySelectorAll("#cctvGroupBody .cctv-group-row").length;
  const el = document.getElementById("groupCount");
  if (el) {
    el.style.display = rows ? "block" : "none";
    el.textContent = `${rows} grupo(s) de cámaras configurados`;
  }
}

function updateBitratePreview(idx) {
  // Preview bitrate for a group (can be called on change)
}

function syncCCTVPoeWatts(idx) {
  const sel = document.getElementById(`cg_${idx}_poe`);
  const watts = sel?.selectedOptions?.[0]?.dataset?.watts;
  const input = document.getElementById(`cg_${idx}_poe_w`);
  if (input && watts) input.value = watts;
}

async function execCCTCCalc() {
  const rows = document.querySelectorAll("#cctvGroupBody .cctv-group-row");
  if (!rows.length) {
    document.getElementById("cctcCalcResult").innerHTML = `<div class='result-box' style='color:var(--danger)'>Agregá al menos un grupo de cámaras</div>`;
    return;
  }
  const groups = [];
  rows.forEach(row => {
    const id = row.id.replace("cg_", "");
    const qty = document.getElementById(`cg_${id}_qty`)?.value;
    const res = document.getElementById(`cg_${id}_res`)?.value;
    const codec = document.getElementById(`cg_${id}_codec`)?.value;
    const fps = document.getElementById(`cg_${id}_fps`)?.value;
    const smart = document.getElementById(`cg_${id}_smart`)?.value;
    const scene = document.getElementById(`cg_${id}_scene`)?.value;
    const poe = document.getElementById(`cg_${id}_poe`)?.value;
    const poeWatts = document.getElementById(`cg_${id}_poe_w`)?.value;
    if (res && codec) {
      groups.push({
        cameras: parseInt(qty) || 1,
        resolution: res, codec: codec,
        fps: parseInt(fps) || 15,
        smart_codec: smart, scene: scene,
        poe_profile: poe,
        poe_watts: parseFloat(poeWatts) || 7.5
      });
    }
  });

  const hours = document.getElementById("cc_hours").value || 24;
  const motion = document.getElementById("cc_motion").value || 100;
  const days = document.getElementById("cc_days").value || 30;
  const storage = document.getElementById("cc_storage").value || 2000;
  const nvrChannels = document.getElementById("cc_nvr")?.value || "";

  const params = new URLSearchParams({
    calc: "cctv_calc", recording_hours: hours,
    motion_percent: motion, retention_days: days,
    total_storage_gb: storage, groups: JSON.stringify(groups)
  });
  if (nvrChannels) params.set("nvr_channels", nvrChannels);

  try {
    const resp = await (await fetch(`${API}/calculators/run?${params}`)).json();
    if (resp.error) {
      document.getElementById("cctcCalcResult").innerHTML =
        `<div class='result-box' style='color:var(--danger)'>Error: ${resp.error}</div>`;
      return;
    }
    const r = resp.result;
    const poeTotal = r.poe?.total_watts ?? r.bandwidth?.poe_budget_watts ?? 0;
    const poeSwitches = Array.isArray(r.poe?.recommended_switch) ? r.poe.recommended_switch : [];
    const warningHtml = (r.warnings || []).length
      ? `<div class='section'><div class='section-header' style='color:var(--warning)'>⚠️ Alertas</div><div class='section-body'>${r.warnings.map(w => `<div class='cmd-item'>${escapeHtml(w)}</div>`).join("")}</div></div>`
      : "";
    let html = `
      ${warningHtml}
      <div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px;margin-top:12px'>
        <div class='section'>
          <div class='section-header' style='color:var(--success)'>💾 Saving Time</div>
          <div class='section-body'>
            <div class='cmd-item'><span style='color:var(--accent2)'>Disco:</span> ${r.saving_time.disk_size_gb} GB (${r.saving_time.disk_size_tb} TB)</div>
            <div class='cmd-item'><span style='color:var(--accent2)'>Cámaras:</span> ${r.total_cameras}</div>
            <hr style='border-color:var(--border);margin:6px 0'>
            <div class='cmd-item' style='font-size:18px;font-weight:700;color:var(--accent1)'>${r.saving_time.days} días</div>
            <div class='cmd-item'>${r.saving_time.weeks} semanas · ${r.saving_time.months} meses</div>
          </div>
        </div>
        <div class='section'>
          <div class='section-header' style='color:var(--warning)'>💿 Disk Space</div>
          <div class='section-body'>
            <div class='cmd-item'><span style='color:var(--accent2)'>Retención:</span> ${r.disk_space.retention_days} días</div>
            <div class='cmd-item'><span style='color:var(--accent2)'>Grabación:</span> ${r.recording_hours}h/día · ${r.motion_percent}% mov.</div>
            <hr style='border-color:var(--border);margin:6px 0'>
            <div class='cmd-item' style='font-size:18px;font-weight:700;color:var(--accent1)'>${r.disk_space.required_tb} TB</div>
            <div class='cmd-item'>${r.disk_space.required_gb} GB</div>
          </div>
        </div>
        <div class='section'>
          <div class='section-header' style='color:var(--accent2)'>🌐 Bandwidth & Red</div>
          <div class='section-body'>
            <div class='cmd-item' style='font-size:18px;font-weight:700;color:var(--accent1)'>${r.bandwidth.total_mbps} Mbps</div>
            <div class='cmd-item'>${r.bandwidth.total_kbps} Kbps total</div>
            <div class='cmd-item'>${r.bandwidth.per_camera_mbps_avg} Mbps promedio/cámara</div>
            <hr style='border-color:var(--border);margin:6px 0'>
            <div class='cmd-item'><span style='color:var(--accent2)'>Switch:</span> ${r.bandwidth.recommended_switch}</div>
            <div class='cmd-item'><span style='color:var(--accent2)'>Puertos:</span> ${r.bandwidth.switch_ports}</div>
            <div class='cmd-item'><span style='color:var(--accent2)'>PoE:</span> ${poeTotal} W</div>
            ${r.nvr ? `<div class='cmd-item'><span style='color:var(--accent2)'>NVR:</span> ${r.nvr.channels_limit || "sin límite"} canales · ${r.nvr.channels_ok ? "OK" : "excede"}</div>` : ""}
          </div>
        </div>
        ${poeSwitches.length ? `<div class='section'>
          <div class='section-header' style='color:var(--accent2)'>⚡ PoE recomendado</div>
          <div class='section-body'>
            ${poeSwitches.map(s => `<div class='cmd-item'><strong>${escapeHtml(s.model)}</strong><div style='color:var(--text2)'>Budget: ${s.budget_w} W · Cámaras: ${s.cameras_fit}</div></div>`).join("")}
          </div>
        </div>` : ""}
      </div>`;

    // Per-group breakdown
    html += `<div class='section'><div class='section-header'>📋 Detalle por Grupo</div><div class='section-body' style='overflow-x:auto'>
      <table style='width:100%;border-collapse:collapse;font-size:12px'>
        <thead><tr style='background:var(--bg2)'>
          <th style='padding:6px'>#</th><th style='padding:6px'>Cámaras</th><th style='padding:6px'>Resolución</th>
          <th style='padding:6px'>Codec</th><th style='padding:6px'>FPS</th><th style='padding:6px'>Smart</th>
          <th style='padding:6px'>Escena</th><th style='padding:6px'>Bitrate</th><th style='padding:6px'>GB/día</th><th style='padding:6px'>PoE</th>
        </tr></thead><tbody>`;
    r.groups.forEach((g, i) => {
      html += `<tr>
        <td style='padding:4px'>${i+1}</td>
        <td style='padding:4px'>${g.cameras}</td>
        <td style='padding:4px'>${g.resolution || groups[i].resolution}</td>
        <td style='padding:4px'>${g.codec || groups[i].codec}</td>
        <td style='padding:4px'>${g.fps || groups[i].fps}</td>
        <td style='padding:4px'>${g.smart_codec || groups[i].smart_codec}</td>
        <td style='padding:4px'>${g.scene || groups[i].scene}</td>
        <td style='padding:4px;font-weight:600'>${g.bitrate_mbps} Mbps (${g.bitrate_kbps} Kbps)</td>
        <td style='padding:4px'>${g.storage_per_day_gb_total} GB</td>
        <td style='padding:4px'>${g.poe_watts_total ?? ""} W</td>
      </tr>`;
    });
    html += `</tbody></table></div></div>`;

    // HDD recommendations
    if (r.disk_space.recommended_hdds && r.disk_space.recommended_hdds.length) {
      html += `<div class='section'><div class='section-header'>💾 Recomendaciones de Disco</div><div class='section-body' style='overflow-x:auto'>
        <table style='width:100%;border-collapse:collapse;font-size:12px'>
          <thead><tr style='background:var(--bg2)'>
            <th style='padding:6px'>Config</th><th style='padding:6px'>Modelo</th><th style='padding:6px'>Total</th>
            <th style='padding:6px'>RAID0</th><th style='padding:6px'>RAID1</th><th style='padding:6px'>RAID5</th><th style='padding:6px'>RAID10</th>
          </tr></thead><tbody>`;
      r.disk_space.recommended_hdds.forEach(h => {
        html += `<tr>
          <td style='padding:4px;font-weight:600'>${h.count}x ${h.size_label}</td>
          <td style='padding:4px'>${h.model}</td>
          <td style='padding:4px'>${h.total_gb ?? h.total_raw_gb} GB</td>
          <td style='padding:4px'>${h.raid0 ?? h.raid0_gb} GB</td>
          <td style='padding:4px'>${h.raid1 ?? h.raid1_gb} GB</td>
          <td style='padding:4px'>${h.raid5 ?? h.raid5_gb} GB</td>
          <td style='padding:4px'>${h.raid10 ?? h.raid10_gb} GB</td>
        </tr>`;
      });
      html += `</tbody></table></div></div>`;
    }

    document.getElementById("cctcCalcResult").innerHTML = html;
  } catch(e) {
    document.getElementById("cctcCalcResult").innerHTML =
      `<div class='result-box' style='color:var(--danger)'>Error: ${e.message}</div>`;
  }
}

// ─── CCTV ────────────────────────────────────────────────────

function showCCTVForm(vendor, btn) {
  document.querySelectorAll("#cctvForm, #cctvResult").forEach(el => {
    if (el) el.innerHTML = "";
  });
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  if (btn) btn.classList.add("active");
  document.getElementById("cctvForm").innerHTML = `
    <div class='section'>
      <div class='section-header'>Conectar a ${vendor.charAt(0).toUpperCase()+vendor.slice(1)}</div>
      <div class='section-body'>
        <div class='input-group'><label>IP del dispositivo</label><input type='text' id='cctv_host' placeholder='192.168.1.100'></div>
        <div class='input-group'><label>Puerto</label><input type='text' id='cctv_port' value='80'></div>
        <div class='input-group'><label>Usuario</label><input type='text' id='cctv_user' value='admin'></div>
        <div class='input-group'><label>Contraseña</label><input type='password' id='cctv_pass'></div>
        <button class='btn' onclick='connectCCTV("${vendor}")'>🔌 Conectar</button>
      </div>
    </div>
  `;
  window._cctvSession = null;
}

function connectCCTV(vendor) {
  const btn = event.target;
  const body = {
    vendor,
    host: document.getElementById("cctv_host").value,
    port: document.getElementById("cctv_port").value || 80,
    user: document.getElementById("cctv_user").value || "admin",
    password: document.getElementById("cctv_pass").value,
  };
  asyncFetchPost("Conectar CCTV " + vendor, `${API}/cctv/connect`, body, "cctvResult", (data, el, error) => {
    if (error) { el.innerHTML = `<div class='result-box' style='color:var(--danger)'>Error: ${escapeHtml(error)}</div>`; return; }
    if (data.online) {
      window._cctvSession = data.session;
      let infoHtml = Object.entries(data.info).map(([k,v]) => `<div class='cmd-item'><span style='color:var(--accent2)'>${k}:</span> ${v}</div>`).join("");
      let methodsHtml = data.methods.map(m => `<button class='btn btn-outline' style='margin-bottom:4px;font-size:12px;padding:6px;width:auto' onclick='execCCTV("${m}")'>${m}()</button>`).join(" ");
      el.innerHTML = `
        <div class='section'>
          <div class='section-header' style='color:var(--success)'>✅ Conectado</div>
          <div class='section-body'>
            ${infoHtml}
            <div style='margin-top:10px;font-size:13px;font-weight:600'>Comandos:</div>
            <div style='margin-top:6px'>${methodsHtml}</div>
            <div id='cctvCmdResult' style='margin-top:10px'></div>
          </div>
        </div>
      `;
    } else {
      el.innerHTML = `<div class='result-box' style='color:var(--danger)'>❌ ${data.error || "No se pudo conectar"}</div>`;
    }
  });
}

function execCCTV(method) {
  asyncFetchPost("Ejecutar " + method, `${API}/cctv/command`, {session: window._cctvSession, method}, "cctvCmdResult",
    (data, el) => { if (el) el.innerHTML = `<div class='result-box'>${JSON.stringify(data, null, 2)}</div>`; }
  );
}

// ─── DIAGNÓSTICO ─────────────────────────────────────────────

function showDiagnostic(name) {
  const encoded = name.split("/").map(s => encodeURIComponent(s)).join("/");
  asyncFetch(`/api/diagnostics/${encoded}`, null,
    r => {
      if (r.error) return showModal(`<div class='result-box' style='color:var(--danger)'>${r.error}</div>`);
      showModal(`
        <button class='modal-close' onclick='closeModal()'>&times;</button>
        <h2>🔍 ${escapeHtml(r.name)}</h2>
        <div class='result-box' style='max-height:70vh;font-size:12px'>${escapeHtml(r.content)}</div>
      `);
      return "";
    }
  );
}

function filterDiagnostics(q) {
  q = q.toLowerCase();
  document.querySelectorAll(".diag-card").forEach(c => {
    c.style.display = c.textContent.toLowerCase().includes(q) ? "block" : "none";
  });
}

// ─── TAREAS EN SEGUNDO PLANO (GLOBAL / PERSISTENTE) ──────────

window.__tasks = {};       // {taskKey: {task_id, label, status, result, error, renderFn, elId}}
window.__pollers = {};     // {task_id: interval_id}
window.__taskCount = 0;

function toggleTaskBar() {
  document.getElementById("taskbar").classList.toggle("active");
}

function updateTaskBar() {
  const now = Date.now();
  for (const [k, t] of Object.entries(window.__tasks)) {
    if (t.status !== "running" && t.ts && (now - t.ts) > 300000) delete window.__tasks[k];
  }
  const bar = document.getElementById("taskbar");
  const toggle = document.getElementById("taskbarToggle");
  const entries = Object.entries(window.__tasks);
  const running = entries.filter(([,t]) => t.status === "running").length;
  if (toggle) toggle.textContent = running ? "📋 " + running : "📋";
  // Update bottom nav badge
  const navTasks = document.getElementById("navTasks");
  if (navTasks) {
    let badge = navTasks.querySelector(".nav-badge");
    if (running) {
      if (!badge) { badge = document.createElement("span"); badge.className = "nav-badge"; navTasks.appendChild(badge); }
      badge.textContent = running;
    } else if (badge) badge.remove();
  }
  if (!entries.length) { bar?.classList.remove("active"); return; }
  bar.innerHTML = `<div style='display:flex;justify-content:space-between;margin-bottom:6px'>
    <span style='font-weight:600'>Tareas</span>
    <span style='font-size:12px;color:var(--accent2);cursor:pointer' onclick='clearDoneTasks()'>Limpiar completadas</span>
  </div>` + entries.map(([key, t]) => {
    const icon = t.status === "running" ? "⏳" : t.status === "done" ? "✅" : t.status === "error" ? "❌" : "⏳";
    const resultHtml = t.status === "done" ? `<div class='task-result'>${escapeHtml(JSON.stringify(t.result, null, 2).slice(0, 200))}</div>` : "";
    const errorHtml = t.status === "error" ? `<div class='task-result' style='color:var(--danger)'>${escapeHtml(t.error)}</div>` : "";
    const link = t.elId ? ` <span style='color:var(--accent);cursor:pointer' onclick='document.getElementById("${t.elId}").scrollIntoView({behavior:"smooth"})'>📍</span>` : "";
    return `<div class='task-item'><span class='task-status'>${icon}</span><div class='task-label'>${escapeHtml(t.label)}${link}${resultHtml}${errorHtml}</div></div>`;
  }).join("");
}

function clearDoneTasks() {
  for (const [k, t] of Object.entries(window.__tasks)) {
    if (t.status !== "running") delete window.__tasks[k];
  }
  updateTaskBar();
}

function startTask(label, url, resultElId, renderFn) {
  const taskKey = label + "_" + Date.now();
  window.__tasks[taskKey] = {label, status: "running", result: null, error: null, renderFn, elId: resultElId, ts: Date.now()};
  window.__taskCount++;
  const el = resultElId ? document.getElementById(resultElId) : null;
  if (el) el.innerHTML = "<div style='color:var(--text2)'>⏳ " + escapeHtml(label) + "...</div>";
  updateTaskBar();

  const sep = url.includes('?') ? '&' : '?';
  fetch(url + sep + "async=true")
    .then(r => r.json())
    .then(data => {
      if (data.task_id) {
        window.__tasks[taskKey].task_id = data.task_id;
        const poll = setInterval(() => {
          fetch("/api/task/" + data.task_id)
            .then(r => r.json())
            .then(task => {
              if (task.status === "done") {
                clearInterval(poll);
                delete window.__pollers[data.task_id];
                window.__tasks[taskKey].status = "done";
                window.__tasks[taskKey].result = task.result;
                window.__tasks[taskKey].ts = Date.now();
                const html = renderFn(task.result);
                if (el) el.innerHTML = html;
                updateTaskBar();
              } else if (task.status === "error") {
                clearInterval(poll);
                delete window.__pollers[data.task_id];
                window.__tasks[taskKey].status = "error";
                window.__tasks[taskKey].error = task.error;
                window.__tasks[taskKey].ts = Date.now();
                const html = "<div class='result-box' style='color:var(--danger)'>Error: " + escapeHtml(task.error) + "</div>";
                if (el) el.innerHTML = html;
                showToast(label + " ❌", "error");
                updateTaskBar();
              }
            });
        }, 2000);
        window.__pollers[data.task_id] = poll;
      } else {
        window.__tasks[taskKey].status = "done";
        window.__tasks[taskKey].result = data;
        window.__tasks[taskKey].ts = Date.now();
        const html = renderFn(data);
        if (el) el.innerHTML = html;
        updateTaskBar();
      }
    })
    .catch(e => {
      window.__tasks[taskKey].status = "error";
      window.__tasks[taskKey].error = e.message;
      window.__tasks[taskKey].ts = Date.now();
      const html = "<div class='result-box' style='color:var(--danger)'>Error: " + escapeHtml(e.message) + "</div>";
      if (el) el.innerHTML = html;
      showToast(label + " ❌", "error");
      updateTaskBar();
    });
  return taskKey;
}

// Compat: old asyncFetch redirects to new system
function asyncFetch(url, resultElId, renderFn) {
  const label = url.split("/api/").pop().split("?")[0].replace(/[-_]/g, " ");
  return startTask(label, url, resultElId, renderFn);
}

function asyncFetchUrl(url, resultElId, renderFn) {
  return asyncFetch(url, resultElId, renderFn);
}

// POST version: envía POST con JSON body + ?async=true, actualiza UI y taskbar
function asyncFetchPost(label, url, body, resultElId, onComplete) {
  const taskKey = label + "_" + Date.now();
  window.__tasks[taskKey] = {label, status: "running", result: null, error: null, renderFn: onComplete, elId: resultElId, ts: Date.now()};
  const el = resultElId ? document.getElementById(resultElId) : null;
  if (el) el.innerHTML = "<div style='color:var(--text2)'>⏳ " + escapeHtml(label) + "...</div>";
  updateTaskBar();
  const sep = url.includes('?') ? '&' : '?';
  fetch(url + sep + "async=true", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(body)
  })
    .then(r => r.json())
    .then(data => {
      if (data.task_id) {
        window.__tasks[taskKey].task_id = data.task_id;
        const poll = setInterval(() => {
          fetch("/api/task/" + data.task_id)
            .then(r => r.json())
            .then(task => {
              if (task.status === "done") {
                clearInterval(poll);
                delete window.__pollers[data.task_id];
                window.__tasks[taskKey].status = "done";
                window.__tasks[taskKey].result = task.result;
                window.__tasks[taskKey].ts = Date.now();
                onComplete(task.result, el, null);
                updateTaskBar();
              } else if (task.status === "error") {
                clearInterval(poll);
                delete window.__pollers[data.task_id];
                window.__tasks[taskKey].status = "error";
                window.__tasks[taskKey].error = task.error;
                window.__tasks[taskKey].ts = Date.now();
                onComplete(null, el, task.error);
                showToast(label + " ❌", "error");
                updateTaskBar();
              }
            });
        }, 2000);
        window.__pollers[data.task_id] = poll;
      } else {
        window.__tasks[taskKey].status = "done";
        window.__tasks[taskKey].result = data;
        window.__tasks[taskKey].ts = Date.now();
        onComplete(data, el, null);
        updateTaskBar();
      }
    })
    .catch(e => {
      window.__tasks[taskKey].status = "error";
      window.__tasks[taskKey].error = e.message;
      window.__tasks[taskKey].ts = Date.now();
      onComplete(null, el, e.message);
      showToast(label + " ❌", "error");
      updateTaskBar();
    });
}

// ─── ESCÁNER DE RED ──────────────────────────────────────────

function showScanner() {
  $("results").innerHTML = `
    <h3 class="section-title">🔍 Escáner de Red</h3>
    <div class='input-group'><label>Host/IP</label><input type='text' id='scan_host' placeholder='192.168.1.1'></div>
    <div class='input-group'><label>Subred</label><input type='text' id='scan_subnet' placeholder='192.168.1.0/24'>
      <div style='display:flex;gap:4px;flex-wrap:wrap;margin-top:4px'>
        <button class='btn btn-xs btn-outline' onclick='presetSubnet("192.168.0.0/24")'>192.168.0.0/24</button>
        <button class='btn btn-xs btn-outline' onclick='presetSubnet("192.168.1.0/24")'>192.168.1.0/24</button>
        <button class='btn btn-xs btn-outline' onclick='presetSubnet("10.0.0.0/24")'>10.0.0.0/24</button>
        <button class='btn btn-xs btn-outline' onclick='presetSubnet("172.16.0.0/24")'>172.16.0.0/24</button>
        <button class='btn btn-xs' onclick='autoDetectSubnet()'>📍 Detectar</button>
      </div>
    </div>
    <div class='section'>
      <div class='section-header'>📡 Ping + OS Detection</div>
      <div class='section-body'>
        <p class='text-sm text-muted mb-8'>Verifica si un host responde y detecta el sistema operativo por TTL</p>
        <button class='btn' onclick='scannerPing()'>📡 Ping + OS</button>
        <div id='scanPingResult'></div>
      </div>
    </div>
    <div class='section'>
      <div class='section-header'>⚡ Quick Scan</div>
      <div class='section-body'>
        <p class='text-sm text-muted mb-8'>Escanea 29 puertos comunes (HTTP, SSH, RDP, SQL, etc.)</p>
        <button class='btn' onclick='scannerQuick()'>⚡ Escaneo Rápido</button>
        <div id='scanQuickResult'></div>
      </div>
    </div>
    <div class='section'>
      <div class='section-header'>🌐 Descubrir Hosts</div>
      <div class='section-body'>
        <p class='text-sm text-muted mb-8'>Descubre hosts activos en una subred mediante ping</p>
        <button class='btn btn-outline' onclick='scannerDiscover()'>🌐 Descubrir</button>
        <div id='scanDiscoverResult'></div>
      </div>
    </div>
    <div class='section'>
      <div class='section-header'>🔄 Traceroute</div>
      <div class='section-body'>
        <p class='text-sm text-muted mb-8'>Traza la ruta de red hasta un host</p>
        <button class='btn btn-outline' onclick='scannerTrace()'>🔄 Trazar Ruta</button>
        <div id='scanTraceResult'></div>
      </div>
    </div>
    <div class='section'>
      <div class='section-header'>📷 Dispositivos CCTV</div>
      <div class='section-body'>
        <p class='text-sm text-muted mb-8'>Escanea puertos específicos de cámaras, DVRs y NVRs</p>
        <div class='flex flex-wrap gap-6'>
          <button class='btn btn-outline' onclick='scannerCCTV()' style='flex:1;min-width:120px'>📷 Escanear Puertos</button>
          <button class='btn btn-outline' onclick='scannerIdentify()' style='flex:1;min-width:120px'>🏷 Identificar</button>
        </div>
        <div id='scanCCTVResult'></div>
      </div>
    </div>
    <div class='section'>
      <div class='section-header'>🚪 Control de Acceso</div>
      <div class='section-body'>
        <p class='text-sm text-muted mb-8'>Escanea puertos de controladores de acceso</p>
        <button class='btn btn-outline' onclick='scannerAC()'>🚪 Escanear Puertos</button>
        <div id='scanACResult'></div>
      </div>
    </div>
    <div class='section'>
      <div class='section-header'>⏱️ Monitoreo Continuo de Subred</div>
      <div class='section-body'>
        <p class='text-sm text-muted mb-8'>Escanea automáticamente cada N segundos y notifica cambios</p>
        <div style='display:flex;gap:6px;flex-wrap:wrap'>
          <div style='flex:1;min-width:120px'><input type='number' id='mon_interval' value='300' min='60' max='86400' placeholder='Intervalo (s)'></div>
          <div style='flex:1;min-width:150px'><input type='text' id='mon_ntfy' placeholder='Topic ntfy.sh (opcional)'></div>
        </div>
        <div style='display:flex;gap:6px;margin-top:6px'>
          <button class='btn' onclick='monitorStart()'>▶ Iniciar</button>
          <button class='btn btn-outline' onclick='monitorStop()'>⏹ Detener</button>
          <button class='btn btn-outline' onclick='monitorStatus()'>🔄 Estado</button>
        </div>
        <div id='monitorResult' class='text-sm text-muted' style='margin-top:6px'></div>
      </div>
    </div>
    <div class='section'>
      <div class='section-header'>🔎 Búsqueda CCTV/AC en Subred</div>
      <div class='section-body'>
        <p class='text-sm text-muted mb-8'>Busca dispositivos CCTV y control de acceso en toda una subred</p>
        <button class='btn btn-outline' onclick='scannerDiscoverCCTV()'>📡 Buscar CCTV/AC</button>
        <div id='scanDiscoverCCTVResult'></div>
      </div>
    </div>
    <div class='section'>
      <div class='section-header'>⚙️ Escaneo Personalizado TCP</div>
      <div class='section-body'>
        <div class='input-group'><label>Puertos (separados por coma)</label><input type='text' id='scan_ports_list' placeholder='80,443,3306,3389,8080'></div>
        <button class='btn btn-outline' onclick='scannerPorts()'>🔎 TCP</button>
        <div id='scanPortsResult'></div>
      </div>
    </div>
    <div class='section'>
      <div class='section-header'>📡 Escaneo UDP</div>
      <div class='section-body'>
        <p class='text-sm text-muted mb-8'>Puertos UDP comunes (53-DNS, 161-SNMP, 123-NTP, 67-DHCP)</p>
        <div style='display:flex;gap:6px;flex-wrap:wrap'>
          <button class='btn btn-outline' onclick='scannerUDP("53,123,161,162,67,68,69,514,520,1900,5353")'>📡 UDP Comunes</button>
          <div style='flex:1;min-width:100px'><input type='text' id='scan_udp_ports' placeholder='Puertos UDP...'></div>
          <button class='btn btn-outline' onclick='scannerUDP(document.getElementById("scan_udp_ports").value)'>🔎 Escanear</button>
        </div>
        <div id='scanUdpResult'></div>
      </div>
    </div>
    <div class='section'>
      <div class='section-header'>🌐 Título HTTP</div>
      <div class='section-body'>
        <p class='text-sm text-muted mb-8'>Obtiene el título y servidor web de un host:puerto</p>
        <div style='display:flex;gap:6px'>
          <div style='flex:1'><input type='text' id='http_title_host' placeholder='Host'></div>
          <div style='flex:0.4'><input type='number' id='http_title_port' value='80' min='1' max='65535'></div>
          <button class='btn btn-outline' onclick='scannerHTTPTitle()'>🌐 Ver</button>
        </div>
        <div id='scanHTTPTitleResult'></div>
      </div>
    </div>
    <div class='section'>
      <div class='section-header'>🔁 Comparar Escaneos</div>
      <div class='section-body'>
        <p class='text-sm text-muted mb-8'>Seleccioná dos resultados de escaneo para ver diferencias</p>
        <div style='display:flex;gap:6px;flex-wrap:wrap'>
          <button class='btn btn-outline' onclick='scannerCompare("1")'>📥 Cargar #1</button>
          <button class='btn btn-outline' onclick='scannerCompare("2")'>📥 Cargar #2</button>
          <button class='btn' onclick='scannerCompareRun()'>🔁 Comparar</button>
        </div>
        <div id='scanCompareResult' class='text-sm text-muted' style='margin-top:4px'></div>
      </div>
    </div>
    <div class='section'>
      <div class='section-header'>📝 Notas por Host</div>
      <div class='section-body'>
        <div style='display:flex;gap:6px'>
          <div style='flex:1'><input type='text' id='note_host' placeholder='IP del host'></div>
          <input type='text' id='note_text' placeholder='Nota...' style='flex:2'>
          <button class='btn btn-outline' onclick='saveNote()'>💾</button>
        </div>
        <div id='notesList' class='text-sm' style='margin-top:6px'></div>
      </div>
    </div>
    <div class='section'>
      <div class='section-header'>📋 Auditoría + Backup</div>
      <div class='section-body'>
        <div style='display:flex;gap:6px;flex-wrap:wrap'>
          <button class='btn btn-outline' onclick='generateReport()'>📋 Auditoría</button>
          <button class='btn btn-outline' onclick='exportAllData()'>💾 Backup</button>
          <button class='btn btn-outline' onclick='importAllData()'>📂 Restaurar</button>
        </div>
      </div>
    </div>
  `;
  fadeIn($("results"));
  renderNotes();
}

// ─── MONITOR ────────────────────────────────────────────────

async function monitorStart() {
  const sub = document.getElementById("scan_subnet").value;
  if (!sub) { showToast("Primero ingresá una subred", "error"); return; }
  const interval = parseInt(document.getElementById("mon_interval").value) || 300;
  const ntfy = document.getElementById("mon_ntfy").value.trim();
  const el = document.getElementById("monitorResult");
  el.innerHTML = "<span class='text-muted'>Iniciando monitoreo...</span>";
  try {
    const r = await (await fetch("/api/monitor/start", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({subnet: sub, interval, ntfy_topic: ntfy})
    })).json();
    if (r.error) { el.innerHTML = `<span style='color:var(--danger)'>${escapeHtml(r.error)}</span>`; return; }
    el.innerHTML = `<span style='color:var(--success)'>✅ Monitoreando ${escapeHtml(r.subnet)} cada ${interval}s</span>`;
  } catch(e) { el.innerHTML = `<span style='color:var(--danger)'>Error: ${escapeHtml(e.message)}</span>`; }
}

async function monitorStop() {
  const sub = document.getElementById("scan_subnet").value;
  if (!sub) return;
  const el = document.getElementById("monitorResult");
  try {
    const r = await (await fetch("/api/monitor/stop", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({subnet: sub})
    })).json();
    el.innerHTML = r.error ? `<span style='color:var(--warning)'>${escapeHtml(r.error)}</span>` : `<span style='color:var(--text2)'>⏹ ${escapeHtml(r.status)}</span>`;
  } catch(e) { el.innerHTML = `<span style='color:var(--danger)'>Error: ${escapeHtml(e.message)}</span>`; }
}

async function monitorStatus() {
  const el = document.getElementById("monitorResult");
  try {
    const r = await (await fetch("/api/monitor/list")).json();
    if (r.error) { el.innerHTML = `<span style='color:var(--danger)'>${escapeHtml(r.error)}</span>`; return; }
    const entries = Object.entries(r);
    if (!entries.length) { el.innerHTML = "<span class='text-muted'>Sin monitoreos activos</span>"; return; }
    let html = "<div class='result-box' style='max-height:none'>";
    entries.forEach(([sub, info]) => {
      html += `<div class='cmd-item' style='flex-direction:column;align-items:flex-start;gap:2px'>
        <div><strong>${escapeHtml(sub)}</strong> · cada ${info.interval}s</div>
        <div class='text-xs text-muted'>Chequeos: ${info.checks} · Último: ${info.last_check ? new Date(info.last_check*1000).toLocaleTimeString() : "—"}</div>
        <div class='text-xs text-muted'>Hosts: ${info.hosts_found}</div>`;
      (info.changes || []).slice(-3).forEach(c => {
        const t = new Date(c.time*1000).toLocaleTimeString();
        if (c.new?.length) html += `<div class='text-xs' style='color:var(--success)'>✅ ${t}: ${escapeHtml(c.new.join(", "))}</div>`;
        if (c.gone?.length) html += `<div class='text-xs' style='color:var(--danger)'>❌ ${t}: ${escapeHtml(c.gone.join(", "))}</div>`;
      });
      html += "</div>";
    });
    html += "</div>";
    el.innerHTML = html;
  } catch(e) { el.innerHTML = `<span style='color:var(--danger)'>Error: ${escapeHtml(e.message)}</span>`; }
}

function presetSubnet(val) {
  document.getElementById("scan_subnet").value = val;
}

async function autoDetectSubnet() {
  const el = document.getElementById("scan_subnet");
  el.placeholder = "Detectando...";
  try {
    const r = await (await fetch("/api/tools/local-ip")).json();
    if (r.subnet && r.subnet !== "unknown") {
      el.value = r.subnet;
    } else {
      el.placeholder = "No se pudo detectar la subred";
    }
  } catch {
    el.placeholder = "Error al detectar";
  }
}

function exportJSONDecoded(enc, fn) { try { exportJSON(JSON.parse(decodeURIComponent(enc)), fn); } catch(e) { showToast("Error al exportar", "error"); } }
function copyJSONDecoded(enc) { try { navigator.clipboard.writeText(JSON.stringify(JSON.parse(decodeURIComponent(enc)), null, 2)); } catch(e) {} }

function renderScanResult(data, type) {
  if (!data || data.error) return `<div class='result-box result-box-error text-danger'>❌ ${escapeHtml(data?.error || "Error desconocido")}</div>`;
  const jsonEnc = encodeURIComponent(JSON.stringify(data));
  const exportBtn = `<div style='display:flex;gap:6px;margin-top:8px;flex-wrap:wrap'>
    <button class='btn btn-xs btn-outline' onclick='exportJSONDecoded("${jsonEnc}","${type}.json")'>📥 Exportar</button>
    <button class='btn btn-xs btn-outline' onclick='copyJSONDecoded("${jsonEnc}")'>📋 Copiar</button>
  </div>`;
  if (type === "ping") {
    const status = data.alive ? "<span class='badge badge-success'>✅ Activo</span>" : "<span class='badge badge-danger'>❌ Inactivo</span>";
    const ttlInfo = data.ttl && data.ttl > 0 ? `TTL: ${data.ttl} · ` : "";
    const osGuess = data.ttl > 0 ? (data.ttl <= 64 ? "Linux / IoT" : data.ttl <= 128 ? "Windows" : "Cisco / Network Device") : "—";
    return `<div class='result-box' style='max-height:none'>
      <div class='mb-6'><strong>${escapeHtml(data.host)}</strong> ${status}</div>
      <div class='text-sm text-muted'>${ttlInfo}Latencia: ${data.latency || "—"} ms</div>
      <div class='text-sm text-muted'>OS detectado: ${escapeHtml(data.os || osGuess)}</div>
    ${exportBtn}</div>`;
  }
  if (type === "quick") {
    let html = `<div class='result-box' style='max-height:none'>
      <div class='mb-8'><strong>${escapeHtml(data.host)}</strong> — <span class='badge badge-accent'>${data.count} puertos abiertos</span> <span class='badge badge-accent'>${escapeHtml(data.os || "")}</span></div>`;
    (data.ports||[]).forEach(p => {
      html += `<div class='cmd-item'><span class='badge badge-success'>${p.port}</span> <strong>${escapeHtml(p.service)}</strong>`;
      if (p.vendor && p.vendor !== "Genérico") html += ` <span class='text-accent2 text-xs'>[${p.vendor}]</span>`;
      if (p.banner) html += `<div class='text-xs text-muted' style='margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap'>${escapeHtml(p.banner)}</div>`;
      html += `</div>`;
    });
    if (!data.ports?.length) html += '<div class="empty-state"><div class="empty-text text-muted">Sin puertos abiertos</div></div>';
    html += exportBtn + "</div>";
    return html;
  }
  if (type === "discover") {
    if (data.count === 0) {
      return `<div class='result-box' style='max-height:none'>
        <div class='mb-6'><span class='badge badge-warning'>⚠️ Sin hosts activos en ${escapeHtml(data.subnet || "")}</span></div>
        <div class='text-sm text-muted'>Posibles causas: los hosts no responden ping, firewall bloquea ICMP, o la subred es incorrecta.</div>
      ${exportBtn}</div>`;
    }
    let html = `<div class='result-box' style='max-height:none'>
      <div class='mb-6'><span class='badge badge-accent'>${data.count} hosts encontrados en ${escapeHtml(data.subnet || "")}</span></div>`;
    (data.hosts||[]).forEach(h => {
      const ip = h.host || h.ip || h;
      const name = h.hostname || "";
      const lat = h.latency ? ` · ${h.latency}ms` : "";
      html += `<div class='cmd-item'><span class='badge badge-success'>${escapeHtml(ip)}</span><span class='text-xs text-muted'>${lat}${name ? " · " + escapeHtml(name) : ""}</span></div>`;
    });
    html += exportBtn + "</div>";
    return html;
  }
  if (type === "trace") {
    let html = `<div class='result-box' style='max-height:none'><div class='mb-6'><strong>Traceroute a ${escapeHtml(data.host||"")}</strong></div>`;
    (data.hops||[]).forEach(h => {
      const hopNum = h.hop || h.index || "";
      html += `<div class='cmd-item'><span class='badge badge-accent'>${hopNum}</span> <span style='margin-left:6px'>${escapeHtml(h.ip||"*")}</span></div>`;
    });
    html += exportBtn + "</div>";
    return html;
  }
  if (type === "ports") {
    let html = `<div class='result-box' style='max-height:none'>
      <div class='mb-6'><strong>${escapeHtml(data.host)}</strong> — <span class='badge badge-accent'>${data.count} puertos escaneados</span></div>`;
    (data.ports||[]).forEach(p => {
      const badge = p.state === "open" ? "badge-success" : "badge-danger";
      html += `<div class='cmd-item'><span class='badge ${badge}'>${p.port}</span> <strong>${escapeHtml(p.service||"")}</strong>`;
      if (p.vendor && p.vendor !== "Genérico") html += ` <span class='text-accent2 text-xs'>[${p.vendor}]</span>`;
      if (p.banner) html += `<div class='text-xs text-muted' style='margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap'>${escapeHtml(p.banner)}</div>`;
      html += `</div>`;
    });
    html += exportBtn + "</div>";
    return html;
  }
  if (type === "cctv" || type === "ac") {
    let html = `<div class='result-box' style='max-height:none'>
      <div class='mb-6'><span class='badge badge-accent'>${data.count} puertos detectados</span></div>`;
    (data.ports||[]).forEach(p => {
      html += `<div class='cmd-item'><span class='badge badge-success'>${p.port}</span> <strong>${escapeHtml(p.service)}</strong>`;
      const vendor = p.vendor || p.device_type;
      if (vendor && vendor !== "Genérico" && vendor !== "CCTV/AC" && vendor !== "AC Device") {
        html += ` <span class='text-accent2 text-xs'>[${escapeHtml(vendor)}]</span>`;
      }
      const banner = p.banner || p.banner_preview;
      if (banner) html += `<div class='text-xs text-muted' style='margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap'>${escapeHtml(banner)}</div>`;
      html += `</div>`;
    });
    html += "</div>";
    return html;
  }
  if (type === "discover-cctv") {
    let html = `<div class='result-box' style='max-height:none'>
      <div class='mb-6'><span class='badge badge-accent'>${data.count} dispositivos CCTV/AC</span></div>`;
    (data.devices||[]).forEach(d => {
      html += `<div class='cmd-item'><span class='badge badge-success'>${escapeHtml(d.ip)}</span> <span class='text-accent2 text-xs'>${(d.device_type||[]).join(", ")}</span>
        <div class='text-xs text-muted'>Puertos: ${(d.open_ports||[]).join(", ")}</div></div>`;
    });
    html += "</div>";
    return html;
  }
  return `<div class='result-box'>${escapeHtml(JSON.stringify(data, null, 2))}</div>`;
}

function scannerPing() {
  const host = document.getElementById("scan_host").value;
  if (!host) return;
  asyncFetch("/api/scanner/ping?host="+encodeURIComponent(host), "scanPingResult",
    r => renderScanResult(r, "ping")
  );
}

function scannerQuick() {
  const host = document.getElementById("scan_host").value;
  if (!host) return;
  asyncFetch("/api/scanner/quick-scan?host="+encodeURIComponent(host),
    "scanQuickResult",
    r => renderScanResult(r, "quick")
  );
}

function scannerDiscover() {
  const sub = document.getElementById("scan_subnet").value;
  if (!sub) return;
  asyncFetch("/api/scanner/discover?subnet="+encodeURIComponent(sub),
    "scanDiscoverResult",
    r => renderScanResult(r, "discover")
  );
}

function scannerTrace() {
  const host = document.getElementById("scan_host").value;
  if (!host) return;
  asyncFetch("/api/scanner/traceroute?host="+encodeURIComponent(host),
    "scanTraceResult",
    r => renderScanResult(r, "trace")
  );
}

function scannerPorts() {
  const host = document.getElementById("scan_host").value;
  const ports = document.getElementById("scan_ports_list").value;
  if (!host) return;
  asyncFetch("/api/scanner/scan-ports?host="+encodeURIComponent(host)+"&ports="+encodeURIComponent(ports),
    "scanPortsResult",
    r => renderScanResult(r, "ports")
  );
}

function scannerCCTV() {
  const host = document.getElementById("scan_host").value;
  if (!host) return;
  asyncFetch("/api/scanner/scan-cctv?host="+encodeURIComponent(host),
    "scanCCTVResult",
    r => renderScanResult(r, "cctv")
  );
}

function scannerIdentify() {
  const host = document.getElementById("scan_host").value;
  if (!host) return;
  asyncFetch("/api/scanner/scan-cctv?host="+encodeURIComponent(host),
    "scanCCTVResult",
    r => {
      let html = `<div class='result-box'><strong>🏷 Identificación de ${escapeHtml(host)}</strong>`;
      const ids = r.device_identity || {};
      const entries = Object.entries(ids);
      if (entries.length) {
        entries.forEach(([port, vendor]) => {
          html += `<div class='cmd-item'>Puerto ${port}: ${escapeHtml(vendor)}</div>`;
        });
      } else {
        html += "<div style='color:var(--text2);margin-top:6px'>No se pudo identificar el dispositivo</div>";
      }
      html += "</div>";
      return html;
    }
  );
}

function scannerAC() {
  const host = document.getElementById("scan_host").value;
  if (!host) return;
  asyncFetch("/api/scanner/scan-ac?host="+encodeURIComponent(host),
    "scanACResult",
    r => renderScanResult(r, "ac")
  );
}

function scannerDiscoverCCTV() {
  const sub = document.getElementById("scan_subnet").value;
  if (!sub) return;
  asyncFetch("/api/scanner/discover-cctv?subnet="+encodeURIComponent(sub),
    "scanDiscoverCCTVResult",
    r => renderScanResult(r, "discover-cctv")
  );
}

// ─── UDP SCAN ────────────────────────────────────────────────

function scannerUDP(ports) {
  const host = document.getElementById("scan_host").value;
  if (!host) return;
  if (!ports) { showToast("Ingresá puertos UDP", "error"); return; }
  asyncFetch("/api/scanner/scan-ports-udp?host="+encodeURIComponent(host)+"&ports="+encodeURIComponent(ports),
    "scanUdpResult",
    r => renderScanResult(r, "ports")
  );
}

// ─── HTTP TITLE ──────────────────────────────────────────────

async function scannerHTTPTitle() {
  const host = document.getElementById("http_title_host").value.trim() || document.getElementById("scan_host").value;
  const port = parseInt(document.getElementById("http_title_port").value) || 80;
  if (!host) return;
  const el = document.getElementById("scanHTTPTitleResult");
  el.innerHTML = "<span class='text-muted'>Obteniendo...</span>";
  try {
    const r = await (await fetch(`/api/tools/http-title?host=${encodeURIComponent(host)}&port=${port}`)).json();
    if (r.error) { el.innerHTML = `<span style='color:var(--danger)'>${escapeHtml(r.error)}</span>`; return; }
    let html = `<div class='result-box' style='max-height:none'>
      <div class='mb-6'><strong>${escapeHtml(r.host)}:${r.port}</strong></div>`;
    if (r.title) html += `<div class='text-sm'>📄 ${escapeHtml(r.title)}</div>`;
    if (r.server) html += `<div class='text-sm'>🖥️ ${escapeHtml(r.server)}</div>`;
    if (r.banner_preview) html += `<div class='text-xs text-muted' style='margin-top:4px'>${escapeHtml(r.banner_preview.slice(0,200))}</div>`;
    html += "</div>";
    el.innerHTML = html;
  } catch(e) { el.innerHTML = `<span style='color:var(--danger)'>Error: ${escapeHtml(e.message)}</span>`; }
}

// ─── COMPARE SCANS ───────────────────────────────────────────

let _scanCompare = {1: null, 2: null};

function scannerCompare(num) {
  const host = document.getElementById("scan_host").value;
  if (!host) { showToast("Primero escaneá un host", "error"); return; }
  _scanCompare[num] = host;
  document.getElementById("scanCompareResult").innerHTML = `<span style='color:var(--success)'>✅ #${num}: ${escapeHtml(host)}</span>`;
}

async function scannerCompareRun() {
  const el = document.getElementById("scanCompareResult");
  if (!_scanCompare[1] || !_scanCompare[2]) {
    el.innerHTML = "<span style='color:var(--warning)'>Cargá dos hosts (#1 y #2)</span>"; return;
  }
  // Escanear ambos y comparar
  const scan1 = await (await fetch(`/api/scanner/quick-scan?host=${encodeURIComponent(_scanCompare[1])}&async=false`)).json();
  const scan2 = await (await fetch(`/api/scanner/quick-scan?host=${encodeURIComponent(_scanCompare[2])}&async=false`)).json();
  try {
    const r = await (await fetch("/api/scanner/compare", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({scan1: scan1.ports || [], scan2: scan2.ports || []})
    })).json();
    if (r.error) { el.innerHTML = `<span style='color:var(--danger)'>${escapeHtml(r.error)}</span>`; return; }
    let html = `<div class='result-box' style='max-height:none'>
      <div class='mb-6'><strong>🔁 ${escapeHtml(_scanCompare[1])} vs ${escapeHtml(_scanCompare[2])}</strong></div>
      <div class='text-sm'>🔵 #1: ${r.total_before} puertos · 🟢 #2: ${r.total_after} puertos</div>`;
    if (r.new_ports?.length) {
      html += `<div style='margin-top:6px;color:var(--success)'><strong>✅ Nuevos en #2:</strong></div>`;
      r.new_ports.forEach(p => html += `<div class='cmd-item'><span class='badge badge-success'>${p.port}</span> ${escapeHtml(p.service)}</div>`);
    }
    if (r.removed_ports?.length) {
      html += `<div style='margin-top:6px;color:var(--danger)'><strong>❌ Desaparecieron en #2:</strong></div>`;
      r.removed_ports.forEach(p => html += `<div class='cmd-item'><span class='badge badge-danger'>${p.port}</span> ${escapeHtml(p.service)}</div>`);
    }
    if (!r.new_ports?.length && !r.removed_ports?.length) html += "<div class='text-sm text-muted' style='margin-top:6px'>Sin diferencias</div>";
    html += "</div>";
    el.innerHTML = html;
  } catch(e) { el.innerHTML = `<span style='color:var(--danger)'>Error: ${escapeHtml(e.message)}</span>`; }
}

// ─── NOTES ───────────────────────────────────────────────────

function getNotes() {
  return JSON.parse(localStorage.getItem("techbot_notes") || "{}");
}

function saveNote() {
  const host = document.getElementById("note_host").value.trim() || document.getElementById("scan_host").value;
  const text = document.getElementById("note_text").value.trim();
  if (!host || !text) return;
  const notes = getNotes();
  if (!notes[host]) notes[host] = [];
  notes[host].push({text, ts: Date.now()});
  localStorage.setItem("techbot_notes", JSON.stringify(notes));
  document.getElementById("note_text").value = "";
  renderNotes();
}

function deleteNote(host, idx) {
  const notes = getNotes();
  if (notes[host]) { notes[host].splice(idx, 1); if (!notes[host].length) delete notes[host]; }
  localStorage.setItem("techbot_notes", JSON.stringify(notes));
  renderNotes();
}

function renderNotes() {
  const el = document.getElementById("notesList");
  const notes = getNotes();
  const entries = Object.entries(notes);
  if (!entries.length) { el.innerHTML = "<span class='text-muted'>Sin notas guardadas</span>"; return; }
  let html = "";
  entries.forEach(([host, items]) => {
    html += `<div style='margin-top:6px'><strong>${escapeHtml(host)}</strong></div>`;
    items.forEach((n, i) => {
      html += `<div class='cmd-item' style='padding:4px 0'>
        <span class='text-xs' style='flex:1'>${escapeHtml(n.text)}</span>
        <span class='text-xs text-muted'>${new Date(n.ts).toLocaleDateString()}</span>
        <button class='btn btn-xs btn-outline' onclick='deleteNote("${escapeHtml(host)}",${i})' style='color:var(--danger)'>✕</button>
      </div>`;
    });
  });
  el.innerHTML = html;
}

// ─── THEME + COMPACT MODE ────────────────────────────────────

function setTheme(color) {
  const root = document.documentElement;
  const themes = {
    "azul":  {"--accent": "#00d4ff", "--accent2": "#e94560", "--bg": "#1a1a2e", "--card": "#16213e"},
    "verde": {"--accent": "#10b981", "--accent2": "#f59e0b", "--bg": "#0f172a", "--card": "#1e293b"},
    "morado":{"--accent": "#a855f7", "--accent2": "#ec4899", "--bg": "#1a1025", "--card": "#2a1a3e"},
    "rojo":  {"--accent": "#ef4444", "--accent2": "#f97316", "--bg": "#1a0f0f", "--card": "#2a1a1a"},
    "gris":  {"--accent": "#64748b", "--accent2": "#94a3b8", "--bg": "#0f1117", "--card": "#1e2028"},
  };
  const t = themes[color];
  if (!t) return;
  Object.entries(t).forEach(([k, v]) => root.style.setProperty(k, v));
  localStorage.setItem("techbot_theme", color);
}

function toggleCompact() {
  document.body.classList.toggle("compact");
  localStorage.setItem("techbot_compact", document.body.classList.contains("compact") ? "1" : "0");
}

function loadThemeAndCompact() {
  const savedTheme = localStorage.getItem("techbot_theme") || "azul";
  setTheme(savedTheme);
  if (localStorage.getItem("techbot_compact") === "1") document.body.classList.add("compact");
}

document.addEventListener("DOMContentLoaded", loadThemeAndCompact);

function showSettings() {
  const currentTheme = localStorage.getItem("techbot_theme") || "azul";
  const isCompact = localStorage.getItem("techbot_compact") === "1";
  showModal(`
    <button class='modal-close' onclick='closeModal()'>&times;</button>
    <h2>⚙️ Ajustes</h2>
    <div class='section' style='margin-top:8px'>
      <div class='section-header'>🎨 Tema</div>
      <div class='section-body'>
        <div style='display:flex;gap:6px;flex-wrap:wrap'>
          <button class='btn btn-sm ${currentTheme==="azul"?"btn":"btn-outline"}' onclick='setTheme("azul");closeModal();showSettings()' style='background:#00d4ff;color:#000;${currentTheme==="azul"?"border-color:#00d4ff":""}'>Azul</button>
          <button class='btn btn-sm ${currentTheme==="verde"?"btn":"btn-outline"}' onclick='setTheme("verde");closeModal();showSettings()' style='background:#10b981;color:#000;${currentTheme==="verde"?"border-color:#10b981":""}'>Verde</button>
          <button class='btn btn-sm ${currentTheme==="morado"?"btn":"btn-outline"}' onclick='setTheme("morado");closeModal();showSettings()' style='background:#a855f7;color:#000;${currentTheme==="morado"?"border-color:#a855f7":""}'>Morado</button>
          <button class='btn btn-sm ${currentTheme==="rojo"?"btn":"btn-outline"}' onclick='setTheme("rojo");closeModal();showSettings()' style='background:#ef4444;color:#000;${currentTheme==="rojo"?"border-color:#ef4444":""}'>Rojo</button>
          <button class='btn btn-sm ${currentTheme==="gris"?"btn":"btn-outline"}' onclick='setTheme("gris");closeModal();showSettings()' style='background:#64748b;color:#000;${currentTheme==="gris"?"border-color:#64748b":""}'>Gris</button>
        </div>
      </div>
    </div>
    <div class='section'>
      <div class='section-header'>📦 Modo Compacto</div>
      <div class='section-body'>
        <label style='display:flex;align-items:center;gap:8px;cursor:pointer'>
          <input type='checkbox' ${isCompact?"checked":""} onchange='toggleCompact();closeModal();showSettings()'>
          <span class='text-sm'>Reducir espacio entre elementos</span>
        </label>
      </div>
    </div>
    <div class='section'>
      <div class='section-header'>💾 Datos</div>
      <div class='section-body'>
        <div style='display:flex;gap:6px;flex-wrap:wrap'>
          <button class='btn btn-outline btn-sm' onclick='exportAllData();closeModal()'>💾 Exportar todo</button>
          <button class='btn btn-outline btn-sm' onclick='importAllData();closeModal()'>📂 Importar</button>
          <button class='btn btn-outline btn-sm' style='color:var(--danger)' onclick='if(confirm("¿Limpiar todos los datos locales?")){localStorage.clear();location.reload()}'>🗑️ Limpiar todo</button>
        </div>
      </div>
    </div>
    <div class='section'>
      <div class='section-header'>ℹ️ Acerca de</div>
      <div class='section-body'>
        <div class='text-sm'>TechBot v1.0 · 92 API endpoints · 232 funciones frontend</div>
        <div class='text-xs text-muted'>Hecho para técnicos de campo. Sin dependencias externas (100% stdlib Python).</div>
        <a href='#' onclick='event.preventDefault();showModal(\`<button class=\"modal-close\" onclick=\"closeModal()\">&times;</button><h2>📖 Ayuda Rápida</h2><div class=\"text-sm\"><p>• Usá el buscador global para encontrar comandos, protocolos y puertos</p><p>• El escáner de red usa TCP ping (no requiere privilegios)</p><p>• Los resultados se pueden exportar a JSON/CSV desde cada sección</p><p>• Las notas y favoritos se guardan en el navegador (localStorage)</p><p>• Hacé backup periódico desde Ajustes > Exportar todo</p><p>• Servidor Flask: python3 webapp/app.py</p></div>\`);closeModal()'>📖 Ayuda rápida</a>
      </div>
    </div>
  `);
}

// ─── SPEEDTEST ──────────────────────────────────────────────────

function showSpeedtest() {
  $("results").innerHTML = `
    <h3 class="section-title">⚡ Test de Velocidad</h3>
    <p class='text-sm text-muted mb-12'>Se ejecuta en segundo plano. Podés usar otras herramientas mientras tanto.</p>
    <div class='section'>
      <div class='section-body text-center'>
        <div style='font-size:48px;margin:16px 0'>⚡</div>
        <button class='btn' id='stBtn' onclick='startSpeedtest()'>▶ Iniciar Speedtest</button>
        <div id='stResult' class='mt-16'></div>
      </div>
    </div>
    <div class='section' id='stHistorySection' style='display:none'>
      <div class='section-header'>📋 Resultados anteriores</div>
      <div class='section-body' id='stHistory'></div>
    </div>
  `;
  loadSpeedtestHistory();
  fadeIn($("results"));
}

let _stPollTimer = null;

function stPoll(taskId) {
  if (_stPollTimer) clearTimeout(_stPollTimer);
  fetch("/api/task/" + taskId)
    .then(r => r.json())
    .then(task => {
      const statusEl = document.getElementById("stStatus");
      if (statusEl) statusEl.textContent = "⏳ " + (task.progress || "Ejecutando...");

      if (task.status === "done") {
        const data = task.result || {};
        document.getElementById("stDl").textContent = data.download_human || "—";
        document.getElementById("stUl").textContent = data.upload_human || "—";
        document.getElementById("stPing").textContent = data.ping_ms ? data.ping_ms + " ms" : "—";
        document.getElementById("stPublicIP").textContent = data.ip || "—";
        document.getElementById("stServer").textContent = data.server || "—";
        const statusEl2 = document.getElementById("stStatus");
        statusEl2.textContent = "✅ Completado";
        statusEl2.style.color = "var(--success)";
        document.getElementById("stBtn").disabled = false;
        document.getElementById("stBtn").textContent = "▶ Repetir Speedtest";
        saveSpeedtestResult(data);
        return;
      }
      if (task.status === "error") {
        document.getElementById("stResult").innerHTML =
          `<div class='result-box' style='color:var(--danger)'>Error: ${task.error}</div>`;
        document.getElementById("stBtn").disabled = false;
        document.getElementById("stBtn").textContent = "▶ Repetir Speedtest";
        return;
      }
      _stPollTimer = setTimeout(() => stPoll(taskId), 1500);
    });
}

async function startSpeedtest() {
  const btn = document.getElementById("stBtn");
  const res = document.getElementById("stResult");
  btn.disabled = true;
  btn.textContent = "⏳ Iniciando...";

  res.innerHTML = `
    <div style='display:grid;grid-template-columns:1fr 1fr;gap:12px'>
      <div class='card' style='padding:20px;cursor:default'>
        <div style='font-size:14px;color:var(--text2)'>📥 Bajada</div>
        <div style='font-size:22px;font-weight:700;color:var(--accent)' id='stDl'>—</div>
      </div>
      <div class='card' style='padding:20px;cursor:default'>
        <div style='font-size:14px;color:var(--text2)'>📤 Subida</div>
        <div style='font-size:22px;font-weight:700;color:var(--accent)' id='stUl'>—</div>
      </div>
    </div>
    <div style='display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:8px'>
      <div class='card' style='padding:16px;cursor:default'>
        <div style='font-size:13px;color:var(--text2)'>📍 Ping</div>
        <div style='font-size:18px;font-weight:600' id='stPing'>—</div>
      </div>
      <div class='card' style='padding:16px;cursor:default'>
        <div style='font-size:13px;color:var(--text2)'>🌐 IP Pública</div>
        <div style='font-size:15px;font-weight:600;word-break:break-all' id='stPublicIP'>—</div>
      </div>
    </div>
    <div style='margin-top:8px'>
      <div class='card' style='padding:12px;cursor:default'>
        <div style='font-size:12px;color:var(--text2)'>🌐 Servidor</div>
        <div style='font-size:13px;font-weight:600;word-break:break-all' id='stServer'>—</div>
      </div>
    </div>
    <div style='margin-top:8px;font-size:12px;color:var(--text2);text-align:center' id='stStatus'>En cola...</div>
  `;

  try {
    const resp = await fetch("/api/speedtest?async=true", { method: "POST" });
    const data = await resp.json();
    if (data.error) {
      res.innerHTML = `<div class='result-box' style='color:var(--danger)'>Error: ${data.error}</div>`;
      btn.disabled = false;
      btn.textContent = "▶ Repetir Speedtest";
      return;
    }
    if (data.task_id) {
      btn.textContent = "⏳ Probando... (podés usar otras fichas)";
      stPoll(data.task_id);
    }
  } catch(e) {
    res.innerHTML = `<div class='result-box' style='color:var(--danger)'>Error: ${e.message}</div>`;
    btn.disabled = false;
    btn.textContent = "▶ Repetir Speedtest";
  }
}

function saveSpeedtestResult(data) {
  try {
    let hist = JSON.parse(localStorage.getItem("stHistory") || "[]");
    hist.unshift({
      date: new Date().toLocaleString("es-AR"),
      dl: data.download_human,
      ul: data.upload_human,
      ping: data.ping_ms,
      server: data.server,
    });
    if (hist.length > 10) hist = hist.slice(0, 10);
    localStorage.setItem("stHistory", JSON.stringify(hist));
    loadSpeedtestHistory();
  } catch(e) {}
}

function loadSpeedtestHistory() {
  try {
    const hist = JSON.parse(localStorage.getItem("stHistory") || "[]");
    const section = document.getElementById("stHistorySection");
    const list = document.getElementById("stHistory");
    if (!section || !list) return;
    if (!hist.length) { section.style.display = "none"; return; }
    section.style.display = "block";
    list.innerHTML = hist.map(h =>
      `<div class='cmd-item'>
        <div style='font-size:11px;color:var(--text2)'>${h.date}</div>
        <div><span class='badge badge-accent'>📥 ${h.dl}</span> <span class='badge badge-accent'>📤 ${h.ul}</span> <span class='badge badge-accent'>📍 ${h.ping} ms</span></div>
        <div style='font-size:11px;color:var(--text2)'>${h.server || ""}</div>
      </div>`
    ).join("");
  } catch(e) {}
}

// ─── MAC LOOKUP ────────────────────────────────────────────────

function showMAC() {
  document.getElementById("results").innerHTML = `
    <h3 style='margin-bottom:12px;font-size:17px'>🏷 Consulta MAC / OUI</h3>
    <div class='section'>
      <div class='section-header'>🔍 Buscar por MAC</div>
      <div class='section-body'>
        <div class='input-group'><label>Dirección MAC</label><input type='text' id='mac_input' placeholder='AA:BB:CC:DD:EE:FF' onkeyup="if(event.key==='Enter')macLookup()"></div>
        <button class='btn' onclick='macLookup()'>🔎 Buscar</button>
        <div id='macResult'></div>
      </div>
    </div>
    <div class='section'>
      <div class='section-header'>🔍 Buscar por Fabricante</div>
      <div class='section-body'>
        <div class='input-group'><label>Nombre del fabricante</label><input type='text' id='mac_vendor_input' placeholder='Cisco, Hikvision, HP...' onkeyup="if(event.key==='Enter')macVendorLookup()"></div>
        <button class='btn btn-outline' onclick='macVendorLookup()'>🔎 Buscar</button>
        <div id='macVendorResult'></div>
      </div>
    </div>
    <div class='section'>
      <div class='section-header'>📋 Listar todos los fabricantes</div>
      <div class='section-body'>
        <button class='btn btn-outline' onclick='macListVendors()'>📋 Mostrar fabricantes</button>
        <div id='macListResult'></div>
      </div>
    </div>
  `;
}

async function macLookup() {
  const mac = document.getElementById("mac_input").value.trim();
  if (!mac) return;
  try {
    const r = await (await fetch(`/api/mac-lookup?mac=${encodeURIComponent(mac)}`)).json();
    if (r.error) {
      document.getElementById("macResult").innerHTML = `<div class='result-box' style='color:var(--danger)'>Error: ${r.error}</div>`;
      return;
    }
    let html = "<div class='section'><div class='section-header' style='color:var(--success)'>✅ Resultado</div><div class='section-body'>";
    for (const [k, v] of Object.entries(r)) {
      const val = v === true ? "✅ Sí" : v === false ? "❌ No" : v;
      html += `<div class='cmd-item'><span style='color:var(--accent2)'>${k}:</span> ${val}</div>`;
    }
    html += "</div></div>";
    document.getElementById("macResult").innerHTML = html;
  } catch(e) {
    document.getElementById("macResult").innerHTML = `<div class='result-box' style='color:var(--danger)'>Error: ${e.message}</div>`;
  }
}

async function macVendorLookup() {
  const q = document.getElementById("mac_vendor_input").value.trim();
  if (!q) return;
  try {
    const r = await (await fetch(`/api/mac-lookup?fabricante=${encodeURIComponent(q)}`)).json();
    if (r.error) {
      document.getElementById("macVendorResult").innerHTML = `<div class='result-box' style='color:var(--danger)'>Error: ${r.error}</div>`;
      return;
    }
    let html = `<div class='section'><div class='section-header'>${r.count} resultado(s) para "${r.query}"</div><div class='section-body'>`;
    if (r.count === 0) {
      html += "<p style='color:var(--text2)'>Sin resultados</p>";
    } else {
      r.results.forEach(item => {
        html += `<div class='cmd-item'><span class='badge badge-accent'>${item.oui}</span> <span>${item.fabricante}</span></div>`;
      });
    }
    html += "</div></div>";
    document.getElementById("macVendorResult").innerHTML = html;
  } catch(e) {
    document.getElementById("macVendorResult").innerHTML = `<div class='result-box' style='color:var(--danger)'>Error: ${e.message}</div>`;
  }
}

async function macListVendors() {
  try {
    const r = await (await fetch(`/api/mac-lookup`)).json();
    const fabricantes = r.fabricantes || [];
    let html = `<div class='section'><div class='section-header'>${fabricantes.length} fabricante(s)</div><div class='section-body'>`;
    fabricantes.forEach(f => {
      html += `<div class='cmd-item'><span class='badge badge-accent'>${f.oui_count}</span> <span style='font-weight:600'>${f.fabricante}</span></div>`;
    });
    html += "</div></div>";
    document.getElementById("macListResult").innerHTML = html;
  } catch(e) {
    document.getElementById("macListResult").innerHTML = `<div class='result-box' style='color:var(--danger)'>Error: ${e.message}</div>`;
  }
}

// ─── HERRAMIENTAS (DNS, SSL, WOL, HTTP, Token) ──────────────

function showTools() {
  const el = document.getElementById("results");
  el.innerHTML = `
    <h3 class="section-title">🧰 Herramientas Multiplataforma</h3>

    <div class="section-header" style="margin-top:12px">🌐 DNS Lookup</div>
    <div style="margin:6px 0;padding:6px;background:var(--card);border-radius:6px">
      <div class="input-group"><label>Host / IP / Dominio</label><input type="text" id="dns_host" placeholder="ej: google.com" value="google.com"></div>
      <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:6px">
        <button class="btn btn-sm" onclick="dnsQuery('A')">A</button>
        <button class="btn btn-sm" onclick="dnsQuery('AAAA')">AAAA</button>
        <button class="btn btn-sm" onclick="dnsQuery('PTR')">PTR</button>
        <button class="btn btn-sm" onclick="dnsQuery('ALL')">ALL</button>
        <button class="btn btn-sm btn-outline" onclick="dnsMX()">MX</button>
      </div>
      <div id="dnsResult" class="text-muted text-sm" style="margin-top:6px"></div>
    </div>

    <div class="section-header" style="margin-top:12px">🔒 SSL Cert Check</div>
    <div style="margin:6px 0;padding:6px;background:var(--card);border-radius:6px">
      <div style="display:flex;gap:6px">
        <div style="flex:2"><input type="text" id="ssl_host" placeholder="Host" value="google.com"></div>
        <div style="flex:0.5"><input type="number" id="ssl_port" value="443" min="1" max="65535"></div>
        <button class="btn" onclick="sslCheck()">Verificar</button>
      </div>
      <div id="sslResult" class="text-muted text-sm" style="margin-top:6px"></div>
    </div>

    <div class="section-header" style="margin-top:12px">📨 HTTP Headers</div>
    <div style="margin:6px 0;padding:6px;background:var(--card);border-radius:6px">
      <div style="display:flex;gap:6px">
        <div style="flex:2"><input type="text" id="http_url" placeholder="URL" value="google.com"></div>
        <button class="btn" onclick="httpHeadersCheck()">Ver</button>
      </div>
      <div id="httpResult" class="text-muted text-sm" style="margin-top:6px"></div>
    </div>

    <div class="section-header" style="margin-top:12px">💤 Wake-on-LAN</div>
    <div style="margin:6px 0;padding:6px;background:var(--card);border-radius:6px">
      <div class="input-group"><label>MAC (AA:BB:CC:DD:EE:FF)</label><input type="text" id="wol_mac" placeholder="AA:BB:CC:DD:EE:FF"></div>
      <div style="display:flex;gap:6px">
        <div style="flex:1"><input type="text" id="wol_broadcast" placeholder="Broadcast" value="255.255.255.255"></div>
        <div style="flex:0.4"><input type="number" id="wol_port" value="9" min="1" max="65535"></div>
      </div>
      <button class="btn" style="margin-top:6px" onclick="wolSend()">💤 Enviar WOL</button>
      <div id="wolResult" class="text-muted text-sm" style="margin-top:6px"></div>
    </div>

    <div class="section-header" style="margin-top:12px">🔑 Token / Password Generator</div>
    <div style="margin:6px 0;padding:6px;background:var(--card);border-radius:6px">
      <div style="display:flex;gap:6px;flex-wrap:wrap">
        <div style="flex:1;min-width:80px"><input type="number" id="token_length" value="32" min="4" max="128" placeholder="Longitud"></div>
        <label style="display:flex;align-items:center;gap:4px;font-size:13px"><input type="checkbox" id="token_digits" checked> Dígitos</label>
        <label style="display:flex;align-items:center;gap:4px;font-size:13px"><input type="checkbox" id="token_symbols" checked> Símbolos</label>
        <button class="btn" onclick="tokenGenerate()">Generar</button>
      </div>
      <div id="tokenResult" class="text-muted text-sm" style="margin-top:6px"></div>
    </div>

    <div class="section-header" style="margin-top:12px">📷 QR Scanner</div>
    <div style="margin:6px 0;padding:6px;background:var(--card);border-radius:6px">
      <p class="text-sm text-muted mb-8">Escaneá un código QR para auto-completar IP, MAC o URL</p>
      <button class="btn" onclick="qrStart()">📷 Abrir Cámara</button>
      <button class="btn btn-outline" onclick="qrStop()" style="display:none" id="qrStopBtn">✕ Cerrar</button>
      <div id="qrReader" style="display:none;margin-top:8px">
        <video id="qrVideo" style="width:100%;max-width:360px;border-radius:8px;background:#000" playsinline></video>
        <canvas id="qrCanvas" style="display:none"></canvas>
        <div id="qrResult" class="text-sm text-muted" style="margin-top:6px"></div>
      </div>
    </div>

    <div class="section-header" style="margin-top:12px">📍 Mi IP / Subred</div>
    <div style="margin:6px 0;padding:6px;background:var(--card);border-radius:6px">
      <button class="btn btn-outline" onclick="showLocalIP()">Detectar</button>
      <div id="localIPResult" class="text-muted text-sm" style="margin-top:6px"></div>
    </div>

    <div class="section-header" style="margin-top:12px">🔍 WHOIS</div>
    <div style="margin:6px 0;padding:6px;background:var(--card);border-radius:6px">
      <div style="display:flex;gap:6px">
        <div style="flex:1"><input type="text" id="whois_query" placeholder="Dominio o IP" value="google.com"></div>
        <button class="btn" onclick="whoisQuery()">Consultar</button>
      </div>
      <div id="whoisResult" class="text-muted text-sm" style="margin-top:6px"></div>
    </div>

    <div class="section-header" style="margin-top:12px">⏰ NTP Time</div>
    <div style="margin:6px 0;padding:6px;background:var(--card);border-radius:6px">
      <p class="text-sm text-muted mb-8">Verifica la hora de un servidor NTP vs la hora local</p>
      <div style="display:flex;gap:6px">
        <div style="flex:1"><input type="text" id="ntp_host" placeholder="Servidor NTP" value="pool.ntp.org"></div>
        <button class="btn" onclick="ntpQuery()">Verificar</button>
      </div>
      <div id="ntpResult" class="text-muted text-sm" style="margin-top:6px"></div>
    </div>

    <div class="section-header" style="margin-top:12px">🚪 Port Knocking</div>
    <div style="margin:6px 0;padding:6px;background:var(--card);border-radius:6px">
      <p class="text-sm text-muted mb-8">Envía secuencia de TCP SYN para abrir puertos ocultos</p>
      <div style="display:flex;gap:6px;flex-wrap:wrap">
        <div style="flex:1;min-width:120px"><input type="text" id="knock_host" placeholder="Host"></div>
        <div style="flex:1;min-width:120px"><input type="text" id="knock_ports" placeholder="Puertos: 7000,8000,9000"></div>
        <button class="btn" onclick="portKnock()">🔨 Knock</button>
      </div>
      <div id="knockResult" class="text-muted text-sm" style="margin-top:6px"></div>
    </div>

    <div class="section-header" style="margin-top:12px">🌐 HTTP Status</div>
    <div style="margin:6px 0;padding:6px;background:var(--card);border-radius:6px">
      <p class="text-sm text-muted mb-8">Verifica código de estado HTTP de una URL</p>
      <div style="display:flex;gap:6px">
        <div style="flex:1"><input type="text" id="http_status_url" placeholder="URL" value="google.com"></div>
        <label style="display:flex;align-items:center;gap:4px;font-size:13px"><input type="checkbox" id="http_status_follow" checked> Seguir redirects</label>
        <button class="btn" onclick="httpStatusCheck()">Verificar</button>
      </div>
      <div id="httpStatusResult" class="text-muted text-sm" style="margin-top:6px"></div>
    </div>

    <div class="section-header" style="margin-top:12px">📊 Latencia (TCP Ping)</div>
    <div style="margin:6px 0;padding:6px;background:var(--card);border-radius:6px">
      <p class="text-sm text-muted mb-8">Mide latencia TCP contra puertos comunes (80,443,22,8080)</p>
      <div style="display:flex;gap:6px">
        <div style="flex:1"><input type="text" id="ping_host" placeholder="Host" value="google.com"></div>
        <button class="btn" onclick="pingLatency()">Medir</button>
      </div>
      <div id="pingLatencyResult" class="text-muted text-sm" style="margin-top:6px"></div>
    </div>

    <div class="section-header" style="margin-top:12px">🖥️ DHCP Discover</div>
    <div style="margin:6px 0;padding:6px;background:var(--card);border-radius:6px">
      <p class="text-sm text-muted mb-8">Envía DHCPDISCOVER broadcast para detectar servidores DHCP en la red</p>
      <button class="btn" onclick="dhcpDiscover()">🔍 Descubrir DHCP</button>
      <div id="dhcpResult" class="text-muted text-sm" style="margin-top:6px"></div>
    </div>
  `;
}

let qrStream = null;
let qrInterval = null;

function qrStart() {
  const reader = document.getElementById("qrReader");
  const stopBtn = document.getElementById("qrStopBtn");
  const video = document.getElementById("qrVideo");
  const canvas = document.getElementById("qrCanvas");
  const ctx = canvas.getContext("2d");
  reader.style.display = "block";
  stopBtn.style.display = "inline-block";
  navigator.mediaDevices.getUserMedia({video: {facingMode: "environment"}}).then(stream => {
    qrStream = stream;
    video.srcObject = stream;
    video.play();
    qrInterval = setInterval(() => {
      if (video.readyState !== video.HAVE_ENOUGH_DATA) return;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const code = jsQR(imageData.data, imageData.width, imageData.height);
      if (code) {
        const val = code.data;
        document.getElementById("qrResult").innerHTML = `<span style='color:var(--success)'>✅ QR detectado: ${escapeHtml(val)}</span>`;
        qrStop();
        fillQRValue(val);
      }
    }, 500);
  }).catch(e => {
    document.getElementById("qrResult").innerHTML = `<span style='color:var(--danger)'>❌ Error: ${escapeHtml(e.message)}</span>`;
  });
}

function qrStop() {
  if (qrInterval) { clearInterval(qrInterval); qrInterval = null; }
  if (qrStream) { qrStream.getTracks().forEach(t => t.stop()); qrStream = null; }
  document.getElementById("qrReader").style.display = "none";
  document.getElementById("qrStopBtn").style.display = "none";
  document.getElementById("qrResult").innerHTML = "";
}

function fillQRValue(val) {
  const inputs = document.querySelectorAll("input[type='text'], input[type='url'], input[type='number']");
  for (const inp of inputs) {
    if (inp.value === "" || inp.placeholder.includes("MAC") || inp.placeholder.includes("Host") || inp.placeholder.includes("IP") || inp.placeholder.includes("URL")) {
      inp.value = val;
      inp.focus();
      inp.style.outline = "2px solid var(--success)";
      setTimeout(() => inp.style.outline = "", 2000);
      showToast("📷 QR: " + val, "success");
      return;
    }
  }
  // Si ningún input vacío, llena el primero visible
  for (const inp of inputs) {
    if (inp.offsetParent !== null) {
      inp.value = val;
      break;
    }
  }
}

async function dnsQuery(type) {
  const host = document.getElementById("dns_host").value.trim();
  if (!host) return;
  const el = document.getElementById("dnsResult");
  el.innerHTML = "<span class='text-muted'>Consultando...</span>";
  try {
    const r = await (await fetch(`/api/tools/dns?host=${encodeURIComponent(host)}&type=${type}`)).json();
    if (r.error) { el.innerHTML = `<span style="color:var(--danger)">${escapeHtml(r.error)}</span>`; return; }
    if (!r.records || r.count === 0) { el.innerHTML = "<span class='text-muted'>Sin resultados</span>"; return; }
    let html = `<div class='result-box' style='max-height:none'><div class='mb-6'><strong>${escapeHtml(r.host)}</strong> · ${r.type} · ${r.count} registro(s)</div>`;
    r.records.forEach(rec => {
      html += `<div class='cmd-item'><span class='badge badge-accent'>${escapeHtml(rec)}</span></div>`;
    });
    html += "</div>";
    el.innerHTML = html;
  } catch(e) { el.innerHTML = `<span style="color:var(--danger)">Error: ${escapeHtml(e.message)}</span>`; }
}

async function dnsMX() {
  const domain = document.getElementById("dns_host").value.trim();
  if (!domain) return;
  const el = document.getElementById("dnsResult");
  el.innerHTML = "<span class='text-muted'>Consultando MX...</span>";
  try {
    const r = await (await fetch(`/api/tools/dns/mx?domain=${encodeURIComponent(domain)}`)).json();
    if (r.error) { el.innerHTML = `<span style="color:var(--danger)">${escapeHtml(r.error)}</span>`; return; }
    if (!r.records || r.count === 0) { el.innerHTML = "<span class='text-muted'>Sin registros MX</span>"; return; }
    let html = `<div class='result-box' style='max-height:none'><div class='mb-6'><strong>MX · ${escapeHtml(r.domain)}</strong> · ${r.count} servidor(es)</div>`;
    r.records.forEach(rec => {
      html += `<div class='cmd-item'><span class='badge badge-accent'>${rec.priority}</span> <span class='text-sm'>${escapeHtml(rec.exchange)}</span></div>`;
    });
    html += "</div>";
    el.innerHTML = html;
  } catch(e) { el.innerHTML = `<span style="color:var(--danger)">Error: ${escapeHtml(e.message)}</span>`; }
}

async function sslCheck() {
  const host = document.getElementById("ssl_host").value.trim();
  const port = parseInt(document.getElementById("ssl_port").value) || 443;
  if (!host) return;
  const el = document.getElementById("sslResult");
  el.innerHTML = "<span class='text-muted'>Verificando certificado...</span>";
  try {
    const r = await (await fetch(`/api/tools/ssl?host=${encodeURIComponent(host)}&port=${port}`)).json();
    if (r.error) { el.innerHTML = `<span style="color:var(--danger)">⚠️ ${escapeHtml(r.error)}</span>`; return; }
    if (!r.valid) { el.innerHTML = `<span style="color:var(--danger)">⚠️ Certificado no válido: ${escapeHtml(r.error||"")}</span>`; return; }
    let html = `<div class='result-box' style='max-height:none'>
      <div class='mb-6'><strong>🔒 ${escapeHtml(r.host)}:${r.port}</strong></div>
      <div class='text-sm'>CN: ${escapeHtml(r.cn)}</div>`;
    if (r.issuer) html += `<div class='text-sm'>Emitido por: ${escapeHtml(r.issuer)}</div>`;
    if (r.subject) html += `<div class='text-sm'>Organización: ${escapeHtml(r.subject)}</div>`;
    if (r.alt_names && r.alt_names.length) html += `<div class='text-sm'>SANs: ${escapeHtml(r.alt_names.join(", "))}</div>`;
    if (r.not_after) html += `<div class='text-sm'>Válido hasta: ${escapeHtml(r.not_after)}</div>`;
    if (r.days_left !== null && r.days_left !== undefined) {
      const cls = r.days_left < 30 ? "danger" : r.days_left < 90 ? "warning" : "success";
      html += `<div class='text-sm'>Días restantes: <span style="color:var(--${cls})">${r.days_left}</span></div>`;
    }
    if (r.protocol) html += `<div class='text-sm'>Protocolo: ${escapeHtml(r.protocol)}</div>`;
    if (r.cipher) html += `<div class='text-sm'>Cipher: ${escapeHtml(r.cipher)}</div>`;
    html += "</div>";
    el.innerHTML = html;
  } catch(e) { el.innerHTML = `<span style="color:var(--danger)">Error: ${escapeHtml(e.message)}</span>`; }
}

async function httpHeadersCheck() {
  let url = document.getElementById("http_url").value.trim();
  if (!url) return;
  if (!url.startsWith("http://") && !url.startsWith("https://")) url = "https://" + url;
  const el = document.getElementById("httpResult");
  el.innerHTML = "<span class='text-muted'>Obteniendo headers...</span>";
  try {
    const r = await (await fetch(`/api/tools/http-headers?url=${encodeURIComponent(url)}`)).json();
    if (r.error) { el.innerHTML = `<span style="color:var(--danger)">⚠️ ${escapeHtml(r.error)}</span>`; return; }
    let html = `<div class='result-box' style='max-height:none'>
      <div class='mb-6'><strong>${escapeHtml(r.url)}</strong> · ${r.status} ${escapeHtml(r.reason||"")}</div>`;
    if (r.headers) {
      const secHeaders = ["strict-transport-security","x-frame-options","x-content-type-options","content-security-policy","x-xss-protection"];
      Object.entries(r.headers).forEach(([k, v]) => {
        const isSec = secHeaders.includes(k.toLowerCase());
        html += `<div class='cmd-item' style='padding:4px 0'><span class='badge ${isSec ? "badge-success" : "badge-accent"}' style='font-size:10px'>${escapeHtml(k)}</span> <span class='text-xs'>${escapeHtml(String(v).slice(0, 120))}</span></div>`;
      });
    }
    html += "</div>";
    el.innerHTML = html;
  } catch(e) { el.innerHTML = `<span style="color:var(--danger)">Error: ${escapeHtml(e.message)}</span>`; }
}

async function wolSend() {
  const mac = document.getElementById("wol_mac").value.trim();
  if (!mac) return;
  const broadcast = document.getElementById("wol_broadcast").value.trim() || "255.255.255.255";
  const port = parseInt(document.getElementById("wol_port").value) || 9;
  const el = document.getElementById("wolResult");
  el.innerHTML = "<span class='text-muted'>Enviando WOL...</span>";
  try {
    const r = await (await fetch("/api/tools/wol", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({mac, broadcast, port})
    })).json();
    if (r.error) { el.innerHTML = `<span style="color:var(--danger)">⚠️ ${escapeHtml(r.error)}</span>`; return; }
    el.innerHTML = `<span style="color:var(--success)">✅ ${escapeHtml(r.message||"WOL enviado")}</span>`;
  } catch(e) { el.innerHTML = `<span style="color:var(--danger)">Error: ${escapeHtml(e.message)}</span>`; }
}

async function tokenGenerate() {
  const length = parseInt(document.getElementById("token_length").value) || 32;
  const digits = document.getElementById("token_digits").checked ? "1" : "0";
  const symbols = document.getElementById("token_symbols").checked ? "1" : "0";
  const el = document.getElementById("tokenResult");
  el.innerHTML = "<span class='text-muted'>Generando...</span>";
  try {
    const r = await (await fetch(`/api/tools/token?length=${length}&digits=${digits}&symbols=${symbols}`)).json();
    if (r.error) { el.innerHTML = `<span style="color:var(--danger)">⚠️ ${escapeHtml(r.error)}</span>`; return; }
    const strengthIcon = r.strength === "strong" ? "🟢" : r.strength === "medium" ? "🟡" : "🔴";
    const html = `<div class='result-box' style='max-height:none'>
      <div class='mb-6' style='font-family:monospace;font-size:16px;word-break:break-all'>${escapeHtml(r.token)}</div>
      <div class='text-sm'>${strengthIcon} ${escapeHtml(r.strength)} · ${r.length} caracteres · ${r.entropy_bits} bits</div>
      <button class='btn btn-sm btn-outline' style='margin-top:6px' onclick='copyText("${escapeHtml(r.token).replace(/"/g, "&quot;")}")'>📋 Copiar</button>
    </div>`;
    el.innerHTML = html;
  } catch(e) { el.innerHTML = `<span style="color:var(--danger)">Error: ${escapeHtml(e.message)}</span>`; }
}

function copyText(text) {
  navigator.clipboard?.writeText(text).catch(() => {});
}

async function showLocalIP() {
  const el = document.getElementById("localIPResult");
  el.innerHTML = "<span class='text-muted'>Detectando...</span>";
  try {
    const r = await (await fetch("/api/tools/local-ip")).json();
    if (r.error) { el.innerHTML = `<span class='text-muted'>${escapeHtml(r.error)}</span>`; return; }
    let html = `<div class='result-box' style='max-height:none'>
      <div class='mb-6'><strong>📍 IP Local: ${escapeHtml(r.ip)}</strong></div>`;
    if (r.subnet && r.subnet !== "unknown") html += `<div class='text-sm'>Subred sugerida: <span class='badge badge-accent' style='cursor:pointer' onclick="document.getElementById('scan_subnet').value='${escapeHtml(r.subnet)}'">${escapeHtml(r.subnet)}</span> (click para usar en scanner)</div>`;
    html += "</div>";
    el.innerHTML = html;
  } catch(e) { el.innerHTML = `<span style="color:var(--danger)">Error: ${escapeHtml(e.message)}</span>`; }
}

// ─── WHOIS ──────────────────────────────────────────────────

async function whoisQuery() {
  const query = document.getElementById("whois_query").value.trim();
  if (!query) return;
  const el = document.getElementById("whoisResult");
  el.innerHTML = "<span class='text-muted'>Consultando WHOIS...</span>";
  try {
    const r = await (await fetch(`/api/tools/whois?query=${encodeURIComponent(query)}`)).json();
    if (r.error) { el.innerHTML = `<span style="color:var(--danger)">⚠️ ${escapeHtml(r.error)}</span>`; return; }
    let html = `<div class='result-box' style='max-height:none'>
      <div class='mb-6'><strong>🔍 ${escapeHtml(r.query)}</strong> · ${r.lines} líneas · servidor: ${escapeHtml(r.server)}</div>
      <pre style='font-size:11px;white-space:pre-wrap;word-break:break-word;max-height:300px;overflow-y:auto;background:var(--bg);padding:8px;border-radius:4px'>${escapeHtml(r.raw)}</pre>
    </div>`;
    el.innerHTML = html;
  } catch(e) { el.innerHTML = `<span style="color:var(--danger)">Error: ${escapeHtml(e.message)}</span>`; }
}

// ─── NTP ────────────────────────────────────────────────────

async function ntpQuery() {
  const host = document.getElementById("ntp_host").value.trim() || "pool.ntp.org";
  const el = document.getElementById("ntpResult");
  el.innerHTML = "<span class='text-muted'>Consultando NTP...</span>";
  try {
    const r = await (await fetch(`/api/tools/ntp?host=${encodeURIComponent(host)}`)).json();
    if (r.error) { el.innerHTML = `<span style="color:var(--danger)">⚠️ ${escapeHtml(r.error)}</span>`; return; }
    const offset = r.offset_seconds;
    const cls = Math.abs(offset) > 1 ? "danger" : Math.abs(offset) > 0.1 ? "warning" : "success";
    const sign = offset > 0 ? "🟠 adelantado" : offset < 0 ? "🔵 atrasado" : "🟢 exacto";
    let html = `<div class='result-box' style='max-height:none'>
      <div class='mb-6'><strong>⏰ ${escapeHtml(r.host)}</strong></div>
      <div class='text-sm'>NTP: ${escapeHtml(r.ntp_time)}</div>
      <div class='text-sm'>Local: ${escapeHtml(r.local_time)}</div>
      <div class='text-sm'>Offset: <span style="color:var(--${cls})">${offset}s</span> (${sign})</div>`;
    if (r.stratum !== undefined) html += `<div class='text-sm'>Stratum: ${r.stratum}</div>`;
    html += "</div>";
    el.innerHTML = html;
  } catch(e) { el.innerHTML = `<span style="color:var(--danger)">Error: ${escapeHtml(e.message)}</span>`; }
}

// ─── PORT KNOCKING ─────────────────────────────────────────

async function portKnock() {
  const host = document.getElementById("knock_host").value.trim() || document.getElementById("scan_host").value;
  const ports = document.getElementById("knock_ports").value.trim();
  if (!host || !ports) { showToast("Host y puertos requeridos", "error"); return; }
  const el = document.getElementById("knockResult");
  el.innerHTML = "<span class='text-muted'>Knockeando...</span>";
  try {
    const r = await (await fetch(`/api/tools/port-knock?host=${encodeURIComponent(host)}&ports=${encodeURIComponent(ports)}`)).json();
    if (r.error) { el.innerHTML = `<span style="color:var(--danger)">⚠️ ${escapeHtml(r.error)}</span>`; return; }
    let html = `<div class='result-box' style='max-height:none'>
      <div class='mb-6'><strong>🚪 Secuencia: ${escapeHtml(r.host)}</strong></div>`;
    r.results.forEach(p => {
      html += `<div class='cmd-item'><span class='badge badge-accent'>${p.port}</span> <span class='text-xs'>${p.status === "open" ? "🟢 abierto" : "🔵 enviado"}</span></div>`;
    });
    html += "</div>";
    el.innerHTML = html;
  } catch(e) { el.innerHTML = `<span style="color:var(--danger)">Error: ${escapeHtml(e.message)}</span>`; }
}

// ─── HTTP STATUS ────────────────────────────────────────────

async function httpStatusCheck() {
  let url = document.getElementById("http_status_url").value.trim();
  if (!url) return;
  const follow = document.getElementById("http_status_follow").checked ? "1" : "0";
  const el = document.getElementById("httpStatusResult");
  el.innerHTML = "<span class='text-muted'>Verificando...</span>";
  try {
    const r = await (await fetch(`/api/tools/http-status?url=${encodeURIComponent(url)}&follow=${follow}`)).json();
    if (r.error) { el.innerHTML = `<span style="color:var(--danger)">⚠️ ${escapeHtml(r.error)}</span>`; return; }
    const statusCls = r.status < 300 ? "success" : r.status < 400 ? "warning" : "danger";
    let html = `<div class='result-box' style='max-height:none'>
      <div class='mb-6'><strong>${escapeHtml(r.url)}</strong></div>
      <div class='text-sm'>Estado: <span style="color:var(--${statusCls})">${r.status} ${escapeHtml(r.reason||"")}</span></div>`;
    if (r.redirected) html += `<div class='text-sm'>Redirect → ${escapeHtml(r.final_url)}</div>`;
    html += "</div>";
    el.innerHTML = html;
  } catch(e) { el.innerHTML = `<span style="color:var(--danger)">Error: ${escapeHtml(e.message)}</span>`; }
}

// ─── PING LATENCY ───────────────────────────────────────────

async function pingLatency() {
  const host = document.getElementById("ping_host").value.trim();
  if (!host) return;
  const el = document.getElementById("pingLatencyResult");
  el.innerHTML = "<span class='text-muted'>Midiendo latencia TCP...</span>";
  try {
    const r = await (await fetch(`/api/tools/ping-latency?host=${encodeURIComponent(host)}`)).json();
    if (r.error) { el.innerHTML = `<span style="color:var(--danger)">⚠️ ${escapeHtml(r.error)}</span>`; return; }
    let html = `<div class='result-box' style='max-height:none'>
      <div class='mb-6'><strong>📊 ${escapeHtml(r.host)}</strong></div>`;
    if (r.results) {
      r.results.forEach(p => html += `<div class='cmd-item'><span class='badge badge-accent'>${p.port}</span> <span class='text-xs'>${p.latency_ms} ms</span></div>`);
    }
    if (r.latency_ms !== null && r.latency_ms !== undefined) {
      html += `<div style='margin-top:6px'><span class='badge badge-accent'>Promedio: ${r.latency_ms} ms</span> <span class='badge badge-accent'>Mín: ${r.min_ms} ms</span> <span class='badge badge-accent'>Máx: ${r.max_ms} ms</span></div>`;
    }
    html += "</div>";
    el.innerHTML = html;
  } catch(e) { el.innerHTML = `<span style="color:var(--danger)">Error: ${escapeHtml(e.message)}</span>`; }
}


// ─── WIFI ────────────────────────────────────────────────────

function showWiFi() {
  document.getElementById("results").innerHTML = `
    <h3 style='margin-bottom:12px'>📶 Escáner WiFi</h3>
    <p class='text-sm text-muted mb-8'>Escanea redes WiFi cercanas usando iwlist (Linux) o netsh (Windows)</p>
    <div style='display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px'>
      <button class='btn' onclick='wifiScan()'>📶 Escanear</button>
      <button class='btn btn-outline' onclick='wifiInterfaces()'>🔌 Interfaces</button>
    </div>
    <div id='wifiScanResult' class='text-muted text-sm'></div>
  `;
}

async function wifiScan() {
  const el = document.getElementById("wifiScanResult");
  el.innerHTML = "<span class='text-muted'>Escaneando redes WiFi...</span>";
  try {
    const r = await (await fetch("/api/wifi/scan")).json();
    if (r.error) { el.innerHTML = `<span style="color:var(--warning)">⚠️ ${escapeHtml(r.error)}</span>`; return; }
    if (!r.networks || r.count === 0) { el.innerHTML = "<span class='text-muted'>No se encontraron redes</span>"; return; }
    let html = `<div class='result-box' style='max-height:none'><div class='mb-6'><strong>📶 ${r.count} redes encontradas</strong> (${escapeHtml(r.interface||"")})</div>`;
    // Ordenar por señal descendente
    r.networks.sort((a,b) => (b.signal_pct||0) - (a.signal_pct||0));
    r.networks.forEach(n => {
      const sig = n.signal_pct !== undefined ? n.signal_pct : 0;
      const cls = sig >= 70 ? "success" : sig >= 40 ? "warning" : "danger";
      html += `<div class='cmd-item' style='padding:6px 0'>
        <span style='flex:1'>
          <strong>${escapeHtml(n.ssid||"<hidden>")}</strong>
          <span class='text-xs text-muted' style='margin-left:6px'>${escapeHtml(n.bssid||"")}</span>
        </span>
        <span style='display:flex;gap:6px;align-items:center'>
          <span class='badge badge-${cls}'>${sig}%</span>
          <span class='text-xs'>CH ${n.channel||"?"}</span>
          <span class='text-xs'>${escapeHtml(n.wpa||n.standard||"")}</span>
        </span>
      </div>`;
    });
    html += "</div>";
    el.innerHTML = html;
  } catch(e) { el.innerHTML = `<span style="color:var(--danger)">Error: ${escapeHtml(e.message)}</span>`; }
}

async function wifiInterfaces() {
  const el = document.getElementById("wifiScanResult");
  el.innerHTML = "<span class='text-muted'>Obteniendo interfaces...</span>";
  try {
    const r = await (await fetch("/api/wifi/interfaces")).json();
    if (r.error) { el.innerHTML = `<span style="color:var(--warning)">⚠️ ${escapeHtml(r.error)}</span>`; return; }
    let html = `<div class='result-box' style='max-height:none'>`;
    if (r.interfaces) {
      r.interfaces.forEach(iface => {
        html += `<div class='cmd-item'>
          <strong>${escapeHtml(iface.name)}</strong>
          ${iface.ssid ? `<span class='text-xs'>SSID: ${escapeHtml(iface.ssid)}</span>` : ""}
          ${iface.mode ? `<span class='text-xs'>Modo: ${iface.mode}</span>` : ""}
          ${iface.quality ? `<span class='text-xs'>Calidad: ${iface.quality}</span>` : ""}
        </div>`;
      });
    } else if (r.raw) {
      html += `<pre style='font-size:11px'>${escapeHtml(r.raw)}</pre>`;
    }
    html += "</div>";
    el.innerHTML = html;
  } catch(e) { el.innerHTML = `<span style="color:var(--danger)">Error: ${escapeHtml(e.message)}</span>`; }
}


// ─── BANDWIDTH MONITOR ──────────────────────────────────────

function showBandwidth() {
  document.getElementById("results").innerHTML = `
    <h3 style='margin-bottom:12px'>📊 Monitor de Ancho de Banda (SNMP)</h3>
    <p class='text-sm text-muted mb-8'>Consulta tráfico en tiempo real de interfaces SNMP. Requiere un dispositivo con SNMP habilitado.</p>
    <div class='input-group'><label>Host</label><input type='text' id='bw_host' placeholder='192.168.1.1'></div>
    <div class='input-group'><label>Community</label><input type='text' id='bw_community' value='public'></div>
    <div class='input-group'><label>IF Index</label><input type='number' id='bw_ifindex' value='1' min='1'></div>
    <div class='input-group'><label>Nombre (opcional)</label><input type='text' id='bw_name' placeholder='WAN, LAN1, etc'></div>
    <div style='display:flex;gap:6px;flex-wrap:wrap;margin-top:8px'>
      <button class='btn' onclick='bwPoll()'>📊 Poll</button>
      <button class='btn btn-outline' onclick='bwStartAuto()'>🔄 Auto (5s)</button>
      <button class='btn btn-outline' onclick='bwStopAuto()'>⏹ Stop</button>
      <button class='btn btn-outline' onclick='bwHistory()'>📈 Historial</button>
    </div>
    <div id='bwResult' class='text-muted text-sm' style='margin-top:10px'></div>
  `;
}

let _bwAutoInterval = null;

async function bwPoll() {
  const host = document.getElementById("bw_host").value;
  const community = document.getElementById("bw_community").value;
  const ifindex = parseInt(document.getElementById("bw_ifindex").value) || 1;
  const name = document.getElementById("bw_name").value || `if${ifindex}`;
  if (!host) { showToast("Host requerido", "error"); return; }
  const el = document.getElementById("bwResult");
  el.innerHTML = "<span class='text-muted'>Consultando SNMP...</span>";
  try {
    const r = await (await fetch(`/api/bandwidth/poll?host=${encodeURIComponent(host)}&community=${encodeURIComponent(community)}&ifindex=${ifindex}&name=${encodeURIComponent(name)}`)).json();
    if (r.error) { el.innerHTML = `<span style="color:var(--danger)">⚠️ ${escapeHtml(r.error)}</span>`; return; }
    let html = `<div class='result-box' style='max-height:none'>
      <div class='mb-6'><strong>📊 ${escapeHtml(r.host)} · ${escapeHtml(r.name||`if${r.ifindex}`)}</strong></div>`;
    if (r.in_bps !== undefined && r.in_bps !== null) {
      html += `<div class='cmd-item'>⬇ In: <strong>${(r.in_bps/1e6).toFixed(2)} Mbps</strong></div>
      <div class='cmd-item'>⬆ Out: <strong>${(r.out_bps/1e6).toFixed(2)} Mbps</strong></div>`;
    } else {
      html += `<div class='text-sm text-muted'>Esperando segunda muestra...</div>`;
    }
    if (r.in_bytes !== null && r.in_bytes !== undefined) {
      html += `<div class='text-xs text-muted'>Total In: ${(r.in_bytes/1e9).toFixed(2)} GB · Out: ${(r.out_bytes/1e9).toFixed(2)} GB</div>`;
    }
    html += "</div>";
    el.innerHTML = html;
  } catch(e) { el.innerHTML = `<span style="color:var(--danger)">Error: ${escapeHtml(e.message)}</span>`; }
}

function bwStartAuto() {
  bwPoll();
  if (_bwAutoInterval) clearInterval(_bwAutoInterval);
  _bwAutoInterval = setInterval(() => bwPoll(), 5000);
  showToast("Auto-poll cada 5s activado", "success");
}

function bwStopAuto() {
  if (_bwAutoInterval) { clearInterval(_bwAutoInterval); _bwAutoInterval = null; }
  showToast("Auto-poll detenido", "info");
}

async function bwHistory() {
  const host = document.getElementById("bw_host").value;
  const ifindex = parseInt(document.getElementById("bw_ifindex").value) || 1;
  if (!host) return;
  const el = document.getElementById("bwResult");
  el.innerHTML = "<span class='text-muted'>Cargando historial...</span>";
  try {
    const r = await (await fetch(`/api/bandwidth/traffic?host=${encodeURIComponent(host)}&ifindex=${ifindex}`)).json();
    if (r.error) { el.innerHTML = `<span style="color:var(--warning)">⚠️ ${escapeHtml(r.error)}</span>`; return; }
    let html = `<div class='result-box' style='max-height:none'>
      <div class='mb-6'><strong>📈 ${escapeHtml(r.host)} · ${escapeHtml(r.name)}</strong></div>
      <div class='cmd-item'>⬇ In: <strong>${r.latest.in_mbps} Mbps</strong></div>
      <div class='cmd-item'>⬆ Out: <strong>${r.latest.out_mbps} Mbps</strong></div>
      <div class='text-xs text-muted'>Promedio In: ${r.avg_in_mbps} · Max In: ${r.max_in_mbps} · Prom Out: ${r.avg_out_mbps} · Max Out: ${r.max_out_mbps}</div>`;
    // Mini gráfico SVG inline
    if (r.points && r.points.length > 1) {
      const w = 300, h = 80, pad = 4;
      const vals = r.points.map(p => Math.max(p.in, p.out));
      const maxVal = Math.max(...vals, 1);
      html += `<div style='margin-top:8px'><svg viewBox='0 0 ${w} ${h}' style='width:100%;max-width:${w}px;height:${h}px;background:var(--bg);border-radius:4px'>`;
      // Grid lines
      for (let i = 0; i <= 4; i++) {
        const y = pad + (h - 2*pad) * (1 - i/4);
        html += `<line x1='${pad}' y1='${y}' x2='${w-pad}' y2='${y}' stroke='rgba(255,255,255,0.05)' stroke-width='1'/>`;
      }
      // Data lines
      const step = (w - 2*pad) / (r.points.length - 1);
      let inPath = "", outPath = "";
      r.points.forEach((p, i) => {
        const x = pad + i * step;
        const inY = pad + (h - 2*pad) * (1 - p.in / maxVal);
        const outY = pad + (h - 2*pad) * (1 - p.out / maxVal);
        inPath += (i === 0 ? "M" : "L") + x.toFixed(1) + " " + inY.toFixed(1);
        outPath += (i === 0 ? "M" : "L") + x.toFixed(1) + " " + outY.toFixed(1);
      });
      html += `<path d='${inPath}' stroke='var(--accent)' stroke-width='2' fill='none' opacity='0.8'/>`;
      html += `<path d='${outPath}' stroke='var(--accent2)' stroke-width='2' fill='none' opacity='0.8'/>`;
      html += `</svg>
        <div class='text-xs text-muted' style='display:flex;justify-content:space-between;max-width:${w}px'>
          <span>⬇ ${r.latest.in_mbps} Mbps</span>
          <span>⬆ ${r.latest.out_mbps} Mbps</span>
        </div></div>`;
    }
    html += `<div class='text-xs text-muted' style='margin-top:6px'>${r.points?.length || 0} muestras</div>`;
    html += "</div>";
    el.innerHTML = html;
  } catch(e) { el.innerHTML = `<span style="color:var(--danger)">Error: ${escapeHtml(e.message)}</span>`; }
}


// ─── DHCP ──────────────────────────────────────────────────

async function dhcpDiscover() {
  const el = document.getElementById("dhcpResult");
  el.innerHTML = "<span class='text-muted'>Escuchando DHCP offers (3s)...</span>";
  try {
    const r = await (await fetch("/api/dhcp/discover")).json();
    if (r.error) { el.innerHTML = `<span style="color:var(--danger)">⚠️ ${escapeHtml(r.error)}</span>`; return; }
    if (!r.servers || r.count === 0) { el.innerHTML = "<span class='text-muted'>No se detectaron servidores DHCP</span>"; return; }
    let html = `<div class='result-box' style='max-height:none'>
      <div class='mb-6'><strong>🖥️ ${r.count} servidor(es) DHCP detectado(s)</strong></div>`;
    r.servers.forEach(s => {
      html += `<div class='section' style='margin-top:6px'>
        <div class='section-header'>🖥️ ${escapeHtml(s.server_id)}</div>
        <div class='section-body'>
          <div class='text-sm'>IP Ofrecida: <strong>${escapeHtml(s.offered_ip||"?")}</strong></div>
          ${s.subnet_mask ? `<div class='text-sm'>Máscara: ${escapeHtml(s.subnet_mask)}</div>` : ""}
          ${s.router ? `<div class='text-sm'>Gateway: ${escapeHtml(s.router)}</div>` : ""}
          ${s.dns_servers ? `<div class='text-sm'>DNS: ${escapeHtml(s.dns_servers.join(", "))}</div>` : ""}
          ${s.domain ? `<div class='text-sm'>Dominio: ${escapeHtml(s.domain)}</div>` : ""}
          ${s.lease_time_s ? `<div class='text-sm'>Lease: ${s.lease_time_s}s (${(s.lease_time_s/3600).toFixed(1)}h)</div>` : ""}
          ${s.mac ? `<div class='text-sm'>MAC: ${escapeHtml(s.mac)}</div>` : ""}
        </div>
      </div>`;
    });
    html += "</div>";
    el.innerHTML = html;
  } catch(e) { el.innerHTML = `<span style="color:var(--danger)">Error: ${escapeHtml(e.message)}</span>`; }
}


// ─── SNMP ────────────────────────────────────────────────────

function showSNMP() {
  document.getElementById("results").innerHTML = `
    <h3 style='margin-bottom:12px'>📡 SNMP</h3>
    <div class='input-group'><label>Host</label><input type='text' id='snmp_host' placeholder='192.168.1.1'></div>
    <div class='input-group'><label>Community</label><input type='text' id='snmp_comm' value='public'></div>
    <div class='tabs'>
      <button class='tab active' onclick='snmpCheck(this)'>🔍 Check</button>
      <button class='tab' onclick='snmpSystem(this)'>💻 Sistema</button>
      <button class='tab' onclick='snmpInterfaces(this)'>🔌 Interfaces</button>
      <button class='tab' onclick='snmpDetectDevice(this)'>📷 CCTV/AC</button>
      <button class='tab' onclick='snmpWalk(this)'>🌲 Walk</button>
    </div>
    <div id='snmpResult'></div>
  `;
}

function snmpCheck(btn) {
  document.querySelectorAll(".tab").forEach(t=>t.classList.remove("active"));
  if(btn)btn.classList.add("active");
  const h=document.getElementById("snmp_host").value, c=document.getElementById("snmp_comm").value;
  if(!h)return;
  asyncFetch("/api/snmp/check?host="+h+"&community="+c, "snmpResult",
    r => `<div class='result-box'>${JSON.stringify(r,null,2)}</div>`
  );
}

function snmpSystem(btn) {
  document.querySelectorAll(".tab").forEach(t=>t.classList.remove("active"));
  if(btn)btn.classList.add("active");
  const h=document.getElementById("snmp_host").value, c=document.getElementById("snmp_comm").value;
  if(!h)return;
  asyncFetch("/api/snmp/system?host="+h+"&community="+c, "snmpResult",
    r => `<div class='result-box'>${JSON.stringify(r,null,2)}</div>`
  );
}

function snmpInterfaces(btn) {
  document.querySelectorAll(".tab").forEach(t=>t.classList.remove("active"));
  if(btn)btn.classList.add("active");
  const h=document.getElementById("snmp_host").value, c=document.getElementById("snmp_comm").value;
  if(!h)return;
  asyncFetch("/api/snmp/interfaces?host="+h+"&community="+c, "snmpResult",
    r => `<div class='result-box'>${JSON.stringify(r,null,2)}</div>`
  );
}

function snmpDetectDevice(btn) {
  document.querySelectorAll(".tab").forEach(t=>t.classList.remove("active"));
  if(btn)btn.classList.add("active");
  const h=document.getElementById("snmp_host").value, c=document.getElementById("snmp_comm").value;
  if(!h)return;
  asyncFetch("/api/snmp/detect-device?host="+h+"&community="+c, "snmpResult",
    r => `<div class='result-box'>${JSON.stringify(r,null,2)}</div>`
  );
}

function snmpWalk(btn) {
  document.querySelectorAll(".tab").forEach(t=>t.classList.remove("active"));
  if(btn)btn.classList.add("active");
  const h=document.getElementById("snmp_host").value, c=document.getElementById("snmp_comm").value;
  if(!h)return;
  asyncFetch("/api/snmp/walk?host="+h+"&community="+c, "snmpResult",
    r => {
      const txt=Object.entries(r).slice(0,30).map(([k,v])=>k+" = "+v).join("\n")+"\n...(truncado)";
      return `<div class='result-box'>${txt}</div>`;
    }
  );
}

// ─── TOPOLOGÍA ───────────────────────────────────────────────

let currentCy = null;
let selectedNode = null;
let currentTopologyId = null;

async function showTopology() {
  const topologies = await (await fetch("/api/topology")).json();
  let html = `
    <h3 style='margin-bottom:12px'>🕸️ Topología de Red</h3>
    <div style='display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap'>
      <button class='btn' style='flex:1;min-width:100px' onclick='newTopology()'>➕ Nueva</button>
      <button class='btn btn-outline' style='flex:1;min-width:130px' onclick='autoDiscoverForm()'>📡 Auto-Descubrir</button>
    </div>
    <div id='topologyList'>`;
  
  if (topologies.length === 0) {
    html += "<p style='color:var(--text2)'>No hay topologías guardadas.</p>";
  } else {
    topologies.forEach(t => {
      html += `
        <div class='card' style='text-align:left;padding:12px 14px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center'>
          <div onclick='openTopology("${t.id}")' style='flex:1;cursor:pointer'>
            <div style='font-weight:600'>${escapeHtml(t.name || "Sin nombre")}</div>
            <div style='font-size:11px;color:var(--text2)'>${t.nodes?.length || 0} dispositivos · ${t.updated_at?.split("T")[0]}</div>
          </div>
          <button class='btn btn-outline' style='width:auto;padding:4px 8px;color:var(--danger)' onclick='deleteTopology("${t.id}")'>✕</button>
        </div>`;
    });
  }
  html += `</div><div id='topologyEditor' style='display:none'></div>`;
  document.getElementById("results").innerHTML = html;
}

async function deleteTopology(id) {
  if (!confirm("¿Eliminar esta topología?")) return;
  await fetch(`/api/topology/${id}`, { method: "DELETE" });
  showTopology();
}

function newTopology() {
  const name = prompt("Nombre de la topología:");
  if (!name) return;
  openTopology(null, name);
}

async function openTopology(id, name = "", preloadData = null) {
  currentTopologyId = id;
  let data = { name, nodes: [], edges: [] };
  if (preloadData) {
    data = preloadData;
  } else if (id) {
    data = await (await fetch(`/api/topology/${id}`)).json();
  }

  document.getElementById("topologyList").style.display = "none";
  document.getElementById("homeGrid").style.display = "none";
  const editor = document.getElementById("topologyEditor");
  editor.style.display = "block";
  editor.innerHTML = `
    <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:10px'>
      <h4 id='topoName'>${escapeHtml(data.name)}</h4>
      <div style='display:flex;gap:6px'>
        <button class='topo-btn' onclick='currentCy.fit()'>⛶ Ajustar</button>
        <button class='topo-btn' onclick='saveTopologyData()'>💾 Guardar</button>
        <button class='topo-btn' onclick='showTopology()'>✕ Cerrar</button>
      </div>
    </div>
    <div class='topo-tools'>
      <button class='topo-btn' onclick='addNode("router")' title='Añadir Router'>🖧 Router</button>
      <button class='topo-btn' onclick='addNode("switch")' title='Añadir Switch'>☲ Switch</button>
      <button class='topo-btn' onclick='addNode("firewall")' title='Añadir Firewall'>🛡️ Firewall</button>
      <button class='topo-btn' onclick='addNode("server")' title='Añadir Servidor'>🖳 Server</button>
      <button class='topo-btn' onclick='addNode("pc")' title='Añadir Computadora'>💻 PC</button>
      <button class='topo-btn' onclick='addNode("ap")' title='Añadir Access Point'>📡 AP</button>
      <button class='topo-btn' onclick='addNode("camera")' title='Añadir Cámara'>📷 Cámara</button>
      <button class='topo-btn' onclick='addNode("nvr")' title='Añadir NVR'>📼 NVR</button>
      <button class='topo-btn' onclick='addNode("dvr")' title='Añadir DVR'>📼 DVR</button>
      <button class='topo-btn' onclick='addNode("cloud")' title='Añadir Internet'>☁️ Internet</button>
      <button class='topo-btn' style='background:var(--accent);color:#000' onclick='addNode("area")' title='Crear Área/Subred'>🔲 Área</button>
      <div style='width:100%; height:4px'></div>
      <button class='topo-btn' style='background:var(--accent2);color:#000' onclick='toggleConnectMode("ethernet")'>🔗 Eth</button>
      <button class='topo-btn' style='background:#f97316;color:#000' onclick='toggleConnectMode("fiber")'>🔗 Fibra</button>
      <button class='topo-btn' style='background:#10b981;color:#000' onclick='toggleConnectMode("wireless")'>📡 WiFi</button>
      <button class='topo-btn' style='background:var(--warning);color:#000' onclick='pollNetworkStatus()'>⚡ Live Status</button>
      <button class='topo-btn' style='background:var(--success);color:#000' onclick='switchMode("simulation")'>▶ SIMULADOR</button>
      <button class='topo-btn' style='background:var(--accent2);color:#000' onclick='scanSubnetToTopology()'>📡 Zenmap Scan</button>
    </div>
    <div id='topologyCanvas'></div>
    
    <!-- Mode Switcher (PT Style) -->
    <div style='display:flex; background:var(--surface); border-top:1px solid rgba(255,255,255,0.1); padding:5px; gap:5px'>
      <button id='btnRealTime' class='topo-btn' style='flex:1; background:var(--accent); color:#000' onclick='switchMode("realtime")'>🌐 Real-Time</button>
      <button id='btnSimulation' class='topo-btn' style='flex:1' onclick='switchMode("simulation")'>⏳ Simulation</button>
    </div>

    <div id='simPanel' style='display:none; background:var(--surface3); padding:10px; border-radius:var(--radius-sm); margin-top:10px; border:1px solid var(--success)'>
      <div style='display:flex; justify-content:space-between; align-items:center'>
        <span style='font-weight:700; color:var(--success)'>ESCENARIOS DE SIMULACIÓN</span>
        <button class='topo-btn' style='padding:2px 8px' onclick='clearSims()'>Limpiar</button>
      </div>
      <div id='simList' style='margin-top:8px; display:flex; flex-direction:column; gap:4px'></div>
      <div id='simLog' style='margin-top:10px; font-family:monospace; font-size:10px; height:80px; overflow-y:auto; background:#000; padding:5px; border-radius:4px'></div>
    </div>
    <div id='nodeInspector' class='topo-inspector'>
      <div style='display:flex;justify-content:space-between;margin-bottom:8px'>
        <strong id='insTitle'>Dispositivo</strong>
        <div style='display:flex;gap:4px'>
          <button id='btnAutoDetect' class='btn btn-outline' style='width:auto;padding:2px 6px;font-size:10px;background:var(--accent2);color:#000' onclick='autoDetectNode()'>🔎 Detectar</button>
          <button class='btn btn-outline' style='width:auto;padding:2px 6px;font-size:10px' onclick='deleteSelected()'>Eliminar</button>
        </div>
      </div>
      <div id='groupNodeProps'>
        <div style='display:grid;grid-template-columns:1fr 1fr;gap:8px'>
          <div class='input-group'><label>Nombre</label><input type='text' id='insLabel' oninput='updateNodeProp("label", this.value)'></div>
          <div class='input-group'><label>IP Address</label><input type='text' id='insIP' oninput='updateNodeProp("ip", this.value)'></div>
        </div>
        <div style='display:grid;grid-template-columns:1fr 1fr;gap:8px'>
          <div class='input-group'><label>Marca (Vendor)</label>
            <select id='insVendor' onchange='updateNodeProp("vendor", this.value)'>
              <option value=''>Genérico</option>
              <option value='Cisco'>Cisco</option>
              <option value='MikroTik'>MikroTik</option>
              <option value='Ubiquiti'>Ubiquiti</option>
              <option value='Fortinet'>Fortinet</option>
              <option value='Hikvision'>Hikvision</option>
              <option value='Dahua'>Dahua</option>
              <option value='ZKTeco'>ZKTeco</option>
              <option value='TP-Link'>TP-Link</option>
              <option value='Huawei'>Huawei</option>
              <option value='Dell'>Dell</option>
              <option value='HP'>HP</option>
            </select>
          </div>
          <div class='input-group'><label>S.O.</label>
            <select id='insOS' onchange='updateNodeProp("os", this.value)'>
              <option value=''>Desconocido</option>
              <option value='IOS'>Cisco IOS</option>
              <option value='RouterOS'>MikroTik RouterOS</option>
              <option value='FortiOS'>FortiOS</option>
              <option value='Linux'>Linux</option>
              <option value='Windows'>Windows</option>
              <option value='Android'>Android</option>
              <option value='MacOS'>MacOS</option>
              <option value='Embedded'>Embedded / RTOS</option>
            </select>
          </div>
        </div>
        <div class='input-group'><label>Modelo / Comentarios</label><input type='text' id='insModel' oninput='updateNodeProp("model", this.value)'></div>
      </div>
      <div id='groupEdgeProps' style='display:none'>
        <div style='display:grid;grid-template-columns:1fr 1fr;gap:8px'>
          <div class='input-group'><label>Puerto Origen</label><input type='text' id='insSourceP' oninput='updateNodeProp("sourcePort", this.value)'></div>
          <div class='input-group'><label>Puerto Destino</label><input type='text' id='insTargetP' oninput='updateNodeProp("targetPort", this.value)'></div>
        </div>
      </div>
      <div id='groupNodeTools' style='display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:10px'>
        <button class='btn btn-sm btn-outline' onclick='topoPing()'>📡 Ping</button>
        <button class='btn btn-sm btn-outline' onclick='topoScan()'>🔍 Scan</button>
      </div>
    </div>
  `;

  initCytoscape(data);
}

// ─── TOPOLOGY DEVICE ICONS (SVG inline data URIs) ────────────

function _ico(s) { return "data:image/svg+xml," + encodeURIComponent('<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">' + s + '</svg>'); }

const TOPO_ICONS = {
  router: _ico('<rect x="25" y="35" width="70" height="55" rx="8" fill="none" stroke="white" stroke-width="3"/><rect x="30" y="42" width="60" height="14" rx="3" fill="rgba(255,255,255,.12)"/><circle cx="38" cy="49" r="3" fill="#22c55e"/><circle cx="50" cy="49" r="3" fill="#22c55e"/><circle cx="62" cy="49" r="3" fill="#f59e0b"/><rect x="30" y="60" width="60" height="18" rx="3" fill="none" stroke="rgba(255,255,255,.25)" stroke-width="2"/><rect x="36" y="63" width="10" height="12" rx="2" fill="rgba(255,255,255,.15)"/><rect x="50" y="63" width="10" height="12" rx="2" fill="rgba(255,255,255,.15)"/><rect x="64" y="63" width="10" height="12" rx="2" fill="rgba(255,255,255,.15)"/><rect x="78" y="63" width="10" height="12" rx="2" fill="rgba(255,255,255,.15)"/><line x1="60" y1="20" x2="60" y2="35" stroke="white" stroke-width="3"/><line x1="45" y1="12" x2="45" y2="28" stroke="white" stroke-width="2.5"/><line x1="75" y1="12" x2="75" y2="28" stroke="white" stroke-width="2.5"/><circle cx="60" cy="18" r="5" fill="#ef4444"/>'),
  switch: _ico('<rect x="10" y="32" width="100" height="56" rx="6" fill="none" stroke="white" stroke-width="3"/><rect x="14" y="38" width="92" height="16" rx="3" fill="rgba(255,255,255,.1)"/><circle cx="24" cy="46" r="3" fill="#22c55e"/><circle cx="36" cy="46" r="3" fill="#22c55e"/><circle cx="48" cy="46" r="3" fill="#22c55e"/><circle cx="60" cy="46" r="3" fill="#22c55e"/><circle cx="72" cy="46" r="3" fill="#f59e0b"/><circle cx="84" cy="46" r="3" fill="#22c55e"/><rect x="14" y="58" width="92" height="22" rx="3" fill="none" stroke="rgba(255,255,255,.2)" stroke-width="2"/><rect x="18" y="61" width="10" height="16" rx="2" fill="rgba(255,255,255,.12)"/><rect x="32" y="61" width="10" height="16" rx="2" fill="rgba(255,255,255,.12)"/><rect x="46" y="61" width="10" height="16" rx="2" fill="rgba(255,255,255,.12)"/><rect x="60" y="61" width="10" height="16" rx="2" fill="rgba(255,255,255,.12)"/><rect x="74" y="61" width="10" height="16" rx="2" fill="rgba(255,255,255,.12)"/><rect x="88" y="61" width="10" height="16" rx="2" fill="rgba(255,255,255,.12)"/>'),
  firewall: _ico('<rect x="20" y="30" width="80" height="60" rx="10" fill="none" stroke="white" stroke-width="3"/><rect x="26" y="38" width="68" height="14" rx="4" fill="rgba(255,255,255,.1)"/><text x="60" y="49" font-size="11" font-weight="bold" fill="white" text-anchor="middle">FW</text><path d="M60 56 L48 65 L54 80 L66 80 L72 65 Z" fill="none" stroke="white" stroke-width="2.5" opacity=".7"/><line x1="60" y1="60" x2="60" y2="74" stroke="#22c55e" stroke-width="3.5" stroke-linecap="round"/><line x1="54" y1="67" x2="66" y2="67" stroke="#22c55e" stroke-width="3.5" stroke-linecap="round"/><rect x="48" y="92" width="24" height="6" rx="2" fill="rgba(255,255,255,.15)"/>'),
  server: _ico('<rect x="30" y="10" width="60" height="100" rx="5" fill="none" stroke="white" stroke-width="3"/><rect x="38" y="18" width="36" height="10" rx="3" fill="rgba(255,255,255,.12)"/><circle cx="64" cy="23" r="3" fill="#22c55e"/><rect x="34" y="34" width="44" height="10" rx="3" fill="rgba(255,255,255,.12)"/><rect x="34" y="48" width="44" height="10" rx="3" fill="rgba(255,255,255,.12)"/><rect x="34" y="62" width="44" height="10" rx="3" fill="rgba(255,255,255,.12)"/><rect x="34" y="76" width="44" height="10" rx="3" fill="rgba(255,255,255,.12)"/><rect x="42" y="90" width="36" height="14" rx="3" fill="rgba(255,255,255,.06)"/><line x1="48" y1="97" x2="72" y2="97" stroke="rgba(255,255,255,.3)" stroke-width="2"/>'),
  pc: _ico('<rect x="22" y="14" width="76" height="54" rx="5" fill="none" stroke="white" stroke-width="3"/><rect x="28" y="20" width="64" height="28" rx="3" fill="rgba(255,255,255,.08)"/><rect x="28" y="52" width="64" height="12" rx="2" fill="rgba(255,255,255,.1)"/><rect x="45" y="68" width="30" height="8" rx="2" fill="rgba(255,255,255,.1)"/><rect x="50" y="76" width="20" height="22" rx="3" fill="none" stroke="white" stroke-width="3"/><rect x="48" y="98" width="24" height="6" rx="2" fill="rgba(255,255,255,.15)"/>'),
  ap: _ico('<rect x="32" y="36" width="56" height="48" rx="10" fill="none" stroke="white" stroke-width="3"/><rect x="38" y="42" width="44" height="14" rx="4" fill="rgba(255,255,255,.1)"/><circle cx="60" cy="64" r="8" fill="none" stroke="white" stroke-width="2.5"/><circle cx="60" cy="64" r="3" fill="white"/><path d="M26 28 Q60 10 94 28" fill="none" stroke="white" stroke-width="2.5" opacity=".4"/><path d="M18 18 Q60 0 102 18" fill="none" stroke="white" stroke-width="2" opacity=".25"/><rect x="46" y="88" width="28" height="8" rx="3" fill="rgba(255,255,255,.12)"/><rect x="40" y="96" width="40" height="5" rx="2" fill="rgba(255,255,255,.08)"/>'),
  camera: _ico('<rect x="15" y="32" width="90" height="50" rx="12" fill="none" stroke="white" stroke-width="3"/><rect x="22" y="38" width="76" height="38" rx="8" fill="rgba(255,255,255,.08)"/><circle cx="60" cy="57" r="16" fill="none" stroke="white" stroke-width="3"/><circle cx="60" cy="57" r="7" fill="white" opacity=".5"/><circle cx="60" cy="57" r="3" fill="white"/><rect x="52" y="82" width="16" height="10" rx="2" fill="rgba(255,255,255,.12)"/><rect x="46" y="92" width="28" height="6" rx="2" fill="rgba(255,255,255,.08)"/>'),
  nvr: _ico('<rect x="18" y="14" width="84" height="72" rx="6" fill="none" stroke="white" stroke-width="3"/><rect x="24" y="22" width="34" height="18" rx="3" fill="rgba(255,255,255,.1)"/><circle cx="30" cy="31" r="2.5" fill="#22c55e"/><rect x="64" y="22" width="32" height="18" rx="3" fill="rgba(255,255,255,.1)"/><circle cx="70" cy="31" r="2.5" fill="#22c55e"/><rect x="24" y="44" width="34" height="18" rx="3" fill="rgba(255,255,255,.1)"/><rect x="64" y="44" width="32" height="18" rx="3" fill="rgba(255,255,255,.1)"/><rect x="24" y="66" width="72" height="14" rx="3" fill="rgba(255,255,255,.05)"/><line x1="30" y1="73" x2="90" y2="73" stroke="rgba(255,255,255,.2)" stroke-width="2"/><rect x="38" y="86" width="44" height="12" rx="2" fill="rgba(255,255,255,.1)"/>'),
  dvr: _ico('<rect x="18" y="20" width="84" height="64" rx="6" fill="none" stroke="white" stroke-width="3"/><rect x="24" y="28" width="72" height="14" rx="3" fill="rgba(255,255,255,.1)"/><circle cx="34" cy="35" r="2.5" fill="#22c55e"/><circle cx="44" cy="35" r="2.5" fill="#f59e0b"/><rect x="24" y="46" width="72" height="14" rx="3" fill="rgba(255,255,255,.1)"/><rect x="24" y="64" width="72" height="14" rx="3" fill="rgba(255,255,255,.05)"/><line x1="30" y1="71" x2="90" y2="71" stroke="rgba(255,255,255,.15)" stroke-width="2"/><rect x="38" y="84" width="44" height="16" rx="2" fill="rgba(255,255,255:.1)"/>'),
  cloud: _ico('<path d="M78 48 Q84 28 66 22 Q54 18 44 24 Q34 20 24 28 Q14 26 10 42 Q6 50 10 64 Q14 72 24 72 L88 72 Q100 72 102 58 Q105 44 92 40 Q84 36 78 48 Z" fill="rgba(255,255,255,.06)" stroke="white" stroke-width="3"/><line x1="60" y1="72" x2="60" y2="90" stroke="white" stroke-width="3" opacity=".6"/><path d="M44 86 Q60 96 76 86" fill="none" stroke="white" stroke-width="2.5" opacity=".4"/>'),
  unknown: _ico('<rect x="30" y="25" width="60" height="60" rx="10" fill="none" stroke="white" stroke-width="3.5"/><circle cx="60" cy="48" r="10" fill="none" stroke="white" stroke-width="3"/><path d="M60 56 L60 72" stroke="white" stroke-width="3.5" stroke-linecap="round"/><line x1="48" y1="84" x2="72" y2="84" stroke="white" stroke-width="3.5" stroke-linecap="round"/>'),
  generic: _ico('<rect x="30" y="25" width="60" height="60" rx="10" fill="none" stroke="white" stroke-width="3.5"/><circle cx="60" cy="48" r="10" fill="none" stroke="white" stroke-width="3"/><path d="M60 56 L60 72" stroke="white" stroke-width="3.5" stroke-linecap="round"/><line x1="48" y1="84" x2="72" y2="84" stroke="white" stroke-width="3.5" stroke-linecap="round"/>'),
};

function _topoIcon(type) { return TOPO_ICONS[type] || TOPO_ICONS['generic'] || ''; }

function initCytoscape(data) {
  const cy = cytoscape({
    container: document.getElementById('topologyCanvas'),
    elements: data.elements || (data.nodes ? data : []),
    style: [
      {
        selector: 'node:not([type="area"])',
        style: {
          'background-color': ele => {
             const status = ele.data('status');
             if(status === 'online') return '#22c55e';
             if(status === 'offline') return '#ef4444';
             return '#1e293b';
          },
          'label': 'data(label)',
          'color': '#fff',
          'text-valign': 'bottom',
          'text-margin-y': 8,
          'font-size': '11px',
          'font-weight': 'bold',
          'width': 58,
          'height': 58,
          'shape': 'ellipse',
          'background-image': ele => _topoIcon(ele.data('type')),
          'background-fit': 'contain',
          'background-image-opacity': 1,
          'background-width': '75%',
          'background-height': '75%',
          'border-width': 2,
          'border-color': ele => {
            const v = (ele.data('vendor') || '').toLowerCase();
            if(v.includes('cisco')) return '#00bcd4';
            if(v.includes('mikrotik')) return '#ff5722';
            if(v.includes('fortinet')) return '#8bc34a';
            if(v.includes('ubiquiti')) return '#ff9800';
            if(v.includes('huawei')) return '#e91e63';
            if(v.includes('hikvision')) return '#2196f3';
            if(v.includes('dahua')) return '#9c27b0';
            return '#334155';
          },
        }
      },
      {
        selector: 'node[type="area"]',
        style: {
          'shape': 'round-rectangle',
          'background-opacity': 0.08,
          'background-color': '#818cf8',
          'border-width': 2,
          'border-style': 'dashed',
          'border-color': '#818cf8',
          'label': 'data(label)',
          'text-valign': 'top',
          'text-halign': 'center',
          'background-image': 'none',
          'width': 'auto',
          'height': 'auto',
          'font-size': '14px',
          'font-weight': 'bold',
          'color': '#818cf8',
          'padding': '20px',
        }
      },
      {
        selector: 'edge.sim-path',
        style: {
          'width': 6,
          'line-color': '#f59e0b',
          'opacity': 1,
          'z-index': 1000
        }
      },
      {
        selector: 'node.selected-sim',
        style: {
          'background-color': '#f59e0b',
          'border-width': 4,
          'border-color': '#fff'
        }
      },
      {
        selector: 'node:selected',
        style: {
          'border-width': 3,
          'border-color': '#fff',
          'background-color': '#818cf8'
        }
      },
      {
        selector: 'edge',
        style: {
          'width': ele => {
             const type = ele.data('type');
             if(type === 'fiber') return 4;
             if(type === 'ethernet') return 3;
             return 2;
          },
          'line-color': ele => {
             const type = ele.data('type');
             if(type === 'fiber') return '#f97316';
             if(type === 'wireless') return '#10b981';
             if(type === 'ethernet') return '#4a5568';
             return '#334155';
          },
          'line-style': ele => ele.data('type') === 'wireless' ? 'dotted' : 'solid',
          'curve-style': 'bezier',
          'target-arrow-shape': 'triangle-backcurve',
          'target-arrow-color': ele => {
             const type = ele.data('type');
             if(type === 'fiber') return '#f97316';
             if(type === 'wireless') return '#10b981';
             return '#4a5568';
          },
          'label': ele => {
             const s = ele.data('sourcePort') || '';
             const t = ele.data('targetPort') || '';
             const label = ele.data('label') || '';
             if (label) return label;
             if (s && t) return s + ' ↔ ' + t;
             return s || t || '';
          },
          'font-size': '9px',
          'color': '#94a3b8',
          'font-weight': 'bold',
          'text-background-opacity': 1,
          'text-background-color': '#0a0c12',
          'text-background-padding': '3px',
          'text-background-shape': 'round-rectangle',
          'text-rotation': 'autorotate',
          'edge-distances': 'node-position',
        }
      },
      {
        selector: '.packet',
        style: {
          'width': 16,
          'height': 16,
          'background-color': '#f59e0b',
          'shape': 'rectangle',
          'z-index': 999
        }
      }
    ],
    layout: {
      name: (data.elements || data.nodes || []).length > 10 ? 'concentric' : 'breadthfirst',
      concentric: function(node) {
        if (node.data('type') === 'cloud') return 0;
        if (node.data('type') === 'router') return 1;
        if (node.data('type') === 'firewall') return 2;
        if (node.data('type') === 'switch') return 3;
        return 4;
      },
      levelWidth: function(nodes) { return 2; },
      spacingFactor: 1.5,
      directed: true,
      nodeDimensionsIncludeLabels: true,
    },
    userZoomingEnabled: true,
    userPanningEnabled: true,
    boxSelectionEnabled: true,
    selectionType: 'single',
    touchTapThreshold: 8,
    desktopTapThreshold: 4,
    autoungrabify: false
  });

  currentCy = cy;

  currentCy.on('select', 'node', function(e) {
    selectedNode = e.target;
    showInspector(selectedNode.data());
  });

  currentCy.on('select', 'edge', function(e) {
    selectedNode = e.target;
    showEdgeInspector(selectedNode.data());
  });

  currentCy.on('unselect', function() {
    selectedNode = null;
    document.getElementById("nodeInspector").style.display = "none";
  });

  // Packet Tracer-style: double-click opens device console
  currentCy.on('tap', 'node', function(e) {
    // single tap handled below for connection/simulation mode
  });

  currentCy.on('dblclick', 'node', function(e) {
    const node = e.target;
    const d = node.data();
    if (d.type === 'area') return;
    openDeviceConsole(d);
  });

  // Handle connection mode
  currentCy.on('tap', 'node', function(e) {
    const targetNode = e.target;
    
    // MODO SIMULACIÓN
    if (window._simMode) {
      if (!window._simSource) {
        window._simSource = targetNode;
        targetNode.addClass('selected-sim');
        showToast("Origen seleccionado: " + targetNode.data('label'), "success");
        updateSimLog("Origen: " + targetNode.data('label'));
      } else if (!window._simTarget) {
        window._simTarget = targetNode;
        updateSimLog("Destino: " + targetNode.data('label'));
        runSimulation(window._simSource, window._simTarget);
      }
      return;
    }

    if (window._connectMode && window._sourceNode) {
      currentCy.add({
        group: 'edges',
        data: { 
          source: window._sourceNode.id(), 
          target: targetNode.id(),
          type: window._connectType || 'ethernet'
        }
      });
      toggleConnectMode(null);
    }
  });
}

function addNode(type) {
  const id = "n" + Date.now();
  // Random offset to avoid perfect overlapping
  const offset = (Math.random() - 0.5) * 60;
  currentCy.add({
    group: 'nodes',
    data: { id, type, label: type.toUpperCase(), ip: '', vendor: '', os: '', model: '' },
    position: { 
      x: (currentCy.width() / 2) + offset, 
      y: (currentCy.height() / 2) + offset 
    }
  });
}

function toggleConnectMode(type = null) {
  if (type === null) {
    window._connectMode = false;
    window._sourceNode = null;
    window._connectType = null;
    return;
  }
  
  window._connectMode = true;
  window._connectType = type;
  
  if (selectedNode) {
    window._sourceNode = selectedNode;
    showToast(`Conectando vía ${type}... Seleccioná destino`, "info");
  } else {
    showToast("Seleccioná primero un dispositivo origen", "error");
    window._connectMode = false;
  }
}

function showEdgeInspector(data) {
  const ins = document.getElementById("nodeInspector");
  ins.style.display = "block";
  document.getElementById("insTitle").textContent = "CONEXIÓN: " + (data.type || "ethernet").toUpperCase();
  
  document.getElementById("groupNodeProps").style.display = "none";
  document.getElementById("groupNodeTools").style.display = "none";
  document.getElementById("btnAutoDetect").style.display = "none";
  document.getElementById("groupEdgeProps").style.display = "block";
  
  document.getElementById("insSourceP").value = data.sourcePort || "";
  document.getElementById("insTargetP").value = data.targetPort || "";
}

function showInspector(data) {
  const ins = document.getElementById("nodeInspector");
  ins.style.display = "block";
  
  document.getElementById("groupNodeProps").style.display = "block";
  document.getElementById("groupNodeTools").style.display = "grid";
  document.getElementById("btnAutoDetect").style.display = "block";
  document.getElementById("groupEdgeProps").style.display = "none";

  document.getElementById("insTitle").textContent = data.type.toUpperCase();
  document.getElementById("insLabel").value = data.label || "";
  document.getElementById("insIP").value = data.ip || "";
  document.getElementById("insVendor").value = data.vendor || "";
  document.getElementById("insOS").value = data.os || "";
  document.getElementById("insModel").value = data.model || "";
}

async function autoDetectNode() {
  const ip = document.getElementById("insIP").value;
  if (!ip) return showToast("Configurá una IP para detectar", "error");
  
  showToast("Detectando dispositivo...", "info");
  try {
    const r = await (await fetch(`/api/scanner/ping?host=${ip}`)).json();
    if (r.os) {
      document.getElementById("insOS").value = r.os;
      updateNodeProp("os", r.os);
      showToast("S.O. detectado: " + r.os);
    }
    // Also try to identify CCTV/Vendor if ports are open
    const cctv = await (await fetch(`/api/scanner/scan-cctv?host=${ip}`)).json();
    if (cctv.device_identity) {
      const vendor = Object.values(cctv.device_identity)[0];
      if (vendor) {
        document.getElementById("insVendor").value = vendor;
        updateNodeProp("vendor", vendor);
        showToast("Fabricante detectado: " + vendor);
      }
    }
  } catch(e) {
    showToast("Error en detección automática", "error");
  }
}

function updateNodeProp(prop, val) {
  if (selectedNode) {
    selectedNode.data(prop, val);
  }
}

function deleteSelected() {
  if (selectedNode) {
    selectedNode.remove();
    selectedNode = null;
    document.getElementById("nodeInspector").style.display = "none";
  }
}

async function saveTopologyData() {
  const data = {
    id: currentTopologyId,
    name: document.getElementById("topoName").textContent,
    elements: currentCy.json().elements
  };
  const resp = await fetch("/api/topology", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  const saved = await resp.json();
  currentTopologyId = saved.id;
  showToast("Topología guardada");
}

function autoDiscoverForm() {
  showModal(`
    <button class='modal-close' onclick='closeModal()'>&times;</button>
    <h2>📡 Auto-Descubrir Topología</h2>
    <p class='text-sm text-muted mb-8'>Descubre dispositivos vía SNMP (ARP + LLDP) a partir de una IP semilla</p>
    <div class='input-group'><label>IP Semilla</label><input type='text' id='auto_seed' placeholder='192.168.1.1' value='${escapeHtml(document.getElementById("scan_host")?.value || "")}'></div>
    <div class='input-group'><label>Community SNMP</label><input type='text' id='auto_comm' value='public'></div>
    <div style='display:flex;gap:6px'>
      <div class='input-group' style='flex:1'><label>Profundidad</label><input type='number' id='auto_depth' value='2' min='1' max='5'></div>
    </div>
    <button class='btn' onclick='runAutoDiscover()' style='margin-top:8px'>🔍 Descubrir</button>
    <div id='autoDiscoverResult' class='text-sm text-muted' style='margin-top:8px'></div>
  `);
}

async function runAutoDiscover() {
  const seed = document.getElementById("auto_seed").value.trim();
  const community = document.getElementById("auto_comm").value.trim() || "public";
  const depth = parseInt(document.getElementById("auto_depth").value) || 2;
  const el = document.getElementById("autoDiscoverResult");
  if (!seed) { el.innerHTML = "<span style='color:var(--danger)'>IP semilla requerida</span>"; return; }
  el.innerHTML = "<span class='text-muted'>Descubriendo red (SNMP + TCP scan)...</span>";
  try {
    const r = await (await fetch("/api/topology/discover", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({seed, community, depth, async: true})
    })).json();
    if (r.task_id) {
      el.innerHTML = "<span class='text-muted'>Escaneando red... <span id='topoPollDot'>.</span></span>";
      // Poll
      const poll = setInterval(async () => {
        try {
          const t = await (await fetch("/api/task/" + r.task_id)).json();
          if (t.status === "running") {
            const dots = document.getElementById("topoPollDot");
            if (dots) dots.textContent = dots.textContent.length < 4 ? dots.textContent + "." : ".";
            return;
          }
          clearInterval(poll);
          if (t.error) { el.innerHTML = `<span style='color:var(--danger)'>${escapeHtml(t.error)}</span>`; return; }
          const data = t.result || {};
          if (!data.devices || data.devices.length === 0) { el.innerHTML = "<span class='text-muted'>No se encontraron dispositivos</span>"; return; }
          el.innerHTML = `<span style='color:var(--success)'>✅ ${data.count} dispositivos encontrados</span>`;
          closeModal();
          newTopologyWithData(data);
        } catch(e) { clearInterval(poll); el.innerHTML = `<span style='color:var(--danger)'>Error: ${escapeHtml(e.message)}</span>`; }
      }, 1500);
      return;
    }
    if (r.error) { el.innerHTML = `<span style='color:var(--danger)'>${escapeHtml(r.error)}</span>`; return; }
    if (!r.devices || r.devices.length === 0) { el.innerHTML = "<span class='text-muted'>No se encontraron dispositivos</span>"; return; }
    el.innerHTML = `<span style='color:var(--success)'>✅ ${r.count} dispositivos encontrados</span>`;
    closeModal();
    newTopologyWithData(r);
  } catch(e) { el.innerHTML = `<span style='color:var(--danger)'>Error: ${escapeHtml(e.message)}</span>`; }
}

function newTopologyWithData(data) {
  const name = prompt("Nombre de la topología:") || "Auto-descubierta";
  currentTopologyId = null;
  let cyData = { name, nodes: [], edges: [] };
  (data.devices || []).forEach(d => {
    cyData.nodes.push({
      data: {
        id: d.id,
        label: d.label || d.ip,
        type: d.type || "unknown",
        ip: d.ip,
        vendor: d.vendor || "",
      }
    });
  });
  (data.edges || []).forEach(e => {
    if (cyData.nodes.find(n => n.data.id === e.source) && cyData.nodes.find(n => n.data.id === e.target)) {
      cyData.edges.push({
        data: {
          id: e.source + "-" + e.target,
          source: e.source,
          target: e.target,
          label: e.label || "link",
          type: e.type || "ethernet",
        }
      });
    }
  });
  openTopology(null, name, cyData);
}

// ─── ZENMAP-STYLE: scan subnet + populate topology ─────────

async function scanSubnetToTopology() {
  const sub = document.getElementById("scan_subnet")?.value || prompt("Subred (ej: 192.168.1.0/24):");
  if (!sub) return;
  const el = document.getElementById("topologyList") || document.getElementById("results");
  el.innerHTML = "<span class='text-muted'>Escaneando subred...</span>";

  try {
    const hosts = await (await fetch(`/api/scanner/discover?subnet=${encodeURIComponent(sub)}`)).json();
    if (!hosts.hosts || hosts.hosts.length === 0) {
      el.innerHTML = "<span class='text-muted'>No se encontraron hosts</span>";
      showModal(`<button class='modal-close' onclick='closeModal()'>&times;</button><h2>📡 Escaneo de Subred</h2><p class='text-muted'>No se encontraron hosts en ${escapeHtml(sub)}</p>`);
      return;
    }

    // Open modal with scan results as topology preview
    let html = `<button class='modal-close' onclick='closeModal()'>&times;</button>
      <h2>📡 Topología ${escapeHtml(sub)}</h2>
      <p class='text-sm text-muted mb-8'>${hosts.hosts.length} hosts encontrados. Creando topología...</p>
      <div class='result-box' style='max-height:300px;overflow-y:auto'>`;

    const nodes = [];
    const edges = [];
    const subnetLabel = sub.replace("/24", "").slice(0, -1) + "0";
    const areaId = "area_" + Date.now();
    nodes.push({data: {id: areaId, label: sub, type: "area"}});

    hosts.hosts.forEach((h, i) => {
      const ip = h.host || h.ip || h;
      const nodeId = "host_" + i;
      let type = "pc";
      const openPorts = h.open_ports || h.ports || [];
      const os = h.os || "";
      if (openPorts.some(p => [80,443,8080,8443].includes(p.port || p))) type = "server";
      if (openPorts.some(p => [23,22].includes(p.port || p))) type = "router";
      if (openPorts.some(p => [554,8000,37777].includes(p.port || p))) type = "camera";
      if (openPorts.some(p => [161,162].includes(p.port || p))) type = "switch";

      const portsInfo = openPorts.slice(0, 5).map(p => (p.port || p)).join(",");
      const label = os ? `${ip}\n${os}` : ip;
      nodes.push({
        data: {
          id: nodeId, label: ip, type, ip,
          os: os || "",
          ports: portsInfo,
          vendor: "",
          parent: areaId,
        }
      });
      // Connect to area
      if (i > 0) {
        edges.push({data: {id: `link_${i}`, source: areaId, target: nodeId}});
      }
    });

    hosts.hosts.slice(0, 30).forEach(h => {
      const ip = h.host || h.ip || h;
      const os = h.os || "";
      html += `<div class='cmd-item'><span class='text-xs'>${escapeHtml(ip)}${os ? " · " + escapeHtml(os) : ""}</span></div>`;
    });
    html += `</div>
      <button class='btn' style='margin-top:10px' onclick='closeModal();createTopologyFromScan(${JSON.stringify(hosts.hosts).replace(/"/g, "&quot;")},"${escapeHtml(sub)}")'>➕ Crear Topología</button>`;
    showModal(html);
  } catch(e) {
    el.innerHTML = `<span style='color:var(--danger)'>Error: ${escapeHtml(e.message)}</span>`;
  }
}

function createTopologyFromScan(hosts, subnet) {
  const name = prompt("Nombre de la topología:", `Subred ${subnet}`);
  if (!name) return;
  const nodes = [];
  const edges = [];
  const areaId = "area_" + Date.now();
  nodes.push({data: {id: areaId, label: subnet, type: "area"}});

  hosts.forEach((h, i) => {
    const ip = h.host || h.ip || h;
    const nodeId = "host_" + i;
    let type = "pc";
    const openPorts = h.open_ports || h.ports || [];
    const os = h.os || "";
    if (openPorts.some(p => [80,443,8080,8443].includes(p.port || p))) type = "server";
    if (openPorts.some(p => [23,22].includes(p.port || p))) type = "router";
    if (openPorts.some(p => [554,8000,37777].includes(p.port || p))) type = "camera";
    if (openPorts.some(p => [161,162].includes(p.port || p))) type = "switch";
    const portsInfo = openPorts.slice(0, 5).map(p => (p.port || p)).join(", ");
    nodes.push({
      data: {
        id: nodeId, label: ip, type, ip,
        os: os || "",
        ports: portsInfo,
        vendor: "",
        parent: areaId,
      }
    });
  });
  openTopology(null, name, {
    name, nodes, edges,
    elements: [...nodes.map(n => ({group: "nodes", ...n})), ...edges.map(e => ({group: "edges", ...e}))]
  });
}

// ─── PACKET TRACER-STYLE DEVICE CONSOLE ────────────────────

function openDeviceConsole(data) {
  const typeIcons = {router:"🖧",switch:"☲",firewall:"🛡️",server:"🖳",pc:"💻",ap:"📡",camera:"📷",nvr:"📼",dvr:"📼",cloud:"☁️"};
  const icon = typeIcons[data.type] || "🖥️";
  showModal(`
    <button class='modal-close' onclick='closeModal()'>&times;</button>
    <div style='display:flex;align-items:center;gap:8px;margin-bottom:12px'>
      <span style='font-size:28px'>${icon}</span>
      <div>
        <h2 style='margin:0'>${escapeHtml(data.label || data.id)}</h2>
        <div class='text-xs text-muted'>${escapeHtml(data.type)} ${data.ip ? "· " + escapeHtml(data.ip) : ""} ${data.vendor ? "· " + escapeHtml(data.vendor) : ""}</div>
      </div>
    </div>
    <div style='display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px'>
      ${data.os ? `<div class='section'><div class='section-header'>💿 SO</div><div class='section-body text-sm'>${escapeHtml(data.os)}</div></div>` : ""}
      ${data.ports ? `<div class='section'><div class='section-header'>🔌 Puertos</div><div class='section-body text-sm'>${escapeHtml(data.ports)}</div></div>` : ""}
      ${data.vendor ? `<div class='section'><div class='section-header'>🏭 Fabricante</div><div class='section-body text-sm'>${escapeHtml(data.vendor)}</div></div>` : ""}
      ${data.model ? `<div class='section'><div class='section-header'>📋 Modelo</div><div class='section-body text-sm'>${escapeHtml(data.model)}</div></div>` : ""}
    </div>
    <div class='section'>
      <div class='section-header'>🖥️ Consola (simulada)</div>
      <div class='section-body'>
        <div id='deviceConsole' style='background:#000;padding:8px;border-radius:4px;font-family:monospace;font-size:11px;min-height:80px;max-height:150px;overflow-y:auto;color:#0f0'>
          > ${escapeHtml(data.label || data.id)}# <span class='text-muted' style='color:#555'>Sistema iniciado. ${data.os ? "SO: " + escapeHtml(data.os) : "Sin SO detectado"}</span>
          <br>> ${data.ip ? "IP: " + escapeHtml(data.ip) : "Sin IP configurada"}
          <br>> ${data.vendor ? "Vendor: " + escapeHtml(data.vendor) : "Vendor genérico"}
          <br>> <span style='color:var(--accent)'>show interfaces</span>
          <br>> ${data.type === "router" ? "GigabitEthernet0/0: up, IP: " + escapeHtml(data.ip || "N/A") : ""}
          ${data.type === "switch" ? "FastEthernet0/1-24: up" : ""}
          ${data.type === "camera" ? "Video stream: active, codec: H.265" : ""}
          ${data.type === "server" ? "Servicios: HTTP" + (data.ports?.includes("443") ? "S" : "") + ", SSH" : ""}
          ${data.type === "firewall" ? "Políticas activas: 12, Conexiones: 145" : ""}
          <br>> <span style='color:#555'>--- Sesión interactiva simulada ---</span>
        </div>
        <div style='display:flex;gap:4px;margin-top:6px'>
          <button class='btn btn-xs btn-outline' onclick='topoPingFromConsole("${escapeHtml(data.ip || data.id)}")'>📡 Ping</button>
          <button class='btn btn-xs btn-outline' onclick='topoScanFromConsole("${escapeHtml(data.ip || data.id)}")'>🔍 Quick Scan</button>
          <button class='btn btn-xs btn-outline' onclick='topoTelnetConsole("${escapeHtml(data.ip || data.id)}")'>💻 Telnet</button>
          <button class='btn btn-xs' onclick="document.getElementById('deviceConsole').innerHTML+='<br>> <span style=\\'color:#555\\'>Comando no disponible en modo simulación</span>'">⏎ Enter</button>
        </div>
      </div>
    </div>
  `);
}

async function topoPingFromConsole(host) {
  const console = document.getElementById("deviceConsole");
  if (!console) return;
  console.innerHTML += `<br>> ping ${escapeHtml(host)} <span class='text-muted' style='color:#555'>... consultando</span>`;
  try {
    const r = await (await fetch(`/api/scanner/ping?host=${encodeURIComponent(host)}&async=false`)).json();
    if (r.alive || r.reachable) {
      console.innerHTML += `<br>> <span style='color:var(--success)'>✅ Respuesta de ${escapeHtml(host)} (${r.latency_ms || "?"} ms)</span>`;
    } else {
      console.innerHTML += `<br>> <span style='color:var(--danger)'>❌ Sin respuesta de ${escapeHtml(host)}</span>`;
    }
  } catch(e) {
    console.innerHTML += `<br>> <span style='color:var(--danger)'>Error: ${escapeHtml(e.message)}</span>`;
  }
  console.scrollTop = console.scrollHeight;
}

async function topoScanFromConsole(host) {
  const console = document.getElementById("deviceConsole");
  if (!console) return;
  console.innerHTML += `<br>> nmap -F ${escapeHtml(host)} <span style='color:#555'>escaneando...</span>`;
  try {
    const r = await (await fetch(`/api/scanner/quick-scan?host=${encodeURIComponent(host)}&async=false`)).json();
    const ports = r.ports || r.results || [];
    if (ports.length) {
      console.innerHTML += `<br>> <span style='color:var(--success)'>✅ ${ports.length} puertos abiertos:</span>`;
      ports.slice(0, 10).forEach(p => {
        console.innerHTML += `<br>>   ${p.port || p}/${p.protocol || "tcp"}  ${escapeHtml(p.service || p.name || "")}`;
      });
    } else {
      console.innerHTML += `<br>> <span class='text-muted'>Sin puertos abiertos</span>`;
    }
  } catch(e) {
    console.innerHTML += `<br>> <span style='color:var(--danger)'>Error: ${escapeHtml(e.message)}</span>`;
  }
  console.scrollTop = console.scrollHeight;
}

function topoTelnetConsole(host) {
  const console = document.getElementById("deviceConsole");
  if (!console) return;
  console.innerHTML += `<br>> telnet ${escapeHtml(host)}<br>> <span style='color:var(--accent)'>Conectando a ${escapeHtml(host)}:23...</span>`;
  setTimeout(() => {
    console.innerHTML += `<br>> <span style='color:var(--warning)'>⚠️ Telnet no soportado en web. Usá: telnet ${escapeHtml(host)} desde tu terminal</span>`;
    console.scrollTop = console.scrollHeight;
  }, 500);
}


function switchMode(mode) {
  const isSim = mode === 'simulation';
  window._simMode = isSim;
  
  document.getElementById('btnRealTime').style.background = isSim ? 'var(--surface3)' : 'var(--accent)';
  document.getElementById('btnRealTime').style.color = isSim ? 'var(--text)' : '#000';
  document.getElementById('btnSimulation').style.background = isSim ? 'var(--success)' : 'var(--surface3)';
  document.getElementById('btnSimulation').style.color = isSim ? '#000' : 'var(--text)';
  
  document.getElementById('simPanel').style.display = isSim ? 'block' : 'none';
  document.getElementById('nodeInspector').style.display = 'none';
  
  if (isSim) {
    showToast("Modo Simulación: Selecciona origen y destino", "success");
    window._simSource = null;
    window._simTarget = null;
  } else {
    currentCy.elements().removeClass('selected-sim sim-path');
    currentCy.remove('.packet');
  }
}

function clearSims() {
  document.getElementById('simList').innerHTML = "";
  document.getElementById('simLog').innerHTML = "";
  currentCy.remove('.packet');
  currentCy.elements().removeClass('selected-sim sim-path');
}

async function runSimulation(source, target) {
  const id = "sim_" + Date.now();
  const dijkstra = currentCy.elements().dijkstra(source);
  const path = dijkstra.pathTo(target);
  
  if (path.length === 0) {
    updateSimLog(`<span style='color:var(--danger)'>Error: No hay ruta entre ${source.data('label')} y ${target.data('label')}</span>`);
    window._simSource = null; window._simTarget = null;
    return;
  }

  const simItem = document.createElement('div');
  simItem.className = 'card';
  simItem.style.padding = '6px';
  simItem.style.fontSize = '11px';
  simItem.innerHTML = `<span style='color:var(--success)'>●</span> ICMP: ${source.data('label')} → ${target.data('label')}`;
  document.getElementById('simList').prepend(simItem);

  updateSimLog(`Iniciando simulación ${id}...`);
  
  for (let i = 0; i < path.length; i++) {
    const ele = path[i];
    if (ele.isNode()) {
      ele.flashClass('selected-sim', 500);
      updateSimLog(`Recibido por ${ele.data('label')}`);
      await new Promise(r => setTimeout(r, 600));
    } else {
      // Crear paquete visual (PDU)
      const sourcePos = ele.source().position();
      const targetPos = ele.target().position();
      
      const pdu = currentCy.add({
        group: 'nodes',
        classes: 'packet',
        data: { id: 'pdu_'+Date.now() },
        position: { ...sourcePos }
      });
      
      updateSimLog(`Transmitiendo por cable...`);
      pdu.animate({
        position: { ...targetPos },
        duration: 800,
        easing: 'linear'
      });
      
      ele.addClass('sim-path');
      await new Promise(r => setTimeout(r, 850));
      pdu.remove();
      ele.removeClass('sim-path');
    }
  }
  
  updateSimLog(`<span style='color:var(--success)'>Entrega exitosa en ${target.data('label')}</span>`);
  window._simSource = null;
  window._simTarget = null;
  currentCy.nodes().removeClass('selected-sim');
}

async function pollNetworkStatus() {
  const nodes = currentCy.nodes('[type != "area"]');
  showToast("Escaneando estado de la red...", "info");
  
  for (const node of nodes) {
    const ip = node.data('ip');
    if (!ip) continue;
    
    try {
      const r = await (await fetch(`/api/scanner/ping?host=${ip}`)).json();
      node.data('status', r.alive ? 'online' : 'offline');
    } catch(e) {
      node.data('status', 'offline');
    }
  }
  showToast("Estado actualizado", "success");
}

// Integración con herramientas TechBot
function topoPing() {
  const ip = document.getElementById("insIP").value;
  if (!ip) return showToast("Configurá una IP primero", "error");
  openSection("scanner");
  setTimeout(() => {
    document.getElementById("scan_host").value = ip;
    scannerPing();
  }, 300);
}

function topoScan() {
  const ip = document.getElementById("insIP").value;
  if (!ip) return showToast("Configurá una IP primero", "error");
  openSection("scanner");
  setTimeout(() => {
    document.getElementById("scan_host").value = ip;
    scannerQuick();
  }, 300);
}

// ─── IPAM ────────────────────────────────────────────────────

let ipamDb = { networks: [], reservations: [], dhcp_scopes: [], dns_records: [], vlans: [], sites: [] };

async function showIPAM() {
  const stats = await (await fetch("/api/ipam/stats")).json();
  document.getElementById("results").innerHTML = `
    <h3 style='margin-bottom:12px'>🌐 IPAM</h3>
    <div style='display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:12px'>
      <div class='card' style='padding:10px;text-align:center'><div style='font-size:20px;font-weight:700'>${stats.networks}</div><div style='font-size:11px;color:var(--text2)'>Redes</div></div>
      <div class='card' style='padding:10px;text-align:center'><div style='font-size:20px;font-weight:700'>${stats.reservations}</div><div style='font-size:11px;color:var(--text2)'>Reservaciones</div></div>
      <div class='card' style='padding:10px;text-align:center'><div style='font-size:20px;font-weight:700'>${stats.dhcp_scopes}</div><div style='font-size:11px;color:var(--text2)'>DHCP</div></div>
      <div class='card' style='padding:10px;text-align:center'><div style='font-size:20px;font-weight:700'>${stats.vlans}</div><div style='font-size:11px;color:var(--text2)'>VLANs</div></div>
    </div>
    <div class='tabs'>
      <button class='tab active' onclick='ipamNetworks(this)'>🌐 Redes</button>
      <button class='tab' onclick='ipamReservations(this)'>📋 Reservas</button>
      <button class='tab' onclick='ipamDNS(this)'>📇 DNS</button>
      <button class='tab' onclick='ipamVLANs(this)'>🏷 VLANs</button>
      <button class='tab' onclick='ipamAddNetwork(this)'>➕ Agregar</button>
    </div>
    <div id='ipamResult'></div>
  `;
  ipamNetworks(document.querySelector(".tab"));
}

async function ipamNetworks(btn) {
  setActiveTab(btn);
  const nets = await (await fetch("/api/ipam/networks")).json();
  let html = nets.map(n => `
    <div class='card' style='text-align:left;padding:10px 14px;margin-bottom:6px'>
      <div style='font-weight:600'>${n.network}</div>
      <div style='font-size:12px;color:var(--text2)'>${n.description||"Sin descripción"} · ${n.used_hosts}/${n.total_hosts} usado · ${n.status||"active"}</div>
    </div>
  `).join("");
  document.getElementById("ipamResult").innerHTML = html || "<p style='color:var(--text2)'>Sin redes. Agregá una.</p>";
}

async function ipamReservations(btn) {
  setActiveTab(btn);
  const res = await (await fetch("/api/ipam/reservations")).json();
  let html = res.map(r => `
    <div class='cmd-item'><span class='badge badge-accent'>${r.ip}</span> ${r.hostname} ${r.mac ? "· "+r.mac : ""}</div>
  `).join("");
  document.getElementById("ipamResult").innerHTML = html || "<p style='color:var(--text2)'>Sin reservaciones.</p>";
}

async function ipamDNS(btn) {
  setActiveTab(btn);
  const recs = await (await fetch("/api/ipam/dns")).json();
  let html = recs.map(r => `
    <div class='cmd-item'><span class='badge badge-success'>${r.type}</span> ${r.name} → ${r.value} (TTL:${r.ttl})</div>
  `).join("");
  document.getElementById("ipamResult").innerHTML = html || "<p style='color:var(--text2)'>Sin registros DNS.</p>";
}

async function ipamVLANs(btn) {
  setActiveTab(btn);
  const vlans = await (await fetch("/api/ipam/vlans")).json();
  let html = vlans.map(v => `
    <div class='card' style='text-align:left;padding:10px 14px;margin-bottom:6px'>
      <div><span class='badge badge-accent'>VLAN ${v.vlan_id}</span> <strong>${v.name}</strong></div>
      <div style='font-size:12px;color:var(--text2)'>${v.network||""}</div>
    </div>
  `).join("");
  document.getElementById("ipamResult").innerHTML = html || "<p style='color:var(--text2)'>Sin VLANs.</p>";
}

async function ipamAddNetwork(btn) {
  setActiveTab(btn);
  document.getElementById("ipamResult").innerHTML = `
    <div class='section'>
      <div class='section-header'>Agregar Red</div>
      <div class='section-body'>
        <div class='input-group'><label>Red (CIDR)</label><input type='text' id='ipam_net' placeholder='192.168.1.0/24'></div>
        <div class='input-group'><label>Descripción</label><input type='text' id='ipam_desc' placeholder='Oficina central'></div>
        <div class='input-group'><label>Sitio</label><input type='text' id='ipam_site' placeholder='Sede 1'></div>
        <button class='btn' onclick='ipamCreateNetwork()'>✅ Crear Red</button>
        <div id='ipamCreateResult'></div>
      </div>
    </div>
    <div class='section'>
      <div class='section-header'>Agregar Reservación IP</div>
      <div class='section-body'>
        <div class='input-group'><label>IP</label><input type='text' id='ipam_res_ip' placeholder='192.168.1.10'></div>
        <div class='input-group'><label>Hostname</label><input type='text' id='ipam_res_name' placeholder='server-01'></div>
        <div class='input-group'><label>MAC</label><input type='text' id='ipam_res_mac' placeholder='AA:BB:CC:DD:EE:FF'></div>
        <div class='input-group'><label>Descripción</label><input type='text' id='ipam_res_desc' placeholder='Servidor principal'></div>
        <button class='btn btn-outline' onclick='ipamCreateReservation()'>📋 Crear Reservación</button>
        <div id='ipamResResult'></div>
      </div>
    </div>
    <div class='section'>
      <div class='section-header'>Agregar VLAN</div>
      <div class='section-body'>
        <div class='input-group'><label>VLAN ID</label><input type='text' id='ipam_vlan_id' placeholder='10'></div>
        <div class='input-group'><label>Nombre</label><input type='text' id='ipam_vlan_name' placeholder='Ventas'></div>
        <button class='btn btn-outline' onclick='ipamCreateVLAN()'>🏷 Crear VLAN</button>
        <div id='ipamVlanResult'></div>
      </div>
    </div>
  `;
}

async function ipamCreateNetwork() {
  const r=await(await fetch("/api/ipam/networks",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({
    network:document.getElementById("ipam_net").value,description:document.getElementById("ipam_desc").value,site:document.getElementById("ipam_site").value
  })})).json();
  document.getElementById("ipamCreateResult").innerHTML=`<div class='result-box'>${JSON.stringify(r,null,2)}</div>`;
}

async function ipamCreateReservation() {
  const r=await(await fetch("/api/ipam/reservations",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({
    ip:document.getElementById("ipam_res_ip").value,hostname:document.getElementById("ipam_res_name").value,
    mac:document.getElementById("ipam_res_mac").value,description:document.getElementById("ipam_res_desc").value
  })})).json();
  document.getElementById("ipamResResult").innerHTML=`<div class='result-box'>${JSON.stringify(r,null,2)}</div>`;
}

async function ipamCreateVLAN() {
  const r=await(await fetch("/api/ipam/vlans",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({
    vlan_id:parseInt(document.getElementById("ipam_vlan_id").value),name:document.getElementById("ipam_vlan_name").value
  })})).json();
  document.getElementById("ipamVlanResult").innerHTML=`<div class='result-box'>${JSON.stringify(r,null,2)}</div>`;
}

// ─── CONTROL DE ACCESO ───────────────────────────────────────

function showACForm(vendor, btn) {
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  if (btn) btn.classList.add("active");
  document.getElementById("acForm").innerHTML = `
    <div class='section'>
      <div class='section-header'>Conectar a ${vendor.charAt(0).toUpperCase()+vendor.slice(1)}</div>
      <div class='section-body'>
        <div class='input-group'><label>IP del controlador</label><input type='text' id='ac_host' placeholder='192.168.1.100'></div>
        <div class='input-group'><label>Puerto</label><input type='text' id='ac_port' value='80'></div>
        <div class='input-group'><label>Usuario</label><input type='text' id='ac_user' value='admin'></div>
        <div class='input-group'><label>Contraseña</label><input type='password' id='ac_pass'></div>
        <button class='btn' onclick='connectAC("${vendor}")'>🔌 Conectar</button>
      </div>
    </div>
  `;
  document.getElementById("acResult").innerHTML = "";
  window._acSession = null;
}

function connectAC(vendor) {
  const body = {
    vendor,
    host: document.getElementById("ac_host").value,
    port: document.getElementById("ac_port").value || 80,
    user: document.getElementById("ac_user").value || "admin",
    password: document.getElementById("ac_pass").value,
  };
  asyncFetchPost("Conectar AC " + vendor, "/api/access-control/connect", body, "acResult", (data, el, error) => {
    if (error) { el.innerHTML = `<div class='result-box' style='color:var(--danger)'>Error: ${escapeHtml(error)}</div>`; return; }
    if (data.online) {
      window._acSession = data.session;
      el.innerHTML = `
        <div class='section'>
          <div class='section-header' style='color:var(--success)'>✅ ${data.vendor_name} - Conectado</div>
          <div class='section-body'>
            <div style='display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px'>
              <button class='btn btn-outline' style='font-size:13px' onclick='execAC("open_door")'>🚪 Abrir Puerta</button>
              <button class='btn btn-outline' style='font-size:13px' onclick='execAC("close_door")'>🔒 Cerrar Puerta</button>
              <button class='btn btn-outline' style='font-size:13px' onclick='execAC("get_door_status")'>📋 Estado Puerta</button>
              <button class='btn btn-outline' style='font-size:13px' onclick='execAC("list_users")'>👥 Usuarios</button>
              <button class='btn btn-outline' style='font-size:13px' onclick='execAC("get_events")'>📅 Eventos</button>
              <button class='btn btn-outline' style='font-size:13px' onclick='execAC("get_audit_trail")'>📜 Auditoría</button>
              <button class='btn btn-outline' style='font-size:13px;grid-column:span 2' onclick='promptHoldDoor()'>⏱ Mantener Puerta</button>
            </div>
            <div id='acCmdResult' style='margin-top:8px'></div>
          </div>
        </div>
      `;
    } else {
      el.innerHTML = `<div class='result-box' style='color:var(--danger)'>❌ ${data.error || "No se pudo conectar"}</div>`;
    }
  });
}

function execAC(method, extraParams = {}) {
  const params = {};
  if (method === "hold_door") {
    params.door_id = extraParams.door_id || 1;
    params.seconds = extraParams.seconds || 5;
  }
  asyncFetchPost("Ejecutar " + method, "/api/access-control/command", {session: window._acSession, method, params}, "acCmdResult",
    (data, el) => {
      if (!el) return;
      if (data.result) {
        el.innerHTML = `<div class='result-box'>${JSON.stringify(data.result, null, 2)}</div>`;
      } else {
        el.innerHTML = `<div class='result-box' style='color:var(--danger)'>Error: ${data.error}</div>`;
      }
    }
  );
}

function promptHoldDoor() {
  const secs = prompt("Segundos para mantener la puerta abierta:", "5");
  if (secs !== null) execAC("hold_door", {seconds: parseInt(secs) || 5});
}

// ─── SCRIPTS ─────────────────────────────────────────────────

async function showScripts(cat, btn) {
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  if (btn) btn.classList.add("active");
  const data = await (await fetch(`${API}/scripts`)).json();
  const list = data[cat] || [];
  let html = `<div style='margin-bottom:8px'><button class='btn btn-outline' onclick='showFullScript("${cat}")' style='font-size:12px;padding:6px 12px;width:auto'>📄 Ver archivo completo</button></div>`;
  list.forEach((fn, i) => {
    html += `<div class='cmd-item' style='cursor:pointer' onclick='showScriptSource("${cat}","${fn}")'>
      <div class='cmd'>${i+1}. ${fn}()</div>
      <div style='font-size:11px;color:var(--text2)'>Click para ver código fuente</div>
    </div>`;
  });
  document.getElementById("scriptsList").innerHTML = html;
}

async function showScriptSource(cat, fnName) {
  const resp = await (await fetch(`${API}/scripts/${cat}/${fnName}`)).json();
  if (resp.error) {
    showModal(`<button class='modal-close' onclick='closeModal()'>&times;</button><h2>Error</h2><div class='result-box' style='color:var(--danger)'>${resp.error}</div>`);
    return;
  }
  showModal(`
    <button class='modal-close' onclick='closeModal()'>&times;</button>
    <h2>${resp.name}${resp.signature}</h2>
    <div class='result-box' style='max-height:70vh;font-size:12px'>${escapeHtml(resp.source)}</div>
  `);
}

async function showFullScript(cat) {
  const resp = await (await fetch(`${API}/scripts/${cat}/full`)).json();
  if (resp.error) {
    showModal(`<button class='modal-close' onclick='closeModal()'>&times;</button><h2>Error</h2><div class='result-box' style='color:var(--danger)'>${resp.error}</div>`);
    return;
  }
  showModal(`
    <button class='modal-close' onclick='closeModal()'>&times;</button>
    <h2>${resp.file.split('/').pop()}</h2>
    <div class='result-box' style='max-height:70vh;font-size:12px'>${escapeHtml(resp.source)}</div>
  `);
}

function escapeHtml(value) {
  const str = value == null ? "" : (typeof value === "string" ? value : JSON.stringify(value));
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ─── ZABBIX ──────────────────────────────────────────────────

function zabbixCheckSession() {
  fetch("/api/ups/zabbix/status")
    .then(r => r.json())
    .then(data => {
      if (data.connected) zabbixRenderConnected(data);
    })
    .catch(() => {});
}

function zabbixRenderConnected(data) {
  const hostsDiv = document.getElementById('zabbixHosts');
  if (!hostsDiv) return;
  hostsDiv.innerHTML = `
    <div class='result-box' style='background:#1e1e2e'>
      <div style='color:var(--success)'>✅ Conectado como <b>${escapeHtml(data.user)}</b></div>
      <div style='font-size:0.85em;color:#888'>${escapeHtml(data.api_url)}</div>
      <div style='margin-top:6px'>
        <button class='btn' onclick='zabbixListHosts()'>📡 Listar UPS</button>
        <button class='btn btn-outline' onclick='zabbixAlerts()'>🚨 Alertas</button>
        <button class='btn btn-outline' style='color:var(--danger)' onclick='zabbixDisconnect()'>⏻ Desconectar</button>
      </div>
      <div id='zabbixHostsResult' style='margin-top:6px'></div>
    </div>`;
}

function zabbixConnect() {
  const apiUrl = document.getElementById('zabbix_api_url').value;
  const user = document.getElementById('zabbix_user').value;
  const pass = document.getElementById('zabbix_pass').value;
  const hostsDiv = document.getElementById('zabbixHosts');
  hostsDiv.innerHTML = '<div class="loading">Conectando a Zabbix...</div>';

  fetch("/api/ups/zabbix/connect", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({api_url: apiUrl, user, password: pass})
  })
    .then(r => r.json())
    .then(data => {
      if (!data.connected) {
        hostsDiv.innerHTML = `<div class="error">${escapeHtml(data.error || "Error de conexión")}</div>`;
        return;
      }
      zabbixRenderConnected({api_url: apiUrl, user});
    })
    .catch(e => { hostsDiv.innerHTML = `<div class="error">${escapeHtml(e.message)}</div>`; });
}

function zabbixDisconnect() {
  fetch("/api/ups/zabbix/disconnect", {method: "POST"})
    .then(r => r.json())
    .then(() => { location.reload(); })
    .catch(() => { location.reload(); });
}

function zabbixListHosts() {
  const rd = document.getElementById('zabbixHostsResult');
  rd.innerHTML = '<div class="loading">Listando UPS...</div>';

  fetch("/api/ups/zabbix/hosts")
    .then(r => r.json())
    .then(data => {
      if (data.error) {
        rd.innerHTML = `<div class="error">${escapeHtml(data.error)}</div>`;
        return;
      }
      if (data.total === 0) {
        rd.innerHTML = '<div class="info">No se encontraron UPS monitoreadas</div>';
        return;
      }
      let html = `<div class='info'>${data.total} UPS encontradas</div>`;
      data.hosts.forEach((h, i) => {
        const tmpl = h.templates.length ? h.templates.join(', ') : '—';
        html += `<div class='result-box' style='cursor:pointer;margin-top:4px' onclick='zabbixShowMetrics(${i})'>
          <b>[${i+1}] ${escapeHtml(h.name)}</b> (${escapeHtml(h.host)})<br>
          <span style='font-size:0.85em;color:#888'>Templates: ${escapeHtml(tmpl)}</span>
        </div>`;
      });
      html += `<div id='zabbixMetrics'></div>`;
      rd.innerHTML = html;
      window._zabbixHosts = data.hosts;
    })
    .catch(e => { rd.innerHTML = `<div class="error">${escapeHtml(e.message)}</div>`; });
}

function zabbixShowMetrics(idx) {
  const hosts = window._zabbixHosts || [];
  const h = hosts[idx];
  if (!h) return;
  const md = document.getElementById('zabbixMetrics');
  if (!h.items || h.items.length === 0) {
    md.innerHTML = '<div class="info">Sin metricas disponibles</div>';
    return;
  }
  let html = `<div class='section-header' style='margin-top:8px'>${escapeHtml(h.name)} — Metricas</div>`;
  h.items.forEach(i => {
    html += `<div style='padding:3px 8px;border-bottom:1px solid #333;display:flex;justify-content:space-between'>
      <span>${escapeHtml(i.name)} <span style='color:#888'>(${escapeHtml(i.key_)})</span></span>
      <span style='color:#a6e3a1'>${escapeHtml(i.lastvalue)} ${escapeHtml(i.units)}</span>
    </div>`;
  });
  md.innerHTML = html;
}

function zabbixAlerts() {
  const rd = document.getElementById('zabbixHostsResult') || document.getElementById('zabbixHosts');
  if (!rd) return;
  rd.innerHTML = '<div class="loading">Consultando alertas...</div>';

  fetch("/api/ups/zabbix/alerts")
    .then(r => r.json())
    .then(data => {
      if (data.error) {
        rd.innerHTML = `<div class="error">${escapeHtml(data.error)}</div>`;
        return;
      }
      if (data.total === 0) {
        rd.innerHTML = '<div class="info">No hay problemas activos</div>';
        return;
      }
      let html = `<div class='info'>${data.total} problemas activos</div>`;
      data.alerts.forEach(a => {
        const sev = a.severity || 0;
        const color = sev >= 4 ? '#f38ba8' : sev >= 2 ? '#fab387' : '#a6e3a1';
        html += `<div style='padding:4px 8px;border-left:3px solid ${color};margin:4px 0;background:#1e1e2e'>
          <b style='color:${color}'>[${escapeHtml(a.severity_name)}]</b> ${escapeHtml(a.name)}<br>
          <span style='font-size:0.85em;color:#888'>${escapeHtml(a.clock)} ${a.acknowledged === '0' ? '🔔' : '✅'}</span>
        </div>`;
      });
      rd.innerHTML = html;
    })
    .catch(e => { rd.innerHTML = `<div class="error">${escapeHtml(e.message)}</div>`; });
}

// ─── UPS ─────────────────────────────────────────────────────

function upsBatteryLife() {
  const date = document.getElementById("ups_bat_date").value;
  const type = document.getElementById("ups_bat_type").value;
  if (!date) return showError("upsResult", "Seleccioná una fecha");
  asyncFetch(`/api/ups/battery-life?date=${date}&type=${type}`,
    "upsResult",
    (r) => {
      if (r.error) { showError("upsResult", r.error); return; }
      let html = "<div class='section-header' style='color:var(--success)'>🔋 Estimación de Vida</div><div class='result-box'>";
      for (const [k, v] of Object.entries(r)) {
        html += `<div><span style='color:#888'>${k}:</span> <span>${escapeHtml(String(v))}</span></div>`;
      }
      html += "</div>";
      document.getElementById("upsResult").innerHTML = html;
    }
  );
}

function upsDiagnostics() {
  asyncFetch("/api/ups/diagnostics",
    "upsResult",
    (r) => {
      const manual = r.procedure || r;
      let html = `<h2>${escapeHtml(manual.title || "Manual de Diagnóstico de UPS")}</h2>`;
      (manual.sections || []).forEach(s => {
        html += `<div class='section' style='margin-top:12px'>
          <div class='section-header'>${escapeHtml(s.icon || "📋")} ${escapeHtml(s.title)}</div>
          <div class='section-body' style='padding:8px'>`;

        // Checklist items
        if (s.checks) {
          s.checks.forEach(c => {
            html += `<div class='cmd-item' style='flex-direction:column;align-items:flex-start;gap:2px;padding:8px 0'>
              <div style='font-weight:600;font-size:13px'>${escapeHtml(c.q)}</div>`;
            if (c.ok) html += `<div class='text-xs' style='color:var(--success)'>✅ ${escapeHtml(c.ok)}</div>`;
            if (c.bad) html += `<div class='text-xs' style='color:var(--danger)'>⚠️ ${escapeHtml(c.bad)}</div>`;
            if (c.tip) html += `<div class='text-xs text-muted' style='margin-top:2px'>💡 ${escapeHtml(c.tip)}</div>`;
            html += `</div>`;
          });
        }

        // Tree items
        if (s.tree) {
          html += `<div style='font-family:monospace;font-size:12px;line-height:1.6;padding:8px;background:var(--card);border-radius:6px'>`;
          s.tree.forEach(line => {
            const color = line.includes("UPS OK") ? "var(--success)" :
                         line.includes("Servicio técnico") || line.includes("Reemplazar") ? "var(--danger)" :
                         line.includes("Revisar") ? "var(--warning)" : "";
            html += `<div${color ? ` style='color:${color}'` : ""}>${escapeHtml(line)}</div>`;
          });
          html += `</div>`;
        }

        // Solutions (paso a paso)
        if (s.solutions) {
          s.solutions.forEach(sol => {
            html += `<div class='card' style='text-align:left;padding:12px;margin-top:8px'>
              <div style='font-weight:600;font-size:14px;margin-bottom:6px'>🔧 ${escapeHtml(sol.problem)}</div>`;
            if (sol.tools) html += `<div class='text-xs text-muted mb-6'>🛠️ ${escapeHtml(sol.tools)}</div>`;
            html += `<ol style='margin:0;padding-left:20px;font-size:12px;line-height:1.7'>`;
            (sol.steps || []).forEach(st => {
              const isBold = st.includes("→") || st.match(/^\s*Opción/i);
              html += `<li${isBold ? " style='font-weight:600;margin-top:6px'" : ""}>${escapeHtml(st)}</li>`;
            });
            html += `</ol>`;
            if (sol.warnings) {
              sol.warnings.forEach(w => {
                html += `<div class='text-xs' style='color:var(--danger);margin-top:4px'>${escapeHtml(w)}</div>`;
              });
            }
            html += `</div>`;
          });
        }

        // Tools
        if (s.tools) {
          Object.entries(s.tools).forEach(([tool, cmds]) => {
            html += `<div class='section-header text-sm' style='margin-top:8px;font-size:12px'>${escapeHtml(tool)}</div>`;
            cmds.forEach(cmd => {
              html += `<div class='cmd-item'><code style='font-size:11px'>${escapeHtml(cmd)}</code></div>`;
            });
          });
        }

        html += `</div></div>`;
      });
      document.getElementById("upsResult").innerHTML = html;
    }
  );
}

function upsPowerChute() {
  const host = document.getElementById("ups_pchute_host").value;
  const port = document.getElementById("ups_pchute_port").value || 6547;
  const user = document.getElementById("ups_pchute_user").value;
  const pass = document.getElementById("ups_pchute_pass").value;
  const ssl = document.getElementById("ups_pchute_ssl").checked;
  if (!host) return;
  asyncFetch(`/api/ups/powerchute-status?host=${encodeURIComponent(host)}&port=${port}&user=${encodeURIComponent(user)}&password=${encodeURIComponent(pass)}&ssl=${ssl}`,
    "upsResult",
    r => `<div class='result-box'>${escapeHtml(JSON.stringify(r, null, 2))}</div>`
  );
}

function upsAPCUPSD() {
  const host = document.getElementById("ups_apcupsd_host").value || "localhost";
  const port = document.getElementById("ups_apcupsd_port").value || 3551;
  if (!host) return;
  asyncFetch(`/api/ups/apcupsd-status?host=${encodeURIComponent(host)}&port=${port}`,
    "upsResult",
    r => `<div class='result-box'>${escapeHtml(JSON.stringify(r, null, 2))}</div>`
  );
}


// ─── EXPORT ──────────────────────────────────────────────────

function downloadBlob(content, filename, mime) {
  const blob = new Blob([content], {type: mime});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

function exportCSV(data, filename) {
  const header = Object.keys(data[0] || {}).join(",");
  const rows = data.map(r => Object.values(r).map(v => `"${String(v).replace(/"/g, '""')}"`).join(","));
  downloadBlob([header, ...rows].join("\n"), filename, "text/csv;charset=utf-8");
}

function exportJSON(data, filename) {
  downloadBlob(JSON.stringify(data, null, 2), filename, "application/json;charset=utf-8");
}

function resultExportBar(data, type, label) {
  const jsonStr = JSON.stringify(data, null, 2).replace(/"/g, "&quot;");
  return `<div style='display:flex;gap:6px;margin-top:8px;flex-wrap:wrap'>
    <button class='btn btn-xs btn-outline' onclick='exportJSON(${jsonStr},"${type}_${label}.json")'>📥 JSON</button>
    <button class='btn btn-xs btn-outline' onclick='navigator.clipboard.writeText(${jsonStr})'>📋 Copiar JSON</button>
  </div>`;
}


// ─── UX: COMPARTIR, FAVORITOS, HISTORIAL ────────────────────

function shareResult(text, title) {
  if (navigator.share) {
    navigator.share({title: title || "TechBot", text}).catch(() => {});
  } else {
    navigator.clipboard?.writeText(text).then(() => {
      const el = document.createElement("div");
      el.className = "toast";
      el.textContent = "📋 Copiado al portapapeles";
      document.getElementById("toastContainer").appendChild(el);
      setTimeout(() => el.remove(), 2000);
    }).catch(() => {});
  }
}

function addFavorite(type, value) {
  const key = "techbot_favs";
  let favs = JSON.parse(localStorage.getItem(key) || "[]");
  if (favs.some(f => f.value === value)) return;
  favs.push({type, value, ts: Date.now()});
  localStorage.setItem(key, JSON.stringify(favs));
}

function removeFavorite(value) {
  const key = "techbot_favs";
  let favs = JSON.parse(localStorage.getItem(key) || "[]");
  favs = favs.filter(f => f.value !== value);
  localStorage.setItem(key, JSON.stringify(favs));
}

function listFavorites() {
  return JSON.parse(localStorage.getItem("techbot_favs") || "[]");
}

function addResultToHistory(type, data) {
  const key = "techbot_history";
  let hist = JSON.parse(localStorage.getItem(key) || "[]");
  hist.unshift({type, data: JSON.parse(JSON.stringify(data)), ts: Date.now()});
  if (hist.length > 50) hist = hist.slice(0, 50);
  localStorage.setItem(key, JSON.stringify(hist));
}

function showFavorites() {
  const favs = listFavorites();
  if (!favs.length) {
    showModal(`
      <button class='modal-close' onclick='closeModal()'>&times;</button>
      <h2>⭐ Favoritos</h2>
      <p class='text-muted'>Todavía no tenés favoritos. Escaneá un host y agregalo desde los resultados.</p>
    `);
    return;
  }
  let html = `<button class='modal-close' onclick='closeModal()'>&times;</button>
    <h2>⭐ Favoritos (${favs.length})</h2>`;
  favs.forEach(f => {
    const icon = f.type === "host" ? "🖥️" : "🌐";
    html += `<div class='cmd-item'>
      <span>${icon}</span>
      <span class='text-sm' style='flex:1;word-break:break-all'>${escapeHtml(f.value)}</span>
      <button class='btn btn-xs btn-outline' onclick='removeFavorite("${escapeHtml(f.value)}");showFavorites();' style='color:var(--danger)'>✕</button>
      <button class='btn btn-xs' onclick='navigator.clipboard.writeText("${escapeHtml(f.value)}")'>📋</button>
    </div>`;
  });
  showModal(html);
}

function showHistory() {
  const hist = JSON.parse(localStorage.getItem("techbot_history") || "[]");
  if (!hist.length) {
    showModal(`
      <button class='modal-close' onclick='closeModal()'>&times;</button>
      <h2>📜 Historial</h2>
      <p class='text-muted'>Sin resultados recientes.</p>
    `);
    return;
  }
  let html = `<button class='modal-close' onclick='closeModal()'>&times;</button>
    <h2>📜 Historial (últimos ${hist.length})</h2>`;
  hist.slice(0, 20).forEach(h => {
    const time = new Date(h.ts).toLocaleTimeString();
    html += `<div class='cmd-item' style='flex-direction:column;align-items:flex-start;gap:2px'>
      <div class='text-xs text-muted'>${time} · ${escapeHtml(h.type)}</div>
      <div class='text-xs' style='word-break:break-all'>${escapeHtml(JSON.stringify(h.data).slice(0, 150))}</div>
    </div>`;
  });
  if (hist.length > 20) html += `<div class='text-xs text-muted' style='margin-top:6px'>... y ${hist.length - 20} más</div>`;
  html += `<button class='btn btn-sm btn-outline' style='margin-top:8px;color:var(--danger)' onclick='localStorage.removeItem("techbot_history");closeModal()'>🗑️ Limpiar historial</button>`;
  showModal(html);
}

// ─── DATA EXPORT / IMPORT ──────────────────────────────────

function exportAllData() {
  const data = {};
  const keys = ["techbot_notes", "techbot_favs", "techbot_history",
    "techbot_theme", "techbot_compact", "techbot_topology_saved",
    "techbot_ipam_subnets", "techbot_ipam_hosts"];
  keys.forEach(k => {
    const val = localStorage.getItem(k);
    if (val) data[k] = JSON.parse(val);
  });
  data._exported_at = new Date().toISOString();
  data._version = "1.0";
  exportJSON(data, "techbot_backup.json");
  showToast("✅ Backup exportado", "success");
}

function importAllData() {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = ".json";
  input.onchange = async (e) => {
    try {
      const text = await e.target.files[0].text();
      const data = JSON.parse(text);
      let count = 0;
      Object.entries(data).forEach(([k, v]) => {
        if (k.startsWith("techbot_") || k.startsWith("_")) {
          localStorage.setItem(k, JSON.stringify(v));
          count++;
        }
      });
      showToast(`✅ ${count} datos importados. Recargá la página.`, "success");
      setTimeout(() => location.reload(), 1500);
    } catch(err) {
      showToast("❌ Error al importar: " + err.message, "error");
    }
  };
  input.click();
}

// ─── NETWORK AUDIT REPORT ──────────────────────────────────

async function generateReport() {
  const host = document.getElementById("scan_host")?.value || prompt("IP del dispositivo a auditar:");
  if (!host) return;
  const el = document.getElementById("results");
  el.innerHTML = "<span class='text-muted'>Generando informe de auditoría...</span>";

  try {
    const [ping, ports, cctv] = await Promise.all([
      fetch(`/api/scanner/ping?host=${encodeURIComponent(host)}&async=false`).then(r => r.json()),
      fetch(`/api/scanner/quick-scan?host=${encodeURIComponent(host)}&async=false`).then(r => r.json()),
      fetch(`/api/scanner/scan-cctv?host=${encodeURIComponent(host)}`).then(r => r.json()).catch(() => ({})),
    ]);

    const now = new Date().toLocaleString();
    const title = `Informe de Auditoría - ${host}`;
    let html = `<div class='result-box' style='max-height:none'>
      <div style='display:flex;justify-content:space-between;align-items:start;flex-wrap:wrap'>
        <div><h3 style='margin:0'>📋 ${title}</h3>
        <div class='text-xs text-muted'>Generado: ${now}</div></div>
        <div style='display:flex;gap:4px'>
          <button class='btn btn-xs btn-outline' onclick='window.print()'>🖨️ Imprimir</button>
          <button class='btn btn-xs btn-outline' onclick='exportJSON(${JSON.stringify({host, ping, ports, cctv, generated: now})},"audit_${host}.json")'>📥 JSON</button>
        </div>
      </div>
      <hr style='border-color:var(--border);margin:10px 0'>`;

    // Estado del host
    const alive = ping.alive || ping.reachable;
    html += `<div class='section' style='margin-top:8px'>
      <div class='section-header'>🖥️ Estado del Host</div>
      <div class='section-body'>
        <div class='text-sm'>IP: <strong>${escapeHtml(host)}</strong></div>
        <div class='text-sm'>Estado: <span style='color:var(--${alive ? "success" : "danger"})'>${alive ? "✅ Activo" : "❌ Sin respuesta"}</span></div>
        ${ping.os ? `<div class='text-sm'>OS: ${escapeHtml(ping.os)}</div>` : ""}
        ${ping.ttl !== undefined ? `<div class='text-sm'>TTL: ${ping.ttl}</div>` : ""}
        ${ping.latency_ms ? `<div class='text-sm'>Latencia: ${ping.latency_ms} ms</div>` : ""}
      </div>
    </div>`;

    // Puertos abiertos
    const portList = ports.ports || ports.results || [];
    html += `<div class='section' style='margin-top:8px'>
      <div class='section-header'>🔌 Puertos Abiertos (${portList.length})</div>
      <div class='section-body'>`;
    if (portList.length) {
      html += "<table style='width:100%;font-size:12px;border-collapse:collapse'>";
      html += "<tr style='color:var(--text2)'><th style='text-align:left;padding:4px'>Puerto</th><th style='text-align:left'>Servicio</th><th style='text-align:left'>Estado</th></tr>";
      portList.forEach(p => {
        const port = p.port || p;
        const svc = p.service || p.name || "";
        html += `<tr style='border-top:1px solid var(--border)'><td style='padding:4px'><strong>${port}</strong></td><td>${escapeHtml(svc)}</td><td style='color:var(--success)'>✅ Abierto</td></tr>`;
      });
      html += "</table>";
    } else {
      html += "<div class='text-muted text-sm'>Sin puertos abiertos detectados</div>";
    }
    html += "</div></div>";

    // CCTV
    if (cctv.device_identity) {
      html += `<div class='section' style='margin-top:8px'>
        <div class='section-header'>📷 Dispositivos CCTV</div>
        <div class='section-body'>`;
      Object.entries(cctv.device_identity).forEach(([port, vendor]) => {
        html += `<div class='text-sm'>Puerto ${port}: ${escapeHtml(vendor)}</div>`;
      });
      html += "</div></div>";
    }

    // Resumen de seguridad
    const criticalPorts = portList.filter(p => [23, 21, 135, 445, 3389].includes(p.port || p));
    if (criticalPorts.length) {
      html += `<div class='section' style='margin-top:8px'>
        <div class='section-header' style='color:var(--danger)'>⚠️ Hallazgos de Seguridad</div>
        <div class='section-body'>
          <div class='text-sm' style='color:var(--danger)'>Puertos críticos expuestos: ${criticalPorts.map(p => p.port || p).join(", ")}</div>
        </div>
      </div>`;
    }

    html += `<hr style='border-color:var(--border);margin:12px 0'>
      <div class='text-xs text-muted'>TechBot Auditoría · ${now}</div>
    </div>`;

    el.innerHTML = html;
    addResultToHistory("audit", {host});
    showToast("✅ Informe generado", "success");
  } catch(e) {
    el.innerHTML = `<span style='color:var(--danger)'>Error generando informe: ${escapeHtml(e.message)}</span>`;
  }
}

// ─── REST API CLIENT ────────────────────────────────────────

function showAPIClient() {
  const el = document.getElementById("results");
  el.innerHTML = `
    <h3 style='margin-bottom:12px'>🌐 Cliente REST API</h3>
    <p class='text-sm text-muted mb-8'>Probá endpoints HTTP directamente desde TechBot</p>
    <div style='display:flex;gap:6px;flex-wrap:wrap'>
      <select id='api_method' style='width:80px;background:var(--card);color:var(--text);border:1px solid var(--border);border-radius:4px;padding:6px'>
        <option value='GET'>GET</option>
        <option value='POST'>POST</option>
        <option value='PUT'>PUT</option>
        <option value='DELETE'>DELETE</option>
        <option value='PATCH'>PATCH</option>
      </select>
      <div style='flex:2;min-width:200px'><input type='text' id='api_url' placeholder='https://api.ejemplo.com/endpoint'></div>
      <button class='btn' onclick='apiRequest()'>Enviar</button>
    </div>
    <div style='margin-top:6px'>
      <textarea id='api_body' placeholder='Body (JSON) para POST/PUT/PATCH' style='width:100%;height:60px;background:var(--card);color:var(--text);border:1px solid var(--border);border-radius:4px;padding:6px;font-size:12px;resize:vertical'></textarea>
    </div>
    <div style='display:flex;gap:6px;margin-top:6px'>
      <label style='font-size:12px;display:flex;align-items:center;gap:4px'><input type='text' id='api_header_key' placeholder='Header Key' style='width:100px;padding:4px;background:var(--card);color:var(--text);border:1px solid var(--border);border-radius:4px'></label>
      <label style='font-size:12px;display:flex;align-items:center;gap:4px'><input type='text' id='api_header_val' placeholder='Header Value' style='width:150px;padding:4px;background:var(--card);color:var(--text);border:1px solid var(--border);border-radius:4px'></label>
      <button class='btn btn-xs btn-outline' onclick='apiAddHeader()'>+ Header</button>
    </div>
    <div id='api_headers_list' class='text-xs' style='margin-top:4px'></div>
    <div id='apiResult' class='text-muted text-sm' style='margin-top:8px'></div>
  `;
}

let _apiHeaders = [];

function apiAddHeader() {
  const k = document.getElementById("api_header_key").value.trim();
  const v = document.getElementById("api_header_val").value.trim();
  if (!k) return;
  _apiHeaders.push({key: k, value: v});
  document.getElementById("api_header_key").value = "";
  document.getElementById("api_header_val").value = "";
  const el = document.getElementById("api_headers_list");
  el.innerHTML = _apiHeaders.map(h => `<span class='badge badge-accent'>${escapeHtml(h.key)}: ${escapeHtml(h.value)} <span style='cursor:pointer;color:var(--danger)' onclick='_apiHeaders=_apiHeaders.filter(x=>x.key!=="${escapeHtml(h.key)}");apiAddHeader()'>✕</span></span>`).join(" ");
}

async function apiRequest() {
  const method = document.getElementById("api_method").value;
  const url = document.getElementById("api_url").value.trim();
  if (!url) { showToast("URL requerida", "error"); return; }
  const el = document.getElementById("apiResult");
  el.innerHTML = "<span class='text-muted'>Enviando...</span>";
  try {
    const headers = {"Content-Type": "application/json"};
    _apiHeaders.forEach(h => headers[h.key] = h.value);
    const opts = {method, headers};
    if (["POST", "PUT", "PATCH"].includes(method)) {
      const body = document.getElementById("api_body").value.trim();
      if (body) opts.body = body;
    }
    const start = performance.now();
    const resp = await fetch(url, opts);
    const elapsed = Math.round(performance.now() - start);
    const contentType = resp.headers.get("content-type") || "";
    let bodyText;
    try { bodyText = await resp.text(); } catch { bodyText = "(no body)"; }
    let bodyHtml;
    try {
      const pretty = JSON.stringify(JSON.parse(bodyText), null, 2);
      bodyHtml = `<pre style='font-size:11px;white-space:pre-wrap;word-break:break-word;max-height:400px;overflow-y:auto;background:var(--bg);padding:8px;border-radius:4px;margin-top:4px'>${escapeHtml(pretty.slice(0, 3000))}</pre>`;
    } catch {
      bodyHtml = `<pre style='font-size:11px;white-space:pre-wrap;word-break:break-word;max-height:200px;overflow-y:auto;background:var(--bg);padding:8px;border-radius:4px;margin-top:4px'>${escapeHtml(bodyText.slice(0, 2000))}</pre>`;
    }
    const statusCls = resp.status < 300 ? "success" : resp.status < 500 ? "warning" : "danger";
    let html = `<div class='result-box' style='max-height:none'>
      <div style='display:flex;justify-content:space-between;align-items:center'>
        <span><strong>${method}</strong> <span class='text-sm'>${escapeHtml(resp.url)}</span></span>
        <span style='color:var(--${statusCls})'>${resp.status} ${resp.statusText}</span>
        <span class='text-xs text-muted'>${elapsed}ms</span>
      </div>`;
    // Headers
    html += `<div style='margin-top:6px'><span class='text-xs' onclick='this.nextElementSibling.style.display=this.nextElementSibling.style.display==="none"?"block":"none"' style='cursor:pointer;color:var(--accent)'>📋 Headers</span>
      <div style='display:none;margin-top:4px;font-size:11px'>`;
    resp.headers.forEach((v, k) => {
      html += `<div><span class='badge badge-accent' style='font-size:9px'>${escapeHtml(k)}</span> ${escapeHtml(v.slice(0, 80))}</div>`;
    });
    html += `</div></div>`;
    html += bodyHtml;
    html += "</div>";
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<span style="color:var(--danger)">Error: ${escapeHtml(e.message)}</span>`;
  }
}

