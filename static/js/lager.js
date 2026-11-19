/* Lager: navigacija po kategorijama, pretraga, količine i izmjena artikla bez ponovnog učitavanja. */
(function () {
    'use strict';

    const cfg = window.LAGER || {};
    const root = document.getElementById('lg');
    if (!root) return;

    const store = {
        get(key, fallback) { try { const v = localStorage.getItem(key); return v === null ? fallback : v; } catch (e) { return fallback; } },
        set(key, value) { try { localStorage.setItem(key, value); } catch (e) { /* privatni prozor */ } },
    };

    const $ = (sel, el) => (el || document).querySelector(sel);
    const $$ = (sel, el) => Array.from((el || document).querySelectorAll(sel));

    const km = (n) => (Number(n) || 0).toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' KM';
    const parsePrice = (s) => parseFloat(String(s || '0').replace(',', '.')) || 0;
    // Baza čuva UTC; prikazujemo lokalno vrijeme pregledača
    const localTime = (iso, withYear) => {
        if (!iso) return '';
        const d = new Date(iso);
        if (isNaN(d)) return '';
        const pad = (n) => String(n).padStart(2, '0');
        return pad(d.getDate()) + '.' + pad(d.getMonth() + 1) + '.' + (withYear ? d.getFullYear() + '.' : '') + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
    };
    const csrf = () => (document.querySelector('meta[name="csrf-token"]') || {}).content || '';

    const panes = $$('.lg-pane');
    const catButtons = $$('.lg-cat');
    const search = $('#lg-q');
    const zeroToggle = $('#lg-zero');
    const markupInput = $('#lg-markup');
    const noResult = $('#lg-noresult');
    const allRows = $$('.lg-main .lg-pane[data-pane-id]:not([data-pane-id="pregled"]):not([data-pane-id="nedavno"]) .lg-row');

    let current = null;

    /* ---------- Prodajna cijena ---------- */
    function markup() { return parseFloat(markupInput.value) || 0; }
    function saleFor(price) { return price * (1 + markup() / 100); }
    function updateSale(row) {
        const cell = $('.lg-sale', row);
        if (cell) cell.textContent = km(saleFor(parseFloat(row.dataset.price)));
    }
    function updateAllSales() {
        $$('.lg-row').forEach(updateSale);
        $$('.lg-markup-label').forEach((el) => { el.textContent = '+' + markup() + '%'; });
    }

    markupInput.value = store.get('lg-markup', markupInput.value);
    markupInput.addEventListener('input', () => { store.set('lg-markup', markupInput.value); updateAllSales(); });

    /* ---------- Prikaz redova (bez stanja / pretraga) ---------- */
    function showZero() { return !!(zeroToggle && zeroToggle.checked); }
    function query() { return (search.value || '').trim().toLowerCase(); }

    function rowVisible(row, q) {
        // Artikli bez stanja samo uz prekidač (nedavno rasprodati su i dalje u "Nedavno izmijenjeno")
        if (!showZero() && row.dataset.stock === '0') return false;
        if (!q) return true;
        return q.split(/\s+/).every((word) => row.dataset.q.includes(word));
    }

    function refreshGroups(pane) {
        let paneVisible = 0;
        $$('[data-group]', pane).forEach((group) => {
            const rows = $$('.lg-row', group);
            const shown = rows.filter((r) => !r.hidden).length;
            paneVisible += shown;
            const counter = $('[data-group-count]', group);
            if (counter) counter.textContent = shown || '';
            const empty = $('.lg-group-empty', group);
            const searching = !!query();
            group.hidden = searching && shown === 0;
            if (empty) empty.hidden = searching || shown > 0;
            $('table', group).hidden = shown === 0;
        });
        return paneVisible;
    }

    function applyFilters() {
        const q = query();
        allRows.forEach((row) => { row.hidden = !rowVisible(row, q); });
        root.classList.toggle('is-searching', !!q);

        if (q) {
            // Rezultati iz svih kategorija, grupisani po kategoriji
            let total = 0;
            panes.forEach((pane) => {
                const id = pane.dataset.paneId;
                if (id === 'pregled' || id === 'nedavno') { pane.hidden = true; return; }
                const n = refreshGroups(pane);
                total += n;
                pane.hidden = n === 0;
            });
            noResult.hidden = total > 0;
            catButtons.forEach((b) => b.classList.remove('is-active'));
        } else {
            noResult.hidden = true;
            panes.forEach((pane) => {
                const id = pane.dataset.paneId;
                if (id !== 'pregled' && id !== 'nedavno') refreshGroups(pane);
            });
            show(current || 'pregled', false);
        }
    }

    /* ---------- Kategorije ---------- */
    function show(id, remember) {
        if (!$(`.lg-pane[data-pane-id="${CSS.escape(id)}"]`)) id = 'pregled';
        current = id;
        if (query()) { search.value = ''; root.classList.remove('is-searching'); allRows.forEach((r) => { r.hidden = !rowVisible(r, ''); }); }
        panes.forEach((pane) => { pane.hidden = pane.dataset.paneId !== id; });
        catButtons.forEach((b) => {
            const active = b.dataset.pane === id;
            b.classList.toggle('is-active', active);
            if (active) b.setAttribute('aria-current', 'true'); else b.removeAttribute('aria-current');
        });
        // Na telefonu je lista kategorija vodoravna: aktivnu dovedi u vidno polje
        const activeBtn = $('.lg-cat.is-active');
        const bar = activeBtn && activeBtn.parentElement;
        if (bar && bar.scrollWidth > bar.clientWidth) {
            bar.scrollTo({ left: activeBtn.offsetLeft - bar.clientWidth / 2 + activeBtn.offsetWidth / 2, behavior: remember === false ? 'auto' : 'smooth' });
        }
        noResult.hidden = true;
        if (remember !== false) {
            store.set('lg-tab', id);
            const url = new URL(window.location.href);
            if (id === 'pregled') url.searchParams.delete('active_tab'); else url.searchParams.set('active_tab', id);
            url.searchParams.delete('search');
            history.replaceState(null, '', url);
        }
    }

    catButtons.forEach((b) => b.addEventListener('click', () => {
        show(b.dataset.pane);
        if (window.matchMedia('(max-width: 991.98px)').matches) {
            const pane = $(`.lg-pane[data-pane-id="${CSS.escape(b.dataset.pane)}"]`);
            if (pane) pane.scrollIntoView({ block: 'start' });
        }
    }));
    $$('[data-goto]').forEach((b) => b.addEventListener('click', () => show(b.dataset.goto)));

    let searchTimer;
    search.addEventListener('input', () => { clearTimeout(searchTimer); searchTimer = setTimeout(applyFilters, 80); });
    search.addEventListener('keydown', (e) => { if (e.key === 'Escape') { search.value = ''; applyFilters(); } });
    document.addEventListener('keydown', (e) => {
        const tag = (document.activeElement && document.activeElement.tagName || '').toLowerCase();
        if (e.key === '/' && !['input', 'textarea', 'select'].includes(tag)) { e.preventDefault(); search.focus(); search.select(); }
    });

    if (zeroToggle) {
        zeroToggle.checked = store.get('lg-zero', '0') === '1';
        zeroToggle.addEventListener('change', () => { store.set('lg-zero', zeroToggle.checked ? '1' : '0'); applyFilters(); });
    }

    /* ---------- Nedavno izmijenjeno (kopije redova) ---------- */
    const recentBody = $('#lg-recent');
    function buildRecent() {
        recentBody.replaceChildren();
        (cfg.recentIds || []).forEach((id) => {
            const src = $(`.lg-main .lg-row[data-id="${id}"]`);
            if (!src) return;
            const copy = src.cloneNode(true);
            copy.hidden = false;
            copy.classList.add('is-recent-copy');
            const name = $('.lg-name', copy);
            const pane = src.closest('.lg-pane');
            if (name && pane) {
                const where = document.createElement('span');
                where.className = 'lg-where';
                where.textContent = pane.dataset.catName + (copy.dataset.updated ? ', ' + localTime(copy.dataset.updated, true) : '');
                name.after(where);
            }
            recentBody.appendChild(copy);
        });
    }

    /* ---------- Vrijednost i brojači ---------- */
    function recalc(slug) {
        const rows = allRows.filter((r) => r.dataset.slug === slug);
        let value = 0, inStock = 0;
        rows.forEach((r) => {
            const stock = parseInt(r.dataset.stock, 10) || 0;
            if (stock > 0) { inStock += 1; value += stock * parseFloat(r.dataset.price); }
        });
        $$(`[data-count-for="${CSS.escape(slug)}"]`).forEach((el) => { el.textContent = inStock; });
        $$(`[data-value-for="${CSS.escape(slug)}"]`).forEach((el) => { el.textContent = km(value); });
        let grand = 0;
        allRows.forEach((r) => { grand += (parseInt(r.dataset.stock, 10) || 0) * parseFloat(r.dataset.price); });
        const g = $('#lg-grand');
        if (g) g.textContent = km(grand);
    }

    function setStock(id, stock) {
        $$(`.lg-row[data-id="${id}"]`).forEach((r) => {
            r.dataset.stock = String(stock);
            r.classList.toggle('is-zero', stock === 0);
            const q = $('.lg-qty', r);
            if (q) q.textContent = stock;
        });
        const main = $(`.lg-main .lg-pane:not([data-pane-id="nedavno"]) .lg-row[data-id="${id}"]`);
        if (main) recalc(main.dataset.slug);
    }

    /* ---------- Količina −/+ (čuva se odmah) ---------- */
    root.addEventListener('click', async (e) => {
        const btn = e.target.closest('.lg-step-btn');
        if (!btn || !cfg.canEdit) return;
        e.stopPropagation();
        const row = btn.closest('.lg-row');
        const id = row.dataset.id;
        const change = parseInt(btn.dataset.change, 10);
        const before = parseInt(row.dataset.stock, 10) || 0;
        if (before + change < 0) return;
        setStock(id, before + change); // odmah, vraća se ako server odbije
        row.classList.add('is-saving');
        try {
            const res = await fetch(cfg.updateStockUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() },
                body: JSON.stringify({ product_id: parseInt(id, 10), change: change }),
            });
            const data = await res.json();
            if (!res.ok || !data.success) throw new Error(data.message || 'Greška');
            setStock(id, data.new_stock);
            flashRow(row);
        } catch (err) {
            setStock(id, before);
            if (window.showModalAlert) window.showModalAlert('Količina nije sačuvana: ' + err.message, 'Greška', 'danger');
        } finally {
            row.classList.remove('is-saving');
        }
    });

    function flashRow(row) {
        row.classList.remove('is-saved');
        void row.offsetWidth;
        row.classList.add('is-saved');
    }

    /* ---------- Izmjena artikla (bočni panel) ---------- */
    const drawerEl = $('#lg-edit');
    const drawer = drawerEl && window.bootstrap ? bootstrap.Offcanvas.getOrCreateInstance(drawerEl) : null;
    const form = $('#lg-edit-form');

    function openEditor(row) {
        if (!drawer) return;
        const d = row.dataset;
        form.action = cfg.updateDetailsUrl.replace(/0$/, d.id);
        $('#lg-edit-title').textContent = d.name;
        const source = $(`.lg-pane:not([data-pane-id="nedavno"]) .lg-row[data-id="${d.id}"]`);
        const pane = source && source.closest('.lg-pane');
        $('#lg-edit-meta').textContent = (pane ? pane.dataset.catName : '') + (d.updated ? ', izmijenjeno ' + localTime(d.updated, true) : '');
        $('#lg-edit-tab').value = d.slug;
        const set = (sel, v) => { const el = $(sel); if (el) el.value = v; };
        set('#lg-f-name', d.name);
        set('#lg-f-stock', d.stock);
        set('#lg-f-price', String(d.price).replace('.', ','));
        set('#lg-f-res', d.res);
        set('#lg-f-note', d.note);
        const firm = $('#lg-f-firm'); if (firm) firm.checked = d.firm === '1';
        const ro = (sel, v) => { const el = $(sel); if (el) el.textContent = v; };
        ro('#lg-f-stock-ro', d.stock);
        ro('#lg-f-price-ro', km(d.price));
        updateDrawerSale();
        drawer.show();
    }

    function updateDrawerSale() {
        const out = $('#lg-f-sale');
        const price = $('#lg-f-price');
        if (out && price) out.textContent = 'Prodajna uz ' + markup() + '% maržu: ' + km(saleFor(parsePrice(price.value)));
    }
    const priceField = $('#lg-f-price');
    if (priceField) priceField.addEventListener('input', updateDrawerSale);
    if (drawerEl) drawerEl.addEventListener('shown.bs.offcanvas', () => {
        if (!window.matchMedia('(pointer: fine)').matches) return; // na telefonu ne otvaraj tastaturu sama
        const first = $('#lg-f-name') || $('#lg-f-res');
        if (first) first.focus();
    });

    root.addEventListener('click', (e) => {
        if (e.target.closest('.lg-step-btn, a, input, select, textarea, label')) return;
        const row = e.target.closest('.lg-row');
        if (row) openEditor(row);
    });
    root.addEventListener('keydown', (e) => {
        const row = e.target.closest && e.target.closest('.lg-row');
        if (row && e.target === row && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); openEditor(row); }
    });

    /* ---------- Novi artikal / podkategorija ---------- */
    const addModalEl = $('#lg-add');
    const catSelect = $('#lg-a-cat');
    const subSelect = $('#lg-a-sub');

    function fillSubs(catName, selected) {
        if (!subSelect) return;
        subSelect.replaceChildren(new Option('Bez podkategorije', ''));
        ((cfg.subcategories || {})[catName] || []).forEach((name) => subSelect.add(new Option(name, name, false, name === selected)));
    }
    if (catSelect) catSelect.addEventListener('change', () => fillSubs(catSelect.value));

    $$('[data-add-product]').forEach((btn) => btn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (!addModalEl) return;
        const pane = current && $(`.lg-pane[data-pane-id="${CSS.escape(current)}"]`);
        const cat = btn.dataset.addProduct || (pane && pane.dataset.catName) || catSelect.value;
        catSelect.value = cat;
        fillSubs(cat, btn.dataset.sub || '');
        bootstrap.Modal.getOrCreateInstance(addModalEl).show();
    }));
    if (addModalEl) addModalEl.addEventListener('shown.bs.modal', () => $('#lg-a-name').focus());

    const subModalEl = $('#lg-sub');
    $$('[data-add-sub]').forEach((btn) => btn.addEventListener('click', () => {
        $('#lg-s-parent').value = btn.dataset.addSub;
        $('#lg-sub-title').textContent = 'Nova podkategorija u ' + btn.dataset.addSub;
        bootstrap.Modal.getOrCreateInstance(subModalEl).show();
    }));
    if (subModalEl) subModalEl.addEventListener('shown.bs.modal', () => $('#lg-s-name').focus());

    /* ---------- Početno stanje ---------- */
    $$('[data-utc]').forEach((el) => { el.textContent = localTime(el.dataset.utc); });
    // Tačka u bočnoj koloni kod kategorija sa nedavnim izmjenama
    $$('.lg-main .lg-row.is-recent').forEach((r) => {
        const b = $(`.lg-cat[data-pane="${CSS.escape(r.dataset.slug)}"]`);
        if (b) b.classList.add('has-recent');
    });
    buildRecent();
    updateAllSales();
    current = cfg.activeTab || store.get('lg-tab', 'pregled');
    if (search.value) applyFilters(); else { applyFilters(); show(current, false); }
})();
