/**
 * Summernote Rich Text Editor initialization for blog posts
 */

(function() {
    'use strict';

    // Wait for DOM to be ready
    function initEditor() {
        var $summernote = $('#summernote');
        var $loading = $('#editor-loading');

        if ($summernote.length === 0) {
            console.error('Summernote textarea not found');
            return;
        }

        // Check if Summernote is available
        if (typeof $.fn.summernote === 'undefined') {
            console.error('Summernote library not loaded');
            showFallbackEditor();
            return;
        }

        try {
            // Initialize Summernote
            $summernote.summernote({
                placeholder: 'Započnite pisanje Vašeg članka ovde...',
                height: 450,
                minHeight: 400,
                maxHeight: 800,
                focus: false,
                lang: 'sr-RS',
                toolbar: [
                    ['style', ['style']],
                    ['font', ['bold', 'italic', 'underline', 'strikethrough', 'clear']],
                    ['fontsize', ['fontsize']],
                    ['color', ['color']],
                    ['para', ['ul', 'ol', 'paragraph']],
                    ['height', ['height']],
                    ['table', ['table']],
                    ['insert', ['link', 'picture', 'video', 'hr']],
                    ['view', ['fullscreen', 'codeview', 'help']]
                ],
                fontSizes: ['8', '9', '10', '11', '12', '14', '16', '18', '20', '24', '28', '32', '36', '48'],
                styleTags: ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'pre'],
                callbacks: {
                    onInit: function() {
                        // Hide loading indicator and show editor
                        $loading.hide();
                        console.log('Summernote editor initialized successfully');
                    },
                    onImageUpload: function(files) {
                        // Handle image upload
                        for (var i = 0; i < files.length; i++) {
                            uploadImage(files[i], $(this));
                        }
                    },
                    onMediaDelete: function(target) {
                        // Optional: handle image deletion
                        console.log('Image deleted from editor');
                    }
                }
            });

            // Show the textarea (Summernote will replace it)
            $summernote.show();

        } catch (error) {
            console.error('Failed to initialize Summernote:', error);
            showFallbackEditor();
        }
    }

    // Show plain textarea as fallback
    function showFallbackEditor() {
        var $loading = $('#editor-loading');
        var $summernote = $('#summernote');

        $loading.html('<i class="fas fa-exclamation-triangle text-warning"></i> Editor nije učitan. Možete koristiti osnovni tekst editor.');

        // Show textarea with basic styling
        $summernote.css({
            'display': 'block',
            'min-height': '400px',
            'font-family': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            'font-size': '16px',
            'line-height': '1.6',
            'padding': '15px'
        });

        // Hide loading after a moment
        setTimeout(function() {
            $loading.hide();
        }, 3000);
    }

    // Upload image to server
    function uploadImage(file, editor) {
        // Validate file type
        if (!file.type.match(/^image\/(jpeg|png|gif|webp)$/)) {
            showModalAlert('Dozvoljeni su samo formati: JPG, PNG, GIF, WEBP', 'Greška', 'danger');
            return;
        }

        // Validate file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            showModalAlert('Maksimalna veličina slike je 5MB', 'Greška', 'danger');
            return;
        }

        var data = new FormData();
        data.append("file", file);

        // Get CSRF token
        var csrfToken = $('meta[name="csrf-token"]').attr('content');
        if (csrfToken) {
            data.append("csrf_token", csrfToken);
        }

        // Show loading indicator
        var $editorArea = editor.closest('.note-editor');
        var loadingHtml = '<div class="upload-loading" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);background:rgba(255,255,255,0.9);padding:20px;border-radius:8px;z-index:1000;"><i class="fas fa-spinner fa-spin"></i> Otpremanje slike...</div>';
        $editorArea.css('position', 'relative').append(loadingHtml);

        $.ajax({
            url: "/admin/posts/upload_image",
            cache: false,
            contentType: false,
            processData: false,
            data: data,
            type: "POST",
            success: function(response) {
                $editorArea.find('.upload-loading').remove();

                if (response.success) {
                    editor.summernote('insertImage', response.url, function($image) {
                        $image.css('max-width', '100%');
                        $image.addClass('img-fluid');
                    });
                } else {
                    showModalAlert(response.error || 'Greška prilikom otpremanja slike.', 'Greška', 'danger');
                }
            },
            error: function(xhr, status, error) {
                $editorArea.find('.upload-loading').remove();
                console.error('Image upload failed:', error);
                showModalAlert('Došlo je do greške na serveru prilikom otpremanja slike.', 'Greška', 'danger');
            }
        });
    }

    // Initialize when jQuery is ready
    if (typeof jQuery !== 'undefined') {
        $(document).ready(function() {
            // Small delay to ensure all scripts are loaded
            setTimeout(initEditor, 100);
        });
    } else {
        console.error('jQuery not loaded - Summernote requires jQuery');
        // Try to show fallback when DOM is ready
        document.addEventListener('DOMContentLoaded', function() {
            var loading = document.getElementById('editor-loading');
            var textarea = document.getElementById('summernote');
            if (loading) {
                loading.innerHTML = '<i class="fas fa-exclamation-triangle text-warning"></i> Editor nije dostupan. Molimo osvježite stranicu.';
            }
            if (textarea) {
                textarea.style.display = 'block';
                textarea.style.minHeight = '400px';
            }
        });
    }

})();
