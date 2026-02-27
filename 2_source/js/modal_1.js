// Универсальный скрипт для модальных окон
document.addEventListener('DOMContentLoaded', function() {
    
    // Открытие модального окна
    document.addEventListener('click', function(e) {
        const trigger = e.target.closest('[data-modal]');
        if (trigger) {
            e.preventDefault();
            const modalId = trigger.getAttribute('data-modal');
            const modal = document.getElementById(modalId) || document.querySelector('[id="' + modalId + '"]');
            if (modal) {
                modal.classList.add('active');
                modal.scrollTop = 0; // Прокручиваем модалку к началу
                document.body.style.overflow = 'hidden'; // Блокируем скролл
                
                // Рендерим данные из БД (если есть контейнеры с data-template внутри модального окна)
                if (window.dbRenderer) {
                    setTimeout(async () => {
                        try {
                            await window.dbRenderer.renderAll();
                            if (window.hideClientSearchLists) window.hideClientSearchLists();
                        } catch (err) {
                            console.error('Ошибка при рендере модалки:', err);
                        }
                    }, 50);
                }
            }
        }
    });
    
    // Закрытие по клику на фон модалки
    document.addEventListener('click', function(e) {
        // Проверяем что это сама модалка (класс начинается с modal)
        const classList = Array.from(e.target.classList);
        const isModal = classList.some(cls => cls.startsWith('modal'));
        if (isModal && e.target.classList.contains('active')) {
            e.target.classList.remove('active');
            document.body.style.overflow = ''; // Разблокируем скролл
        }
    });
    
    // Закрытие по клику на кнопку закрытия
    document.addEventListener('click', function(e) {
        const closeBtn = e.target.closest('[data-modal-close]');
        if (closeBtn) {
            const modal = closeBtn.closest('[class*="modal"]');
            if (modal) {
                modal.classList.remove('active');
                document.body.style.overflow = '';
            }
        }
    });
    
    // Закрытие по клику на иконку close
    document.addEventListener('click', function(e) {
        const closeIcon = e.target.closest('.content-close');
        if (closeIcon) {
            const modal = closeIcon.closest('[class*="modal"]');
            if (modal && modal.classList.contains('active')) {
                modal.classList.remove('active');
                document.body.style.overflow = '';
            }
        }
    });
    
    // Закрытие по Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const activeModal = document.querySelector('[class*="modal"].active');
            if (activeModal) {
                activeModal.classList.remove('active');
                document.body.style.overflow = '';
            }
        }
    });
    
    // Обработка toggle для чекбоксов
    document.addEventListener('change', function(e) {
        const checkbox = e.target.closest('input[type="checkbox"][data-toggle]');
        if (checkbox) {
            const toggleTarget = checkbox.getAttribute('data-toggle');
            const targetElement = document.querySelector(`.${toggleTarget}`);
            if (targetElement) {
                if (checkbox.checked) {
                    targetElement.classList.add('visible');
                } else {
                    targetElement.classList.remove('visible');
                }
            }
        }
    });
    
});

