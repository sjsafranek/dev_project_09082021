
/*

    I initally started using Vue as a simple templating engine for this project.
    As I got sucked further into this little project I started to have a little
    more fun with it.

    The aside from its templating functionaly, it automatically setups events
    and data bindings with elements the DOM. It can also determine and generate
    parent and child relationships based on "components".

*/

var App = function(models) {

    return new Vue({

        el: '#view',

        delimiters: ["<%","%>"],

        data: {
            models: models,
            filters: {
                id: null,
                name: null,
                make: null,
                color: null,
                status: null,
                create_at: null,
                update_at: null
            }
        },

        mounted: function () {
            let self = this;

            // Lets setup the basic D3 chart to show the 'status' values.
            this.chart = new PieChart();
            this.chart.update(this._data.models.map(function(d) {
                return d.status;
            }));
        },

        methods: {
            // Fun little indicators for behavior
            toggleCreate: function() {
                $('.label-create').toggleClass('pulsate-info-text text-bold text-underline');
            },

            toggleRead: function() {
                $('.label-read').toggleClass('pulsate-info-text text-bold text-underline');
            },

            toggleUpdate: function() {
                $('.label-update').toggleClass('pulsate-info-text text-bold text-underline');
            },

            toggleDelete: function() {
                $('.label-delete').toggleClass('pulsate-info-text text-bold text-underline');
            },

            // Simple method to report errors back to the user.
            showError: function(message) {
                return Swal.fire({
                    icon: 'error',
                    text: message
                });
            },

            // Helper function to quickly find the 'table' element for a given Model object.
            getRowByModelID: function(model) {
                return $(this.$el).find('#'+model.id.replace(/ /g, ''));
            },

            // Ultimately if I were to do this again I would make each
            // "Model" object a Vue 'Component'. That way I could have the
            // parent (app) send Events to its children.
            // https://vuejs.org/v2/guide/components.html
            filterChange: function(model) {
                let self = this;

                // Because we are doing many DOM manipluations I will run
                // this in a callback function via the Array.filter function.
                let models = this._data.models.filter(function(d) {
                    let _show = true;
                    for (let field in self._data.filters) {
                        let value = self._data.filters[field];
                        if (value) {
                            if (!d[field] || -1 == d[field].indexOf(value)) {
                                _show = false;
                                break;
                            }
                        }
                    }
                    let $elem = self.getRowByModelID(d);
                    _show ? $elem.fadeIn(250) : $elem.fadeOut(250);
                    return _show;
                });

                // Update SVG chart to display filtered 'status' values.
                this.chart.update(
                    models.map(function(d) {
                        return d.status;
                    })
                );
            },

            // I read the "copy/edit" item as coping an individual model object,
            // not coping the entire data set (all model objects).
            copyModel: function(old_model) {
                let self = this;
                // Future proofing by returning a Promise.
                return Swal.fire({
                    title: 'Copy Model',
                    // Ultimately the "status" property should be controlled by a <select> not an <input>.
                    html: `
                        <div>
                            <div class="input-group input-group-sm pb-1">
                                <span class="input-group-text">
                                    Name
                                </span>
                                <input type="text" id="name" class="form-control form-control-sm" placeholder="name" required>
                            </div>
                            <div class="input-group input-group-sm pb-1">
                                <span class="input-group-text">
                                    Make
                                </span>
                                <input type="text" id="make" class="form-control form-control-sm" placeholder="make" value="${old_model.make}">
                            </div>
                            <div class="input-group input-group-sm pb-1">
                                <span class="input-group-text">
                                    Color
                                </span>
                                <input type="text" id="color" class="form-control form-control-sm" placeholder="color" value="${old_model.color}">
                            </div>
                            <div class="input-group input-group-sm pb-1">
                                <span class="input-group-text">
                                    Status
                                </span>
                                <input type="text" id="status" class="form-control form-control-sm" placeholder="status" value="${old_model.status}">
                            </div>
                        </div>
                    `,
                    showCloseButton: true,
                    showCancelButton: true,
                    focusConfirm: false,
                    backdrop: true,
                    showLoaderOnConfirm: true,
                    allowOutsideClick: function(){ return !Swal.isLoading(); },
                    didOpen: function() {
                        // Setup some controls on requiring the 'name' field.
                        let $confirmButton = $(Swal.getPopup().querySelector('.swal2-confirm'));
                        $confirmButton.prop('disabled', true);
                        $(Swal.getPopup().querySelector('#name')).on('change', function(event) {
                            $confirmButton.prop('disabled', '' == this.value);
                        });
                    },
                    preConfirm: function() {
                        return fetch('/api/v1/model', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                "method": "create_model",
                                "params": {
                                    name: Swal.getPopup().querySelector('#name').value,
                                    make: Swal.getPopup().querySelector('#make').value,
                                    color: Swal.getPopup().querySelector('#color').value,
                                    status: Swal.getPopup().querySelector('#status').value
                                }
                            })
                        }).then(function(response) {
                            if (!response.ok) {
                                // This should dump us into the next 'catch' statement of the Promise.
                                throw new Error(response.statusText);
                            }
                            return response.json();
                        }).catch(function(error) {
                            Swal.showValidationMessage(`Request failed: ${error}`);
                        });
                    }
                }).then(function(result) {
                    if (result.isConfirmed) {
                        let new_model = result.value.data.model;
                        self._data.models.push(new_model);

                        // Allow Vue to add element to DOM before scrolling to view.
                        // This is a little hacky but it works.
                        setTimeout(function() {
                            // We are going to 'trigger' the filterChange. I could also do this
                            // with a custom event and have Vue listen for this when it gets 'mounted'.
                            self.filterChange();

                            // Auto scroll to the newly added element.
                            self.getRowByModelID(new_model)[0]
                                .scrollIntoView({
                                    behavior: "smooth",
                                    block: "start" // "end"
                                });
                        }, 200);
                    }
                });
            },

            /*
                Since these are simple edits we are going to fire off an API request to make
                these changes on the fly. Since this is attached to a 'change' event and not
                a 'keypress' event, I don't anticipate a high volume of requests.

                This also probably doesn't conform to the exact spefications for the "update/edit",
                requirement because it is automatically saving the changes.
            */
            updateModel: function(model) {
                let self = this;

                // I was getting empty strings set for the column values.
                // It might be nicer to control for this at the database level.
                for (let i in model) {
                    if ('' == model[i]) {
                        model[i] = null;
                    }
                    model[i] = model[i];
                }

                // Send api call via browsers fetch functionaly.
                // It would be nicer to have a websocket to dynamically fire these events to the
                // server side.
                return fetch('/api/v1/model/' + model.id, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({"method":"update_model","params":model})
                }).then(function(response) {
                    return response.json().then(function(data) {
                        // TODO: Display toast alert to notify user.
                        if ('ok' != data.status) {
                            return self.showError(data.error.message);
                        }

                        // Update Model object in list
                        // Vue doesn't seem to capture the change event if I write
                        // over the original Model object.
                        for (let i in data.data.model) {
                            model[i] = data.data.model[i];
                        }

                        self.filterChange();
                    });
                }).catch(function(error) {
                    // NOTE: Ideally, I should "rollback" the user update and restore it to the previous value...
                    self.showError('Unable to communicate with server');
                });
            },

            // deleteModel issues api call to delete the selected Model object.
            deleteModel: function(model) {
                // Always warn the user about "dangerous" operations.
                let self = this;
                return Swal.fire({
                    title: 'Are you sure?',
                    icon: 'warning',
                    // Hope no one uses Internet Explorer cause the Template_literals will not work...
                    // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Template_literals
                    html: `
                        <div>Do you wish to delete ${model.name}.</div>
                        <div class="pulsate-warning-text text-bold">This cannot be undone.</div>
                    `,
                    showCloseButton: true,
                    showCancelButton: true,
                    focusConfirm: false,
                    backdrop: true,
                    showLoaderOnConfirm: true,
                    allowOutsideClick: function(){ return !Swal.isLoading(); },
                    // Here is a nice example of a Promise chain
                    preConfirm: function() {
                        return fetch('/api/v1/model/' + model.id, {
                            method: 'DELETE'
                        }).then(function(response) {
                            return response.json();
                        }).catch(function(error) {
                            Swal.showValidationMessage(`Request failed: ${error}`);
                        });
                    }
                }).then(function(result) {
                    if (result.isConfirmed) {
                        if ('ok' == result.value.status) {
                            // Vue does a great job of binding our data to the DOM.
                            // By removing the model from our list Vue will automatically
                            // detect the changes and update the DOM dynamically.
                            self._data.models = self._data.models.filter(function(d) {
                                return d.id != model.id;
                            });
                            return self.filterChange();
                        }
                        self.showError(data.error.message);
                    }
                }).catch(function(error) {
                    self.showError('Unable to communicate with server');
                });
            },

            getModelByID: function(id) {
                let model = this._data.models
                            .filter(function(d) {
                                return id == d.id;
                            });
                return model.length ? model[0] : null;
            },

            // Bonus!!! Bonus!!! Bonus!!!
            compareModel: function(model) {
                let self = this;
                return Swal.fire({
                    title: 'Compare Models',
                    html: `
                        <div class="row compare-container">

                            <table class="table">
                                <thead>
                                    <tr>
                                        <th scope="col">Column</th>
                                        <th scope="col">${model.name}</th>
                                        <th scope="col compare-name">
                                            <select id="compare-options" class="form-control form-control-sm text-bold"></select>
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr class="compare-make-row">
                                        <th scope="row">Make</th>
                                        <td>${model.make}</td>
                                        <td class="compare-make-cell"></td>
                                    </tr>
                                    <tr class="compare-color-row">
                                        <th scope="row">Color</th>
                                        <td>${model.color}</td>
                                        <td class="compare-color-cell"></td>
                                    </tr>
                                    <tr class="compare-status-row">
                                        <th scope="row">Status</th>
                                        <td>${model.status}</td>
                                        <td class="compare-status-cell"></td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    `,
                    didOpen: function() {
                        // Setup some controls on requiring the 'name' field.
                        $(Swal.getPopup().querySelector('#compare-options'))
                            .append(
                                self._data.models
                                    .filter(function(d) {
                                        return d.id != model.id;
                                    })
                                    .map(function(d) {
                                        return $('<option>', {value: d.id}).text(d.name)
                                    })
                            )
                            .on('change', function() {
                                let $popup = $(Swal.getPopup());

                                // Get selected model
                                let selected = self.getModelByID(this.value);

                                // Populate values in cell
                                $popup.find('.compare-make-cell').text(selected.make);
                                $popup.find('.compare-color-cell').text(selected.color);
                                $popup.find('.compare-status-cell').text(selected.status);

                                // Show if column values match
                                let class_list = 'pulsate-info-text text-success';
                                (selected.make == model.make) ?
                                    $popup.find('.compare-make-row').addClass(class_list) : $popup.find('.compare-make-row').removeClass(class_list);

                                (selected.color == model.color) ?
                                    $popup.find('.compare-color-row').addClass(class_list) : $popup.find('.compare-color-row').removeClass(class_list);

                                (selected.status == model.status) ?
                                    $popup.find('.compare-status-row').addClass(class_list) : $popup.find('.compare-status-row').removeClass(class_list);

                            })
                            .trigger('change');
                    }
                });
            }

        }
    });

}
