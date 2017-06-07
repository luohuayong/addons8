openerp.bysun_delivery = function (instance) {
    instance.web.form.One2ManyListView.include({
        do_activate_record: function (index, id, dataset) {
            var self = this;
            if (self.model !== 'ebiz.delivery.capacity') {
                return this._super(index, id);
            }
            dataset.read_ids([id]).then(function (records) {
                var r = records[0];
                var action_data = {
                    type: 'object',
                    name: 'on_select_delivery',
                    context: {
                        'delivery_code': r.delivery_code,
                        'delivery_date': r.delivery_date,
                        'delivery_hour': r.delivery_hour
                    }
                };
                var wizard_view = self.o2m.view;
                wizard_view.do_execute_action(action_data, wizard_view.dataset);
            });
        }
    })

};