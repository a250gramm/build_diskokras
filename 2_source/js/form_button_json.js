// Кнопка button_json: конфиг — единственный источник. name_key = ключ в результате, source = data-bd-source, rowsSelector/radioName/data задают способ сбора.

document.addEventListener('DOMContentLoaded', function() {
    document.addEventListener('click', function(e) {
        var btn = e.target.closest('[data-action="button_json"]');
        if (!btn) return;

        var form = btn.closest('form');
        if (!form) return;

        var configName = btn.getAttribute('data-button-json');
        if (!configName) return;

        e.preventDefault();

        function runCollect(config, name) {
            var out = {};
            var collect = config.collect || [];
            for (var i = 0; i < collect.length; i++) {
                var item = collect[i];
                var nameKey = item.name_key;
                var dataSpec = item.data || {};
                if (item.source && item.rowsSelector) {
                    out[nameKey] = collectByRows(form, item.source, item.rowsSelector, dataSpec);
                } else if (item.source && item.radioName) {
                    out[nameKey] = collectByRadio(form, item.source, item.radioName, dataSpec);
                } else if (item.data) {
                    out[nameKey] = collectByFormFun(form, dataSpec);
                }
            }
            downloadJson(out, name + '_result.json');
        }

        var configUrl = '../button_json/' + configName + '.json';
        fetch(configUrl)
            .then(function(res) {
                if (res.ok) return res.json();
                return Promise.reject(new Error('HTTP ' + res.status));
            })
            .then(function(config) {
                runCollect(config, configName);
            })
            .catch(function(err) {
                var el = document.querySelector('script[type="application/json"][data-button-json-config="' + configName + '"]');
                if (el && el.textContent) {
                    try {
                        runCollect(JSON.parse(el.textContent.trim()), configName);
                    } catch (e) { console.error('button_json: не удалось прочитать конфиг со страницы', e); }
                } else {
                    console.error('button_json: конфиг не загружен', err);
                }
            });
    });

    function getBdRecords(sourceName) {
        var script = document.querySelector('script[type="application/json"][data-bd-source="' + sourceName + '"]');
        if (!script || !script.textContent) return [];
        try {
            return JSON.parse(script.textContent.trim());
        } catch (e) {
            return [];
        }
    }

    function collectByRows(form, source, rowsSelector, dataSpec) {
        var records = getBdRecords(source);
        var rows = form.querySelectorAll(rowsSelector);
        var arr = [];
        for (var i = 0; i < rows.length && i < records.length; i++) {
            var input = rows[i].querySelector('input, textarea');
            var price = input ? String(input.value || '').trim() : '';
            if (price === '') continue;
            var rec = records[i];
            var obj = {};
            for (var key in dataSpec) {
                if (dataSpec[key] === 'bd') obj[key] = rec[key];
                else if (dataSpec[key] === 'input') obj[key] = price;
                else if (dataSpec[key] === 'input_number') obj[key] = Number(String(price).replace(/\s/g, '').replace(',', '.')) || 0;
            }
            arr.push(obj);
        }
        return arr;
    }

    function collectByRadio(form, source, radioName, dataSpec) {
        var records = getBdRecords(source);
        var radio = form.querySelector('input[name="' + radioName + '"]:checked');
        if (!radio) return {};
        var id = radio.value;
        var rec = null;
        for (var r = 0; r < records.length; r++) {
            if (String(records[r].id) === id) { rec = records[r]; break; }
        }
        if (!rec) return { id: id };
        var obj = {};
        for (var key in dataSpec) {
            if (dataSpec[key] === 'bd' && rec.hasOwnProperty(key)) obj[key] = rec[key];
        }
        return obj;
    }

    function collectByFormFun(form, dataSpec) {
        var obj = {};
        for (var key in dataSpec) {
            var el = form.querySelector('[data-function-result="' + key + '"]');
            var val = el ? (el.textContent || '').trim() : '';
            if (dataSpec[key] === 'number') {
                var num = parseFloat(val.replace(/\s/g, '').replace(',', '.')) || 0;
                obj[key] = num;
            } else {
                obj[key] = val;
            }
        }
        return obj;
    }

    function downloadJson(data, filename) {
        var blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        var a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = filename;
        a.click();
        URL.revokeObjectURL(a.href);
    }
});
