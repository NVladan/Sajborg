/**
 * Main JavaScript file for PC Parts Shop
 *
 * Flash Message Modal System:
 * --------------------------
 * All user feedback (success, error, info, warning) is displayed using a Bootstrap modal popup.
 * Flash messages are passed from Flask to a hidden div, and this script processes them to show as modals.
 * No inline alerts are rendered in the HTML.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Show flash messages in a modal
    const flashMessagesData = document.getElementById('flash-messages-data');
    if (flashMessagesData && flashMessagesData.children.length > 0) {
        const modal = new bootstrap.Modal(document.getElementById('flash-message-modal'));
        const modalTitle = document.getElementById('flashMessageModalLabel');
        const modalBody = document.getElementById('flash-message-content');

        let messagesHtml = '';
        let category = 'info'; // Default category

        for (const child of flashMessagesData.children) {
            messagesHtml += `<p>${child.dataset.message}</p>`;
            category = child.dataset.category; // Use the last category for title
        }

        // Set modal title based on category
        switch (category) {
            case 'success':
                modalTitle.textContent = 'Uspeh';
                break;
            case 'danger':
            case 'error':
                modalTitle.textContent = 'Greška';
                break;
            case 'warning':
                modalTitle.textContent = 'Upozorenje';
                break;
            default:
                modalTitle.textContent = 'Obaveštenje';
        }

        modalBody.innerHTML = messagesHtml;
        modal.show();
    }

    // Handle quantity +/- buttons
    document.querySelectorAll('.quantity-control').forEach(control => {
        const minusBtn = control.querySelector('.quantity-minus');
        const plusBtn = control.querySelector('.quantity-plus');
        const input = control.querySelector('.quantity-input');

        if (minusBtn && plusBtn && input) {
            minusBtn.addEventListener('click', () => {
                let currentValue = parseInt(input.value);
                if (currentValue > 1) {
                    input.value = currentValue - 1;
                }
            });

            plusBtn.addEventListener('click', () => {
                let currentValue = parseInt(input.value);
                const max = parseInt(input.max);
                if (!max || currentValue < max) {
                    input.value = currentValue + 1;
                }
            });
        }
    });

  // Payment method selection
  const paymentMethodCards = document.querySelectorAll('.payment-method-card');
  const paymentMethodInput = document.getElementById('payment_method');

  if (paymentMethodCards.length > 0 && paymentMethodInput) {
    paymentMethodCards.forEach(function(card) {
      card.addEventListener('click', function() {
        const value = this.dataset.value;

        // Remove selected class from all cards
        paymentMethodCards.forEach(function(c) {
          c.classList.remove('selected');
        });

        // Add selected class to clicked card
        this.classList.add('selected');

        // Set the input value
        paymentMethodInput.value = value;
      });
    });
  }

  // Admin forms - slug generation
  const nameInput = document.getElementById('name');
  const slugInput = document.getElementById('slug');

  if (nameInput && slugInput) {
    nameInput.addEventListener('input', function() {
      // Only generate slug if it's empty or hasn't been manually edited
      if (!slugInput.dataset.edited) {
        // Convert to lowercase, replace spaces with hyphens, remove special chars
        const slug = this.value.toLowerCase()
          .replace(/\s+/g, '-')
          .replace(/[^\w\-]+/g, '')
          .replace(/\-\-+/g, '-')
          .replace(/^-+/, '')
          .replace(/-+$/, '');

        slugInput.value = slug;
      }
    });

    // Mark slug as edited when user changes it
    slugInput.addEventListener('input', function() {
      this.dataset.edited = 'true';
    });
  }

  // JSON formatting for specs
  const specsTextarea = document.getElementById('specs');
  const formatJsonBtn = document.getElementById('format-json-btn');

  if (specsTextarea && formatJsonBtn) {
    formatJsonBtn.addEventListener('click', function(e) {
      e.preventDefault();

      try {
        // Parse and format JSON
        const specs = JSON.parse(specsTextarea.value || '{}');
        const formatted = JSON.stringify(specs, null, 2);
        specsTextarea.value = formatted;
      } catch (error) {
        showModalAlert('Nevažeći JSON format: ' + error.message, 'Greška', 'danger');
      }
    });
  }

  const alertDiv = document.getElementById('compatibility-alert');
  if (alertDiv) {
    const observer = new MutationObserver((mutations) => {
      mutations.forEach(mutation => {
        console.log('compatibility-alert mutated:', mutation);
      });
    });
    observer.observe(alertDiv, { childList: true, subtree: true });
  }

  const searchForm = document.getElementById('search-form');
  // --- Autocomplete for search bar ---
  if (searchForm) {
    const searchInput = searchForm.querySelector('input[type="search"]');
    let suggestionBox = null;
    let lastQuery = '';

    // Create suggestion box
    function createSuggestionBox() {
      if (!suggestionBox) {
        suggestionBox = document.createElement('div');
        suggestionBox.className = 'autocomplete-suggestions';
        suggestionBox.style.position = 'absolute';
        suggestionBox.style.zIndex = '1000';
        suggestionBox.style.background = '#222';
        suggestionBox.style.color = '#fff';
        suggestionBox.style.width = searchInput.offsetWidth + 'px';
        suggestionBox.style.borderRadius = '0 0 0.5rem 0.5rem';
        suggestionBox.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)';
        suggestionBox.style.maxHeight = '260px';
        suggestionBox.style.overflowY = 'auto';
        suggestionBox.style.fontSize = '1rem';
        suggestionBox.style.display = 'none';
        searchInput.parentNode.appendChild(suggestionBox);
      }
    }

    // Position suggestion box
    function positionSuggestionBox() {
      if (!suggestionBox) return;
      const rect = searchInput.getBoundingClientRect();
      suggestionBox.style.top = (searchInput.offsetTop + searchInput.offsetHeight) + 'px';
      suggestionBox.style.left = searchInput.offsetLeft + 'px';
      suggestionBox.style.width = searchInput.offsetWidth + 'px';
    }

    // Show suggestions
    function showSuggestions(suggestions) {
      createSuggestionBox();
      if (!suggestions.length) {
        suggestionBox.style.display = 'none';
        return;
      }
      suggestionBox.innerHTML = '';
      suggestions.forEach(function(suggestion) {
        const item = document.createElement('div');
        item.className = 'autocomplete-suggestion px-3 py-2';
        item.style.cursor = 'pointer';
        item.textContent = suggestion;
        item.addEventListener('mousedown', function(e) {
          e.preventDefault();
          searchInput.value = suggestion;
          suggestionBox.style.display = 'none';
          searchForm.submit();
        });
        suggestionBox.appendChild(item);
      });
      suggestionBox.style.display = 'block';
      positionSuggestionBox();
    }

    // Hide suggestions
    function hideSuggestions() {
      if (suggestionBox) suggestionBox.style.display = 'none';
    }

    // Fetch suggestions
    function fetchSuggestions(query) {
      if (!query) {
        showSuggestions([]);
        return;
      }
      fetch(`/search-suggestions?q=${encodeURIComponent(query)}`)
        .then(res => res.json())
        .then(data => {
          showSuggestions(data);
        });
    }

    searchInput.addEventListener('input', function(e) {
      const query = searchInput.value.trim();
      if (query === lastQuery) return;
      lastQuery = query;
      fetchSuggestions(query);
    });

    searchInput.addEventListener('focus', function() {
      if (searchInput.value.trim()) {
        fetchSuggestions(searchInput.value.trim());
      }
    });

    document.addEventListener('click', function(e) {
      if (!suggestionBox || !suggestionBox.contains(e.target)) {
        hideSuggestions();
      }
    });

    window.addEventListener('resize', positionSuggestionBox);
  }


  // --- Back to Top button ---
  const backToTopBtn = document.getElementById('back-to-top');
  if (backToTopBtn) {
    window.addEventListener('scroll', function() {
      if (window.scrollY > 400) {
        backToTopBtn.classList.add('visible');
      } else {
        backToTopBtn.classList.remove('visible');
      }
    });
    backToTopBtn.addEventListener('click', function() {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // --- Search keyboard shortcut (/ to focus search) ---
  document.addEventListener('keydown', function(e) {
    // Only trigger if not already in an input/textarea/contenteditable
    const tag = document.activeElement.tagName.toLowerCase();
    const isEditable = document.activeElement.isContentEditable;
    if (tag === 'input' || tag === 'textarea' || tag === 'select' || isEditable) return;

    if (e.key === '/') {
      e.preventDefault();
      const searchInput = document.querySelector('#search-form input[type="search"]');
      if (searchInput) searchInput.focus();
    }
  });

  // --- Cookie Consent Banner ---
  const cookieBanner = document.getElementById('cookie-consent-banner');
  const cookieAcceptBtn = document.getElementById('cookie-accept-btn');
  if (cookieBanner && !localStorage.getItem('cookieConsent')) {
    setTimeout(function() { cookieBanner.classList.add('cc-visible'); }, 800);
  }
  if (cookieAcceptBtn) {
    cookieAcceptBtn.addEventListener('click', function() {
      localStorage.setItem('cookieConsent', 'accepted');
      cookieBanner.classList.remove('cc-visible');
      cookieBanner.classList.add('cc-hiding');
    });
  }
});

/**
 * Format price with currency
 * @param {number} price - The price value
 * @param {string} currency - Currency code (default: 'BAM')
 * @returns {string} Formatted price with currency symbol
 */
function formatPrice(price, currency = 'BAM') {
  if (currency === 'BAM') {
    return price.toFixed(2) + ' KM';
  } else if (currency === 'EUR') {
    return '€' + price.toFixed(2);
  }
  return price.toFixed(2);
}

/**
 * Handle subscription form submission with AJAX
 * @param {HTMLFormElement} form - The subscription form element
 */
function subscribeNewsletter(form) {
  // Get form data
  const formData = new FormData(form);

  // Create request
  fetch(form.action, {
    method: 'POST',
    body: formData,
    headers: {
      'X-Requested-With': 'XMLHttpRequest'
    }
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      // Show success message
      showAlert('success', data.message);
      form.reset();
    } else {
      // Show error message
      showAlert('danger', data.message);
    }
  })
  .catch(error => {
    console.error('Greška:', error);
    showAlert('danger', 'Došlo je do greške. Molimo pokušajte ponovo.');
  });

  return false; // Prevent form submission
}

/**
 * Show bootstrap alert
 * @param {string} type - Alert type (success, danger, warning, info)
 * @param {string} message - Alert message
 */
function showAlert(type, message) {
  // Use modal instead of alert
  showFlashModal(type, message);
}

/**
 * Process flash messages from the hidden div and display them as modals
 */
function processFlashMessages() {
  const flashMessagesContainer = document.getElementById('flash-messages-data');
  if (!flashMessagesContainer) return;

  const flashMessages = flashMessagesContainer.querySelectorAll('div[data-category][data-message]');
  if (flashMessages.length === 0) return;

  // Get the first message (we'll show one at a time)
  const firstMessage = flashMessages[0];
  const category = firstMessage.getAttribute('data-category');
  const message = firstMessage.getAttribute('data-message');

  // Show the message as a modal
  showFlashModal(category, message);

  // Remove the processed message
  firstMessage.remove();

  // Set up a listener for when the modal is hidden to show the next message (if any)
  const modalElement = document.getElementById('flash-message-modal');
  if (modalElement) {
    modalElement.addEventListener('hidden.bs.modal', function() {
      // Check if there are more messages to display
      if (flashMessagesContainer.querySelectorAll('div[data-category][data-message]').length > 0) {
        // Process the next message after a short delay
        setTimeout(processFlashMessages, 300);
      }
    });
  }
}

/**
 * Show flash message in a modal popup
 * @param {string} type - Message type (success, danger, warning, info)
 * @param {string} message - Message content
 */
function showFlashModal(type, message) {
  // Get modal elements
  const modalElement = document.getElementById('flash-message-modal');
  const modalContent = document.getElementById('flash-message-content');
  const modalTitle = document.getElementById('flashMessageModalLabel');

  if (!modalElement || !modalContent) return;

  // Set modal content based on message type
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

  // Set modal title and content
  modalTitle.innerHTML = title;
  modalContent.innerHTML = `<div class="d-flex align-items-center">${icon}<span>${message}</span></div>`;

  // Get or create modal instance
  let modal = bootstrap.Modal.getInstance(modalElement);
  if (modal) {
    // If modal is already shown, hide it first then show again
    modal.hide();
    // Wait for hide animation to complete before showing new content
    modalElement.addEventListener('hidden.bs.modal', function showNewModal() {
      modal.show();
      // Remove this event listener after it runs once
      modalElement.removeEventListener('hidden.bs.modal', showNewModal);
    });
  } else {
    // Create new modal instance and show it
    modal = new bootstrap.Modal(modalElement);
    modal.show();
  }

  // Ensure backdrop is cleaned up when modal is closed
  modalElement.addEventListener('hidden.bs.modal', function cleanupBackdrop() {
    // Remove any lingering backdrops
    const backdrops = document.querySelectorAll('.modal-backdrop');
    backdrops.forEach(backdrop => backdrop.remove());
    // Remove modal-open class from body
    document.body.classList.remove('modal-open');
    // Reset body padding
    document.body.style.paddingRight = '';
    // Remove this event listener after it runs
    modalElement.removeEventListener('hidden.bs.modal', cleanupBackdrop);
  }, { once: true });
}