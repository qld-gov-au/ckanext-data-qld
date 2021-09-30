ckan.module('dataset-deletion-confirm-action', function (jQuery) {
    return {
        /* An object of module options */
        options: {
            /* Content can be overriden by setting data-module-content to a
             * *translated* string inside the template, e.g.
             *
             *     <a href="..."
             *        data-module="confirm-action"
             *        data-module-content="{{ _('Are you sure?') }}">
             *    {{ _('Delete') }}
             *    </a>
             */
            content: '',

            /* This is part of the old i18n system and is kept for backwards-
             * compatibility for templates which set the content via the
             * `i18n.content` attribute instead of via the `content` attribute
             * as described above.
             */
            i18n: {
                content: '',
            },

            href: '',

            template: [
                '<div class="modal fade">',
                '<div class="modal-dialog">',
                '<div class="modal-content">',
                '<div class="modal-header">',
                '<button type="button" class="close" data-dismiss="modal">×</button>',
                '<h3 class="modal-title"></h3>',
                '</div>',
                '<div class="modal-body">',
                '<br/><br/>',
                '<div class="modal-reason">Briefly describe the reason for deleting this dataset:<br/>',
                '<input id="reason" name="deletion_reason" type="text" class="form-control" maxlength="250" /></div>',
                '</div>',
                '<div class="modal-footer">',
                '<button class="btn btn-default btn-cancel"></button>',
                '<button class="btn btn-primary" disabled="disabled"></button>',
                '</div>',
                '</div>',
                '</div>',
                '</div>'
            ].join('\n')
        },

        deletion_reason: '',

        /* Sets up the event listeners for the object. Called internally by
         * module.createInstance().
         *
         * Returns nothing.
         */
        initialize: function () {
            jQuery.proxyAll(this, /_on/);
            this.el.removeAttr('disabled');
            this.el.on('click', this._onClick);
        },

        /* Presents the user with a confirm dialogue to ensure that they wish to
         * continue with the current action.
         *
         * Examples
         *
         *   jQuery('.delete').click(function () {
         *     module.confirm();
         *   });
         *
         * Returns nothing.
         */
        confirm: function () {
            this.sandbox.body.append(this.createModal());
            this.modal.modal('show');

            // Center the modal in the middle of the screen.
            this.modal.css({
                'margin-top': this.modal.height() * -0.5,
                'top': '50%'
            });
        },

        /* Performs the action for the current item.
         *
         * Returns nothing.
         */
        performAction: function () {
            // create a form and submit it to confirm the deletion
            var form = jQuery('<form/>', {
                action: this.options.href,
                method: 'POST'
            });

            form.append('<input type="hidden" name="deletion_reason" value="' + this.deletion_reason + '">');
            form.appendTo('body').submit();
        },

        /* Creates the modal dialog, attaches event listeners and localised
         * strings.
         *
         * Returns the newly created element.
         */
        createModal: function () {
            if (!this.modal) {
                var element = this.modal = jQuery(this.options.template);
                element.on('click', '.btn-primary', this._onConfirmSuccess);
                element.on('click', '.btn-cancel', this._onConfirmCancel);
                element.on('keyup', '#reason', this._onKeyUp);
                element.modal({show: false});

                element.find('.modal-title').text(this._('Please Confirm Action'));
                var content = this.options.content ||
                    this.options.i18n.content || /* Backwards-compatibility */
                    this._('Are you sure you want to perform this action?');
                element.find('.modal-body').prepend(content);
                element.find('.btn-primary').text(this._('Confirm'));
                element.find('.btn-cancel').text(this._('Cancel'));
            }
            return this.modal;
        },

        /* Event handler that displays the confirm dialog */
        _onClick: function (event) {
            event.preventDefault();
            this.confirm();
        },

        /* Event handler for the success event */
        _onConfirmSuccess: function (event) {
            this.performAction();
        },

        /* Event handler for the cancel event */
        _onConfirmCancel: function (event) {
            this.modal.modal('hide');
        },

        _onKeyUp: function (event) {
            var value = jQuery(event.target).val().trim();
            if (value.length >= 10) {
                this.deletion_reason = value;
                this.modal.find('.modal-footer .btn-primary').removeAttr('disabled');
            } else {
                this.deletion_reason = '';
                this.modal.find('.modal-footer .btn-primary').attr('disabled', 'disabled');
            }
        }
    };
});
