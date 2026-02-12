(function ($) {
    $(document).ready(function () {
        // Function to add toggle button to a password field
        function addPasswordToggle(fieldId) {
            var $field = $('#' + fieldId);
            if ($field.length && !$field.parent('.password-toggle-wrapper').length) {
                // Ensure field is visible (Unfold fix)
                $field.show().css({
                    'display': 'block',
                    'visibility': 'visible',
                    'opacity': '1'
                });

                // Wrap and add button
                $field.wrap('<div class="password-toggle-wrapper"></div>');
                var $btn = $('<button type="button" class="password-toggle-btn" tabindex="-1">👁️</button>');
                $field.after($btn);

                $btn.on('click', function () {
                    var type = $field.attr('type') === 'password' ? 'text' : 'password';
                    $field.attr('type', type);
                    $(this).text(type === 'password' ? '👁️' : '🔒');
                });
            }
        }

        // Apply to User Add form fields
        addPasswordToggle('id_password1');
        addPasswordToggle('id_password2');

        // Also apply to Change view password field (though it's usually a hash display)
        addPasswordToggle('id_password');

        // Watch for dynamically added fields (if any)
        var observer = new MutationObserver(function (mutations) {
            addPasswordToggle('id_password1');
            addPasswordToggle('id_password2');
            addPasswordToggle('id_password');
        });

        var config = { childList: true, subtree: true };
        var target = document.querySelector('#content-main') || document.body;
        observer.observe(target, config);
    });
})(django.jQuery || jQuery);
