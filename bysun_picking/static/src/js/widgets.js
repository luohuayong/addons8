function openerp_pack_widgets(instance){
    var module = instance.bysun_picking;
    var _t     = instance.web._t;
    var QWeb   = instance.web.qweb;
    module.MobileWidget = instance.web.Widget.extend({
        start: function(){
            if(!$('#oe-mobilewidget-viewport').length){
                $('head').append('<meta id="oe-mobilewidget-viewport" name="viewport" content="initial-scale=1.0; maximum-scale=1.0; user-scalable=0;">');
            }
            return this._super();
        },
        destroy: function(){
            $('#oe-mobilewidget-viewport').remove();
            return this._super();
        },
    });

    module.PackEditorWidget = instance.web.Widget.extend({
        template: 'PackEditorWidget',
        init: function(parent,options){
            this._super(parent,options);
            var self = this;
            this.rows = [];
            this.search_filter = "";
            jQuery.expr[":"].Contains = jQuery.expr.createPseudo(function(arg) {
                return function( elem ) {
                    return jQuery(elem).text().toUpperCase().indexOf(arg.toUpperCase()) >= 0;
                };
            });
        },
        get_header: function(){
            return this.getParent().get_header();
        },
        get_logisticunit: function(){
            var model = this.getParent();
            var ul = [];
            var self = this;
            _.each(model.uls, function(ulog){
                ul.push({name: ulog.name, id: ulog.id,});
            });
            return ul;
        },
        get_rows: function(){
            var model = this.getParent();
            this.rows = [];
            var self = this;
            var pack_created = [];
            _.each( model.packoplines, function(packopline){
                    var pack = undefined;
                    var color = "";
                    if (packopline.product_id[1] !== undefined){ pack = packopline.package_id[1];}
                    if (packopline.product_qty == packopline.qty_done){ color = "success "; }
                    if (packopline.product_qty < packopline.qty_done){ color = "danger "; }
                    //also check that we don't have a line already existing for that package
                    if (packopline.result_package_id[1] !== undefined && $.inArray(packopline.result_package_id[0], pack_created) === -1){
                        var myPackage = $.grep(model.packages, function(e){ return e.id == packopline.result_package_id[0]; })[0];
                        self.rows.push({
                            cols: { product: packopline.result_package_id[1],
                                    qty: '',
                                    rem: '',
                                    uom: undefined,
                                    lot: undefined,
                                    pack: undefined,
                                    container: packopline.result_package_id[1],
                                    container_id: undefined,
                                    loc: packopline.location_id[1],
                                    dest: packopline.location_dest_id[1],
                                    id: packopline.result_package_id[0],
                                    product_id: undefined,
                                    can_scan: false,
                                    head_container: true,
                                    processed: packopline.processed,
                                    package_id: myPackage.id,
                                    ul_id: myPackage.ul_id[0],
                            },
                            classes: ('success container_head ') + (packopline.processed === "true" ? 'processed hidden ':''),
                        });
                        pack_created.push(packopline.result_package_id[0]);
                    }
                    self.rows.push({
                        cols: { product: packopline.product_id[1] || packopline.package_id[1],
                                qty: packopline.product_qty,
                                rem: packopline.qty_done,
                                uom: packopline.product_uom_id[1],
                                lot: packopline.lot_id[1],
                                pack: pack,
                                container: packopline.result_package_id[1],
                                container_id: packopline.result_package_id[0],
                                loc: packopline.location_id[1],
                                dest: packopline.location_dest_id[1],
                                id: packopline.id,
                                product_id: packopline.product_id[0],
                                can_scan: packopline.result_package_id[1] === undefined ? true : false,
                                head_container: false,
                                processed: packopline.processed,
                                package_id: undefined,
                                ul_id: -1,
                        },
                        classes: color + (packopline.result_package_id[1] !== undefined ? 'in_container_hidden ' : '') + (packopline.processed === "true" ? 'processed hidden ':''),
                    });
            });
            //sort element by things to do, then things done, then grouped by packages
            group_by_container = _.groupBy(self.rows, function(row){
                return row.cols.container;
            });
            var sorted_row = [];
            if (group_by_container.undefined !== undefined){
                group_by_container.undefined.sort(function(a,b){return (b.classes === '') - (a.classes === '');});
                $.each(group_by_container.undefined, function(key, value){
                    sorted_row.push(value);
                });
            }

            $.each(group_by_container, function(key, value){
                if (key !== 'undefined'){
                    $.each(value, function(k,v){
                        sorted_row.push(v);
                    });
                }
            });

            return sorted_row;
        },
        renderElement: function(){
            var self = this;
            this._super();
            this.check_content_screen();
            this.$('.js_pick_print').click(function(){ self.getParent().print_picking(); });
            this.$('.js_putinpack').click(function(){ self.getParent().pack(); });
            this.$('.js_drop_down').click(function(){ self.getParent().drop_down();});
            this.$('.js_pick_quit').click(function(){ self.getParent().quit(); });
            
            this.$('.pack_pick_ref').focus(function(){
                self.getParent().disconnect();
            });
            this.$('.pack_pick_ref').blur(function(){
                self.getParent().scan_connect(function(ean){
                    self.getParent().scan(ean);
                });
            });

            this.$('#js_select').change(function(){
                var selection = self.$('#js_select option:selected').attr('value');
                if (selection === "ToDo"){
                    self.getParent().$('.js_pick_pack').removeClass('hidden')
                    self.getParent().$('.js_drop_down').removeClass('hidden')
                    self.$('.js_pack_op_line.processed').addClass('hidden')
                    self.$('.js_pack_op_line:not(.processed)').removeClass('hidden')
                }else{
                    self.getParent().$('.js_pick_pack').addClass('hidden')
                    self.getParent().$('.js_drop_down').addClass('hidden')
                    self.$('.js_pack_op_line.processed').removeClass('hidden')
                    self.$('.js_pack_op_line:not(.processed)').addClass('hidden')
                }
            });
            this.$('.js_plus').click(function(){
                var id = $(this).data('product-id');
                var op_id = $(this).parents("[data-id]:first").data('id');
                self.getParent().scan_product_id(id,true,op_id);
            });
            this.$('.js_minus').click(function(){
                var id = $(this).data('product-id');
                var op_id = $(this).parents("[data-id]:first").data('id');
                self.getParent().scan_product_id(id,false,op_id);
            });
            this.$('.js_unfold').click(function(){
                var op_id = $(this).parent().data('id');
                var line = $(this).parent();
                //select all js_pack_op_line with class in_container_hidden and correct container-id
                select = self.$('.js_pack_op_line.in_container_hidden[data-container-id='+op_id+']')
                if (select.length > 0){
                    //we unfold
                    line.addClass('warning');
                    select.removeClass('in_container_hidden');
                    select.addClass('in_container');
                }
                else{
                    //we fold
                    line.removeClass('warning');
                    select = self.$('.js_pack_op_line.in_container[data-container-id='+op_id+']')
                    select.removeClass('in_container');
                    select.addClass('in_container_hidden');
                }
            });
            this.$('.js_create_lot').click(function(){
                var op_id = $(this).parents("[data-id]:first").data('id');
                var lot_name = false;
                self.$('.js_lot_scan').val('');
                var $lot_modal = self.$el.siblings('#js_LotChooseModal');
                //disconnect scanner to prevent scanning a product in the back while dialog is open
                self.getParent().disconnect();
                $lot_modal.modal()
                //focus input
                $lot_modal.on('shown.bs.modal', function(){
                    self.$('.js_lot_scan').focus();
                })
                //reactivate scanner when dialog close
                $lot_modal.on('hidden.bs.modal', function(){
                    self.getParent().scan_connect(function(ean){
                        self.getParent().scan(ean);
                    });
                })
                self.$('.js_lot_scan').focus();
                //button action
                self.$('.js_validate_lot').click(function(){
                    //get content of input
                    var name = self.$('.js_lot_scan').val();
                    if (name.length !== 0){
                        lot_name = name;
                    }
                    $lot_modal.modal('hide');
                    //we need this here since it is not sure the hide event
                    //will be catch because we refresh the view after the create_lot call
                    self.getParent().scan_connect(function(ean){
                        self.getParent().scan(ean);
                    });
                    self.getParent().create_lot(op_id, lot_name);
                });
            });
            this.$('.js_delete_pack').click(function(){
                var pack_id = $(this).parents("[data-id]:first").data('id');
                self.getParent().delete_package_op(pack_id);
            });
            this.$('.js_print_pack').click(function(){
                var pack_id = $(this).parents("[data-id]:first").data('id');
                // $(this).parents("[data-id]:first").data('id')
                self.getParent().print_package(pack_id);
            });
            this.$('.js_submit_pick_ref').submit(function(event){
                self.getParent().load_picking().then(function(){
                   self.getParent().refresh_ui();
                   self.getParent().scan_connect(function(ean){
                       self.getParent().scan(ean);
                    });
                });
                return false;
            });
            
            this.$('.js_submit_value').submit(function(event){
                var op_id = $(this).parents("[data-id]:first").data('id');
                var value = parseFloat($("input", this).val());
                if (value>=0){
                    self.getParent().set_operation_quantity(value, op_id);
                }
                $("input", this).val("");
                self.getParent().scan_connect(function(ean){
                    self.getParent().scan(ean);
                });
                return false;
            });
            this.$('.js_qty').focus(function(){
                self.getParent().disconnect();
            });
            this.$('.js_qty').blur(function(){
                var op_id = $(this).parents("[data-id]:first").data('id');
                var value = parseFloat($(this).val());
                if (value>=0){
                    self.getParent().set_operation_quantity(value, op_id);
                }
                self.getParent().scan_connect(function(ean){
                    self.getParent().scan(ean);
                });
            });
            this.$('.js_change_src').click(function(){
                var op_id = $(this).parents("[data-id]:first").data('id');//data('op_id');
                self.$('#js_loc_select').addClass('source');
                self.$('#js_loc_select').data('op-id',op_id);
                self.$el.siblings('#js_LocationChooseModal').modal();
            });
            this.$('.js_change_dst').click(function(){
                var op_id = $(this).parents("[data-id]:first").data('id');
                self.$('#js_loc_select').data('op-id',op_id);
                self.$el.siblings('#js_LocationChooseModal').modal();
            });
            this.$('.js_pack_change_dst').click(function(){
                var op_id = $(this).parents("[data-id]:first").data('id');
                self.$('#js_loc_select').addClass('pack');
                self.$('#js_loc_select').data('op-id',op_id);
                self.$el.siblings('#js_LocationChooseModal').modal();
            });
            this.$('.js_validate_location').click(function(){
                //get current selection
                var select_dom_element = self.$('#js_loc_select');
                var loc_id = self.$('#js_loc_select option:selected').data('loc-id');
                var src_dst = false;
                var op_id = select_dom_element.data('op-id');
                if (select_dom_element.hasClass('pack')){
                    select_dom_element.removeClass('source');
                    op_ids = [];
                    self.$('.js_pack_op_line[data-container-id='+op_id+']').each(function(){
                        op_ids.push($(this).data('id'));
                    });
                    op_id = op_ids;
                }
                else if (select_dom_element.hasClass('source')){
                    src_dst = true;
                    select_dom_element.removeClass('source');
                }
                if (loc_id === false){
                    //close window
                    self.$el.siblings('#js_LocationChooseModal').modal('hide');
                }
                else{
                    self.$el.siblings('#js_LocationChooseModal').modal('hide');
                    self.getParent().change_location(op_id, parseInt(loc_id), src_dst);

                }
            });
            this.$('.js_pack_configure').click(function(){
                var pack_id = $(this).parents(".js_pack_op_line:first").data('package-id');
                var ul_id = $(this).parents(".js_pack_op_line:first").data('ulid');
                self.$('#js_packconf_select').val(ul_id);
                self.$('#js_packconf_select').data('pack-id',pack_id);
                self.$el.siblings('#js_PackConfModal').modal();
            });
            this.$('.js_validate_pack').click(function(){
                //get current selection
                var select_dom_element = self.$('#js_packconf_select');
                var ul_id = self.$('#js_packconf_select option:selected').data('ul-id');
                var pack_id = select_dom_element.data('pack-id');
                self.$el.siblings('#js_PackConfModal').modal('hide');
                if (pack_id){
                    self.getParent().set_package_pack(pack_id, ul_id);
                    $('.container_head[data-package-id="'+pack_id+'"]').data('ulid', ul_id);
                }
            });
            
            //remove navigtion bar from default openerp GUI
            $('td.navbar').html('<div></div>');
        },
        on_searchbox: function(query){
            //hide line that has no location matching the query and highlight location that match the query
            this.search_filter = query;
            var processed = ".processed";
            if (this.$('#js_select option:selected').attr('value') == "ToDo"){
                processed = ":not(.processed)";
            }
            if (query !== '') {
                this.$('.js_loc:not(.js_loc:Contains('+query+'))').removeClass('info');
                this.$('.js_loc:Contains('+query+')').addClass('info');
                this.$('.js_pack_op_line'+processed+':not(.js_pack_op_line:has(.js_loc:Contains('+query+')))').addClass('hidden');
                this.$('.js_pack_op_line'+processed+':has(.js_loc:Contains('+query+'))').removeClass('hidden');
            }
            //if no query specified, then show everything
            if (query === '') {
                this.$('.js_loc').removeClass('info');
                this.$('.js_pack_op_line'+processed+'.hidden').removeClass('hidden');
            }
            this.check_content_screen();
        },
        check_content_screen: function(){
            //get all visible element and if none has positive qty, disable put in pack and process button
            var self = this;
            var processed = this.$('.js_pack_op_line.processed');
            var qties = this.$('.js_pack_op_line:not(.processed):not(.hidden) .js_qty').map(function(){return $(this).val()});
            var container = this.$('.js_pack_op_line.container_head:not(.processed):not(.hidden)')
            var disabled = true;
            $.each(qties,function(index, value){
                if (parseInt(value)>0){
                    disabled = false;
                }
            });

            if (disabled){
                if (container.length===0){
                    self.$('.js_drop_down').addClass('disabled');
                }
                else {
                    self.$('.js_drop_down').removeClass('disabled');
                }
                self.$('.js_pick_pack').addClass('disabled');
                if (processed.length === 0){
                    self.$('.js_pick_done').addClass('disabled');
                }
                else {
                    self.$('.js_pick_done').removeClass('disabled');
                }
            }
            else{
                self.$('.js_drop_down').removeClass('disabled');
                self.$('.js_pick_pack').removeClass('disabled');
                self.$('.js_pick_done').removeClass('disabled');
            }
        },
        get_current_op_selection: function(ignore_container){
            //get ids of visible on the screen
            pack_op_ids = [];
            qty_done = {};
            this.$('.js_pack_op_line:not(.processed):not(.js_pack_op_line.hidden):not(.container_head)').each(function(){
                cur_id = $(this).data('id');
                pack_op_ids.push(parseInt(cur_id));
            });
            //get list of element in this.rows where rem > 0 and container is empty is specified
            list = []
            _.each(this.rows, function(row){
                if (row.cols.rem > 0 && (ignore_container || row.cols.container === undefined)){
                    list.push(row.cols.id);
                    qty_done[row.cols.id] = row.cols.rem;
                }
            });
            //return only those visible with rem qty > 0 and container empty
            pack_op_ids = _.intersection(pack_op_ids, list)
            return [pack_op_ids, qty_done];
        },
        remove_blink: function(){
            this.$('.js_pack_op_line.blink_me').removeClass('blink_me');
        },
        blink: function(op_id){
            this.$('.js_pack_op_line[data-id="'+op_id+'"]').addClass('blink_me');
        },
        check_done: function(){
            var model = this.getParent();
            var self = this;
            var done = true;
            _.each( model.packoplines, function(packopline){
                if (packopline.processed === "false"){
                    done = false;
                    return done;
                }
            });
            return done;
        },
        get_visible_ids: function(){
            var self = this;
            var visible_op_ids = []
            var op_ids = this.$('.js_pack_op_line:not(.processed):not(.hidden):not(.container_head):not(.in_container):not(.in_container_hidden)').map(function(){
                return $(this).data('id');
            });
            $.each(op_ids, function(key, op_id){
                visible_op_ids.push(parseInt(op_id));
            });
            return visible_op_ids;
        },
    });

    module.PackMainWidget = module.MobileWidget.extend({
        template: 'PackMainWidget',
        init: function(parent,params){
            this._super(parent,params);
            var self = this;
            init_hash = $.bbq.getState();
            self.clear_picking();
            this.loaded =  this.load_init();
        },

        load_init: function(){
            var self = this;
            new instance.web.Model('stock.picking').call('check_group_pack')
                .then(function(result){
                   self.show_pack = result;
                   return new instance.web.Model('stock.picking').call('check_group_lot')
                }).then(function(result){
                   self.show_lot = result;
                });
        },

        start: function(){
            this._super();
            var self = this;
            instance.webclient.set_content_full_screen(true);
            this.scan_connect(function(ean){
                    self.scan(ean);
            });

            this.$('.js_reload_op').click(function(){ self.reload_pack_operation();});

            $.when(this.loaded).done(function(){
                self.picking_editor = new module.PackEditorWidget(self);
                self.picking_editor.replace(self.$('.oe_placeholder_picking_editor'));
                if (!self.show_pack){
                    self.$('.js_pick_pack').addClass('hidden');
                }
                if (!self.show_lot){
                    self.$('.js_create_lot').addClass('hidden');
                }
            }).fail(function(error) {console.log(error);});
        },

        load_picking: function(){
            self = this;
            pick_ref = self.$('.pack_pick_ref').val();
            if(pick_ref === ''){
                return;
            }
            if(self.picking_id !== null && self.picking.name === pick_ref){
                return new instance.web.Model('stock.picking')
                    .call('load_picking_from_ui',[self.picking_id ])
                    .then(function(pick_dict){
                        self.init_picking(pick_dict);
                    });
            }
            return new instance.web.Model('stock.picking')
                .call('get_picking_from_ref',[pick_ref ])
                .then(function(pick_dict){
                    self.init_picking(pick_dict);
                });
        },
        clear_picking: function(){
            this.picking_id = null;
            this.picking = null;
            this.picking_type_id = null;
            this.packoplines = null;
            this.selected_operation = { id: null, picking_id: null};
            this.packages = null;
            this.locations = [];
            this.uls = [];
        },
        init_picking: function(pick_dict){
            if(pick_dict['picking'] !== undefined){
                self.picking = pick_dict['picking'];
                self.picking_id = self.picking.id;
                self.picking_type_id = self.picking.picking_type_id[0];
            }
            if(pick_dict['packoplines'] !== undefined){
                self.packoplines = pick_dict['packoplines'];
            }
            if(pick_dict['packages'] !== undefined){
                self.packages = pick_dict['packages'];
            }
            if(pick_dict['uls'] !== undefined){
                self.uls = pick_dict['uls'];
            }
        },
        refresh_ui: function(){
            var self = this;
            self.picking_editor.remove_blink();
            self.picking_editor.renderElement();
            if (!self.show_pack){
                self.$('.js_pick_pack').addClass('hidden');
            }
            if (!self.show_lot){
                self.$('.js_create_lot').addClass('hidden');
            }
            self.$('.oe_reload_op').addClass('hidden');
            if (self.picking != null && self.picking.recompute_pack_op){
                self.$('.oe_reload_op').removeClass('hidden');
            }
        },
        
        get_header: function(){
            if(this.picking){
                return this.picking.name;
            }else{
                return '';
            }
        },
        
        scan: function(ean){ //scans a barcode, sends it to the server, then reload the ui
            var self = this;
            operations = self.packoplines;
            refresh = false;
            for(var i = 0; i < operations.length; i++){
                //是否是批次码扫描
                if(operations[i].lot_name === ean || operations[i].lot_ref === ean){
                    operations[i].qty_done += 1;
                    refresh = true;
                    break;
                }
                //是否是产品条码扫描
                if(operations[i].default_code === ean || operations[i].ean13 === ean){
                    operations[i].qty_done += 1;
                    refresh = true;
                    break;
                }
            };
            if(refresh){
                self.refresh_ui();
            }
        },
        scan_product_id: function(product_id,increment,op_id){ //performs the same operation as a scan, but with product id instead
            var self = this;
            operations = self.packoplines;
            for(var i = 0; i < operations.length; i++){
                if(operations[i].id === op_id){
                    if(increment){
                        operations[i].qty_done += 1;
                    }else{
                        operations[i].qty_done -= 1;
                        if(operations[i].qty_done < 0){
                            operations[i].qty_done = 0;
                        }
                    }
                    break;
                }
            };
            self.refresh_ui();
        },
        set_operation_quantity: function(quantity, op_id){
            var self = this;
            operations = self.packoplines;
            for(var i = 0; i < operations.length; i++){
                if(operations[i].id === op_id){
                    if(quantity >= 0){
                        operations[i].qty_done = quantity;
                    }else{
                        operations[i].qty_done = 0;
                    }
                    break;
                }
            };
            self.refresh_ui();
        },
        
        pack: function(){
            var self = this;
            var op = self.picking_editor.get_current_op_selection(false);
            var pack_op_ids = op[0];
            var qty_done = op[1];
            var weight = 0;
            /* 此段代码在打包时候录入包裹重量
            weight = prompt('请输入包裹重量:');
            if (weight == '' || weight == null){
                return;
            };
            if (weight == '0' || isNaN(weight)){
                alert('请输入正确的包裹重量');
                return;
            }; */
            if (pack_op_ids.length !== 0){
                return new instance.web.Model('stock.picking')
                    .call('action_pack2',[[self.picking.id], pack_op_ids, qty_done, weight])
                    .then(function(pack){
                        return self.load_picking().then(function(){
                            instance.session.user_context.current_package_id = false;
                            self.refresh_ui();
                        });
                    });
            }
        },
        
        drop_down: function(){
            var self = this;
            var op = self.picking_editor.get_current_op_selection(true);
            var pack_op_ids = op[0];
            var qty_done = op[1];
            var weight = 0.00;
            var weight_window =window.prompt("请输入包裹重量：","");

            if (weight_window==null || weight_window==""){
                alert("包裹重量不能为空！");
                return;
            }
            else{
                weight = weight_window;
            };
            // 在这下调试返回的重量weight 
            if (pack_op_ids.length !== 0){
                return new instance.web.Model('stock.pack.operation')
                    .call('action_drop_down2', [pack_op_ids, qty_done,weight])
                    .then(function(){
                        return self.load_picking().then(function(){
                            self.refresh_ui();
                            if (self.picking_editor.check_done()){
                                return self.done();
                            };
                        });
                    });
            }
        },
        done: function(){
            var self = this;
            return new instance.web.Model('stock.picking')
                .call('action_done_from_ui',[self.picking.id, {'default_picking_type_id': self.picking_type_id}])
                .then(function(new_picking_ids){
                    self.clear_picking();
                    self.refresh_ui();
                    $(".pack_pick_ref")[0].focus();
                });
        },
        create_lot: function(op_id, lot_name){
            var self = this;
            return new instance.web.Model('stock.pack.operation')
                .call('create_and_assign_lot',[parseInt(op_id), lot_name])
                .then(function(){
                    return self.refresh_ui(self.picking.id);
                });
        },
        print_picking: function(){
            var self = this;
            if(self.picking == null){return;}
            else{
            return new instance.web.Model('stock.picking')
                .call('action_print',[[self.picking.id]])
                .then(function(action){
                    return self.do_action(action);
                })};
        },
        print_package: function(package_id){
            var self = this;
            return new instance.web.Model('stock.quant.package')
                .call('action_print',[[package_id]])
                .then(function(action){
                    return self.do_action(action);
                });
        },
        delete_package_op: function(pack_id){
            var self = this;
            return new instance.web.Model('stock.pack.operation').call('search', [[['result_package_id', '=', pack_id]]])
                .then(function(op_ids) {
                    return new instance.web.Model('stock.pack.operation').call('write', [op_ids, {'result_package_id':false}])
                        .then(function() {
                            new instance.web.Model('stock.quant.package').call('unpack', [pack_id,]);
                            return self.load_picking().then(function(){
                                instance.session.user_context.current_package_id = false;
                                self.refresh_ui();
                            });
                        });
                });
        },
        set_package_pack: function(package_id, pack){
            var self = this;
                return new instance.web.Model('stock.quant.package')
                    .call('write',[[package_id],{'ul_id': pack }]);
            return;
        },

        reload_pack_operation: function(){
            var self = this;
            if(self.picking == null){return;}
            else{
            return new instance.web.Model('stock.picking')
                .call('do_prepare_partial',[[self.picking.id]])
                .then(function(){
                    self.refresh_ui(self.picking.id);
                })};
        },

        quit: function(){
            this.destroy();
            return new instance.web.Model("ir.model.data").get_func("search_read")([['name', '=', 'action_picking_type_form']], ['res_id']).pipe(function(res) {
                    window.location = '/web#action=' + res[0]['res_id'];
                });
        },
        destroy: function(){
            this._super();
            this.disconnect();
            instance.webclient.set_content_full_screen(false);
        },

        key_press: function(e){
            self = this;
            if(e.which === 13){

            }
        },
        scan_connect: function(callback){
            var code = "";
            var timeStamp = 0;
            var timeout = null;
            self = this;

            this.handler = function(e){
                //console.log(e);
                if(timeStamp + 50 < new Date().getTime()){
                    code = "";
                }
                if(code === ""){
                    self.key_press(e);
                    // return;
                }
                if(e.which === 13){ //ignore returns
                    return;
                }
                timeStamp = new Date().getTime();
                clearTimeout(timeout);
                code += String.fromCharCode(e.which);
                timeout = setTimeout(function(){
                    if(code.length >= 3){
                        callback(code);
                    }
                    code = "";
                },100);
            };
            $('body').on('keypress', this.handler);
        },
        disconnect: function(){
            $('body').off('keypress', this.handler);
        },
    });
    openerp.web.client_actions.add('bysun_picking.ui', 'instance.bysun_picking.PackMainWidget');

    instance.web.bysun_picking = instance.web.bysun_picking || {};
    instance.web.views.add('tree_picking_wave_quickpick', 'instance.web.bysun_picking.QuickPickView');
    instance.web.bysun_picking.QuickPickView = instance.web.ListView.extend({
        init: function() {
            this._super.apply(this, arguments);
            this.products = [];
            this.partners = [];
            this.current_products = null;
            this.current_partners = null;
            this.date_start = new instance.web.DateTimeWidget(this);
            this.date_end = new instance.web.DateTimeWidget(this);
        },
        start:function(){
            var tmp = this._super.apply(this, arguments);
            var self = this;
            var defs = [];
            this.$el.parent().prepend(QWeb.render("QuickPickView", {widget: this}));
            div_start = this.$el.parent().find('.date_search_start')
            this.date_start.appendTo(div_start)
            div_end = this.$el.parent().find('.date_search_end')
            this.date_end.appendTo(div_end)            

            this.$el.parent().find('.oe_sale_select_product').change(function() {
                    self.current_products = this.value === '' ? null : parseInt(this.value);
                });

            this.$el.parent().find('.oe_tree_button_search').click(function() {
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });

            var mod = new instance.web.Model("stock.picking.wave", self.dataset.context, self.dataset.domain);
            defs.push(mod.call("list_products", []).then(function(result) {
                self.products = result;
                var o;
                self.$el.parent().find('.oe_sale_select_product').children().remove().end();
                self.$el.parent().find('.oe_sale_select_product').append(new Option('', ''));
                for (var i = 0;i < self.products.length;i++){
                    o = new Option(self.products[i][1], self.products[i][0]);
                    if (self.products[i][0] === self.current_products){
                        $(o).attr('selected',true);
                    }
                    self.$el.parent().find('.oe_sale_select_product').append(o);
                }
            }));

            return $.when(tmp, defs);
        },
        do_search: function(domain, context, group_by) {
            var self = this;
            this.last_domain = domain;
            this.last_context = context;
            this.last_group_by = group_by;
            this.old_search = _.bind(this._super, this);
            var o;
            self.$el.parent().find('.oe_sale_select_product').children().remove().end();
            self.$el.parent().find('.oe_sale_select_product').append(new Option('', ''));
            for (var i = 0;i < self.products.length;i++){
                o = new Option(self.products[i][1], self.products[i][0]);
                if (self.products[i][0] === self.current_products){
                    $(o).attr('selected',true);
                }
                self.$el.parent().find('.oe_sale_select_product').append(o);
            }
            return self.search_by_journal_period();
        },
        search_by_journal_period: function() {
            var self = this;
            var domain = [];

            if (self.current_products !== null) domain.push(["carrier_id", "=", self.current_products]);
            self.last_context["carrier_id"] = self.current_products === null ? false : self.current_products;
            
            if (self.current_partners !== null) domain.push(["partner_id", "=", self.current_partners]);
            self.last_context["partner_id"] = self.current_partners === null ? false : self.current_partners;

            date_start = self.date_start.get_value();
            date_end = self.date_end.get_value();
            
            if (date_start !== false) domain.push(["min_date", ">=", date_start]);
            if (date_end !== false) domain.push(["min_date", "<=", date_end]);

            var compound_domain = new instance.web.CompoundDomain(self.last_domain, domain);
            self.dataset.domain = compound_domain.eval();
            return self.old_search(compound_domain, self.last_context, self.last_group_by);
        },
    });
}

openerp.bysun_picking = function(openerp) {
    openerp.bysun_picking = openerp.bysun_picking || {};
    openerp_pack_widgets(openerp);
}
