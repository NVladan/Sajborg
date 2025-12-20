/**
 * Funkcionalnost korpe za kupovinu - Ispravljena verzija
 */

// Globalna funkcija za dobijanje CSRF tokena
function getCsrfToken() {
  const metaTag = document.querySelector('meta[name="csrf-token"]');
  return metaTag ? metaTag.getAttribute('content') : '';
}

// Debounce funkcija da se ne šalje previše zahteva serveru
function debounce(func, delay = 500) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            func.apply(this, args);
        }, delay);
    };
}

document.addEventListener('DOMContentLoaded', function() {
    const cartItemsContainer = document.getElementById('cart-items-container');

    // Debounce-ovana verzija funkcije za ažuriranje korpe
    const debouncedUpdateCart = debounce(updateCart);

    const setupEventListeners = (container) => {
        // Ažuriranje količine i garancije
        const cartItems = container.querySelectorAll('.cart-item');

        cartItems.forEach(function(item) {
            const quantityInput = item.querySelector('.cart-quantity-input');
            const warrantyCheckbox = item.querySelector('.warranty-checkbox');
            const minusBtn = item.querySelector('.quantity-minus');
            const plusBtn = item.querySelector('.quantity-plus');

            const triggerUpdate = () => {
                updateCartItem(quantityInput); // Prvo vizuelno ažuriraj
                debouncedUpdateCart(); // Zatim pošalji na server
            };

            if (quantityInput) {
                quantityInput.addEventListener('change', triggerUpdate);
            }
            if (warrantyCheckbox) {
                warrantyCheckbox.addEventListener('change', triggerUpdate);
            }
            if (minusBtn) {
                minusBtn.addEventListener('click', () => {
                    let currentValue = parseInt(quantityInput.value);
                    if (currentValue > 0) { // Dozvoljavamo smanjenje na 0 za brisanje
                        quantityInput.value = currentValue - 1;
                        triggerUpdate();
                    }
                });
            }
            if (plusBtn) {
                plusBtn.addEventListener('click', () => {
                    let currentValue = parseInt(quantityInput.value);
                    quantityInput.value = currentValue + 1;
                    triggerUpdate();
                });
            }
        });

        // Dugme za ažuriranje korpe (opciono, ali dobra praksa ostaviti ga)
        const updateCartBtn = document.getElementById('update-cart-btn');
        if (updateCartBtn) {
            updateCartBtn.addEventListener('click', function(e) {
                e.preventDefault();
                updateCart();
            });
        }
    };

    if (cartItemsContainer) {
        setupEventListeners(cartItemsContainer);
    }
});


/**
 * Ažuriranje prikaza pojedinačne stavke u korpi (samo vizuelno)
 * @param {HTMLInputElement} input - Element za unos količine
 */
function updateCartItem(input) {
  const itemId = input.dataset.itemId;
  const quantity = parseInt(input.value);
  const price = parseFloat(input.dataset.price);
  const subtotalElement = document.getElementById(`subtotal-${itemId}`);
  const warrantyCheckbox = document.getElementById(`warranty-${itemId}`);
  let finalPrice = price;

  if (warrantyCheckbox && warrantyCheckbox.checked) {
      finalPrice *= 1.1;
  }

  if (subtotalElement) {
    const subtotal = finalPrice * quantity;
    subtotalElement.textContent = formatPrice(subtotal);
  }
}

/**
 * Ažuriranje cele korpe pomoću AJAX-a i slanje podataka na server
 */
function updateCart() {
  const updateBtn = document.getElementById('update-cart-btn');
  if (updateBtn) {
    updateBtn.disabled = true;
    updateBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Ažuriranje...';
  }

  const cartData = {};
  const cartItems = document.querySelectorAll('.cart-item');

  cartItems.forEach(function(item) {
      const quantityInput = item.querySelector('.cart-quantity-input');
      const warrantyInput = item.querySelector('.warranty-checkbox');
      const itemId = quantityInput.dataset.itemId;

      cartData[itemId] = {
          quantity: parseInt(quantityInput.value),
          extended_warranty: warrantyInput ? warrantyInput.checked : false
      };
  });

  fetch('/cart/update', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': getCsrfToken()
      },
      body: JSON.stringify(cartData)
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        const subtotalElement = document.getElementById('cart-subtotal');
        const shippingElement = document.getElementById('shipping-cost');
        const totalElement = document.getElementById('cart-grand-total');

        if (subtotalElement) subtotalElement.textContent = formatPrice(data.subtotal);
        if (shippingElement) shippingElement.textContent = formatPrice(data.shipping_cost);
        if (totalElement) totalElement.textContent = formatPrice(data.total);

        // ### IZMENA JE OVDE - LINIJA ISPOD JE ZAKOMENTARISANA ###
        // showAlert('success', 'Korpa je uspešno ažurirana');

        // Ukloni stavke koje su postavljene na 0
        document.querySelectorAll('.cart-quantity-input').forEach(function(input) {
          if (parseInt(input.value) <= 0) {
            input.closest('.cart-item').remove();
          }
        });

        if (document.querySelectorAll('.cart-item').length === 0) {
            const cartContainer = document.getElementById('cart-items-container');
            cartContainer.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-shopping-cart fa-3x mb-3 text-muted"></i>
                    <h3>Vaša korpa je prazna</h3>
                    <p>Izgleda da još niste dodali nijedan proizvod.</p>
                    <a href="/proizvodi" class="btn btn-primary">Pregledajte proizvode</a>
                </div>
            `;
            document.getElementById('checkout-btn').style.display = 'none';
        }

      } else {
        showAlert('danger', data.message || 'Greška pri ažuriranju korpe');
        // Vrati stranicu u prethodno stanje ako je moguće, ili je osveži
        setTimeout(() => window.location.reload(), 2000);
      }
    })
    .catch(error => {
      console.error('Greška:', error);
      showAlert('danger', 'Došlo je do greške. Molimo pokušajte ponovo.');
    })
    .finally(() => {
        if (updateBtn) {
            updateBtn.disabled = false;
            updateBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Ažuriraj korpu';
        }
    });
}

/**
 * Uklanjanje stavke iz korpe (ostaje isto)
 * @param {number} itemId - ID stavke za uklanjanje
 */
function removeCartItem(itemId) {
  showModalConfirm(
    'Da li ste sigurni da želite da uklonite ovu stavku iz korpe?',
    function() {
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = `/cart/remove/${itemId}`;
      const csrfToken = getCsrfToken();
      if (csrfToken) {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'csrf_token';
        input.value = csrfToken;
        form.appendChild(input);
      }
      document.body.appendChild(form);
      form.submit();
    },
    null,
    'Potvrda',
    'Da, ukloni',
    'Otkaži'
  );
}

// Pomoćne funkcije iz main.js da bi skripta bila samostalna
function formatPrice(price, currency = 'BAM') {
    if (currency === 'BAM') {
        return price.toFixed(2) + ' KM';
    } else if (currency === 'EUR') {
        return '€' + price.toFixed(2);
    }
    return price.toFixed(2);
}

function showAlert(type, message) {
  const modalElement = document.getElementById('flash-message-modal');
  const modalContent = document.getElementById('flash-message-content');
  const modalTitle = document.getElementById('flashMessageModalLabel');
  if (!modalElement || !modalContent) return;
  let icon = '';
  let title = 'Obaveštenje';
  switch(type) {
    case 'success':
      icon = '<i class="fas fa-check-circle text-success me-2"></i>';
      title = 'Uspeh';
      break;
    case 'danger':
      icon = '<i class="fas fa-exclamation-circle text-danger me-2"></i>';
      title = 'Greška';
      break;
    case 'warning':
      icon = '<i class="fas fa-exclamation-triangle text-warning me-2"></i>';
      title = 'Upozorenje';
      break;
    case 'info':
      icon = '<i class="fas fa-info-circle text-info me-2"></i>';
      title = 'Informacija';
      break;
  }
  modalTitle.innerHTML = title;
  modalContent.innerHTML = `<div class="d-flex align-items-center">${icon}<span>${message}</span></div>`;
  const modal = new bootstrap.Modal(modalElement);
  modal.show();
}