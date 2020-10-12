/* © 2015 Nedas Žilinskas <nedas.zilinskas@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */
odoo.define('website_embed.editor', function(require) {
    "use strict";

    var core = require('web.core');
    var ajax = require('web.ajax');
    var website = require('website.utils');
    var options = require('web_editor.snippets.options');

    var _t = core._t;

    options.registry.custom_snippet_embed = options.Class.extend({

        on_prompt: function() {
            var self = this;
            return website.prompt({
                window_title: _t("Embed HTML"),
                textarea: _t("HTML"),
                init: function(field) {
                    var contents = {};

                    field.parents('.modal-dialog:first').css('max-width', '70%');
                    field.parents('div:first').attr('class', 'col-sm-12');

                    field.attr('style', 'height:235px;');

                    var form = field.parents('form:first');
                    var form_group = $('<div/>', {
                        'class': 'form-group mt16 row hidden'
                    });
                    var label = $('<label/>', {
                        'class': 'col-sm-12 control-label',
                        'text': _t('Load HTML from template:')
                    }).appendTo(form_group);
                    var field_group = $('<div/>', {
                        'class': 'col-sm-12'
                    }).appendTo(form_group);
                    var populate_from_select = $('<select/>', {
                        'class': 'form-control',
                        'id': 'website_embed_populate',
                    }).on('change', function() {
                        var field_contents = contents[String($(this).val())];
                        field.val(field_contents);
                    }).appendTo(field_group);
                    $('<option/>', {
                        'text': _t('Select template...')
                    }).appendTo(populate_from_select);
                    form_group.appendTo(form)

                    ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                        model: 'website.embed',
                        method: 'search_read',
                        args: [],
                        kwargs: {}
                    }).then(function(result) {
                        if (result.length > 0) {
                            $(result).each(function(k, v) {
                                $('<option/>', {
                                    'value': v.id,
                                    'text': v.name
                                }).appendTo(populate_from_select);
                                contents[String(v.id)] = v.html_text;
                            });
                            form_group.removeClass('hidden');
                        }
                    });

                    return $.trim(self.$target.html());
                },
            }).then(function(content) {
                self.$target.html(content);
            });
        },

        on_prompt_save: function() {
            var self = this;
            return website.prompt({
                window_title: _t("Create HTML Template"),
                input: _t("Template Title"),
            }).then(function(title) {
                var title = $.trim(title);
                var contents = $.trim(self.$target.html());
                ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                    model: 'website.embed',
                    method: 'create',
                    args: [{
                        'name': title,
                        'html_text': contents,
                    }],
                    kwargs: {}
                });
            });
        },

        onBuilt: function() {
            var self = this;
            this._super();
            this.on_prompt().fail(function() {
                self.onRemove();
            });
        },

        editHtml: function(previewMode) {
            this.on_prompt();
        },

        createSnippet: function(previewMode) {
            this.on_prompt_save();
        }

    });
});
