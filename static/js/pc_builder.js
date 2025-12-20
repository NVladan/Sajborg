/**
 * PC Builder JavaScript functionality
 */

// Global state for the PC builder
const builderState = {
  components: {}, // Selected components by type
  totalPrice: 0,
  isCompatible: true,
  compatibilityMessages: []
};

// Get CSRF token from meta tag
function getCsrfToken() {
  const metaTag = document.querySelector('meta[name="csrf-token"]');
  if (!metaTag) {
    console.error('CSRF token meta tag not found');
    return null;
  }
  const token = metaTag.getAttribute('content');
  if (!token) {
    console.error('CSRF token is empty');
    return null;
  }
  return token;
}

document.addEventListener('DOMContentLoaded', function() {
  // Initialize PC Builder interface
  initializeBuilder();

  // Save build button
  const saveBuildBtn = document.getElementById('save-build-btn');
  if (saveBuildBtn) {
    saveBuildBtn.addEventListener('click', function() {
      saveBuild();
    });
  }

  // Add all to cart button
  const addAllToCartBtn = document.getElementById('add-all-to-cart-btn');
  if (addAllToCartBtn) {
    addAllToCartBtn.addEventListener('click', function() {
      addAllToCart();
    });
  }

  // Load saved build
  const loadBuildSelect = document.getElementById('load-build-select');
  if (loadBuildSelect) {
    loadBuildSelect.addEventListener('change', function() {
      const buildId = this.value;
      if (buildId) {
        loadBuild(buildId);
      }
    });
  }
});

/**
 * Initialize the PC Builder interface
 */
function initializeBuilder() {
  // Get component type tabs
  const componentTypes = document.querySelectorAll('.component-type-tab');

  // Add click event to component type tabs
  componentTypes.forEach(tab => {
    tab.addEventListener('click', function() {
      const componentType = this.dataset.componentType;
      loadComponentOptions(componentType);
    });
  });

  // Initially load the first component type
  if (componentTypes.length > 0) {
    componentTypes[0].click();
  }

  // Update price display
  updateTotalPrice();
}

/**
 * Load component options for a specific type
 * @param {string} componentType - Type of component to load
 */
function loadComponentOptions(componentType) {
  // Show loading state
  const componentsList = document.getElementById('components-list');
  componentsList.innerHTML = `
    <div class="text-center p-5">
      <div class="spinner-border" role="status">
        <span class="visually-hidden">Učitavanje...</span>
      </div>
      <p class="mt-2">Učitavanje komponenti...</p>
    </div>
  `;

  // Highlight active tab
  document.querySelectorAll('.component-type-tab').forEach(tab => {
    if (tab.dataset.componentType === componentType) {
      tab.classList.add('active');
    } else {
      tab.classList.remove('active');
    }
  });

  // Fetch components via AJAX
  fetch(`/pc-builder/components/${componentType}`)
    .then(response => response.json())
    .then(data => {
      if (data.success && data.components) {
        renderComponentOptions(componentType, data.components);
      } else {
        componentsList.innerHTML = `
          <div class="alert alert-warning" role="alert">
            Neuspešno učitavanje komponenti. ${data.message || ''}
          </div>
        `;
      }
    })
    .catch(error => {
      console.error('Greška:', error);
      componentsList.innerHTML = `
        <div class="alert alert-danger" role="alert">
          Greška pri učitavanju komponenti. Molimo pokušajte ponovo.
        </div>
      `;
    });
}

/**
 * Render component options in the list
 * @param {string} componentType - Type of components
 * @param {Array} components - Array of component objects
 */
function renderComponentOptions(componentType, components) {
  const componentsList = document.getElementById('components-list');

  // Clear previous content
  componentsList.innerHTML = '';

  if (components.length === 0) {
    componentsList.innerHTML = `
      <div class="alert alert-info" role="alert">
        Nema pronađenih ${componentType} komponenti.
      </div>
    `;
    return;
  }

  // Create component cards
  components.forEach(component => {
    const isSelected = builderState.components[componentType] &&
                      builderState.components[componentType].id === component.id;

    const isOutOfStock = component.stock <= 0;

    const componentCard = document.createElement('div');
    componentCard.className = `card mb-3 ${isSelected ? 'border-primary' : ''}`;
    componentCard.innerHTML = `
      <div class="row g-0">
        <div class="col-md-2 text-center">
          <img src="${component.image_url || '/static/img/no-image.svg'}"
               class="img-fluid rounded-start p-2" alt="Komponenta za PC Konfigurator: ${component.name}"
               style="max-height: 100px; object-fit: contain;">
        </div>
        <div class="col-md-8">
          <div class="card-body">
            <h5 class="card-title">${component.name}</h5>
            <p class="card-text">
              ${formatPrice(component.price)}
              ${isOutOfStock ? '<span class="badge bg-danger ms-2">Nema na stanju</span>' : ''}
            </p>
            <p class="card-text"><small class="text-muted">
              ${formatSpecsPreview(component.specs)}
            </small></p>
          </div>
        </div>
        <div class="col-md-2 d-flex align-items-center justify-content-center">
          <button class="btn ${isSelected ? 'btn-danger' : 'btn-primary'} component-select-btn"
                  data-component-id="${component.id}"
                  data-component-type="${componentType}"
                  data-component-name="${component.name}"
                  data-component-price="${component.price}"
                  ${isOutOfStock ? 'disabled' : ''}>
            ${isSelected ? 'Ukloni' : 'Izaberi'}
          </button>
        </div>
      </div>
    `;

    componentsList.appendChild(componentCard);

    // Add click event to select button
    const selectBtn = componentCard.querySelector('.component-select-btn');
    selectBtn.addEventListener('click', function() {
      toggleComponentSelection(this);
    });
  });
}

/**
 * Toggle component selection
 * @param {HTMLElement} button - The select/remove button
 */
function toggleComponentSelection(button) {
  const componentId = parseInt(button.dataset.componentId);
  const componentType = button.dataset.componentType;
  const componentName = button.dataset.componentName;
  const componentPrice = parseFloat(button.dataset.componentPrice);

  if (builderState.components[componentType] &&
      builderState.components[componentType].id === componentId) {
    // Deselect the component
    delete builderState.components[componentType];
    button.textContent = 'Izaberi';
    button.classList.replace('btn-danger', 'btn-primary');
    button.closest('.card').classList.remove('border-primary');
  } else {
    // Select the component
    builderState.components[componentType] = {
      id: componentId,
      name: componentName,
      price: componentPrice
    };
    button.textContent = 'Ukloni';
    button.classList.replace('btn-primary', 'btn-danger');
    button.closest('.card').classList.add('border-primary');

    // Change other selected components of the same type
    document.querySelectorAll(`.component-select-btn[data-component-type="${componentType}"]`).forEach(btn => {
      if (btn !== button && btn.textContent === 'Ukloni') {
        btn.textContent = 'Izaberi';
        btn.classList.replace('btn-danger', 'btn-primary');
        btn.closest('.card').classList.remove('border-primary');
      }
    });
  }

  // Update the build summary
  updateBuildSummary();

  // Check compatibility
  checkCompatibility();

  // Update total price
  updateTotalPrice();
}

/**
 * Update the build summary display
 */
function updateBuildSummary() {
  const summaryList = document.getElementById('build-summary-list');
  if (!summaryList) return;

  // Clear previous content
  summaryList.innerHTML = '';

  // Create list items for each selected component
  for (const componentType in builderState.components) {
    const component = builderState.components[componentType];

    const listItem = document.createElement('li');
    listItem.className = 'list-group-item d-flex justify-content-between align-items-center';
    listItem.innerHTML = `
      <span>
        <strong>${componentType}:</strong> ${component.name}
      </span>
      <span>${formatPrice(component.price)}</span>
    `;

    summaryList.appendChild(listItem);
  }

  // Show empty state if no components selected
  if (Object.keys(builderState.components).length === 0) {
    const emptyItem = document.createElement('li');
    emptyItem.className = 'list-group-item text-center text-muted';
    emptyItem.textContent = 'Nema izabranih komponenti';
    summaryList.appendChild(emptyItem);
  }
}

/**
 * Update the total price display
 */
function updateTotalPrice() {
  // Calculate total price
  let total = 0;
  for (const componentType in builderState.components) {
    total += builderState.components[componentType].price;
  }

  builderState.totalPrice = total;

  // Update display
  const totalElement = document.getElementById('build-total-price');
  if (totalElement) {
    totalElement.textContent = formatPrice(total);
  }
}

/**
 * Check component compatibility
 */
function checkCompatibility() {
  // Get component IDs
  const componentIds = [];
  for (const componentType in builderState.components) {
    componentIds.push(builderState.components[componentType].id);
  }

  // If fewer than 2 components, just show info message and return
  if (componentIds.length < 2) {
    builderState.isCompatible = true;
    builderState.compatibilityMessages = [];
    updateCompatibilityDisplay();
    return;
  }

  // Show loading state (but don't call updateCompatibilityDisplay here)
  const compatibilityAlert = document.getElementById('compatibility-alert');
  if (compatibilityAlert) {
    compatibilityAlert.innerHTML = `
      <div class="alert alert-info">
        <i class="fas fa-sync fa-spin"></i> Provera kompatibilnosti...
      </div>
    `;
  }

  // Send request to check compatibility
  fetch('/pc-builder/check-compatibility', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest'
    },
    beforeSend: function(xhr) {
      const token = getCsrfToken();
      if (token) {
        xhr.setRequestHeader('X-CSRFToken', token);
      }
    },
    body: JSON.stringify({ components: componentIds })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      builderState.isCompatible = data.is_compatible;
      builderState.compatibilityMessages = data.messages || [];
    } else {
      console.error('Greška pri proveri kompatibilnosti:', data.message);
      builderState.isCompatible = false;
      builderState.compatibilityMessages = data.messages || [`Greška pri proveri kompatibilnosti: ${data.message || 'Nepoznata greška'}`];
    }
    updateCompatibilityDisplay();
  })
  .catch(error => {
    console.error('Mrežna greška pri proveri kompatibilnosti:', error);
    builderState.isCompatible = false;
    builderState.compatibilityMessages = ['Greška pri proveri kompatibilnosti: Mrežna ili serverska greška'];
    updateCompatibilityDisplay();
  });
}

/**
 * Update compatibility display
 */
function updateCompatibilityDisplay() {
  const compatibilityAlert = document.getElementById('compatibility-alert');
  if (!compatibilityAlert) return;
  console.log('updateCompatibilityDisplay called', JSON.stringify(builderState));

  let html = '';
  if (Object.keys(builderState.components).length < 2) {
    html = `
      <div class="alert alert-info compatibility-alert-box alert-permanent">
        <i class="fas fa-info-circle"></i> Dodajte još komponenti da biste proverili kompatibilnost.
      </div>
    `;
  } else if (builderState.isCompatible) {
    html = `
      <div class="alert alert-success compatibility-alert-box alert-permanent">
        <i class="fas fa-check-circle"></i> Sve komponente su kompatibilne!
      </div>
    `;
  } else if (builderState.compatibilityMessages && builderState.compatibilityMessages.length > 0) {
    let messageHtml = '';
    builderState.compatibilityMessages.forEach(message => {
      messageHtml += `<li>${message}</li>`;
    });
    html = `
      <div class="alert alert-warning compatibility-alert-box alert-permanent">
        <i class="fas fa-exclamation-triangle"></i> <strong>Problemi sa kompatibilnošću:</strong>
        <ul class="mb-0 mt-2">
          ${messageHtml}
        </ul>
      </div>
    `;
  } else {
    // Fallback: always show something
    html = `
      <div class="alert alert-info compatibility-alert-box alert-permanent">
        <i class="fas fa-info-circle"></i> Dodajte još komponenti da biste proverili kompatibilnost.
      </div>
    `;
  }
  compatibilityAlert.innerHTML = html;
}

/**
 * Format specs preview from JSON string
 * @param {string} specsJson - JSON string of specifications
 * @returns {string} HTML string with key specs
 */
function formatSpecsPreview(specsJson) {
  if (!specsJson) return '';

  try {
    const specs = JSON.parse(specsJson);
    const previewItems = [];

    // Add common specs based on what's available
    if (specs.cores) previewItems.push(`${specs.cores} jezgara`);
    if (specs.threads) previewItems.push(`${specs.threads} niti`);
    if (specs.base_clock) previewItems.push(`${specs.base_clock}`);
    if (specs.memory) previewItems.push(`${specs.memory}`);
    if (specs.capacity) previewItems.push(`${specs.capacity}`);
    if (specs.wattage) previewItems.push(`${specs.wattage}W`);
    if (specs.speed) previewItems.push(`${specs.speed}`);
    if (specs.socket) previewItems.push(`Podnožje: ${specs.socket}`);

    // Limit to 3 items
    return previewItems.slice(0, 3).join(' • ');
  } catch (e) {
    return '';
  }
}

/**
 * Save the current build
 */
function saveBuild() {
  // Check if we have at least one component
  if (Object.keys(builderState.components).length === 0) {
    showAlert('warning', 'Molimo izaberite bar jednu komponentu pre čuvanja');
    return;
  }

  // Open save build modal
  const modal = new bootstrap.Modal(document.getElementById('save-build-modal'));
  modal.show();

  // Handle save form submission
  document.getElementById('save-build-form').onsubmit = function(e) {
    e.preventDefault();

    const buildName = document.getElementById('build-name').value;
    const buildDescription = document.getElementById('build-description').value;
    const isPublic = document.getElementById('build-is-public').checked;

    if (!buildName) {
      showModalAlert('Molimo unesite naziv za Vašu konfiguraciju', 'Upozorenje', 'warning');
      return;
    }

    // Get component IDs
    const componentIds = [];
    for (const componentType in builderState.components) {
      componentIds.push(builderState.components[componentType].id);
    }

    // Create build data
    const buildData = {
      name: buildName,
      description: buildDescription,
      is_public: isPublic,
      components: componentIds
    };

    // Show loading state
    const saveBtn = document.getElementById('save-build-submit');
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Čuvanje...';

    // CSRF token
    const csrfToken = document.querySelector('meta[name="csrf-token"]');

    // Send request to save build
    fetch('/pc-builder/save', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrfToken ? csrfToken.content : ''
      },
      body: JSON.stringify(buildData)
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // Close modal
        modal.hide();

        // Show success message
        showAlert('success', data.message || 'Konfiguracija je uspešno sačuvana!');

        // Refresh page to show the new build (alternative: add to saved builds dropdown)
        setTimeout(() => {
          window.location.reload();
        }, 1500);
      } else {
        // Show error message
        showModalAlert(data.message || 'Greška pri čuvanju konfiguracije', 'Greška', 'danger');
      }

      // Reset button state
      saveBtn.disabled = false;
      saveBtn.innerHTML = 'Sačuvaj Konfiguraciju';
    })
    .catch(error => {
      console.error('Greška:', error);
      showModalAlert('Došlo je do greške. Molimo pokušajte ponovo.', 'Greška', 'danger');

      // Reset button state
      saveBtn.disabled = false;
      saveBtn.innerHTML = 'Sačuvaj Konfiguraciju';
    });
  };
}

/**
 * Load a saved build
 * @param {number} buildId - ID of the build to load
 */
function loadBuild(buildId) {
  // Fetch build data
  fetch(`/pc-builder/load/${buildId}`)
    .then(response => response.json())
    .then(data => {
      if (data.success && data.build) {
        // Clear current selection
        builderState.components = {};

        // Load components into builder state
        data.build.components.forEach(component => {
          builderState.components[component.component_type] = {
            id: component.id,
            name: component.name,
            price: component.price
          };
        });

        // Update UI
        updateBuildSummary();
        updateTotalPrice();
        checkCompatibility();

        // Show success message
        showFlashModal('success', `Konfiguracija "${data.build.name}" je učitana!`);

        // Reload the current component list to show selections
        const activeTab = document.querySelector('.component-type-tab.active');
        if (activeTab) {
          loadComponentOptions(activeTab.dataset.componentType);
        }
      } else {
        showFlashModal('danger', data.message || 'Greška pri učitavanju konfiguracije');
      }
    })
    .catch(error => {
      console.error('Greška:', error);
      showFlashModal('danger', 'Došlo je do greške pri učitavanju konfiguracije');
    });
}

/**
 * Add all components to cart
 */
function addAllToCart() {
  // Check if we have at least one component
  if (Object.keys(builderState.components).length === 0) {
    showAlert('warning', 'Molimo prvo izaberite bar jednu komponentu');
    return;
  }

  // Confirm with modal
  showModalConfirm(
    'Dodaj sve izabrane komponente u korpu?',
    function() {
      // Execute add to cart on confirm
      executeAddAllToCart();
    },
    null,
    'Potvrda',
    'Dodaj u korpu',
    'Otkaži'
  );
}

// Separate function to execute the add to cart logic
function executeAddAllToCart() {
  // Collect all add-to-cart promises
  const addToCartPromises = [];
  const csrfToken = document.querySelector('meta[name="csrf-token"]');

  for (const componentType in builderState.components) {
    const component = builderState.components[componentType];
    const formData = new FormData();
    formData.append('product_id', component.id);
    formData.append('quantity', 1);
    if (csrfToken) {
      formData.append('csrf_token', csrfToken.content);
    }
    addToCartPromises.push(
      fetch('/interaction/add-to-cart', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin'
      })
    );
  }

  Promise.all(addToCartPromises).then(() => {
    window.location.href = '/cart';
  });
}