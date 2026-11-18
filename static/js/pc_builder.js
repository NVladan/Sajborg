/* PC konfigurator: slotovi, izbor kompatibilnih komponenti, potrošnja i provjere. */
(function () {
    'use strict';

    const cfg = window.PB || {};
    const root = document.getElementById('pb');
    if (!root) return;

    const $ = (sel, el) => (el || document).querySelector(sel);
    const $$ = (sel, el) => Array.from((el || document).querySelectorAll(sel));
    const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    const km = (n) => (Number(n) || 0).toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' KM';
    const csrf = () => (document.querySelector('meta[name="csrf-token"]') || {}).content || '';
    const store = {
        get(k) { try { return JSON.parse(localStorage.getItem(k) || 'null'); } catch (e) { return null; } },
        set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* privatni prozor */ } },
    };

    const slots = cfg.slots || [];
    const slotLabel = Object.fromEntries(slots.map((s) => [s.type, s.label]));
    const required = slots.filter((s) => s.required && s.available).map((s) => s.type);

    /* ---------- Atributi ---------- */
    const norm = (s) => String(s).replace(/\s+/g, '').toLowerCase();
    function attr(part, ...names) {
        if (!part || !part.attrs) return null;
        const wanted = names.map(norm);
        for (const [k, v] of Object.entries(part.attrs)) {
            if (wanted.includes(norm(k)) && v !== null && String(v).trim() !== '') return String(v).trim();
        }
        return null;
    }
    const num = (v) => { const m = String(v || '').match(/\d+(?:[.,]\d+)?/); return m ? parseFloat(m[0].replace(',', '.')) : null; };
    const yes = (v) => ['true', '1', 'da', 'yes'].includes(String(v).trim().toLowerCase());

    // Najvažnije osobine po tipu, za kratki opis u listi
    const CHIPS = {
        'CPU': [['socket'], ['Broj jezgara', (v) => v + ' jezgara'], ['Broj Threadova', (v) => v + ' niti'], ['TDP (W)', (v) => v + ' W TDP']],
        'Motherboard': [['socket'], ['chipset'], ['RAM'], ['RAM Slotovi', (v) => v + ' slota za RAM']],
        'RAM': [['Kapacitet(GB)', (v) => v + ' GB'], ['RAM'], ['Brzina(MHz)', (v) => v + ' MHz']],
        'GPU': [['VRAM (GB)', (v) => v + ' GB'], ['Tip Memorije'], ['TDP(W)', (v) => v + ' W']],
        'Storage': [['Kapacitet'], ['Tip'], ['Interfejs']],
        'Power Supply': [['Snaga(W)', (v) => v + ' W'], ['Efikasnost'], ['Modularno', (v) => (yes(v) ? 'modularno' : null)]],
        'Case': [['Tip'], ['Ventilatori', (v) => 'ventilatori: ' + v]],
        'CPU Cooler': [['TDP (W)', (v) => 'hladi do ' + v + ' W'], ['Veličina ventilatora (mm)', (v) => v + ' mm']],
    };
    function chips(type, part) {
        return (CHIPS[type] || []).map(([name, fmt]) => {
            const v = attr(part, name);
            if (!v) return null;
            return fmt ? fmt(v) : v;
        }).filter(Boolean);
    }

    /* ---------- Stanje ---------- */
    let build = store.get('pb-build') || {};   // tip -> komponenta {id, name, price, image_url, url, attrs}
    const cache = {};                          // tip -> lista komponenti
    let checkResult = null;

    function save() { store.set('pb-build', build); }

    /* ---------- Potrošnja (ista formula kao na serveru) ---------- */
    function power() {
        const p = cfg.power;
        const cpuTdp = num(attr(build['CPU'], 'TDP (W)', 'TDP'));
        const gpuTdp = num(attr(build['GPU'], 'TDP (W)', 'TDP', 'TBP'));
        const cpuW = Math.round((cpuTdp || 0) * p.cpuFactor);
        const gpuW = Math.round(gpuTdp || 0);
        const load = cpuW + gpuW + p.other;
        const recommended = Math.ceil(load * p.headroom / p.step) * p.step;
        const psu = num(attr(build['Power Supply'], 'Snaga (W)', 'Snaga', 'Wattage'));
        return { cpuW, gpuW, load, recommended, psu, known: !!(build['CPU'] || build['GPU']) };
    }

    /* ---------- Kompatibilnost (za filter u listi; server daje konačne poruke) ---------- */
    function conflicts(type, part) {
        const why = [];
        const cpu = build['CPU'], mb = build['Motherboard'], ram = build['RAM'], cooler = build['CPU Cooler'];
        const sock = (p) => (attr(p, 'socket') || '').toLowerCase();
        if (type === 'CPU') {
            if (mb && sock(mb) && sock(part) && sock(mb) !== sock(part)) why.push(`ploča je ${attr(mb, 'socket')}`);
            if (cooler && sock(part)) { const s = attr(cooler, attr(part, 'socket')); if (s !== null && !yes(s)) why.push(`kuler nema nosač za ${attr(part, 'socket')}`); }
        }
        if (type === 'Motherboard') {
            if (cpu && sock(cpu) && sock(part) && sock(cpu) !== sock(part)) why.push(`procesor je ${attr(cpu, 'socket')}`);
            const rt = attr(ram, 'RAM'), mt = attr(part, 'RAM');
            if (rt && mt && !mt.toLowerCase().includes(rt.toLowerCase())) why.push(`RAM je ${rt}`);
        }
        if (type === 'RAM') {
            const rt = attr(part, 'RAM'), mt = attr(mb, 'RAM');
            if (rt && mt && !mt.toLowerCase().includes(rt.toLowerCase())) why.push(`ploča podržava ${mt}`);
        }
        if (type === 'CPU Cooler' && cpu && attr(cpu, 'socket')) {
            const s = attr(part, attr(cpu, 'socket'));
            if (s !== null && !yes(s)) why.push(`nema nosač za ${attr(cpu, 'socket')}`);
        }
        if (type === 'Power Supply') {
            const pw = power(), w = num(attr(part, 'Snaga (W)', 'Snaga'));
            if (pw.known && w && w < pw.load) why.push(`preslabo za ~${pw.load} W`);
        }
        return why;
    }

    function hint(type, part) {
        if (type === 'Power Supply') {
            const pw = power(), w = num(attr(part, 'Snaga (W)', 'Snaga'));
            if (pw.known && w && w >= pw.recommended) return 'preporučeno';
        }
        if (type === 'CPU Cooler' && build['CPU']) {
            const c = num(attr(part, 'TDP (W)')), t = num(attr(build['CPU'], 'TDP (W)'));
            if (c && t && c < t) return 'slab za ovaj procesor';
        }
        return null;
    }

    /* ---------- Prikaz slotova i sažetka ---------- */
    function renderSlots() {
        // Sljedeći korak: prvi neizabrani obavezni slot dobija istaknuto dugme
        const next = slots.find((s) => s.available && s.required && !build[s.type]);
        $$('.pb-slot').forEach((el) => {
            const type = el.dataset.slot;
            const part = build[type];
            const partEl = $('[data-part]', el), empty = $('[data-empty]', el);
            const removeBtn = $('[data-remove]', el), pickLabel = $('[data-pick-label]', el);
            el.classList.toggle('is-filled', !!part);
            if (part) {
                const ch = chips(type, part);
                partEl.innerHTML = `
                    <img src="${esc(part.image_url)}" alt="" class="pb-thumb" loading="lazy">
                    <div class="pb-part-text">
                        <a href="${esc(part.url || '#')}" target="_blank" rel="noopener" class="pb-part-name">${esc(part.name)}</a>
                        ${ch.length ? `<span class="pb-chips">${ch.map((c) => `<span>${esc(c)}</span>`).join('')}</span>` : ''}
                    </div>
                    <span class="pb-part-price">${km(part.price)}</span>`;
            } else {
                partEl.innerHTML = '';
            }
            partEl.hidden = !part;
            empty.hidden = !!part;
            if (removeBtn) removeBtn.hidden = !part;
            if (pickLabel) pickLabel.textContent = part ? 'Promijeni' : 'Izaberi';
            const pickBtn = $('[data-pick]', el);
            if (pickBtn) {
                const isNext = next && next.type === type;
                pickBtn.classList.toggle('btn-primary', isNext);
                pickBtn.classList.toggle('btn-outline-primary', !part && !isNext);
                pickBtn.classList.toggle('btn-outline-secondary', !!part);
            }
            el.classList.toggle('is-next', !!(next && next.type === type));
        });
    }

    function renderSummary() {
        const parts = Object.values(build);
        $('#pb-total').textContent = km(parts.reduce((s, p) => s + (p.price || 0), 0));
        const done = required.filter((t) => build[t]).length;
        $('#pb-progress-fill').style.width = (required.length ? (done / required.length) * 100 : 0) + '%';
        $('#pb-progress-text').textContent = done === required.length
            ? 'Sve osnovne komponente su izabrane'
            : `${done} od ${required.length} osnovnih komponenti`;
        $('#pb-reset').hidden = parts.length === 0;
        $('#pb-cart').disabled = parts.length === 0;
        const saveBtn = $('#pb-save'); if (saveBtn) saveBtn.disabled = parts.length === 0;

        // Potrošnja
        const pw = power();
        const loadEl = $('#pb-power-load'), text = $('#pb-power-text');
        const meter = $('#pb-meter-load'), rec = $('#pb-meter-rec'), box = $('#pb-power');
        box.classList.remove('is-ok', 'is-warn', 'is-error');
        if (!pw.known) {
            loadEl.textContent = '—';
            meter.style.width = '0'; rec.style.left = '0'; rec.hidden = true;
            text.textContent = 'Izaberite procesor i grafičku da procijenimo potrošnju.';
            return;
        }
        loadEl.textContent = `~${pw.load} W`;
        const scale = Math.max(pw.psu || 0, pw.recommended) * 1.1;
        meter.style.width = (pw.load / scale * 100) + '%';
        rec.hidden = false;
        rec.style.left = (pw.recommended / scale * 100) + '%';
        if (pw.psu) {
            const status = pw.psu < pw.load ? 'is-error' : (pw.psu < pw.recommended ? 'is-warn' : 'is-ok');
            box.classList.add(status);
            box.style.setProperty('--pb-psu', (pw.psu / scale * 100) + '%');
            text.innerHTML = `Napajanje <strong>${pw.psu} W</strong>, preporuka <strong>${pw.recommended} W</strong>.`;
        } else {
            box.style.removeProperty('--pb-psu');
            text.innerHTML = `Preporučeno napajanje: <strong>${pw.recommended} W</strong> ili jače.`;
        }
    }

    const ICON = { ok: 'fa-circle-check', info: 'fa-circle-info', warn: 'fa-triangle-exclamation', error: 'fa-circle-xmark' };
    const availableTypes = new Set(slots.filter((s) => s.available).map((s) => s.type));
    function renderChecks() {
        const list = $('#pb-checks');
        const items = [];
        if (checkResult) {
            checkResult.checks.forEach((c) => items.push(c));
            const missing = (checkResult.missing || []).filter((t) => availableTypes.has(t));
            if (missing.length && Object.keys(build).length) {
                items.push({ status: 'todo', title: 'Nedostaje', missing });
            }
        }
        if (!Object.keys(build).length) {
            list.innerHTML = '<li class="pb-check is-todo"><i class="fas fa-circle-info" aria-hidden="true"></i><div>Počnite od procesora. Ponudićemo samo dijelove koji mu odgovaraju.</div></li>';
            return;
        }
        list.innerHTML = items.map((c) => {
            if (c.status === 'todo') {
                return `<li class="pb-check is-todo"><i class="fas fa-list-check" aria-hidden="true"></i><div><strong>Još izaberite:</strong>
                    <span class="pb-missing">${c.missing.map((t) => `<button type="button" data-pick="${esc(t)}">${esc(slotLabel[t] || t)}</button>`).join('')}</span></div></li>`;
            }
            return `<li class="pb-check is-${c.status}"><i class="fas ${ICON[c.status]}" aria-hidden="true"></i>
                <div><strong>${esc(c.title)}</strong>${c.detail ? `<span>${esc(c.detail)}</span>` : ''}</div></li>`;
        }).join('');

        // Problemi i uz sam slot
        $$('.pb-slot').forEach((el) => { $('[data-issues]', el).innerHTML = ''; el.classList.remove('has-error', 'has-warn'); });
        const slotFor = (title) => {
            if (/ploč/i.test(title) && /Procesor/i.test(title)) return ['CPU', 'Motherboard'];
            if (/RAM/i.test(title)) return ['RAM'];
            if (/Kuler/i.test(title)) return ['CPU Cooler'];
            if (/Napajanje|napajanja/i.test(title)) return ['Power Supply'];
            return [];
        };
        (checkResult ? checkResult.checks : []).filter((c) => c.status === 'warn' || c.status === 'error').forEach((c) => {
            slotFor(c.title).forEach((type) => {
                const el = $(`.pb-slot[data-slot="${CSS.escape(type)}"]`);
                if (!el || !build[type]) return;
                el.classList.add(c.status === 'error' ? 'has-error' : 'has-warn');
                $('[data-issues]', el).insertAdjacentHTML('beforeend', `<li class="is-${c.status}"><i class="fas ${ICON[c.status]}" aria-hidden="true"></i> ${esc(c.detail || c.title)}</li>`);
            });
        });
    }

    function renderMobileBar() {
        const parts = Object.values(build);
        const bar = $('#pb-mobilebar');
        bar.hidden = parts.length === 0;
        if (!parts.length) return;
        $('#pb-mobile-total').textContent = km(parts.reduce((s, p) => s + (p.price || 0), 0));
        const status = $('#pb-mobile-status');
        const checks = checkResult ? checkResult.checks : [];
        const errors = checks.filter((c) => c.status === 'error').length;
        const warns = checks.filter((c) => c.status === 'warn').length;
        const missing = required.filter((t) => !build[t]).length;
        status.className = 'pb-mobilebar-status' + (errors ? ' is-error' : (warns ? ' is-warn' : ''));
        status.textContent = errors ? `${errors} ${errors === 1 ? 'problem' : 'problema'} sa kompatibilnošću`
            : (warns ? 'Provjerite upozorenja' : (missing ? `Još ${missing} ${missing === 1 ? 'osnovna komponenta' : (missing < 5 ? 'osnovne komponente' : 'osnovnih komponenti')}` : 'Sve se slaže'));
    }
    $('#pb-mobile-go').addEventListener('click', () => $('.pb-summary').scrollIntoView({ behavior: 'smooth', block: 'start' }));

    let checkTimer, checkSeq = 0;
    function refresh() {
        save();
        renderSlots();
        renderSummary();
        clearTimeout(checkTimer);
        checkTimer = setTimeout(async () => {
            const seq = ++checkSeq;
            const ids = Object.values(build).map((p) => p.id);
            if (!ids.length) { checkResult = null; renderChecks(); return; }
            try {
                const res = await fetch('/pc-builder/check-compatibility', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() },
                    body: JSON.stringify({ components: ids }),
                });
                const data = await res.json();
                if (seq === checkSeq && data.success) { checkResult = data; renderChecks(); renderMobileBar(); }
            } catch (e) { /* provjera će se ponoviti pri sljedećoj izmjeni */ }
        }, 120);
        renderChecks();
        renderMobileBar();
    }

    /* ---------- Izbor komponente ---------- */
    const pickerEl = $('#pb-picker');
    const picker = bootstrap.Offcanvas.getOrCreateInstance(pickerEl);
    const list = $('#pb-options'), q = $('#pb-q'), onlyCompat = $('#pb-only-compatible'), sort = $('#pb-sort');
    let currentType = null;

    async function load(type) {
        if (cache[type]) return cache[type];
        const res = await fetch('/pc-builder/components/' + encodeURIComponent(type));
        const data = await res.json();
        cache[type] = data.success ? data.components : [];
        return cache[type];
    }

    async function openPicker(type) {
        currentType = type;
        $('#pb-picker-title').textContent = slotLabel[type] || type;
        $('#pb-picker-sub').textContent = '';
        q.value = '';
        onlyCompat.checked = true;
        list.innerHTML = '<li class="pb-option-loading"><span class="spinner-border spinner-border-sm" aria-hidden="true"></span> Učitavanje…</li>';
        picker.show();
        await load(type);
        renderOptions();
    }

    function renderOptions() {
        const type = currentType;
        const all = cache[type] || [];
        const words = q.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
        let items = all.map((p) => ({ p, why: conflicts(type, p) }))
            .filter(({ p }) => words.every((w) => p.name.toLowerCase().includes(w)));
        const compatibleCount = items.filter((i) => !i.why.length).length;
        if (onlyCompat.checked) items = items.filter((i) => !i.why.length);
        const by = sort.value;
        items.sort((a, b) => by === 'name' ? a.p.name.localeCompare(b.p.name) : (by === 'price-desc' ? b.p.price - a.p.price : a.p.price - b.p.price));

        const hidden = all.length - compatibleCount;
        $('#pb-picker-sub').textContent = `${items.length} ${items.length === 1 ? 'artikal' : 'artikala'} na stanju`
            + (onlyCompat.checked && hidden > 0 ? `, ${hidden} nekompatibilnih skriveno` : '');

        if (!items.length) {
            list.innerHTML = `<li class="pb-option-empty">${all.length ? (onlyCompat.checked && hidden ? 'Nijedan artikal ne odgovara izabranim dijelovima. Isključite „Samo kompatibilne" da vidite sve.' : 'Ništa ne odgovara pretrazi.') : 'Trenutno nema ovih komponenti na stanju.'}</li>`;
            return;
        }
        const selectedId = build[type] && build[type].id;
        list.innerHTML = items.map(({ p, why }) => {
            const ch = chips(type, p), h = hint(type, p), sel = p.id === selectedId;
            return `<li class="pb-option${sel ? ' is-selected' : ''}${why.length ? ' is-conflict' : ''}">
                <img src="${esc(p.image_url)}" alt="" class="pb-thumb" loading="lazy">
                <div class="pb-option-text">
                    <span class="pb-option-name">${esc(p.name)}</span>
                    ${ch.length ? `<span class="pb-chips">${ch.map((c) => `<span>${esc(c)}</span>`).join('')}</span>` : ''}
                    ${why.length ? `<span class="pb-option-why"><i class="fas fa-circle-xmark" aria-hidden="true"></i> Ne odgovara: ${esc(why.join(', '))}</span>` : ''}
                    ${h ? `<span class="pb-option-hint${h.startsWith('slab') ? ' is-warn' : ''}">${esc(h)}</span>` : ''}
                </div>
                <div class="pb-option-side">
                    <span class="pb-option-price">${km(p.price)}</span>
                    <button type="button" class="btn btn-sm ${sel ? 'btn-success' : 'btn-outline-primary'}" data-choose="${p.id}">${sel ? '<i class="fas fa-check" aria-hidden="true"></i> Izabrano' : 'Izaberi'}</button>
                </div>
            </li>`;
        }).join('');
    }

    list.addEventListener('click', (e) => {
        const btn = e.target.closest('[data-choose]');
        if (!btn) return;
        const part = (cache[currentType] || []).find((p) => p.id === parseInt(btn.dataset.choose, 10));
        if (!part) return;
        build[currentType] = part;
        refresh();
        picker.hide();
    });
    q.addEventListener('input', renderOptions);
    onlyCompat.addEventListener('change', renderOptions);
    sort.addEventListener('change', renderOptions);
    pickerEl.addEventListener('shown.bs.offcanvas', () => { if (window.matchMedia('(pointer: fine)').matches) q.focus(); });

    document.addEventListener('click', (e) => {
        const pick = e.target.closest('[data-pick]');
        if (pick && !pick.closest('#pb-picker')) { openPicker(pick.dataset.pick); return; }
        const rm = e.target.closest('[data-remove]');
        if (rm) { delete build[rm.dataset.remove]; refresh(); }
    });

    $('#pb-reset').addEventListener('click', () => {
        if (!confirm('Ukloniti sve izabrane komponente?')) return;
        build = {}; refresh();
    });

    /* ---------- Korpa ---------- */
    $('#pb-cart').addEventListener('click', async () => {
        if (!cfg.loggedIn) { window.location.href = cfg.loginUrl; return; }
        const btn = $('#pb-cart');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm" aria-hidden="true"></span> Dodajem…';
        for (const part of Object.values(build)) {
            const form = new FormData();
            form.append('product_id', part.id);
            form.append('quantity', 1);
            form.append('csrf_token', csrf());
            // eslint-disable-next-line no-await-in-loop
            await fetch('/interaction/add-to-cart', { method: 'POST', body: form, credentials: 'same-origin', headers: { 'X-Requested-With': 'XMLHttpRequest' } });
        }
        window.location.href = '/cart';
    });

    /* ---------- Čuvanje i učitavanje ---------- */
    const saveModalEl = $('#pb-save-modal');
    const saveBtn = $('#pb-save');
    if (saveBtn) saveBtn.addEventListener('click', () => bootstrap.Modal.getOrCreateInstance(saveModalEl).show());
    if (saveModalEl) saveModalEl.addEventListener('shown.bs.modal', () => $('#pb-save-name').focus());
    const saveForm = $('#pb-save-form');
    if (saveForm) saveForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submit = $('#pb-save-submit');
        submit.disabled = true;
        try {
            const res = await fetch('/pc-builder/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf(), 'X-Requested-With': 'XMLHttpRequest' },
                body: JSON.stringify({
                    name: $('#pb-save-name').value.trim(),
                    description: $('#pb-save-desc').value.trim(),
                    is_public: $('#pb-save-public').checked,
                    components: Object.values(build).map((p) => p.id),
                }),
            });
            const data = await res.json();
            if (!data.success) throw new Error(data.message);
            window.location.reload();
        } catch (err) {
            submit.disabled = false;
            if (window.showModalAlert) window.showModalAlert(err.message || 'Konfiguracija nije sačuvana.', 'Greška', 'danger');
        }
    });

    $$('[data-load-build]').forEach((btn) => btn.addEventListener('click', async () => {
        const res = await fetch('/pc-builder/load/' + btn.dataset.loadBuild);
        const data = await res.json();
        if (!data.success) { if (window.showModalAlert) window.showModalAlert(data.message, 'Greška', 'danger'); return; }
        build = {};
        data.build.components.forEach((c) => { if (c.component_type) build[c.component_type] = c; });
        refresh();
    }));

    // Konfiguracija sačuvana prije izmjena na sajtu: izbaci dijelove kojih više nema u ponudi
    (async () => {
        const types = Object.keys(build);
        for (const type of types) {
            // eslint-disable-next-line no-await-in-loop
            const fresh = (await load(type)).find((p) => p.id === build[type].id);
            if (fresh) build[type] = fresh; else delete build[type];
        }
        if (types.length) refresh();
    })();

    refresh();
})();
