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
        
        # Time commitment patterns
        r"\b\d+(-\d+)?\s*час(?:а|ов)?\s+в\s+день\b",
        r"\b1-2\s*часа?\s*работы\b",
        r"\b2-3\s*часа\s*в\s*день\b",
        r"\bдо\s+\d+\s*час(?:а|ов)?\s+в\s+день\b",

        # Age restriction patterns
        r"[\+\-]?\s*\d+\s*(долларов|день|usd|\$)",
        r"(?:от|с)\s*\d+\s*(?:лет|год(?:а|ов)?)",
        r"\b\d+\+",
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