
### Как запустить backend приложение:

Форкнуть и клонировать репозиторий на компьютер и перейти в него в командной строке:
~~~bash
Ссылка исходного проекта: https://github.com/karpova-el-m/foodgram
~~~
~~~bash
После скачивания: cd foodgram/
~~~

В корневой директории создать и открыть через редактор файл для сохранения переменных окружения:

~~~bash
nano .env
~~~

Добавить в файл переменные и сохранить:
~~~bash
SECRET_KEY=...
DEBUG=True/False
ALLOWED_HOSTS=127.0.0.1,localhost,84.252.136.172,https://foodgram-project.ddnsking.com/
~~~

Перейти в директорию backend/foodgram_project/:
~~~bash
cd backend/foodgram_project/
~~~

Создать Docker volume:
~~~bash
docker volume create sqlite_data
~~~

Собрать образ из Dockerfile:
~~~bash
docker build -t foodgram_backend .
~~~

Запустить контейнер с Docker volume:
~~~bash
docker run --name foodgram_backend_container -p 8000:8000 -v sqlite_data:/data foodgram_backend
~~~

В отдельном окне терминала вновь запустить миграции:
~~~bash
docker exec foodgram_backend_container python manage.py migrate
~~~
