// api_loader.js
// Загрузка данных через API для элементов с data-source="api"

document.addEventListener('DOMContentLoaded', () => {
    // Находим все элементы с атрибутом data-source="api"
    const apiElements = document.querySelectorAll('[data-source="api"]');
    
    if (apiElements.length === 0) {
        return;
    }
    
    console.log(`Найдено ${apiElements.length} элементов для загрузки через API`);
    
    // Функция для загрузки данных одного элемента
    function loadApiData(element) {
        const apiUrl = element.getAttribute('data-api-url');
        
        if (!apiUrl) {
            console.warn('Элемент с data-source="api" не имеет атрибута data-api-url:', element);
            return;
        }
        
        // Загружаем данные
        fetch(apiUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.text();
            })
            .then(data => {
                // Специальная обработка для real_time (формат JSON)
                if (apiUrl && apiUrl.includes('real_time')) {
                    try {
                        const timeData = JSON.parse(data.trim());
                        // Используем размер из PHP или по умолчанию 50%
                        const secondsSize = timeData.secondsSize || 50;
                        // Создаем HTML структуру с разными размерами
                        const html = `<span style="font-size: 100%;">${timeData.main}</span><span style="font-size: ${secondsSize}%;">:${timeData.seconds}</span>`;
                        element.innerHTML = html;
                        console.log(`✅ Время обновлено: ${timeData.main}:${timeData.seconds}`);
                    } catch (e) {
                        console.error('Ошибка парсинга JSON для real_time:', e, data);
                        // Если не JSON, используем как обычный текст
                        element.textContent = data.trim();
                    }
                } else {
                    // Для остальных элементов используем обычный текст
                    element.textContent = data.trim();
                }
            })
            .catch(error => {
                console.error(`❌ Ошибка загрузки данных из ${apiUrl}:`, error);
            });
    }
    
    // Загружаем данные сразу для всех элементов
    apiElements.forEach(element => {
        loadApiData(element);
    });
    
    // Определяем, какие элементы нужно обновлять в реальном времени
    // (например, время обновляется каждую секунду)
    apiElements.forEach(element => {
        const apiUrl = element.getAttribute('data-api-url');
        
        // Если это скрипт времени (real_time), обновляем каждую секунду
        if (apiUrl && apiUrl.includes('real_time')) {
            setInterval(() => {
                loadApiData(element);
            }, 1000); // Обновляем каждую секунду
        }
        // Для других элементов можно добавить другие интервалы или оставить без автообновления
    });
});

