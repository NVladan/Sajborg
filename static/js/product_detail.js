document.addEventListener('DOMContentLoaded', function() {
    const priceElement = document.getElementById('current-price');
    const warrantyCheckbox = document.getElementById('extended_warranty_checkbox');

    // Provera da li elementi postoje pre izvršavanja logike
    if (!priceElement || !warrantyCheckbox) {
        // Ako je na stranici bez garancije (npr. Polovno) ili ako je HTML neispravan, izlazimo
        return;
    }

    const basePrice = parseFloat(priceElement.dataset.basePrice);
    const currencySymbol = ' KM'; // Valuta je uvek KM

    // Funkcija za ažuriranje cene na osnovu stanja checkboxa
    function updatePrice() {
        if (isNaN(basePrice)) return;

        let newPrice = basePrice;

        if (warrantyCheckbox.checked) {
            // Dodajemo 10% od osnovne cene
            const warrantyCost = basePrice * 0.1;
            newPrice += warrantyCost;
        }

        // Formatiranje cene na dve decimale (koristi se toLocaleString radi lakšeg prikaza)
        const formattedPrice = newPrice.toFixed(2);

        // Ažuriranje prikaza cene
        priceElement.textContent = formattedPrice.replace('.', ',') + currencySymbol;
    }

    // Dodajemo slušaoca događaja (event listener) za promenu stanja checkboxa
    warrantyCheckbox.addEventListener('change', updatePrice);

    // *****************************************************************
    // Funkcionalnost quantity kontrola (ako već nije definisana negde drugde)
    // *****************************************************************
    const quantityMinus = document.querySelector('.quantity-minus');
    const quantityPlus = document.querySelector('.quantity-plus');
    const quantityInput = document.querySelector('.quantity-input');

    if (quantityInput) {
        const maxStock = parseInt(quantityInput.getAttribute('max'));
        const minStock = parseInt(quantityInput.getAttribute('min'));

        if (quantityMinus) {
            quantityMinus.addEventListener('click', function() {
                let currentValue = parseInt(quantityInput.value);
                if (currentValue > minStock) {
                    quantityInput.value = currentValue - 1;
                }
            });
        }

        if (quantityPlus) {
            quantityPlus.addEventListener('click', function() {
                let currentValue = parseInt(quantityInput.value);
                if (currentValue < maxStock) {
                    quantityInput.value = currentValue + 1;
                }
            });
        }
    }
});