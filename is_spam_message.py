import re

def has_critical_patterns(text):
    crit_spam_phrases = [
		  # Whole message examples
        r"\bесть\s+несколько\s+мест\s+на\s+удаленк[ау]\s+с\s+хорошим\s+доходом\b",
        r"\bзанятость\s+[0-9]+(-[0-9]+)?\s+час(а|ов)?\s+в\s+день\b",
        r"\bздравствуй,\s+друг\b",
        r"\bтолько\s+[0-9]+(\s*\+)?\s*лет\b"
        r"\bсредний\s+доход\s+[0-9]+\$?\s+в\s+(неделю|день|месяц)\b",
        r"\bс\s+тебя\s+телефон\s+и\s+два\s+часа\s+свободного\s+времени\s+в\s+день\b",
        r"\bзаработок\s+очень\s+достойный\b",
        r"\bвзаимовыгодное\s+сотрудничество\s+от\s+[0-9]+(-[0-9]+)?\$?\s+в\s+день\b",
        r"\bхотите\s+увеличить\s+свой\s+доход,\s+затрачивая\s+минимум\s+времени\s+и\s+работая\s+удаленно\?\b",
        r"\bприсоединяйтесь\s+к\s+нашей\s+команде\b",
        r"\bмы\s+ищем\s+совершеннолетних\s+целеустремленных\s+людей\b",
        r"[‼️]+\s*срочно\s*[‼️]+\b",
        r"касается\s+каждого\s+в\s+этой\s+группе",
        r"\bпроходит\s+обучение\s+для\s+новичков\b",
        r"\bбез\s+наркотиков,\s+инвестиций\s+и\s+прочей\s+ерунды\b",
        r"\bприбыль\s+вы\s+получите\s+уже\s+в\s+первый\s+день\s+работы\b",
        r"\bвсего\s+[0-9]+\s+час(а|ов)?\s+твоего\s+времени\s+в\s+день\b",
        r"\bдовед[её]м\s+вас\s+за\s+ручку",
        r"\bработаем\s+[зн]а\s+%\b",
        r"\bудал[её]нн(?:ый|ую|ая|ое)\s+(формат|работ[ау]|деятельность)\b",
        r"\bналичие\s+телефона\s+и\s+\d+\s+час(?:а|ов)?\s+свободного\s+времени\b",
        r"\bищу\s+людей\s+с\s+биржами\b",
        
		  r"(?=.*\bзаинтересова\w*)(?=.*\bпиши\w*).*",
        r'(?:ставь(?:те)?|пиши(?:те)?|напиши(?:те)?|писать)(?:\s+(?:мне|в\s*лс))?\s*[«""]?\+[»""]?',
        r"\bпиши\s+плюс\s+в\b",
        
		  # Earnings
        r"\bпервые\s+хорошие\s+деньги\b",
        # "До 1200$ в неделю","от 400 баксов в неделю","От 1000$ в неделю","от 900 долларов в неделю","от $700 в неделю", "Доход от 300 длр в день", "от +300$ в день", "до 1200 баксов в день"
        r"(?i)(?:от|до)\s*(?:\$?\s*\d+(?:[.,]\d+)?|\d+(?:[.,]\d+)?\s*(?:баксов|долларов|длр|USD|\$))(?:\s*[.,])?\s+в\s+(?:неделю|день)",
        r"(?i)\d+\/неделю[\s\S]*",
        
		  # Gambling
        r"jeton_games",
        r"slotston_bot",
        r"\bтелеграм\s+бот\s+казино\b",
        r"казино\s*бот",
        r"\w*казино\s+JetTon\b",
        r"\w*казино\s+TONCOIN\b",
        r"\bSugar\s+Rush\b",
        r"\bбонуску\b",
        r"(?=.*\bвыигрыш\b)(?=.*\bказино\b)(?=.*\bдепозит\b).*",
        r"(?=.*\bвыигрыш\b)(?=.*\bказино\b)(?=.*\bTONCOIN\b).*",
        
		  # Adult
        r"\bфото[,\.]?\s+видео\s+девушек\b",
        r"\bпереписки\s+и\s+сохраненные\s+фото\b",
        r"\bмоментальная\s+проверка\s+соц\.\s+сети\s+девушки\b",
        r"\bсобраны\s+все\s+сливы\b",
        r"\bдевушек\s+твоего\s+города\b",
        r"\bинтимны[ех]\s+фото\w*",
        r"\bинтимны[ех]\s+фото\b",
        r"\bобнаж[её]нны[ех]\s+фото\w*",
        r"\bинтим\s+фото\b",
        r"\bпикантны[ех]\s+фото\b",
        r"проверь.*(?:подругу|девушку|жену)",
	 ]
    crit_pattern = re.compile("|".join(crit_spam_phrases), re.IGNORECASE | re.DOTALL)
    has_crit = crit_pattern.search(text)
    return has_crit

def new_is_spam_message(text):
    # Main spam phrases
    main_spam_phrases = [
        # Recruitment patterns
        r"\bнужн[аы]?\s+(люди|сотрудники)\b",
        r"\bсотрудник(?:и|ов)?\s+для\s+удал[её]нной\s+работы\b",
        r"\bид[её]т\s+набор\s+людей\b",
        r"\bнабор\s+для\s+сотрудничества\b",
        r"\bлюдей\s+для\s+сотрудничества\b",
        r"\bна\s+удал[её]нную\s+деятельность\b",
        r"\bместа\s+ограничены\b",
        r"\bмест\s+мало\b",
        r"\bвзаимовыгодн(?:ое|ая|ые)\s+сотрудничество\b",
        r"\bнужны\s+люди\s+для\s+сотрудничества\b",
        r"\bищ[уем]+\s+ответственного?\s+человека\b",
        r"\bдля\s+удалённого\s+сотрудничества\b",
        r"\bудалённого\s+заработка\b",
        r"\bзаинтересованных\s+людей\b",
        r"\bтребуются\s+люди\b",
        r"\bищ[уем]+\s+людей\b",
        r"\bнужн[аы]?\s+(люди|сотрудники)\b",
        r"\bищ[уем]+\s+партн[её]ров\b",
        r"\bнабира[юем]+\s+партн[её]ров\b",
        r"\bамбициозного\s+человека\b",
        r"\bамбициозных\s+людей\b",
        r"\bлюдей\s+в\s+команду\b",
        r"\bчастичная\s+занятость\b",
        r"\bинтересная\s+занятость\b",
        r"\bкоманду\s+для\s+сотрудничества\b",
        

		  # Remote
		  r"\bонлайн\s+через\s+телефон\b",
		  r"(?=.*\bудалён\w*)(?=.*\bсотруднич\w*)",
        
        # Earnings patterns
        r"\bпассивный\s+источник\s+дохода\b",
        r"\bновое\s+направление\b",
        r"\bот\s+\d+(-\d+)?\s*(\$|долларов?)\s+(в\s+день|в\s+месяц)?\b",
        r"\bзарабатывать\s+каждый\s+день\s+от\s+\d+\s*(\$|долларов?)\b",
        r"\bзарабатывать\s+пассивно\b",
        r"\bежедневн(?:ый|о)\s+доход\b",
        r"\bдоход\s+в\s+неделю\b",
        r"\bприбыль\s+ежедневно\b",
        r"\bвысокий\s+доход\b",
        r"\bдостойный\s+заработок\b",
        r"\bпассивный\s+заработок\b",
        r"\bпасивного\s+заработка\b",
        r"\bпассивного\s+дохода\b",
        r"\bна\s+пассиве\b",
        r"\bлегальная\s+доходность\b",
        r"\bЕсть\s+ТЕМКА\b",
        r"\bЕсть\s+Тема\b",
        r"\bлегальная\s+доходность\b",
        r"\bполучать\s+доход\b",
        r"\bпассивная\s+прибыль\b",
        r"\bпассивного\s+заработка\b",
        r"\bпассивного\s+дохода\b",
        r"\bпомогу\s+заработать\b",
        r"\bеженедельный\s+доход\b",
        r"\bдоход\s+онлайн\b",
        r"\bработ[ау]\s+на\s+удал[её]нке\b",
        r"\bудал[её]нная\s+занятость\b",
        r"\bудобный\s+график\b",
        r"\bработ[ау]\s+с\s+телефона\b",
        r"\bвс[её]\s+с\s+телефона\b",
        r"\bнужен только телефон\b",
        r"\bнужен\s+человек\s+на\b",
        r"\bна\s+удалённую\b",
        r"\bдля\s+взаимовыгодного\s+сотрудничества\b",
        r"\bна\s+удал[её]нный\s+заработок\b",
        r"\bзаработок\s+от\b",
        r"\bдля\s+хорошего\s+дохода\b",
        r"\bвсе\s+легально\b",
        r"\bдля\s+работы\s+нужен\s+смартфон\b",
        r"\bДоход\s+каждый\s+день\b",
        r"\bДоходность\b",
        r"\bстабильный\s+доход\b",
        r"\bдополнительный\s+доход\b",
        r"\bвысокая\s+оплата\b",
        r"\bзарабатывать\s+в\s+интернете\b",
        r"\bспособ\s+заработать\b",
        
        r"(?i)(?:от|до)\s+(?:ста|тысячи)\s+баксов",
        r"(?i)пассивн(?:ым\s+онлайн\s+доходом|ый\s+прибыл)|на\s+пассиве",
        r"(?=.*\bдоход\w*)(?=.*\bонлайн\b)",
        r"(?=.*\bонлайн\b)(?=.*\bзанятость\b)",
        r"(?=.*\bдоход\w*)(?=.*\bприбыл\w*)",

        # Training and support patterns
        r"\bбесплатное\s+обучение\b",
        r"\bподдержк[ау]\s+на\s+всех\s+этапах\b",
        r"\bдля\s+новичков\s+бесплатное\s+обучение\b",

        # Urgency patterns
        r"\bместа\s+ограничены\b",
        r"\bмест\s+мало\b",
        r"\bсрочно\s+треб[ею]тся\b",

        # Adult content patterns
        r"\bслитые\s+фото\b",
        r"\bслив\s+фото",
        r"\bсливы\b",
        r"\bслив\b",
        
		  # Gambling
        r"\bбукмекер\b",
	     r"\bвыигрыш\b",
    ]

    supporting_phrases = [
        # Age restrictions
        r"\bс\s+\d+\s+лет\b",
        r"\bот\s+\d+\s+лет\b",
        r"\b\d+\+\b",

        # Contact invitation patterns
        r"в\s+л[и|у]ч[н|к][и|е]",
        r"л\.?\s*с",
        r"за\s+деталями\s+в\s+лс",
        r"за\s+деталями\s+пиш[ие]",
        r"пишите\s+мне",
        r"пиши\s+мне",
        r"в\s+личны[ех]\s+сообщениях",
        r"для\s+подробностей\s+пиш[ие]",
        r"пишите\s+в\s+лс\s+за\s+деталями",
        r"\bпишите\s+в\s+лс\s+за\s+деталями\b",
        r"\bпиши(\s*\+)?\s*(и\s+я\s+отправлю\s+всю\s+информацию)?\b",
        r"\bпишите\s+в\s+лс\s*\+\b",
        r"\bпишите\s+личку\b",
        r"\bпишите\s+\+\s+в\s+личные\b",
        r"\bпишите\s+в\s+лс\b",
        r"\bнапишите\s+в\s+личку\b",
        r"\bпиш[ие]те?\s+в\s+личные\s+сообщения\b",
        r"\bза\s+деталями\s+пишите\b",
        r"\bжду\s+в\s+личных?\s+(сообщениях|смс)\b",
        r"\bв\s+личные\s+сообщения\b",
        r"\bпиши\s+в\s+личные\b",
        r"\bза\s+подробностями\b",
        r"\bличны[ех]\s+смс\b",
        r"\bличный\s+чат\b",
        r"\bв\s+личном\s+чате\b",
        r"\bдетали\s+в\s+личных\b",
        r"\bзаинтересованных\s+жду\b",
        r"\bза\s+подробностями\s+в\s+личные\s+сообщения\b",
        
		  r"(?=.*\bжду\b)(?=.*\bсообщен\w*)",
        
        # Time commitment patterns
        r"\b\d+(-\d+)?\s*час(?:а|ов)?\s+в\s+день\b",
        r"\b\d+(-\d+)?\s*час(?:а|ов)?\s+работы\b",
        r"\bдо\s+\d+\s*час(?:а|ов)?\s+в\s+день\b",

        # Age restriction patterns
        r"[\+\-]?\s*\d+\s*(долларов|день|usd|\$)",
        r"(?:от|с)\s*\d+\s*(?:лет|год(?:а|ов)?)",
        r"\b\d+\+",
        r"\bстрого\s+[0-9]+(\s*\+)?\b",
        r"\bсовершеннолетн(?:им|ие|ий|их)\b",
        
		  # To catch adult leak bots
		  r"\bдевуш(?:ек|ки)\b",
        r"\bличные\s+переписки\b"
    ]

    # Compile patterns
    main_pattern = re.compile("|".join(main_spam_phrases), re.IGNORECASE | re.DOTALL)
    supporting_pattern = re.compile("|".join(supporting_phrases), re.IGNORECASE | re.DOTALL)

    return main_pattern.search(text) and supporting_pattern.search(text)

def has_mixed_words(text):
    regex = r"\b(?=[^\s_-]*[а-яА-ЯёЁ]+)[^\s_-]*[^-\sа-яА-ЯёЁ\W\d_]+[^\s_-]*\b"
    matches = re.findall(regex, text)
    return matches