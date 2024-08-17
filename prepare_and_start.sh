#!/usr/bin/bash


print_help() {
    echo "usage"
    echo "    prepare_and_start.sh <python script>"
    echo "Запускает виртуальное окружение, устанавливает необходимые библиотеки и запускает указанный скрипт"
    echo "main.py - основа бота"
    echo "summarize.py - подведение итогов по расписанию"
}


# Проверка на наличие аргумента (запускаемый файл)
# main.py - основа бота
# summarize.py - подведение итогов по расписанию


if [ $# != "1" ]; then
    print_help
    exit
fi


# Проверка на наличие виртуального окружения

if [ -d "venv" ]; then
    echo  "Найдено виртуальное окружение"
    source ./venv/bin/activate
else
    echo "Не найдено виртуальное окружение"
    echo "Создание виртуального окружение"

    if python3 -m venv venv; then
        echo "Виртуальное окружение создано"
        source ./venv/bin/activate
    else
        echo "Не удалось создать виртуальное окружение"
        exit 1
    fi
fi


# Установка необходимых библиотек

pip install -r requirements.txt


# Запуск указанного скрипта

python3 "$1"