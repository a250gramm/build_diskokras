// Кнопка button_json: source = ключ в результате и источник данных (data-bd-source), rowsSelector/radioName/data задают способ сбора.

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
            var items = [];
            if (config.collect && Array.isArray(config.collect)) {
                for (var i = 0; i < config.collect.length; i++) {
                    var it = config.collect[i];
                    items.push({ src: it.source, dataSpec: it.data || {}, rowsSelector: it.rowsSelector, radioName: it.radioName, hasData: !!it.data });
                }
            } else {
                var keys = Object.keys(config);
                for (var k = 0; k < keys.length; k++) {
                    var src = keys[k];
                    var it = config[src];
                    if (it && typeof it === 'object') {
                        items.push({ src: src, dataSpec: it.data || {}, rowsSelector: it.rowsSelector, radioName: it.radioName, hasData: !!it.data });
                    }
                }
            }
            for (var i = 0; i < items.length; i++) {
                var item = items[i];
                var src = item.src;
                var dataSpec = item.dataSpec;
                if (src && item.rowsSelector) {
                    out[src] = collectByRows(form, src, item.rowsSelector, dataSpec);
                } else if (src && item.radioName) {
                    out[src] = collectByRadio(form, src, item.radioName, dataSpec);
                } else if (item.hasData) {
                    if (isFormulaBlock(dataSpec)) {
                        out[src] = computeFormulas(out, dataSpec, src);
                    } else {
                        out[src] = collectByFormFun(form, dataSpec);
                    }
                }
            }
            var isLocal = (typeof location !== 'undefined' && (location.hostname === 'localhost' || location.hostname === '127.0.0.1' || location.protocol === 'file:'));
            if (isLocal) {
                downloadJson(out, name + '_result.json');
            } else {
                saveJsonToServer(out, name);
            }
        }

        function saveJsonToServer(data, name) {
            var url = '../php/save_button_json.php';
            fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
                .then(function(res) { return res.json(); })
                .then(function(r) {
                    if (r.ok) {
                        window.open('../tmp/' + r.file, '_blank');
                    }
                })
                .catch(function() {});
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

    function isFormulaBlock(dataSpec) {
        for (var k in dataSpec) {
            var v = dataSpec[k];
            if (Array.isArray(v) && v.length >= 2 && typeof v[0] === 'string') return true;
        }
        return false;
    }

    function getValue(out, path) {
        var parts = path.split('.');
        var key = parts[0];
        var rest = parts.slice(1).join('.');
        var val = out[key];
        if (val === undefined) return 0;
        if (!rest) return val;
        if (Array.isArray(val)) {
            var sum = 0;
            for (var i = 0; i < val.length; i++) sum += Number(val[i][rest]) || 0;
            return sum;
        }
        return val[rest] !== undefined ? Number(val[rest]) || 0 : 0;
    }

    function evalFormula(out, formula) {
        if (!Array.isArray(formula) || formula.length < 2) return 0;
        var cmd = formula[0];
        var negative = formula[formula.length - 1] === 'negative';
        var args = negative ? formula.slice(1, -1) : formula.slice(1);
        var result = 0;
        if (cmd === 'sum') {
            if (args.length === 1) result = getValue(out, args[0]);
            else if (args.length >= 2 && args[args.length - 1] === 'number') {
                var paths = args.slice(0, -1);
                for (var p = 0; p < paths.length; p++) result += getValue(out, paths[p]);
            }
        } else if (cmd === 'percent_of' && args.length >= 3) {
            var base = getValue(out, args[0]);
            var pct = getValue(out, args[1]);
            result = base * pct / 100;
        }
        return negative ? -result : result;
    }

    function computeFormulas(out, dataSpec, src) {
        out[src] = {};
        for (var key in dataSpec) {
            var formula = dataSpec[key];
            if (Array.isArray(formula) && formula.length >= 2) {
                out[src][key] = evalFormula(out, formula);
            }
        }
        return out[src];
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
