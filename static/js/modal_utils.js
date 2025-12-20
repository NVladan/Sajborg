/**
 * Modal Utilities
 * Reusable modal dialogs for alerts and confirmations
 */

/**
 * Show a modal alert dialog
 * @param {string} message - The message to display
 * @param {string} title - The modal title (default: 'Obavještenje')
 * @param {string} type - The type of alert: 'info', 'success', 'warning', 'danger' (default: 'info')
 */
function showModalAlert(message, title = 'Obavještenje', type = 'info') {
  // Remove any existing alert modals
  const existingModal = document.getElementById('globalAlertModal');
  if (existingModal) {
    existingModal.remove();
  }

  // Icon mapping based on type
  const icons = {
    info: '<i class="fas fa-info-circle text-info"></i>',
    success: '<i class="fas fa-check-circle text-success"></i>',
    warning: '<i class="fas fa-exclamation-triangle text-warning"></i>',
    danger: '<i class="fas fa-times-circle text-danger"></i>',
    error: '<i class="fas fa-times-circle text-danger"></i>'
  };

  const icon = icons[type] || icons.info;

  // Create modal HTML
  const modalHTML = `
    <div class="modal fade" id="globalAlertModal" tabindex="-1" aria-labelledby="globalAlertModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header border-0">
            <h5 class="modal-title" id="globalAlertModalLabel">
              ${icon} ${title}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            ${message}
          </div>
          <div class="modal-footer border-0">
            <button type="button" class="btn btn-primary" data-bs-dismiss="modal">U redu</button>
          </div>
        </div>
      </div>
    </div>
  `;

  // Add modal to body
  document.body.insertAdjacentHTML('beforeend', modalHTML);

  // Show modal
  const modalElement = document.getElementById('globalAlertModal');
  const modal = new bootstrap.Modal(modalElement);
  modal.show();

  // Remove modal from DOM after it's hidden
  modalElement.addEventListener('hidden.bs.modal', function () {
    modalElement.remove();
  });
}

/**
 * Show a modal confirmation dialog
 * @param {string} message - The confirmation message
 * @param {Function} onConfirm - Callback function to execute if user confirms
 * @param {Function} onCancel - Callback function to execute if user cancels (optional)
 * @param {string} title - The modal title (default: 'Potvrda')
 * @param {string} confirmText - The confirm button text (default: 'Potvrdi')
 * @param {string} cancelText - The cancel button text (default: 'Otkaži')
 */
function showModalConfirm(message, onConfirm, onCancel = null, title = 'Potvrda', confirmText = 'Potvrdi', cancelText = 'Otkaži') {
  // Remove any existing confirm modals
  const existingModal = document.getElementById('globalConfirmModal');
  if (existingModal) {
    existingModal.remove();
  }

  // Create modal HTML
  const modalHTML = `
    <div class="modal fade" id="globalConfirmModal" tabindex="-1" aria-labelledby="globalConfirmModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header border-0">
            <h5 class="modal-title" id="globalConfirmModalLabel">
              <i class="fas fa-question-circle text-warning"></i> ${title}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            ${message}
          </div>
          <div class="modal-footer border-0">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" id="confirmCancelBtn">${cancelText}</button>
            <button type="button" class="btn btn-danger" id="confirmOkBtn">${confirmText}</button>
          </div>
        </div>
      </div>
    </div>
  `;

  // Add modal to body
  document.body.insertAdjacentHTML('beforeend', modalHTML);

  // Show modal
  const modalElement = document.getElementById('globalConfirmModal');
  const modal = new bootstrap.Modal(modalElement);
  modal.show();

  // Attach event handlers
  const confirmBtn = document.getElementById('confirmOkBtn');
  const cancelBtn = document.getElementById('confirmCancelBtn');

  confirmBtn.addEventListener('click', function () {
    modal.hide();
    if (typeof onConfirm === 'function') {
      onConfirm();
    }
  });

  if (onCancel) {
    cancelBtn.addEventListener('click', function () {
      modal.hide();
      if (typeof onCancel === 'function') {
        onCancel();
      }
    });
  }

  // Remove modal from DOM after it's hidden
  modalElement.addEventListener('hidden.bs.modal', function () {
    modalElement.remove();
  });
}

/**
 * Helper function to replace form's onsubmit confirm with modal
 * @param {HTMLFormElement} form - The form element
 * @param {string} message - The confirmation message
 */
function confirmFormSubmit(form, message) {
  // Prevent default submit
  event.preventDefault();

  // Show modal confirmation
  showModalConfirm(
    message,
    function () {
      // On confirm, submit the form
      form.submit();
    },
    null,
    'Potvrda',
    'Da',
    'Ne'
  );

  return false;
}

/**
 * Replace all confirm() calls in onclick attributes with modal confirms
 * This should be called on page load
 */
function initializeModalConfirms() {
  // Find all elements with onclick containing confirm()
  const elements = document.querySelectorAll('[onclick*="confirm"]');

  elements.forEach(element => {
    const onclickAttr = element.getAttribute('onclick');

    // Extract confirm message using regex
    const confirmMatch = onclickAttr.match(/confirm\s*\(\s*['"`](.+?)['"`]\s*\)/);

    if (confirmMatch) {
      const message = confirmMatch[1];

      // Store original onclick
      const originalOnclick = onclickAttr;

      // Remove onclick attribute
      element.removeAttribute('onclick');

      // Add new click handler
      element.addEventListener('click', function(e) {
        e.preventDefault();

        // Show modal confirmation
        showModalConfirm(
          message,
          function() {
            // On confirm, execute original action
            // Check if it's a form submission
            if (element.tagName === 'BUTTON' && element.type === 'submit') {
              const form = element.closest('form');
              if (form) {
                form.submit();
              }
            } else {
              // Execute the code after confirm
              const codeAfterConfirm = originalOnclick.replace(/if\s*\(\s*confirm\s*\([^)]+\)\s*\)\s*\{?\s*/, '').replace(/\}?\s*$/, '');
              try {
                eval(codeAfterConfirm);
              } catch (error) {
                console.error('Error executing onclick code:', error);
              }
            }
          },
          null,
          'Potvrda',
          'Da',
          'Ne'
        );
      });
    }
  });

  // Find all forms with onsubmit containing confirm()
  const forms = document.querySelectorAll('form[onsubmit*="confirm"]');

  forms.forEach(form => {
    const onsubmitAttr = form.getAttribute('onsubmit');

    // Extract confirm message
    const confirmMatch = onsubmitAttr.match(/confirm\s*\(\s*['"`](.+?)['"`]\s*\)/);

    if (confirmMatch) {
      const message = confirmMatch[1];

      // Remove onsubmit attribute
      form.removeAttribute('onsubmit');

      // Add new submit handler
      form.addEventListener('submit', function(e) {
        e.preventDefault();

        showModalConfirm(
          message,
          function() {
            // Remove this event listener to avoid infinite loop
            form.removeEventListener('submit', arguments.callee);
            form.submit();
          },
          null,
          'Potvrda',
          'Da',
          'Ne'
        );
      });
    }
  });
}

// Auto-initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeModalConfirms);
} else {
  initializeModalConfirms();
}
