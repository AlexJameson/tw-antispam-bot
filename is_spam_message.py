import re

#def new_is_spam_message(text):
#    return has_spam_patterns(text)

def new_is_spam_message(text):
    # Main spam phrases
    main_spam_phrases = [
        # Recruitment patterns
        r"\bнужн[аы]?\s+(люди|сотрудники)\b",
        r"\bсотрудник(?:и|ов)?\s+для\s+удал[её]нной\s+работы\b",
        r"\bид[её]т\s+набор\s+людей\b",
        r"\bна\s+удал[её]нную\s+деятельность\b",
        r"\bместа\s+ограничены\b",
        r"\bмест\s+мало\b",
        r"\bвзаимовыгодн(?:ое|ая|ые)\s+сотрудничество\b",
        r"\bнужны\s+люди\s+для\s+сотрудничества\b",
        r"\bищ[уем]+\s+ответственного?\s+человека\b",
        
        # Earnings patterns
        r"\bот\s+\d+(-\d+)?\s*(\$|долларов?)\s+(в\s+день|в\s+месяц)?\b",
        r"\bзарабатывать\s+каждый\s+день\s+от\s+\d+\s*(\$|долларов?)\b",
        r"\bежедневн(?:ый|о)\s+доход\b",
        r"\bприбыль\s+ежедневно\b",
        r"\bвысокий\s+доход\b",
        r"\bдостойный\s+заработок\b",
        r"\bпассивный заработок\b",
        
        # Remote work patterns
        r"\bудал[её]нн(?:ый|ую|ая|ое)\s+(формат|работ[ау]|деятельность)\b",
        r"\bработ[ау]\s+на\s+удал[её]нке\b",
        r"\bудал[её]нная\s+занятость\b",
        r"\bудобный\s+график\b",
        r"\bработ[ау]\s+с\s+телефона\b",
        r"\bналичие\s+телефона\s+и\s+\d+\s+час(?:а|ов)?\s+свободного\s+времени\b",
        r"\bнужен только телефон\b",
        
        # Contact invitation patterns
        r"\bпишите\s+\+\s+в\s+личные\b",
        r"\bпишите\s+в\s+л[ис]\b",
        r"\bнапишите\s+в\s+личку\b",
        r"\bпиш[ие]те?\s+в\s+личные\s+сообщения\b",
        r"\bза\s+деталями\s+пишите\s+в\s+личные\b",
        r"\bжду\s+в\s+личных?\s+(сообщениях|смс)\b",
        r"\bинтереcно\?\s*пиши\s+в\s+личные\s+сообщения\b",

        # Training and support patterns
        r"\bбесплатное\s+обучение\b",
        r"\bподдержк[ау]\s+на\s+всех\s+этапах\b",
        r"\bдля\s+новичков\s+бесплатное\s+обучение\b",

        # Urgency patterns
        r"\bместа\s+ограничены\b",
        r"\bмест\s+мало\b",
        r"\bсрочно\b",

        # Adult content patterns
        r"\bбот[,\.]?\s+где\s+собраны\s+все\s+сливы\b",
        r"\bфото[,\.]?\s+видео\s+девушек\b",
        r"\bих\s+переписки\s+и\s+сохраненные\s+фото\b",
        r"\bмоментальная\s+проверка\s+соц\.\s+сети\s+девушки\b",
        r"\bсобраны\s+все\s+сливы\s+2018-2024\s+годов\b",
        r"\bслитые\s+фото\b",
        r"\bслив\s+фото",
        r"\bпроверка\s+девушек\s+твоего\s+города\b",
        r"\bсливы\b",
        r"\bслив\b",
        
		  # whole message examples
        r"\bесть\s+несколько\s+мест\s+на\s+удаленк[ау]\s+с\s+хорошим\s+доходом\b",
        r"\bзанятость\s+[0-9]+(-[0-9]+)?\s+час(а|ов)?\s+в\s+день\b",
        r"\bздравствуй,\s+друг\b",
        r"\bпассивный\s+источник\s+дохода\b",
        r"\bновое\s+направление\b",
        r"\bтолько\s+[0-9]+(\s*\+)?\s*лет\b"
        r"\bсредний\s+доход\s+[0-9]+\$?\s+в\s+(неделю|день|месяц)\b",
        r"\bнужно\s+[0-9]+\s+человека?\s+на\s+удаленный\s+заработок\b",
        r"\bс\s+тебя\s+телефон\s+и\s+два\s+часа\s+свободного\s+времени\s+в\s+день\b",
        r"\bзаработок\s+очень\s+достойный\b",
        r"\bвзаимовыгодное\s+сотрудничество\s+от\s+[0-9]+(-[0-9]+)?\$?\s+в\s+день\b",
        r"\bхотите\s+увеличить\s+свой\s+доход,\s+затрачивая\s+минимум\s+времени\s+и\s+работая\s+удаленно\?\b",
        r"\bприсоединяйтесь\s+к\s+нашей\s+команде\b",
        r"\bмы\s+ищем\s+совершеннолетних\s+целеустремленных\s+людей\b",
        r"[‼️]+\s*срочно\s*[‼️]+\b",
        r"\bэто\s+касается\s+каждого\s+в\s+этой\s+группе\b",
        r"\bпроходит\s+обучение\s+для\s+новичков\b",
        r"\bбез\s+наркотиков,\s+инвестиций\s+и\s+прочей\s+ерунды\b",
        r"\bприбыль\s+вы\s+получите\s+уже\s+в\s+первый\s+день\s+работы\b",
        r"\bвсе\s+легально\b",
        r"\bдля\s+работы\s+нужен\s+смартфон",
        r"\bвсего\s+[0-9]+\s+час(а|ов)?\s+твоего\s+времени\s+в\s+день\b",
        r"\bдовед[её]м\s+вас\s+за\s+ручку",
        r"\bработаем\s+[зн]а\s+%\b"
    ]

    supporting_phrases = [
        # Age restrictions
        r"\bс\s+\d+\s+лет\b",
        r"\bот\s+\d+\s+лет\b",
        r"\b\d+\+\b",

        # Contact invitation patterns
        r"пишите\s+в\s+личные",
        r"в\s+л[и|у]ч[н|к][и|е]",
        r"л\.?\s*с",
        r"за\s+деталями\s+в\s+лс",
        r"за\s+деталями\s+пиш[ие]",
        r"пишите\s+мне",
        r"в\s+личных\s+сообщениях",
        r"для\s+подробностей\s+пиш[ие]",
        r"пишите\s+в\s+личку",
        r"пишите\s+в\s+лс\s+за\s+деталями",
        r"\bпишите\s+в\s+лс\s+за\s+деталями\b",
        r"\bпиши(\s*\+)?\s*(и\s+я\s+отправлю\s+всю\s+информацию)?\b",
        r"\bпишите\s+в\s+лс\s*\+\b",
        
        # Time commitment patterns
        r"\b\d+(-\d+)?\s*час(?:а|ов)?\s+в\s+день\b",
        r"\b1-2\s*часа?\s*работы\b",
        r"\b2-3\s*часа\s*в\s*день\b",
        r"\bдо\s+\d+\s*час(?:а|ов)?\s+в\s+день\b",

        # Age restriction patterns
        r"[\+\-]?\s*\d+\s*(долларов|день|usd|\$)",
        r"(?:от|с)\s*\d+\s*(?:лет|год(?:а|ов)?)",
        r"\b\d+\+",
        r"\bстрого\s+[0-9]+(\s*\+)?\b",
        
		  # To catch adult leak bots
		  r"\bдевушек\b",
        r"\bдевушки\b",
        r"\bличные\s+переписки\b",

    ]

    # Compile patterns
    main_pattern = re.compile("|".join(main_spam_phrases), re.IGNORECASE | re.DOTALL)
    supporting_pattern = re.compile("|".join(supporting_phrases), re.IGNORECASE | re.DOTALL)

    # Check for main spam patterns
    has_main = main_pattern.search(text) is not None

    # Check for supporting patterns
    has_supporting = supporting_pattern.search(text) is not None

    #return has_main and has_supporting 
    return main_pattern.search(text) and supporting_pattern.search(text)