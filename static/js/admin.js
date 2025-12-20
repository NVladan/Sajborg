/**
 * Admin Panel JavaScript functionality
 */

document.addEventListener('DOMContentLoaded', function() {
  // Format JSON button for product specs
  const formatJsonBtn = document.getElementById('format-json-btn');
  const specsTextarea = document.getElementById('specs');

  if (formatJsonBtn && specsTextarea) {
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

  // Auto-generate slug from name
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

  // Product deletion confirmation
  window.confirmDelete = function(productId, productName) {
    const modal = document.getElementById('deleteModal');
    if (modal) {
      const nameSpan = document.getElementById('deleteProductName');
      const deleteForm = document.getElementById('deleteForm');

      nameSpan.textContent = productName;
      deleteForm.action = `/admin/products/delete/${productId}`;

      const deleteModal = new bootstrap.Modal(modal);
      deleteModal.show();
    } else {
      showModalConfirm(
        `Da li ste sigurni da želite da obrišete "${productName}"? Ova akcija se ne može opozvati.`,
        function() {
          const form = document.createElement('form');
          form.method = 'POST';
          form.action = `/admin/products/delete/${productId}`;
          document.body.appendChild(form);
          form.submit();
        },
        null,
        'Potvrda brisanja',
        'Da, obriši',
        'Otkaži'
      );
    }
  };

  // Category deletion confirmation
  window.confirmDeleteCategory = function(categoryId, categoryName) {
    showModalConfirm(
      `Da li ste sigurni da želite da obrišete kategoriju "${categoryName}"? Ova akcija se ne može opozvati.`,
      function() {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/admin/categories/delete/${categoryId}`;
        document.body.appendChild(form);
        form.submit();
      },
      null,
      'Potvrda brisanja',
      'Da, obriši',
      'Otkaži'
    );
  };

  // Order filter form (submit on change)
  const filterForms = document.querySelectorAll('#order-filter-form, #product-filter-form, #user-filter-form');
  filterForms.forEach(function(form) {
    const selectElements = form.querySelectorAll('select');
    selectElements.forEach(function(select) {
      select.addEventListener('change', function() {
        form.submit();
      });
    });
  });

  // Search forms (submit on enter)
  const searchInputs = document.querySelectorAll('input[name="q"]');
  searchInputs.forEach(function(input) {
    input.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        e.target.form.submit();
      }
    });
  });

  // Preview image from URL
  const imageUrlInput = document.getElementById('image_url');
  if (imageUrlInput) {
    const previewContainer = document.createElement('div');
    previewContainer.className = 'mt-2';
    previewContainer.innerHTML = `
      <div class="d-none" id="image-preview-container">
        <label class="form-label">Pregled slike:</label>
        <div class="border p-2 text-center bg-dark">
          <img id="image-preview" class="img-fluid" style="max-height: 200px;" alt="Preview">
        </div>
      </div>
    `;

    imageUrlInput.parentNode.appendChild(previewContainer);

    const previewImg = document.getElementById('image-preview');
    const previewContainer2 = document.getElementById('image-preview-container');

    imageUrlInput.addEventListener('input', function() {
      const url = this.value.trim();
      if (url) {
        previewImg.src = url;
        previewImg.onload = function() {
          previewContainer2.classList.remove('d-none');
        };
        previewImg.onerror = function() {
          previewContainer2.classList.add('d-none');
        };
      } else {
        previewContainer2.classList.add('d-none');
      }
    });

    // Trigger preview for initial value
    if (imageUrlInput.value.trim()) {
      previewImg.src = imageUrlInput.value.trim();
      previewImg.onload = function() {
        previewContainer2.classList.remove('d-none');
      };
    }
  }
});