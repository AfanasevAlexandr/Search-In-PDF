from pdf2image import convert_from_path
import pytesseract
import cv2
import matplotlib.pyplot as plt
import os
import json

# путь до папки с poppler.exe
poppler_path = r'poppler\bin'
# путь до tesseract.exe
pytesseract.pytesseract.tesseract_cmd = r'Tesseract-OCR\tesseract.exe'
custom_config = r'--oem 3 --psm 6'


# конвертируем PDF в изображения
def convert_pdf_to_image(pdf_file):
    # выделяем имя файла
    inputfile = os.path.split(pdf_file)[1]
    img_files = []

    # если фалы есть в кэше, то берем их оттуда
    if os.path.isdir(os.path.join('cache', inputfile)):
        for file in os.listdir(os.path.join('cache', inputfile)):
            file_name, file_extension = os.path.splitext(file)
            if file_extension.lower() == '.png':
                img_files.append(os.path.join('cache', inputfile, file))
    # иначе конвертируем
    else:
        print('Запускаем poppler.exe. Подождите....')
        pages = convert_from_path(inputfile, dpi=300, poppler_path=poppler_path, grayscale=True)
        os.mkdir(os.path.join('cache', inputfile))

        for i, page in enumerate(pages, start=1):
            print(f'Конвертируем страницу {i} из {len(pages)}')
            page.save(os.path.join('cache', inputfile, f'page_{i}.png'), 'PNG')
            img_files.append(os.path.join('cache', inputfile, f'page_{i}.png'))

    return img_files


def recognize_text(pdf_file=None, img_files=None):
    # выделяем имя файла
    inputfile = os.path.split(pdf_file)[1]

    data = []
    # если файл уже обработан, загружаем данные из кэша
    if os.path.isfile(os.path.join('cache', inputfile, 'data.txt')):
        with open(os.path.join('cache', inputfile, 'data.txt'), 'r', encoding="utf-8") as datafile:
            data = json.load(datafile)

    # иначе распознаем и сохраням в файл в кэш
    else:
        for i, img in enumerate(img_files, start=1):
            print(f'Анализ страницы {i} из {len(img_files)}')
            image = cv2.imread(img)
            data.append(pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, lang='rus', config=custom_config))

        # сохраняем данные в файл
        with open(os.path.join('cache', inputfile, 'data.txt'), 'w', encoding="utf-8") as datafile:
            json.dump(data, datafile)

    return data


def search_text():
    # выбор файла
    while True:
        pdf_file = input('Укажите путь к файлу PDF: ').strip()
        if os.path.isfile(pdf_file):
            file_name, file_extension = os.path.splitext(pdf_file)
            if file_extension.lower() == '.pdf':
                img_files = convert_pdf_to_image(pdf_file)
                data = recognize_text(pdf_file=pdf_file, img_files=img_files)
                break
            else:
                print('Формат файла не поддреживается!')
        else:
            print('Файл не найден!')

    # поиск совпадений
    while True:
        target_words = input('Что ищем? ').split(',')
        target_words = list(map(str.lower, target_words))
        target_words = list(map(str.strip, target_words))
        target_words = list(filter(None, target_words))

        # если поисковый запрос не пустой
        if target_words:
            for i, img_data in enumerate(data):
                print(f'Ищем на странице {i+1}')
                # word_occurences = [i for i, word in enumerate(img_data["text"]) if target_word.lower() in word.lower()]
                word_occurences = []
                for j, word in enumerate(img_data["text"]):
                    for t_word in target_words:
                        if t_word.lower().strip() in word.lower():
                            word_occurences.append(j)

                # если совпадения найдены рисуем рамки и сохраняем изображение
                # if len(word_occurences) > 0:
                if word_occurences:
                    image = cv2.imread(img_files[i])
                    image_copy = image.copy()

                    for occ in word_occurences:
                        # извлекаем ширину, высоту, верхнюю и левую позицию для обнаруженного слова
                        w = img_data["width"][occ]
                        h = img_data["height"][occ]
                        l = img_data["left"][occ]
                        t = img_data["top"][occ]

                        # определяем все точки окружающей рамки
                        p1 = (l, t)
                        p2 = (l + w, t)
                        p3 = (l + w, t + h)
                        p4 = (l, t + h)

                        # рисуем 4 линии (прямоугольник)
                        image_copy = cv2.line(image_copy, p1, p2, color=(255, 0, 0), thickness=3)
                        image_copy = cv2.line(image_copy, p2, p3, color=(255, 0, 0), thickness=3)
                        image_copy = cv2.line(image_copy, p3, p4, color=(255, 0, 0), thickness=3)
                        image_copy = cv2.line(image_copy, p4, p1, color=(255, 0, 0), thickness=3)

                    # создаем отдельную папку с результатами для каждого запроса
                    folder_name = os.path.join('result', str(os.path.split(pdf_file)[1]), ''.join(target_words))
                    if not os.path.isdir(folder_name):
                        os.makedirs(folder_name)

                    plt.imsave(os.path.join(folder_name, f'page_{i+1}.png'), image_copy)
                    print(f'Найдено совпадений: {len(word_occurences)} ')
                else:
                    print('Ничего не найдено.')
        else:
            print('Введен путой поисковый запрос.')


def main():
    # создаем папки для кэша и результатов поиска
    if not os.path.isdir('result'):
        os.mkdir('result')
    if not os.path.isdir('cache'):
        os.mkdir('cache')
        
    search_text()


if __name__ == "__main__":
    main()
