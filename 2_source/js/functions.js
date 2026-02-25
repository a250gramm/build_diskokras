/**
 * Система функций для автоматических вычислений
 * Работает с objects_fun.json конфигурацией
 */

class FunctionsManager {
    constructor() {
        this.functions = {};
        this.results = {};
        this.init();
    }

    init() {
        // Ждем загрузки DOM
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }

    setup() {
        // Находим все элементы с функциями
        this.findFunctionElements();
        
        // Слушатели только при первой инициализации (делегирование через document)
        if (!this._listenersAttached) {
            this.attachInputListeners();
            this._listenersAttached = true;
        }
        
        // Первый расчет
        this.calculateAll();
    }

    /**
     * Обновить список input для сумм после динамического рендера (шаблоны, инклуды).
     * Вызывается из DatabaseRenderer после renderAll().
     */
    refreshAfterRender() {
        this.findFunctionElements();
        this.calculateAll();
    }

    /**
     * Находит элементы с data-function-sum атрибутами
     */
    findFunctionElements() {
        this.functions = {};
        const inputs = document.querySelectorAll('input[data-function-sum]');
        
        inputs.forEach(input => {
            const resultVar = input.getAttribute('data-function-sum');
            
            if (!this.functions[resultVar]) {
                this.functions[resultVar] = {
                    type: 'sum',
                    inputs: []
                };
            }
            
            // Добавляем input в список
            this.functions[resultVar].inputs.push(input);
        });
    }

    /**
     * Устанавливает слушателей на все input поля (один раз на document — делегирование)
     */
    attachInputListeners() {
        if (this._delegationBound) return;
        this._delegationBound = true;
        document.addEventListener('input', (e) => {
            const el = e.target;
            if (el && el.matches('input[data-function-sum]')) {
                const start = el.selectionStart, end = el.selectionEnd;
                const raw = String(el.value || '').replace(/\s/g, '').replace(',', '.');
                const digitsAndDot = raw.replace(/[^\d.]/g, '').split('.');
                const intPart = (digitsAndDot[0] || '').slice(0, 15);
                const decPart = digitsAndDot.length > 1 ? (digitsAndDot[1] || '').slice(0, 2) : '';
                const rawNumStr = decPart ? intPart + '.' + decPart : intPart;
                const formatted = this.formatInputValue(rawNumStr);
                const digitsBeforeCursor = String(el.value || '').slice(0, start).replace(/\D/g, '').length;
                let newPos = 0, digitCount = 0;
                for (let i = 0; i < formatted.length; i++) {
                    if (digitCount >= digitsBeforeCursor) break;
                    if (/\d/.test(formatted[i])) digitCount++;
                    newPos = i + 1;
                }
                el.value = formatted;
                el.setSelectionRange(newPos, newPos);
                this.calculateAll();
                return;
            }
            if (el && (el.matches('input[type="text"]') || el.matches('input[type="number"]'))) {
                this.calculateAll();
            }
        });
        document.addEventListener('blur', (e) => {
            const el = e.target;
            if (el && el.matches('input[data-function-sum]')) {
                const raw = String(el.value || '').replace(/\s/g, '');
                const num = parseFloat(raw);
                if (!isNaN(num)) {
                    el.value = this.formatNumber(num);
                }
            }
        }, true);
    }

    /**
     * Выполняет все функции
     */
    calculateAll() {
        for (const [varName, config] of Object.entries(this.functions)) {
            let result = 0;
            
            switch (config.type) {
                case 'sum':
                    result = this.calculateSum(config);
                    break;
                case 'avg':
                    result = this.calculateAverage(config);
                    break;
                case 'count':
                    result = this.calculateCount(config);
                    break;
            }
            
            // Сохраняем результат
            this.results[varName] = result;
        }
        
        // Обновляем отображение
        this.updateDisplay();
    }

    /**
     * Суммирование значений
     * Для полей внутри .fp04-field учитываем только если строка выбрана (.selected)
     */
    calculateSum(config) {
        const inputs = config.inputs || [];
        let sum = 0;
        
        inputs.forEach(input => {
            const row = input.closest('.fp04-field');
            if (row && !row.classList.contains('selected')) return;
            const raw = String(input.value || '').replace(/\s/g, '');
            const value = parseFloat(raw) || 0;
            sum += value;
        });
        
        return sum;
    }

    /**
     * Среднее значение
     */
    calculateAverage(config) {
        const sum = this.calculateSum(config);
        const inputs = config.inputs || [];
        const count = inputs.filter(input => input.value !== '').length;
        
        return count > 0 ? sum / count : 0;
    }

    /**
     * Подсчет заполненных полей
     */
    calculateCount(config) {
        const inputs = config.inputs || [];
        return inputs.filter(input => input.value !== '').length;
    }

    /**
     * Обновляет отображение результатов
     */
    updateDisplay() {
        // Обновляем элементы с data-function-result
        document.querySelectorAll('[data-function-result]').forEach(el => {
            const varName = el.getAttribute('data-function-result');
            const value = this.results[varName] || 0;
            
            // Форматируем число
            const formatted = this.formatNumber(value);
            
            // Обновляем содержимое (formatted уже строка с пробелами)
            if (el.tagName === 'INPUT') {
                el.value = formatted;
            } else {
                el.textContent = formatted;
            }
        });
    }

    /**
     * Форматирует число с пробелами как разделитель тысяч (1 000, 10 000, 100 000)
     */
    formatNumber(value) {
        const num = Math.round(value * 100) / 100;
        const parts = String(num).split('.');
        const intPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
        return parts.length > 1 ? intPart + '.' + parts[1] : intPart;
    }

    /**
     * Форматирует строку ввода (цифры и точка) с пробелами в момент набора
     */
    formatInputValue(str) {
        if (!str) return '';
        const parts = String(str).replace(/\s/g, '').split('.');
        const intPart = (parts[0] || '').replace(/\D/g, '');
        const decPart = parts.length > 1 ? (parts[1] || '').replace(/\D/g, '').slice(0, 2) : '';
        const formattedInt = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
        return decPart ? formattedInt + '.' + decPart : formattedInt;
    }
}

// Инициализация при загрузке страницы
const functionsManager = new FunctionsManager();

/**
 * Система рендеринга элементов из базы данных
 */
class DatabaseRenderer {
    constructor() {
        this.dataCache = {}; // Кэш загруженных данных
        this.init();
    }

    init() {
        // Запускаем рендеринг при открытии модального окна
        document.addEventListener('click', (e) => {
            const trigger = e.target.closest('[data-modal]');
            if (trigger) {
                console.log('🔵 DatabaseRenderer: Открыто модальное окно, запускаю рендеринг...');
                // Ждем, пока модальное окно откроется
                setTimeout(() => {
                    this.renderAll();
                }, 200);
            }
        });
        
        // Также пробуем при загрузке (если элементы уже видны)
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                setTimeout(() => this.renderAll(), 500);
            });
        } else {
            setTimeout(() => this.renderAll(), 500);
        }
    }

    /**
     * Рендерит все шаблоны с базами данных
     */
    async renderAll() {
        console.log('===========================================');
        console.log('DatabaseRenderer: renderAll started');
        console.log('===========================================');
        
        // Находим все контейнеры с data-template
        const containers = document.querySelectorAll('[data-template]');
        console.log('DatabaseRenderer: Найдено контейнеров с data-template:', containers.length);
        
        if (containers.length === 0) {
            console.warn('⚠️ DatabaseRenderer: Контейнеры с data-template не найдены!');
            return;
        }
        
        for (const container of containers) {
            console.log('DatabaseRenderer: Обрабатываю контейнер:', container);
            let templateStr = container.getAttribute('data-template');
            // Декодируем HTML entities если они есть
            if (templateStr && templateStr.includes('&quot;')) {
                const textarea = document.createElement('textarea');
                textarea.innerHTML = templateStr;
                templateStr = textarea.value;
            }
            const template = JSON.parse(templateStr);
            
            // Ищем источники данных (api1, api2, ...)
            // Ищем в родительском элементе и его родителях (для случая когда span в div.wr-fields, а container в div.gr)
            const bdSources = {};
            let searchContainer = container.parentElement; // div.gr
            // Если не нашли, ищем в родителе родителя (div.wr-fields)
            if (searchContainer) {
                const bdSpans = searchContainer.querySelectorAll('span[data-bd-source]');
                if (bdSpans.length === 0 && searchContainer.parentElement) {
                    // Ищем в родителе родителя
                    searchContainer = searchContainer.parentElement;
                }
            }
            
            console.log('DatabaseRenderer: Контейнер для поиска span:', searchContainer);
            
            if (searchContainer) {
                const bdSpans = searchContainer.querySelectorAll('span[data-bd-source]');
                console.log('DatabaseRenderer: Найдено span-ов:', bdSpans.length);
                
                for (const span of bdSpans) {
                    const apiName = span.getAttribute('data-bd-api'); // api1, api2, ...
                    const sourceName = span.getAttribute('data-bd-source'); // front_pay_met, front_wall, ...
                    const url = span.getAttribute('data-bd-url');
                    const link = span.getAttribute('data-bd-link');
                    
                    console.log('DatabaseRenderer: span ->', apiName, sourceName, url, link);
                    
                    if (apiName) {
                        bdSources[apiName] = {
                            source: sourceName, // Имя источника для поиска script тега
                            url: url,
                            link: link,
                            data: null
                        };
                    }
                }
            }
            
            console.log('DatabaseRenderer: Источники данных:', bdSources);
            
            // Загружаем данные
            await this.loadDataSources(bdSources);
            
            // Если container находится внутри div.gr, добавляем элементы напрямую в div.gr
            const parentGr = container.closest('.gr');
            const renderContainer = parentGr || container;
            
            console.log('DatabaseRenderer: renderContainer=', renderContainer, 'parentGr=', parentGr, 'container=', container);
            
            // Очищаем renderContainer перед добавлением элементов
            if (renderContainer !== container) {
                renderContainer.innerHTML = '';
            }
            
            // Рендерим шаблон
            this.renderTemplate(renderContainer, template, bdSources);
            
            // Удаляем пустой container если элементы были добавлены в parentGr
            if (parentGr && parentGr !== container && container.parentNode) {
                container.remove();
            }
        }
        
        // Подхватываем input[data-function-sum] из динамически созданных полей (инклуды) и пересчитываем суммы
        functionsManager.refreshAfterRender();
    }

    /**
     * Загружает JSON файл (работает с file:// протоколом)
     */
    loadJsonFile(url) {
        return new Promise((resolve, reject) => {
            // Пробуем fetch (работает с http/https)
            if (window.location.protocol === 'http:' || window.location.protocol === 'https:') {
                fetch(url)
                    .then(res => {
                        if (!res.ok) throw new Error(`HTTP ${res.status}`);
                        return res.json();
                    })
                    .then(resolve)
                    .catch(reject);
                return;
            }
            
            // Для file:// используем XMLHttpRequest
            const xhr = new XMLHttpRequest();
            xhr.open('GET', url, true);
            xhr.onreadystatechange = function() {
                console.log(`🔵 XMLHttpRequest ${url}: readyState=${xhr.readyState}, status=${xhr.status}, responseLength=${xhr.responseText ? xhr.responseText.length : 0}`);
                if (xhr.readyState === 4) {
                    if (xhr.status === 0 || xhr.status === 200) {
                        if (!xhr.responseText || xhr.responseText.trim() === '') {
                            reject(new Error(`Файл пустой или не найден: ${url}`));
                            return;
                        }
                        try {
                            const data = JSON.parse(xhr.responseText);
                            resolve(data);
                        } catch (e) {
                            console.error(`❌ Ошибка парсинга JSON для ${url}:`, e);
                            console.error(`   responseText (первые 200 символов):`, xhr.responseText.substring(0, 200));
                            reject(new Error(`Ошибка парсинга JSON: ${e.message}`));
                        }
                    } else {
                        reject(new Error(`HTTP ${xhr.status}`));
                    }
                }
            };
            xhr.onerror = function() {
                console.error(`❌ XMLHttpRequest ошибка для ${url}`);
                reject(new Error('Ошибка сети'));
            };
            xhr.send();
        });
    }

    /**
     * Загружает данные из всех источников
     */
    async loadDataSources(bdSources) {
        console.log('DatabaseRenderer: Загружаем данные из источников:', Object.keys(bdSources));
        
        const promises = [];
        
        for (const [apiName, config] of Object.entries(bdSources)) {
            console.log(`DatabaseRenderer: Проверяем ${apiName} (${config.url})`);
            
            // Сначала пробуем загрузить из script тега (встроенные данные)
            if (config.source) {
                const scriptTag = document.querySelector(`script[type="application/json"][data-bd-source="${config.source}"]`);
                if (scriptTag) {
                    try {
                        const data = JSON.parse(scriptTag.textContent);
                        console.log(`✅ ${config.source}: загружено из script тега ${data.length} записей`);
                        this.dataCache[config.url] = data;
                        config.data = data;
                        continue; // Пропускаем загрузку через fetch/XHR
                    } catch (e) {
                        console.warn(`⚠️ Ошибка парсинга данных из script тега для ${config.source}:`, e);
                    }
                }
            }
            
            // Если нет в script теге, загружаем через fetch/XHR
            if (!this.dataCache[config.url]) {
                console.log(`DatabaseRenderer: Загружаем ${config.url}...`);
                promises.push(
                    this.loadJsonFile(config.url)
                        .then(data => {
                            console.log(`✅ ${config.url}: загружено ${data.length} записей`);
                            this.dataCache[config.url] = data;
                            config.data = data;
                        })
                        .catch(err => {
                            console.error(`❌ Ошибка загрузки ${config.url}:`, err);
                            config.data = [];
                        })
                );
            } else {
                console.log(`DatabaseRenderer: Используем кэш для ${config.url}`);
                config.data = this.dataCache[config.url];
            }
        }
        
        await Promise.all(promises);
        console.log('DatabaseRenderer: Загрузка данных завершена');
    }

    /**
     * Рендерит шаблон с данными
     */
    renderTemplate(container, template, bdSources) {
        console.log('renderTemplate: container=', container, 'template=', template, 'bdSources=', bdSources);
        
        // Определяем основной источник данных (api1)
        const mainSource = bdSources['api1'];
        if (!mainSource || !mainSource.data) {
            console.warn('renderTemplate: Нет данных из api1', mainSource);
            return;
        }
        
        const mainData = mainSource.data;
        console.log('renderTemplate: mainData=', mainData);
        
        // Очищаем контейнер
        container.innerHTML = '';
        
        // template уже является шаблоном элемента (объект с ключами label, percent, etc)
        // Ищем ключ "cycle" - это явное указание на цикл
        // ИЛИ если это вложенный объект с ключом div_*, то извлекаем его
        let elementTemplate = template;
        
        // Функция для рекурсивного поиска cycle
        function findCycle(obj) {
            if (!obj || typeof obj !== 'object') return null;
            if (obj.cycle) return obj.cycle;
            for (const value of Object.values(obj)) {
                if (typeof value === 'object' && value !== null) {
                    const found = findCycle(value);
                    if (found) return found;
                }
            }
            return null;
        }
        
        const cycleContent = findCycle(template);
        let elementKey = null; // Сохраняем ключ div_* для определения класса
        if (cycleContent) {
            // Если есть ключ cycle, извлекаем div_* из него
            for (const [key, value] of Object.entries(cycleContent)) {
                if (key.startsWith('div_')) {
                    elementTemplate = value;
                    elementKey = key; // Сохраняем ключ
                    console.log('renderTemplate: Найден ключ cycle, извлечен шаблон', key);
                    break;
                }
            }
        } else {
            // Иначе ищем div_* ключ напрямую
            for (const [key, value] of Object.entries(template)) {
                if (key.startsWith('div_')) {
                    elementTemplate = value;
                    elementKey = key; // Сохраняем ключ
                    console.log('renderTemplate: Найден вложенный шаблон', key);
                    break;
                }
            }
        }
        
        console.log('renderTemplate: Используем шаблон', elementTemplate, 'ключ:', elementKey);
        
        // Если в том же wr-fields или в форме есть data-function-result — добавляем data-function-sum к полям (fun:total_price из инклудов)
        let sumVar = null;
        const wrFields = container.closest('.wr-fields');
        if (wrFields) {
            const resultEl = wrFields.querySelector('[data-function-result]');
            if (resultEl) sumVar = resultEl.getAttribute('data-function-result');
        }
        if (!sumVar) {
            const form = container.closest('form');
            if (form) {
                const resultEl = form.querySelector('[data-function-result]');
                if (resultEl) sumVar = resultEl.getAttribute('data-function-result');
            }
        }
        
        // Для каждой записи из основного источника
        for (const record of mainData) {
            const element = this.createElementFromTemplate(elementTemplate, record, bdSources, elementKey, sumVar);
            container.appendChild(element);
        }
        
        console.log('renderTemplate: Создано элементов:', container.children.length);
    }

    /**
     * Парсит синтаксис col: из ключа элемента
     * Возвращает {cleanKey, colInfo} где colInfo может быть null
     */
    parseColSyntax(key) {
        // Ищем паттерн " col:X,Y,Z" или " col:X%" или "-col:X%"
        const colPatternSpace = /\s+col:([0-9,%]+)/;
        const colPatternDash = /-col:([0-9,%]+)/;
        
        let match = key.match(colPatternSpace);
        let colPattern = colPatternSpace;
        
        if (!match) {
            match = key.match(colPatternDash);
            if (match) {
                colPattern = colPatternDash;
            }
        }
        
        if (!match) {
            return { cleanKey: key, colInfo: null };
        }
        
        const colValue = match[1];
        // Для "-col:X%" заменяем только ":X%", оставляя "-col" в cleanKey
        // Для " col:X%" заменяем полностью
        let cleanKey;
        if (colPattern === colPatternDash) {
            // Для "div_2-col:80%" -> "div_2-col" (убираем только ":80%", оставляя "-col")
            cleanKey = key.replace(/-col:([0-9,%]+)/, '-col').trim();
        } else {
            cleanKey = key.replace(colPattern, '').trim();
        }
        
        // Проверяем формат col:20% (процентная ширина)
        if (colValue.includes('%')) {
            const percentage = parseFloat(colValue.replace('%', ''));
            return {
                cleanKey: cleanKey,
                colInfo: {
                    type: 'percentage',
                    percentage: percentage
                }
            };
        }
        
        // Проверяем формат col:2,1,1 (адаптивные колонки)
        if (colValue.includes(',')) {
            const parts = colValue.split(',');
            if (parts.length === 3) {
                return {
                    cleanKey: cleanKey,
                    colInfo: {
                        type: 'adaptive',
                        desktop: parseInt(parts[0].trim()),
                        tablet: parseInt(parts[1].trim()),
                        mobile: parseInt(parts[2].trim())
                    }
                };
            } else if (parts.length === 1) {
                const cols = parseInt(parts[0].trim());
                return {
                    cleanKey: cleanKey,
                    colInfo: {
                        type: 'adaptive',
                        desktop: cols,
                        tablet: cols,
                        mobile: cols
                    }
                };
            }
        }
        
        // Просто число без запятых
        const cols = parseInt(colValue);
        return {
            cleanKey: cleanKey,
            colInfo: {
                type: 'adaptive',
                desktop: cols,
                tablet: cols,
                mobile: cols
            }
        };
    }

    /**
     * Создает элемент из шаблона
     */
    createElementFromTemplate(template, record, bdSources, elementKey = null, sumVar = null) {
        // Определяем тег и класс из шаблона
        const tagName = 'div';
        
        // Определяем класс из ключа элемента, обрабатывая синтаксис col:
        let className = 'field-paymet'; // По умолчанию
        let colInfo = null;
        
        if (elementKey) {
            // Парсим синтаксис col:
            const parsed = this.parseColSyntax(elementKey);
            const cleanKey = parsed.cleanKey;
            colInfo = parsed.colInfo;
            
            if (cleanKey.startsWith('div_')) {
                const suffix = cleanKey.replace(/^div[_-]/, '');
                // Если суффикс начинается с цифры (например, "1-col", "2-col"), добавляем префикс "content-"
                // — иначе CSS селектор .1-col невалиден. Для fp04-field, field-paymet — класс без префикса.
                if (suffix && /^\d/.test(suffix)) {
                    className = 'content-' + suffix;
                } else {
                    className = suffix;
                }
            }
        }
        
        const element = document.createElement(tagName);
        const classes = [className];
        
        // Добавляем классы для col: синтаксиса
        if (colInfo) {
            if (colInfo.type === 'adaptive') {
                classes.push(`_col-${colInfo.desktop}`);
            } else if (colInfo.type === 'percentage') {
                classes.push(`_col-${Math.round(colInfo.percentage)}pct`);
            }
        }
        
        element.className = classes.join(' ');
        
        // Обрабатываем каждый элемент шаблона
        for (const [key, value] of Object.entries(template)) {
            // Пропускаем элементы, ключ которых содержит звездочку (игнорируем их)
            if (key.includes('*')) {
                continue;
            }
            
            // Обрабатываем вложенные элементы (например, div_1-col:20%, div_2-col:80%)
            if (typeof value === 'object' && !Array.isArray(value) && value !== null) {
                // Это вложенный элемент - рекурсивно создаем его
                const nestedParsed = this.parseColSyntax(key);
                const nestedElement = this.createElementFromTemplate(value, record, bdSources, nestedParsed.cleanKey, sumVar);
                element.appendChild(nestedElement);
                continue;
            }
            
            if (!Array.isArray(value) || value.length < 2) {
                continue;
            }
            
            const elementType = value[0]; // "text", "img", etc
            const content = value[1]; // "api1:sub_cat", "api2:img", etc
            
            // Получаем значение
            let fieldValue = this.resolveValue(content, record, bdSources);
            // Если задан if:ключ — переводим значение через словарь из if.json (api1:stat_pay + if:stat_pay → подпись)
            if (value.length >= 3 && typeof value[2] === 'string' && value[2].startsWith('if:')) {
                const dictKey = value[2].slice(3);
                const ifLabels = window.ifLabels || (function() {
                    const el = document.querySelector('script[type="application/json"][data-if-labels]');
                    window.ifLabels = el ? JSON.parse(el.textContent) : {};
                    return window.ifLabels;
                })();
                if (ifLabels[dictKey] && fieldValue != null && fieldValue !== '') {
                    let label = ifLabels[dictKey][String(fieldValue).trim()];
                    if (Array.isArray(label) && label[0]) label = label[0];
                    if (typeof label === 'string') {
                        fieldValue = label.startsWith('text:') ? label.replace(/^text:/, '') : this.resolveValue(label, record, bdSources);
                    }
                }
            }
            
            // Создаем элемент
            if (elementType === 'text') {
                // Создаем text элемент только если есть значение
                // Проверяем что fieldValue существует и не пустое
                if (fieldValue && String(fieldValue).trim() !== '') {
                const textEl = document.createElement(key === 'label' ? 'label' : 'span');
                textEl.className = `content-${key}`;
                    textEl.textContent = String(fieldValue).trim();
                element.appendChild(textEl);
                }
                // Если fieldValue пустое - не создаем элемент text, чтобы не было пустого места
            } else if (elementType === 'input') {
                // Маркеры "required" или "required_one:groupId" — подтип со следующего индекса
                let idx = 1;
                let isRequired = false;
                let requiredOneGroup = null;
                if (value.length > 1 && typeof value[1] === 'string') {
                    if (value[1] === 'required') {
                        isRequired = true;
                        idx = 2;
                    } else if (value[1].startsWith('required_one:')) {
                        requiredOneGroup = value[1].replace(/^required_one:/, '');
                        idx = 2;
                    }
                }
                const inputSubtype = (value.length > idx) ? value[idx] : 'text';
                const inputEl = document.createElement('input');
                if (inputSubtype === 'radio' || inputSubtype === 'checkbox') {
                    inputEl.type = inputSubtype;
                    inputEl.className = `${key} input`;
                    const radioValue = (value.length >= idx + 2) ? this.resolveValue(value[idx + 1], record, bdSources) : fieldValue;
                    inputEl.value = (radioValue != null && radioValue !== '') ? String(radioValue) : '';
                    if (value.length > idx + 2 && typeof value[idx + 2] === 'string' && value[idx + 2].startsWith('name:')) {
                        inputEl.name = value[idx + 2].replace(/^name:/, '');
                    }
                } else {
                    // Формат "type:placeholder" (например "number:Введите сумму") — тип для мобильной клавиатуры
                    let inputType = 'text';
                    let placeholderText = fieldValue ? String(fieldValue).trim() : '';
                    if (typeof inputSubtype === 'string' && inputSubtype.includes(':')) {
                        const colonIdx = inputSubtype.indexOf(':');
                        inputType = inputSubtype.slice(0, colonIdx).trim();
                        placeholderText = inputSubtype.slice(colonIdx + 1).trim();
                    }
                    // type="number" несовместим с форматированием пробелами (1 234) — браузер сбрасывает значение.
                    // Используем type="text" + inputmode="decimal": клавиатура цифровая, значение можно форматировать.
                    if (inputType === 'number') {
                        inputEl.type = 'text';
                        inputEl.setAttribute('inputmode', 'decimal');
                    } else {
                        inputEl.type = inputType;
                    }
                    inputEl.className = `${key} input`;
                    if (placeholderText) {
                        inputEl.placeholder = placeholderText;
                    }
                    if (sumVar && key === 'field') {
                        inputEl.setAttribute('data-function-sum', sumVar);
                    }
                }
                if (isRequired) {
                    inputEl.setAttribute('required', '');
                }
                if (requiredOneGroup) {
                    inputEl.setAttribute('data-required-one', requiredOneGroup);
                }
                element.appendChild(inputEl);
            } else if (elementType === 'img') {
                // Создаем img элемент только если есть значение
                // Проверяем что fieldValue существует и не пустое
                if (fieldValue && String(fieldValue).trim() !== '') {
                const imgEl = document.createElement('img');
                    const imgValue = String(fieldValue).trim();
                // Путь к картинке может быть абсолютным или относительным
                    if (imgValue.startsWith('/')) {
                        // Если путь начинается с /, преобразуем в относительный
                        // /pavel_sto/... -> ../...
                        // /img/pm_kaspi.png -> ../img/pm_kaspi.png
                        // /logo_0.png -> ../img/logo_0.png (просто имя файла)
                        if (imgValue.includes('/pavel_sto')) {
                            imgEl.src = imgValue.replace('/pavel_sto', '..');
                        } else if (imgValue.startsWith('/img')) {
                            imgEl.src = '..' + imgValue;
                        } else {
                            const fileName = imgValue.replace(/^\//, '');
                            imgEl.src = `../img/${fileName}`;
                        }
                } else {
                        imgEl.src = `../${imgValue}`;
                }
                imgEl.alt = '';
                element.appendChild(imgEl);
                }
                // Если fieldValue пустое - не создаем элемент img, чтобы не было пустого места
            } else if (elementType === 'button') {
                const btnEl = document.createElement('button');
                btnEl.type = 'button';
                btnEl.className = `${key} button`;
                btnEl.textContent = fieldValue != null ? String(fieldValue).trim() : '';
                element.appendChild(btnEl);
            }
        }
        
        // Строки услуг (fp04-field): по клику по строке переключаем «выбран» и показываем/скрываем поле ввода и суффикс
        if (className === 'fp04-field') {
            element.addEventListener('click', function(e) {
                if (e.target.closest('input')) return;
                element.classList.toggle('selected');
                const fieldEl = element.querySelector('input.field') || element.querySelector('.field');
                const suffixEl = element.querySelector('.content-suffix') || element.querySelector('suffix');
                const setShow = function(el, show) {
                    if (!el) return;
                    el.style.setProperty('display', show ? 'block' : 'none', 'important');
                };
                const setShowInline = function(el, show) {
                    if (!el) return;
                    el.style.setProperty('display', show ? 'inline' : 'none', 'important');
                };
                if (element.classList.contains('selected')) {
                    setShow(fieldEl, true);
                    setShowInline(suffixEl, true);
                    if (fieldEl) {
                        fieldEl.focus();
                    }
                } else {
                    setShow(fieldEl, false);
                    setShowInline(suffixEl, false);
                }
                if (typeof functionsManager !== 'undefined') functionsManager.calculateAll();
            });
        }
        
        return element;
    }

    /**
     * Резолвит значение из записи или связанного источника
     */
    resolveValue(content, record, bdSources) {
        if (typeof content !== 'string' || !content.includes(':')) {
            return content;
        }
        
        const [source, field] = content.split(':');
        
        // Если это статический текст (text:...), возвращаем значение после :
        if (source === 'text') {
            return field || '';
        }
        
        // Если это api1 - берем из текущей записи
        if (source === 'api1') {
            return record[field] || '';
        }
        
        // Если это другой источник (api2, api3, ...)
        const sourceConfig = bdSources[source];
        if (sourceConfig && sourceConfig.data) {
            // Если есть связь - ищем связанную запись
            if (sourceConfig.link) {
                // link имеет формат "link:api1.id_wallet"
                const linkParts = sourceConfig.link.split(':');
                if (linkParts.length >= 2) {
                    const linkPath = linkParts[1]; // "api1.id_wallet"
                    const linkSource = linkPath.split('.')[0]; // "api1"
                    const linkField = linkPath.split('.')[1]; // "id_wallet"
                    
                    // Получаем значение из текущей записи
                    const linkValue = record[linkField];
                    
                    // Если значение пустое - возвращаем пустую строку
                    if (!linkValue) {
                        return '';
                    }
                    
                    // Ищем запись в связанном источнике где id === linkValue
                    const linkedRecord = sourceConfig.data.find(r => r.id === linkValue);
                    if (linkedRecord) {
                        return linkedRecord[field] || '';
                    }
                }
            } else {
                // Нет связи - берем первую запись (или как-то иначе)
                if (sourceConfig.data.length > 0) {
                    return sourceConfig.data[0][field] || '';
                }
            }
        }
        
        return '';
    }
}

// Инициализация рендерера БД
// Делаем глобальным для доступа из других скриптов (например, при открытии модального окна)
window.dbRenderer = new DatabaseRenderer();

// Спойлер в карточках списка заказов: по клику на «Детали» показываем/скрываем блок с текстом
document.addEventListener('click', function(e) {
    var btn = e.target.closest('.btn_details');
    if (!btn) return;
    var card = btn.closest('.card') || btn.closest('.div_card');
    if (!card) return;
    var spoiler = card.querySelector('.spoiler');
    if (spoiler) spoiler.classList.toggle('open');
});
