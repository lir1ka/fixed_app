# fixed_app

## Инструкция по сборке и запуску приложения

Для сборки и запуска приложения выполните следующие команды:

```bash
docker build -t fixed_app .
docker run -p 5000:5000 fixed_app
```
## Ниже будут представлены исправления уявзимостей, которые содержатся в этом приложении
### Исправление XXS уязвимости
   Добавление функции escape() из Flask для обработки пользовательских данных (book_title и review_text) гарантирует, что любые HTML-теги или JavaScript, содержащиеся в этих данных, будут экранированы. Удаление фильтра | safe в шаблонах Jinja2 убирает возможность отключения экранирования HTML. Это важно, потому что даже если данные были безопасно обработаны на стороне сервера, использование | safe в шаблоне могло бы всё равно позволить вредоносному коду выполниться. Удаление этого фильтра гарантирует, что все данные будут автоматически экранироваться при их отображении, устраняя таким образом риск XSS-атак.
   Также можно использовать CSP (Content Security Policy), что позволит указать, откуда браузер должен загружать ресурсы и блокировать загрузку вредоносных скриптов.
### Исправление Path Traversal и IDOR уязвимостей:
   Добавлена проверка на то, что пользователь обращается к безопасному каталогу (каталогу, где хранятся обложки книг). А также проверка на то, пользователь обращается к обложке, которая есть в базе данных, то есть доступна для просмотра.
   Реализовано с помощью функций os.path.abspath, os.path.join.

