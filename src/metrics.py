import re
from math import log
from collections import Counter
from difflib import SequenceMatcher

def check_h1_tags(description):
    """
    Проверяет наличие ровно одного непустого заголовка в тегах <h1>
    Возвращает 1 — если есть, 0 — если нет
    """
    h1_pattern = r'<h1>(.*?)</h1>'
    matches = re.findall(h1_pattern, description, re.DOTALL | re.IGNORECASE)

    # Должен быть ровно один непустой заголовок
    if len(matches) != 1:
        return 0

    # Проверяем, что заголовок не пустой и не состоит только из пробелов
    h1_content = matches[0].strip()
    if not h1_content or len(h1_content) < 3:
        return 0

    return 1

def similarity_ratio(a, b):
    """Вычисляет коэффициент схожести строк (0.0-1.0)"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def calculate_lexical_diversity(text):
    """
    Вычисляет лексическое разнообразие с учётом уникальности слов
    и штрафует за повторяющиеся последовательности
    """
    # Удаляем HTML-теги
    clean_text = re.sub(r'<[^>]+>', '', text)
    words = re.findall(r'\b\w+\b', clean_text.lower())

    if len(words) < 5:  # Минимальное количество слов для анализа
        return 0.0

    # Подсчитываем частоту слов
    word_counts = Counter(words)
    total_words = len(words)
    unique_words = len(word_counts)

    # Базовая метрика разнообразия
    base_diversity = unique_words / total_words

    # Штраф за повторяющиеся последовательности
    repeat_penalty = 1.0
    for i in range(len(words) - 3):
        sequence = ' '.join(words[i:i+3])
        if sequence in ' '.join(words[i+3:]):
            repeat_penalty *= 0.7  # Штраф за повторение последовательностей

    # Комбинированная метрика
    diversity = base_diversity * repeat_penalty
    return min(diversity, 1.0)

def check_paragraph_formatting(description):
    """
    Строгая проверка форматирования абзацев
    """
    p_pattern = r'<p>(.*?)</p>'
    paragraphs = re.findall(p_pattern, description, re.DOTALL | re.IGNORECASE)

    if not paragraphs:
        return 0.0

    valid_count = 0
    for paragraph in paragraphs:
        # Убираем теги и проверяем содержание
        clean_content = re.sub(r'<[^>]+>', '', paragraph).strip()

        # Абзац должен содержать значимый текст (не только теги)
        if (len(clean_content) >= 10 and  # Минимальная длина
            not clean_content.isdigit() and  # Не только цифры
            len(set(clean_content.split())) >= 3):  # Минимум 3 уникальных слова
            valid_count += 1

    return valid_count / len(paragraphs) if paragraphs else 0.0

def is_characteristic_present(text, char_name, char_value, threshold=0.6):
    """
    Более строгая проверка наличия характеристики
    """
    text_lower = text.lower()
    char_name_lower = char_name.lower()
    char_value_lower = str(char_value).lower()

    # Проверяем полное совпадение или значимое частичное
    if (char_name_lower in text_lower and char_value_lower in text_lower):
        return True

    # Проверяем семантическую близость с более высоким порогом
    name_similarity = similarity_ratio(char_name_lower, text_lower)
    value_similarity = similarity_ratio(char_value_lower, text_lower)

    # Требуем высокой схожести для обеих частей характеристики
    return (name_similarity >= threshold and value_similarity >= threshold)

def check_paragraph_tags(description, characteristics, threshold=0.6):
    """
    Строгая проверка абзацев: один абзац = одна характеристика
    """
    if not characteristics:
        return 1.0

    p_pattern = r'<p>(.*?)</p>'
    paragraphs = re.findall(p_pattern, description, re.DOTALL | re.IGNORECASE)

    if not paragraphs:
        return 0.0

    # Штрафуем за дубликаты абзацев
    unique_paragraphs = set()
    duplicate_penalty = 1.0

    for paragraph in paragraphs:
        clean_text = re.sub(r'<[^>]+>', '', paragraph).strip()
        if clean_text in unique_paragraphs:
            duplicate_penalty *= 0.5  # Сильный штраф за дубликаты
        unique_paragraphs.add(clean_text)

    # Сопоставляем характеристики с абзацами
    char_matched = {char: False for char in characteristics}
    valid_matches = 0

    for paragraph in paragraphs:
        clean_text = re.sub(r'<[^>]+>', '', paragraph).strip()

        # Ищем характеристику в абзаце
        matched_chars = []
        for char_name, char_value in characteristics.items():
            if is_characteristic_present(clean_text, char_name, char_value, threshold):
                matched_chars.append(char_name)

        # Абзац должен содержать ровно одну характеристику
        if len(matched_chars) == 1 and not char_matched.get(matched_chars[0], False):
            char_matched[matched_chars[0]] = True
            valid_matches += 1

    # Учитываем штраф за дубликаты
    coverage_score = sum(1 for matched in char_matched.values() if matched) / len(characteristics)
    return coverage_score * duplicate_penalty

def check_all_characteristics_covered(description, characteristics, threshold=0.5):
    """
    Проверяет coverage характеристик с учётом уникальности
    """
    if not characteristics:
        return 1.0

    clean_description = re.sub(r'<[^>]+>', '', description)
    found_chars = set()

    for char_name, char_value in characteristics.items():
        if is_characteristic_present(clean_description, char_name, char_value, threshold):
            found_chars.add(char_name)

    return len(found_chars) / len(characteristics)

def check_text_quality(description):
    """
    Новая функция: проверяет общее качество текста
    """
    clean_text = re.sub(r'<[^>]+>', '', description)
    words = clean_text.split()

    if len(words) < 10:
        return 0.0

    # Проверяем разнообразие (повторы, уникальность)
    word_counts = Counter(words)
    unique_ratio = len(word_counts) / len(words)

    # Штрафуем за слишком частые повторы
    repeat_penalty = 1.0
    for word, count in word_counts.items():
        if count > len(words) * 0.1:  # Слово повторяется более 10% текста
            repeat_penalty *= 0.7

    return min(unique_ratio * repeat_penalty, 1.0)

def calculate_total_score(description, characteristics):
    """
    Пересмотренная система оценки с более строгими критериями
    """
    # Выполняем все проверки
    h1_score = check_h1_tags(description)
    paragraph_score = check_paragraph_tags(description, characteristics, threshold=0.7)
    coverage_score = check_all_characteristics_covered(description, characteristics, threshold=0.6)
    diversity_score = calculate_lexical_diversity(description)
    formatting_score = check_paragraph_formatting(description)
    text_quality_score = check_text_quality(description)

    # Новые весовые коэффициенты (увеличиваем вес за качество)
    weights = {
        'h1': 0.10,
        'paragraphs': 0.25,
        'coverage': 0.15,
        'diversity': 0.20,
        'formatting': 0.15,
        'quality': 0.15  # Новый критерий качества текста
    }

    total_score = (
        h1_score * weights['h1'] +
        paragraph_score * weights['paragraphs'] +
        coverage_score * weights['coverage'] +
        diversity_score * weights['diversity'] +
        formatting_score * weights['formatting'] +
        text_quality_score * weights['quality']
    ) * 100

    return {
        'total_score': round(total_score, 2),
        'detailed_scores': {
            'h1_present': h1_score,
            'paragraphs_validation': round(paragraph_score, 2),
            'characteristics_coverage': round(coverage_score, 2),
            'lexical_diversity': round(diversity_score, 2),
            'paragraph_formatting': round(formatting_score, 2),
            'text_quality': round(text_quality_score, 2)
        }
    }

# Пример использования
if __name__ == "__main__":
    test_description = """
    <h1>Смартфон Premium X</h1>
    <p>Данная модель обладает превосходным дисплеем размером 6.7 дюймов.</p>
    <p>Основная камера 108 мегапикселей обеспечивает отличное качество фото.
    <p>Процессор Snapdragon 8 второго поколения обеспечивает высокую производительность.</p>
    """

    test_characteristics = {
        'экран': '6.7 дюймов',
        'камера': '108 Мп',
        'батарея': '5000 мАч',
        'процессор': 'Snapdragon 8 Gen 2'
    }

    result = calculate_total_score(test_description, test_characteristics)
    print("Общий скор:", result['total_score'])
    print("Детальные результаты:", result['detailed_scores'])