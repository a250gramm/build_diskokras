# Конфликты подключаемых инклюдов в объектах

## Как подключаются инклюды

- **Страница /shino:** `objects.json` → `main_btn.if["/shino"]` = `["include", "shino/form"]`  
  → `form.json` подставляет `servi_shino: ["include", "shino/servi"]`, `pay_met: ["include", "shino/pay_met"]`.

- **Страница /geo:** `objects.json` → `main_btn.if["/geo"]` → внутри разметки  
  `servi_shino: ["include", "servi_shino_geo"]`, `pay_met: ["include", "pay_met_geo"]`.

Все эти файлы при сборке попадают в один `objects_css`. В процессоре CSS группы разворачиваются в плоский словарь по **ключам правил** (например `div_fp04-field`, `div_field-paymet`).

## Конфликт 1: Одинаковые ключи CSS

| Ключи CSS | Файлы |
|-----------|--------|
| `div_fp04-field`, `div_fp04-field label`, `div_fp04-field .field`, `div_fp04-field suffix` | **shino/servi.json** и **servi_shino_geo.json** (одинаковый контент) |
| `cycle_gr8`, `div_field-paymet`, `div_field-paymet 1-col`, `div_field-paymet 2-col`, … | **shino/pay_met.json** и **pay_met_geo.json** (одинаковый контент) |

При обходе `objects_css` порядок такой: сначала добавляются стили из инклюдов для /shino (shino/servi, shino/pay_met), затем при разрешении /geo — servi_shino_geo и pay_met_geo. В плоский словарь записываются **те же ключи** ещё раз, поэтому **побеждает тот, кто обработан последним** (servi_shino_geo и pay_met_geo перезаписывают shino/servi и shino/pay_met).

Сейчас контент в парах файлов совпадает, поэтому визуально всё ок, но:
- на странице **shino** в итоге применяются стили из **servi_shino_geo** и **pay_met_geo** (порядок сборки);
- при расхождении контента между shino/servi и servi_shino_geo стили для shino будут не те, что ожидаются.

## Конфликт 2: design/objects_css.json

В `design/objects_css.json` группа «Поле с методом оплаты» задаёт правила с префиксом **main_btn** (например `main_btn div_field-paymet`, `main_btn cycle_gr8`). Это другие ключи, они не перезаписывают правила из инклюдов. В итоговом CSS есть и:

- `[data-path='main_btn'] div.field-paymet` (из design),
- `div.field-paymet` (из include).

Оба могут совпадать с одними и теми же элементами внутри модалки; итог зависит от порядка и специфичности правил в `style.css`.

## Рекомендация

Чтобы убрать конфликт по ключам и не зависеть от порядка:

- Для **/geo** в `objects.json` подключать те же инклюды, что и для shino:  
  `servi_shino: ["include", "shino/servi"]`, `pay_met: ["include", "shino/pay_met"]`.
- Тогда в `objects_css` остаётся один набор правил (из shino/servi и shino/pay_met), перезаписи нет.
- Файлы **servi_shino_geo.json** и **pay_met_geo.json** можно удалить или оставить только если позже понадобится отдельный контент/стили именно для geo.

После такого изменения конфликт контента подключаемых инклюдов в объектах будет снят.
