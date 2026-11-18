/* Prodavnica: brzo dodavanje u korpu, stranica proizvoda, korpa. */
(function () {
    'use strict';

    const $ = (sel, el) => (el || document).querySelector(sel);
    const $$ = (sel, el) => Array.from((el || document).querySelectorAll(sel));
    const csrf = () => (document.querySelector('meta[name="csrf-token"]') || {}).content || '';
    const km = (n) => (Number(n) || 0).toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' KM';

    // Uspjeh: kratki toast koji sam nestane; greška: modal koji se mora zatvoriti
    function toast(message, type) {
        if (type !== 'danger' && window.showFlashToast && window.showFlashToast(type, message)) return;
        if (window.showModalAlert) window.showModalAlert(message, type === 'danger' ? 'Greška' : 'Obavještenje', type);
    }

    // Brojač u ikonici korpe u headeru
    function bumpCartBadge(by) {
        const link = document.querySelector('.navbar a[href$="/cart"]');
        if (!link) return;
        let badge = link.querySelector('.cart-badge');
        if (!badge) {
            badge = document.createElement('span');
            badge.className = 'position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger cart-badge';
            badge.textContent = '0';
            link.appendChild(badge);
        }
        badge.textContent = String((parseInt(badge.textContent, 10) || 0) + by);
    }

    async function postForm(form) {
        const res = await fetch(form.action, {
            method: 'POST',
            body: new FormData(form),
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            credentials: 'same-origin',
        });
        return res.json();
    }

    /* ---------- Prijava / registracija ---------- */
    $$('[data-toggle-password]').forEach((btn) => btn.addEventListener('click', () => {
        const input = document.getElementById(btn.dataset.togglePassword);
        const show = input.type === 'password';
        input.type = show ? 'text' : 'password';
        btn.setAttribute('aria-pressed', show ? 'true' : 'false');
        btn.setAttribute('aria-label', show ? 'Sakrij lozinku' : 'Prikaži lozinku');
        btn.innerHTML = `<i class="fas ${show ? 'fa-eye-slash' : 'fa-eye'}" aria-hidden="true"></i>`;
    }));

    const rules = $('#sh-pass-rules');
    if (rules) {
        const pass = $('#password');
        const tests = { len: (v) => v.length >= 8, upper: (v) => /[A-Z]/.test(v), lower: (v) => /[a-z]/.test(v), digit: (v) => /[0-9]/.test(v) };
        const check = () => $$('li', rules).forEach((li) => li.classList.toggle('is-ok', tests[li.dataset.rule](pass.value)));
        pass.addEventListener('input', check);
        check();
    }

    /* ---------- Tabovi u profilu ---------- */
    const tabs = $$('.sh-tabs [data-tab]');
    if (tabs.length) {
        const show = (id, push) => {
            if (!document.getElementById('pane-' + id)) id = tabs[0].dataset.tab;
            tabs.forEach((t) => {
                const on = t.dataset.tab === id;
                t.classList.toggle('is-active', on);
                t.setAttribute('aria-selected', on ? 'true' : 'false');
            });
            $$('.sh-tab-pane').forEach((p) => { p.hidden = p.id !== 'pane-' + id; });
            if (push) history.replaceState(null, '', '#' + id);
        };
        tabs.forEach((t) => t.addEventListener('click', (e) => { e.preventDefault(); show(t.dataset.tab, true); }));
        // Forma sa greškom ostaje otvorena na svom tabu
        const withError = $('.sh-tab-pane .is-invalid');
        // Sekcije imaju id "pane-…", pa hash (#dostava) ne skroluje stranicu ispod tabova
        show(withError ? withError.closest('.sh-tab-pane').id.replace('pane-', '') : location.hash.slice(1), false);
    }

    /* ---------- Profil: etiketa adrese uživo ---------- */
    const shipForm = $('#sh-ship-form');
    if (shipForm) {
        const val = (id) => ((document.getElementById(id) || {}).value || '').trim();
        const required = ['first_name', 'last_name', 'address', 'city', 'phone_number'];
        const status = $('#sh-ship-status');
        const render = () => {
            $$('[data-preview]').forEach((el) => {
                const text = el.dataset.preview.split(' ').map(val).filter(Boolean).join(' ');
                el.textContent = text || el.dataset.empty;
                el.classList.toggle('is-empty', !text);
            });
            const missing = required.filter((id) => !val(id)).length;
            status.className = 'sh-ship-status ' + (missing ? 'is-todo' : 'is-ok');
            status.innerHTML = missing
                ? `<i class="fas fa-circle-exclamation" aria-hidden="true"></i> Još ${missing} ${missing === 1 ? 'polje' : (missing < 5 ? 'polja' : 'polja')} do brze narudžbe`
                : '<i class="fas fa-circle-check" aria-hidden="true"></i> Spremno za brzu narudžbu';
        };
        shipForm.addEventListener('input', render);
        render();
    }

    /* ---------- Traka kategorija: aktivna kategorija u vidnom polju ---------- */
    const activeCat = $('.sh-cats .is-active');
    if (activeCat && activeCat.parentElement.scrollWidth > activeCat.parentElement.clientWidth) {
        const bar = activeCat.parentElement;
        bar.scrollLeft = activeCat.offsetLeft - bar.clientWidth / 2 + activeCat.offsetWidth / 2;
    }

    /* ---------- Brzo dodavanje sa kartice ---------- */
    document.addEventListener('submit', async (e) => {
        const form = e.target.closest('.sh-quick-add');
        if (!form) return;
        e.preventDefault();
        const btn = form.querySelector('button');
        btn.disabled = true;
        try {
            const data = await postForm(form);
            if (!data.success) throw new Error(data.message);
            btn.classList.add('is-done');
            btn.innerHTML = '<i class="fas fa-check" aria-hidden="true"></i>';
            bumpCartBadge(1);
            toast(data.message, 'success');
            setTimeout(() => {
                btn.classList.remove('is-done');
                btn.innerHTML = '<i class="fas fa-cart-plus" aria-hidden="true"></i>';
                btn.disabled = false;
            }, 1600);
        } catch (err) {
            btn.disabled = false;
            toast(err.message || 'Proizvod nije dodat u korpu.', 'danger');
        }
    });

    /* ---------- Količina (−/+) ---------- */
    function setupQty(box, onChange) {
        const input = $('input', box);
        const minus = $('[data-step="-1"]', box), plus = $('[data-step="1"]', box);
        const min = parseInt(input.min || '1', 10), max = parseInt(input.max || '999', 10);
        const sync = () => {
            let v = parseInt(input.value, 10);
            if (isNaN(v)) v = min;
            v = Math.max(min, Math.min(max, v));
            input.value = v;
            minus.disabled = v <= min;
            plus.disabled = v >= max;
        };
        minus.addEventListener('click', () => { input.value = parseInt(input.value, 10) - 1; sync(); if (onChange) onChange(); });
        plus.addEventListener('click', () => { input.value = parseInt(input.value, 10) + 1; sync(); if (onChange) onChange(); });
        input.addEventListener('change', () => { sync(); if (onChange) onChange(); });
        sync();
    }

    /* ---------- Stranica proizvoda ---------- */
    const main = $('#sh-main-img');
    $$('.sh-thumb').forEach((thumb) => thumb.addEventListener('click', () => {
        main.src = thumb.dataset.src;
        $$('.sh-thumb').forEach((t) => { t.classList.toggle('is-active', t === thumb); t.setAttribute('aria-pressed', t === thumb ? 'true' : 'false'); });
    }));

    const buyForm = $('#sh-buy-form');
    if (buyForm) {
        const priceEl = $('#sh-price');
        const base = parseFloat(priceEl.dataset.base);
        const warranty = $('#sh-warranty');
        const qtyBox = $('.sh-qty', buyForm);
        const update = () => {
            const qty = parseInt($('input', qtyBox).value, 10) || 1;
            const unit = base * (warranty && warranty.checked ? 1.1 : 1);
            priceEl.textContent = km(unit * qty);
        };
        setupQty(qtyBox, update);
        if (warranty) warranty.addEventListener('change', update);

        buyForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = $('button[type=submit]', buyForm);
            const label = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm" aria-hidden="true"></span> Dodajem…';
            try {
                const data = await postForm(buyForm);
                if (!data.success) throw new Error(data.message);
                bumpCartBadge(parseInt($('input', qtyBox).value, 10) || 1);
                btn.innerHTML = '<i class="fas fa-check" aria-hidden="true"></i> Dodato u korpu';
                $('#sh-after-add').hidden = false;
            } catch (err) {
                btn.innerHTML = label;
                toast(err.message || 'Proizvod nije dodat u korpu.', 'danger');
            } finally {
                btn.disabled = false;
            }
        });
    }

    // Ocjena zvjezdicama u formi za recenziju
    const stars = $('.sh-star-input');
    if (stars) {
        const field = $('#' + stars.dataset.field);
        const paint = (n) => $$('button', stars).forEach((b, i) => {
            b.classList.toggle('is-on', i < n);
            b.setAttribute('aria-checked', i + 1 === n ? 'true' : 'false');
        });
        $$('button', stars).forEach((b, i) => b.addEventListener('click', () => { field.value = i + 1; paint(i + 1); }));
        paint(parseInt(field.value, 10) || 5);
    }

    /* ---------- Korpa ---------- */
    const cart = $('#sh-cart');
    if (cart) {
        let timer;
        const lines = () => $$('.sh-line', cart);

        const save = () => {
            clearTimeout(timer);
            timer = setTimeout(async () => {
                const payload = {};
                lines().forEach((line) => {
                    const warranty = $('.sh-line-warranty input', line);
                    payload[line.dataset.id] = {
                        quantity: parseInt($('.sh-qty input', line).value, 10) || 1,
                        extended_warranty: warranty ? warranty.checked : false,
                    };
                    line.classList.add('is-saving');
                });
                try {
                    const res = await fetch(cart.dataset.updateUrl, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf(), 'X-Requested-With': 'XMLHttpRequest' },
                        body: JSON.stringify(payload),
                    });
                    const data = await res.json();
                    if (!data.success) throw new Error(data.message);
                    $('#sh-subtotal').textContent = km(data.subtotal);
                    $('#sh-shipping').textContent = km(data.shipping_cost);
                    $('#sh-total').textContent = km(data.total);
                } catch (err) {
                    toast(err.message || 'Korpa nije sačuvana.', 'danger');
                    setTimeout(() => window.location.reload(), 1500);
                } finally {
                    lines().forEach((l) => l.classList.remove('is-saving'));
                }
            }, 350);
        };

        const lineTotal = (line) => {
            const qty = parseInt($('.sh-qty input', line).value, 10) || 1;
            const warranty = $('.sh-line-warranty input', line);
            const unit = parseFloat(line.dataset.price) * (warranty && warranty.checked ? 1.1 : 1);
            $('.sh-line-total', line).textContent = km(unit * qty);
        };

        lines().forEach((line) => {
            setupQty($('.sh-qty', line), () => { lineTotal(line); save(); });
            const warranty = $('.sh-line-warranty input', line);
            if (warranty) warranty.addEventListener('change', () => { lineTotal(line); save(); });
        });

        cart.addEventListener('click', (e) => {
            const btn = e.target.closest('.sh-remove');
            if (!btn) return;
            const name = btn.closest('.sh-line').dataset.name;
            const go = () => {
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = btn.dataset.url;
                form.innerHTML = `<input type="hidden" name="csrf_token" value="${csrf()}">`;
                document.body.appendChild(form);
                form.submit();
            };
            if (window.showModalConfirm) window.showModalConfirm(`Ukloniti „${name}" iz korpe?`, go, null, 'Ukloni iz korpe', 'Ukloni', 'Odustani');
            else if (confirm(`Ukloniti „${name}" iz korpe?`)) go();
        });
    }
})();
