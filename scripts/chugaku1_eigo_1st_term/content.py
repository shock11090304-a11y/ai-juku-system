# 中学1年1学期英文法 選択式演習問題集 100問
# データのみを定義。ビルドは build_pdf.py で処理
# 2026-08-01: 3並列エージェント検証により問48/78/79の文法バグ・問66,69,70,71の非現実的選択肢・
# 正解位置の偏り(D=3回のみ/冒頭12問連続C)を修正済み

PROBLEMS = [
    # be動詞
    {
        'number': 1,
        'category': 'be動詞',
        'difficulty': '基礎',
        'question': 'I _____ a student.',
        'options': ['is', 'are', 'am', 'be'],
        'answer_index': 2,
        'explanation': '1人称単数「I」の後には「am」を使います。「私は学生です。」',
        'tips': 'be動詞：I→am, you→are, he/she/it→is, we/you/they→are'
    },
    {
        'number': 2,
        'category': 'be動詞',
        'difficulty': '基礎',
        'question': 'She _____ a teacher.',
        'options': ['are', 'am', 'be', 'is'],
        'answer_index': 3,
        'explanation': '3人称単数「she」の後には「is」を使います。「彼女は先生です。」',
        'tips': '3人称単数（he/she/it）は「is」'
    },
    {
        'number': 3,
        'category': 'be動詞',
        'difficulty': '基礎',
        'question': 'We _____ from Japan.',
        'options': ['is', 'are', 'am', 'be'],
        'answer_index': 1,
        'explanation': '1人称複数「we」の後には「are」を使います。「私たちは日本から来ました。」',
        'tips': '複数形（we/you/they）は「are」'
    },
    {
        'number': 4,
        'category': 'be動詞',
        'difficulty': '基礎',
        'question': 'You _____ a doctor.',
        'options': ['is', 'am', 'are', 'be'],
        'answer_index': 2,
        'explanation': '「you」は単数・複数どちらでも「are」です。「あなたは医者です。」',
        'tips': 'you は常に are を使う'
    },
    {
        'number': 5,
        'category': 'be動詞',
        'difficulty': '基礎',
        'question': 'They _____ students.',
        'options': ['is', 'are', 'am', 'be'],
        'answer_index': 1,
        'explanation': '3人称複数「they」の後には「are」を使います。「彼らは学生です。」',
        'tips': '複数形は常に are'
    },
    {
        'number': 6,
        'category': 'be動詞',
        'difficulty': '基礎',
        'question': 'This _____ a pen.',
        'options': ['are', 'am', 'is', 'be'],
        'answer_index': 2,
        'explanation': '「this」は3人称単数扱いなので「is」です。「これはペンです。」',
        'tips': '指示代名詞 this/that は単数なので is'
    },
    {
        'number': 7,
        'category': 'be動詞',
        'difficulty': '基礎',
        'question': 'Tom _____ a student.',
        'options': ['are', 'am', 'is', 'be'],
        'answer_index': 2,
        'explanation': '人名「Tom」は3人称単数なので「is」です。',
        'tips': '人名は3人称単数'
    },
    {
        'number': 8,
        'category': 'be動詞',
        'difficulty': '基礎',
        'question': 'These apples _____ red.',
        'options': ['are', 'is', 'am', 'be'],
        'answer_index': 0,
        'explanation': 'これらのリンゴ「these apples」は複数なので「are」です。',
        'tips': 'these/those は複数なので are'
    },
    {
        'number': 9,
        'category': 'be動詞',
        'difficulty': '応用',
        'question': 'The book and the pen _____ on the desk.',
        'options': ['are', 'is', 'am', 'be'],
        'answer_index': 0,
        'explanation': 'and で接続された主語は複数扱いなので「are」です。',
        'tips': 'A and B という主語は複数'
    },
    {
        'number': 10,
        'category': 'be動詞',
        'difficulty': '応用',
        'question': 'There _____ many students in the class.',
        'options': ['is', 'am', 'be', 'are'],
        'answer_index': 3,
        'explanation': '「There are～」で「～がいる」という存在表現。students が複数なので「are」。',
        'tips': 'There is/are は後ろの名詞の単複で決まる'
    },
    {
        'number': 11,
        'category': 'be動詞',
        'difficulty': '応用',
        'question': 'Ken and Yuki _____ friends.',
        'options': ['are', 'is', 'am', 'be'],
        'answer_index': 0,
        'explanation': '2人の名前が and で接続されているので複数扱い。「are」です。',
        'tips': '複数の人名は複数扱い'
    },
    {
        'number': 12,
        'category': 'be動詞',
        'difficulty': '応用',
        'question': 'My mother _____ a nurse.',
        'options': ['are', 'is', 'am', 'be'],
        'answer_index': 1,
        'explanation': '「my mother」は3人称単数。「私の母は看護師です。」',
        'tips': '所有代名詞＋名詞は元の人称で判断'
    },
    {
        'number': 13,
        'category': 'be動詞',
        'difficulty': '応用',
        'question': 'That _____ not a cat. It _____ a dog.',
        'options': ['is...is', 'is...are', 'are...is', 'am...are'],
        'answer_index': 0,
        'explanation': '「that」は3人称単数なので両方とも「is」。「それは猫ではなく、犬です。」',
        'tips': '否定文でも is/are の選択は変わらない'
    },
    {
        'number': 14,
        'category': 'be動詞',
        'difficulty': '基礎',
        'question': 'I _____ fine, thank you.',
        'options': ['is', 'are', 'am', 'be'],
        'answer_index': 2,
        'explanation': '1人称単数「I」は「am」。「お陰様で元気です。」',
        'tips': '定型表現 I am fine...'
    },
    {
        'number': 15,
        'category': 'be動詞',
        'difficulty': '基礎',
        'question': 'It _____ a nice day.',
        'options': ['is', 'are', 'am', 'be'],
        'answer_index': 0,
        'explanation': '「it」は3人称単数なので「is」。「素晴らしい日ですね。」',
        'tips': 'it は天気や時間を表す時も is'
    },
    # 一般動詞
    {
        'number': 16,
        'category': '一般動詞',
        'difficulty': '基礎',
        'question': 'I play soccer every day.',
        'options': ['plays', 'playing', 'to play', 'play'],
        'answer_index': 3,
        'explanation': '1人称は動詞の原形。「毎日サッカーをします。」',
        'tips': '一般動詞は主語によって形が変わる'
    },
    {
        'number': 17,
        'category': '一般動詞',
        'difficulty': '基礎',
        'question': 'She _____ English every day.',
        'options': ['studies', 'study', 'studying', 'to study'],
        'answer_index': 0,
        'explanation': '3人称単数の現在形は動詞に s を付けます。「彼女は毎日英語を勉強します。」',
        'tips': '3人称単数の現在形は -s/-es を付ける'
    },
    {
        'number': 18,
        'category': '一般動詞',
        'difficulty': '基礎',
        'question': 'We eat lunch at 12 o\'clock.',
        'options': ['eats', 'eating', 'to eat', 'eat'],
        'answer_index': 3,
        'explanation': '複数形は動詞の原形。「12時に昼食を食べます。」',
        'tips': '複数形と1人称は原形'
    },
    {
        'number': 19,
        'category': '一般動詞',
        'difficulty': '基礎',
        'question': 'My brother _____ tennis.',
        'options': ['play', 'plays', 'playing', 'to play'],
        'answer_index': 1,
        'explanation': '「my brother」は3人称単数なので「plays」。',
        'tips': '所有代名詞＋名詞は元の人称で判断'
    },
    {
        'number': 20,
        'category': '一般動詞',
        'difficulty': '基礎',
        'question': 'They _____ Japanese.',
        'options': ['speak', 'speaks', 'speaking', 'to speak'],
        'answer_index': 0,
        'explanation': '3人称複数は原形。「彼らは日本語を話します。」',
        'tips': '複数形は原形のまま'
    },
    {
        'number': 21,
        'category': '一般動詞',
        'difficulty': '基礎',
        'question': 'He _____ to school by bus.',
        'options': ['go', 'going', 'goes', 'to go'],
        'answer_index': 2,
        'explanation': 'go は3人称単数で goes。「彼はバスで学校に行きます。」',
        'tips': '不規則：go→goes, do→does, have→has'
    },
    {
        'number': 22,
        'category': '一般動詞',
        'difficulty': '基礎',
        'question': 'I _____ a book now.',
        'options': ['read', 'reads', 'reading', 'to read'],
        'answer_index': 0,
        'explanation': '1人称は原形。「今本を読んでいます。」',
        'tips': '進行形ではなく現在形の場合'
    },
    {
        'number': 23,
        'category': '一般動詞',
        'difficulty': '応用',
        'question': 'She _____ a piano.',
        'options': ['play', 'plays', 'playing', 'to play'],
        'answer_index': 1,
        'explanation': '3人称単数。「彼女はピアノを弾きます。」',
        'tips': 'play an instrument の表現'
    },
    {
        'number': 24,
        'category': '一般動詞',
        'difficulty': '応用',
        'question': 'My father _____ at a hospital.',
        'options': ['work', 'working', 'works', 'to work'],
        'answer_index': 2,
        'explanation': '3人称単数。「私の父は病院で働いています。」',
        'tips': '職業を表す場合も現在形'
    },
    {
        'number': 25,
        'category': '一般動詞',
        'difficulty': '応用',
        'question': 'Ken _____ baseball every Saturday.',
        'options': ['play', 'playing', 'plays', 'to play'],
        'answer_index': 2,
        'explanation': '3人称単数。「ケンは毎週土曜日に野球をします。」',
        'tips': '習慣的な行動は現在形'
    },
    {
        'number': 26,
        'category': '一般動詞',
        'difficulty': '基礎',
        'question': 'You _____ English.',
        'options': ['speaks', 'speak', 'speaking', 'to speak'],
        'answer_index': 1,
        'explanation': 'you は複数扱いなので原形。「あなたは英語を話します。」',
        'tips': 'you は複数扱い'
    },
    {
        'number': 27,
        'category': '一般動詞',
        'difficulty': '基礎',
        'question': 'Dogs _____ every morning.',
        'options': ['barks', 'barking', 'to bark', 'bark'],
        'answer_index': 3,
        'explanation': '複数形は原形。「犬は毎朝吠えます。」',
        'tips': '複数名詞は原形'
    },
    {
        'number': 28,
        'category': '一般動詞',
        'difficulty': '応用',
        'question': 'This book _____ very interesting.',
        'options': ['seem', 'seeming', 'to seem', 'seems'],
        'answer_index': 3,
        'explanation': '3人称単数。「この本は非常に面白く見えます。」',
        'tips': 'seem, look, sound などの知覚動詞も-s を付ける'
    },
    {
        'number': 29,
        'category': '一般動詞',
        'difficulty': '応用',
        'question': 'That store _____ good coffee.',
        'options': ['sell', 'selling', 'sells', 'to sell'],
        'answer_index': 2,
        'explanation': 'store は3人称単数。「その店は良いコーヒーを売っています。」',
        'tips': '場所を表す名詞も3人称単数'
    },
    {
        'number': 30,
        'category': '一般動詞',
        'difficulty': '基礎',
        'question': 'I _____ tennis on Sundays.',
        'options': ['plays', 'play', 'playing', 'to play'],
        'answer_index': 1,
        'explanation': '1人称は原形。「日曜日にテニスをします。」',
        'tips': '曜日を使った習慣的な行動'
    },
    # 否定文
    {
        'number': 31,
        'category': '否定文',
        'difficulty': '基礎',
        'question': 'I _____ like apples.',
        'options': ['am not', 'does not', 'do not', 'will not'],
        'answer_index': 2,
        'explanation': '一般動詞の否定は do not を使います。「私はりんごが好きではありません。」',
        'tips': '一般動詞の否定：do not + 原形'
    },
    {
        'number': 32,
        'category': '否定文',
        'difficulty': '基礎',
        'question': 'She _____ play soccer.',
        'options': ['does not', 'do not', 'is not', 'am not'],
        'answer_index': 0,
        'explanation': '3人称単数は does not を使います。「彼女はサッカーをしません。」',
        'tips': '3人称単数の否定は does not'
    },
    {
        'number': 33,
        'category': '否定文',
        'difficulty': '基礎',
        'question': 'They _____ eat meat.',
        'options': ['does not', 'do not', 'is not', 'am not'],
        'answer_index': 1,
        'explanation': '複数形は do not を使います。「彼らは肉を食べません。」',
        'tips': '複数形と1人称は do not'
    },
    {
        'number': 34,
        'category': '否定文',
        'difficulty': '基礎',
        'question': 'He _____ a teacher.',
        'options': ['does not', 'do not', 'is not', 'am not'],
        'answer_index': 2,
        'explanation': 'be動詞の否定は is not を使います。「彼は先生ではありません。」',
        'tips': 'be動詞の否定：is not/are not/am not'
    },
    {
        'number': 35,
        'category': '否定文',
        'difficulty': '基礎',
        'question': 'We _____ students.',
        'options': ['do not', 'does not', 'are not', 'am not'],
        'answer_index': 2,
        'explanation': 'be動詞で複数形は are not を使います。「私たちは学生ではありません。」',
        'tips': '複数形の be動詞の否定は are not'
    },
    {
        'number': 36,
        'category': '否定文',
        'difficulty': '応用',
        'question': 'My brother _____ like fruits.',
        'options': ['does not', 'do not', 'is not', 'am not'],
        'answer_index': 0,
        'explanation': '3人称単数なので does not を使います。',
        'tips': '所有代名詞＋名詞は元の人称で判断'
    },
    {
        'number': 37,
        'category': '否定文',
        'difficulty': '応用',
        'question': 'Ken and Yuki _____ go to school by bus.',
        'options': ['do not', 'does not', 'is not', 'am not'],
        'answer_index': 0,
        'explanation': '複数の主語は複数扱いなので do not を使います。',
        'tips': 'and で接続された主語は複数'
    },
    {
        'number': 38,
        'category': '否定文',
        'difficulty': '基礎',
        'question': 'This _____ a pen. It _____ a pencil.',
        'options': ['is not...is not', 'is not...is', 'does not...is not', 'am not...is'],
        'answer_index': 1,
        'explanation': '「これはペンではなく、それは鉛筆です。」最初の is not は否定、2番目の is は肯定。',
        'tips': '否定と肯定を組み合わせた文'
    },
    {
        'number': 39,
        'category': '否定文',
        'difficulty': '応用',
        'question': 'I _____ understand this problem.',
        'options': ['am not', 'does not', 'do not', 'is not'],
        'answer_index': 2,
        'explanation': '一般動詞の否定は do not を使います。「この問題が分かりません。」',
        'tips': 'understand, know などの動詞も do not で否定'
    },
    {
        'number': 40,
        'category': '否定文',
        'difficulty': '応用',
        'question': 'She _____ drink coffee.',
        'options': ['do not', 'is not', 'am not', 'does not'],
        'answer_index': 3,
        'explanation': '3人称単数は does not を使います。「彼女はコーヒーを飲みません。」',
        'tips': '3人称単数の一般動詞の否定は does not'
    },
    # 疑問文
    {
        'number': 41,
        'category': '疑問文',
        'difficulty': '基礎',
        'question': 'Do you like sports?',
        'options': ['Yes, I am.', 'Yes, I like.', 'Yes, I do.', 'Yes, I does.'],
        'answer_index': 2,
        'explanation': '「スポーツが好きですか？」という質問に対する答え。',
        'tips': 'Do you...? に対しては Yes, I do. / No, I do not.'
    },
    {
        'number': 42,
        'category': '疑問文',
        'difficulty': '基礎',
        'question': 'Does he play tennis?',
        'options': ['Yes, he is.', 'Yes, he play.', 'Yes, he do.', 'Yes, he does.'],
        'answer_index': 3,
        'explanation': '「彼はテニスをしますか？」という質問。答えは Yes, he does.',
        'tips': 'Does he...? に対しては Yes, he does. / No, he does not.'
    },
    {
        'number': 43,
        'category': '疑問文',
        'difficulty': '基礎',
        'question': '_____ you from Japan?',
        'options': ['Do', 'Are', 'Does', 'Is'],
        'answer_index': 1,
        'explanation': 'be動詞の疑問文。「あなたは日本出身ですか？」',
        'tips': 'be動詞の疑問文：Are you...? / Is he...?'
    },
    {
        'number': 44,
        'category': '疑問文',
        'difficulty': '基礎',
        'question': '_____ they students?',
        'options': ['Do', 'Are', 'Does', 'Is'],
        'answer_index': 1,
        'explanation': '複数形は Are を使います。「彼らは学生ですか？」',
        'tips': '複数形：Are you...? / Are they...?'
    },
    {
        'number': 45,
        'category': '疑問文',
        'difficulty': '基礎',
        'question': '_____ is a teacher?',
        'options': ['Do', 'Does', 'Are', 'Who'],
        'answer_index': 3,
        'explanation': '疑問詞を使った疑問文。「誰が先生ですか？」',
        'tips': 'Who is...? で「誰が」という質問'
    },
    {
        'number': 46,
        'category': '疑問文',
        'difficulty': '応用',
        'question': '_____ do you study English?',
        'options': ['What', 'How', 'Why', 'Where'],
        'answer_index': 1,
        'explanation': '「どのように英語を勉強しますか？」という質問。',
        'tips': 'How do you...? で方法を尋ねる'
    },
    {
        'number': 47,
        'category': '疑問文',
        'difficulty': '応用',
        'question': '_____ does your brother live?',
        'options': ['What', 'Which', 'Who', 'Where'],
        'answer_index': 3,
        'explanation': '「あなたの兄（弟）はどこに住んでいますか？」',
        'tips': 'Where do/does...? で場所を尋ねる'
    },
    {
        'number': 48,
        'category': '疑問文',
        'difficulty': '基礎',
        'question': '_____ she play tennis?',
        'options': ['Do', 'Does', 'When', 'Why'],
        'answer_index': 1,
        'explanation': '3人称単数なので Does を使います。「彼女はテニスをしますか？」',
        'tips': '3人称単数の疑問文は Does'
    },
    {
        'number': 49,
        'category': '疑問文',
        'difficulty': '応用',
        'question': 'What _____ you like?',
        'options': ['do', 'does', 'are', 'is'],
        'answer_index': 0,
        'explanation': '「何が好きですか？」という質問。you は複数扱いなので do を使います。',
        'tips': 'What do you like? は頻出表現'
    },
    {
        'number': 50,
        'category': '疑問文',
        'difficulty': '応用',
        'question': 'Where _____ they from?',
        'options': ['are', 'do', 'does', 'is'],
        'answer_index': 0,
        'explanation': '「彼らはどこから来ましたか？」be動詞で複数形なので are を使います。',
        'tips': 'from は be動詞を伴うことが多い'
    },
    {
        'number': 51,
        'category': '疑問文',
        'difficulty': '基礎',
        'question': 'Is this a cat? _____, it is.',
        'options': ['No', 'Not', 'Yes', 'No, it is not'],
        'answer_index': 2,
        'explanation': '「これは猫ですか？はい、そうです。」',
        'tips': 'Yes, it is. / No, it is not. という答え方'
    },
    {
        'number': 52,
        'category': '疑問文',
        'difficulty': '応用',
        'question': 'Does she have a car? No, she _____ .',
        'options': ['has not', 'do not', 'is not', 'does not'],
        'answer_index': 3,
        'explanation': '「彼女は車を持っていますか？いいえ、持っていません。」',
        'tips': 'does not の短縮形は doesn\'t'
    },
    {
        'number': 53,
        'category': '疑問文',
        'difficulty': '応用',
        'question': '_____ you play soccer? Yes, _____ .',
        'options': ['Does...I do', 'Do...I do', 'Do...I am', 'Are...I am'],
        'answer_index': 1,
        'explanation': '「サッカーをしますか？はい、します。」',
        'tips': 'Do you...? に対しては Yes, I do.'
    },
    {
        'number': 54,
        'category': '疑問文',
        'difficulty': '基礎',
        'question': 'When _____ you study English?',
        'options': ['does', 'are', 'do', 'is'],
        'answer_index': 2,
        'explanation': '「いつ英語を勉強しますか？」you は複数扱いなので do を使います。',
        'tips': 'When do you...? は時間を尋ねる表現'
    },
    {
        'number': 55,
        'category': '疑問文',
        'difficulty': '応用',
        'question': 'Why _____ he like English?',
        'options': ['do', 'is', 'does', 'are'],
        'answer_index': 2,
        'explanation': '「なぜ彼は英語が好きなのですか？」3人称単数なので does を使います。',
        'tips': 'Why does he...? で理由を尋ねる'
    },
    # 代名詞
    {
        'number': 56,
        'category': '代名詞',
        'difficulty': '基礎',
        'question': 'I like cats. _____ are cute.',
        'options': ['It', 'They', 'He', 'She'],
        'answer_index': 1,
        'explanation': 'cats（複数）を指すので they を使います。「猫が好きです。それらはかわいいです。」',
        'tips': '複数形の代名詞は they'
    },
    {
        'number': 57,
        'category': '代名詞',
        'difficulty': '基礎',
        'question': 'My father is a doctor. _____ works at a hospital.',
        'options': ['He', 'It', 'She', 'You'],
        'answer_index': 0,
        'explanation': 'father（男性）を指すので he を使います。',
        'tips': '男性は he、女性は she、単数物は it'
    },
    {
        'number': 58,
        'category': '代名詞',
        'difficulty': '基礎',
        'question': 'Do you like this book? Yes, I like _____.',
        'options': ['he', 'she', 'it', 'they'],
        'answer_index': 2,
        'explanation': 'book（単数物）を指すので it を使います。「この本が好きですか？はい、好きです。」',
        'tips': '単数物は it で受ける'
    },
    {
        'number': 59,
        'category': '代名詞',
        'difficulty': '基礎',
        'question': 'Tom and Ken are students. _____ study hard.',
        'options': ['It', 'She', 'They', 'He'],
        'answer_index': 2,
        'explanation': 'Tom and Ken（複数）を指すので they を使います。',
        'tips': '複数の人は they で受ける'
    },
    {
        'number': 60,
        'category': '代名詞',
        'difficulty': '基礎',
        'question': 'She is my friend. I like _____.',
        'options': ['she', 'hers', 'his', 'her'],
        'answer_index': 3,
        'explanation': '目的格は her を使います。「彼女は私の友人です。私は彼女が好きです。」',
        'tips': '主語の後は主格、動詞の後は目的格'
    },
    {
        'number': 61,
        'category': '代名詞',
        'difficulty': '基礎',
        'question': 'He is Ken. I know _____.',
        'options': ['him', 'he', 'his', 'he\'s'],
        'answer_index': 0,
        'explanation': '目的格は him を使います。「彼はケンです。私は彼を知っています。」',
        'tips': 'know の後は目的格'
    },
    {
        'number': 62,
        'category': '代名詞',
        'difficulty': '応用',
        'question': 'Can you help _____ ? Yes, I can help _____ .',
        'options': ['me...me', 'me...you', 'I...you', 'I...I'],
        'answer_index': 1,
        'explanation': '「私を手伝えますか？はい、あなたを手伝えます。」目的格を使う。',
        'tips': '動詞の後は常に目的格'
    },
    {
        'number': 63,
        'category': '代名詞',
        'difficulty': '応用',
        'question': 'This is Yuki. I like _____.',
        'options': ['she', 'hers', 'his', 'her'],
        'answer_index': 3,
        'explanation': 'like の後は目的格なので her を使います。',
        'tips': 'like, know, help などの後は目的格'
    },
    {
        'number': 64,
        'category': '代名詞',
        'difficulty': '応用',
        'question': 'These apples are red. _____ are fresh.',
        'options': ['They', 'It', 'He', 'She'],
        'answer_index': 0,
        'explanation': 'apples（複数）を指すので they を使います。',
        'tips': '複数名詞は they で受ける'
    },
    {
        'number': 65,
        'category': '代名詞',
        'difficulty': '基礎',
        'question': 'I see a dog. _____ is brown.',
        'options': ['He', 'She', 'They', 'It'],
        'answer_index': 3,
        'explanation': 'dog（単数物）を指すので it を使います。',
        'tips': '動物も単数なら it'
    },
    # 複数形
    {
        'number': 66,
        'category': '複数形',
        'difficulty': '基礎',
        'question': 'I have one cat. He has three _____.',
        'options': ['cats', 'cat', 'cat\'s', 'cates'],
        'answer_index': 0,
        'explanation': '3つなので複数形 cats を使います。「cat\'s」は所有格(～の)を表すアポストロフィで、複数形ではありません。',
        'tips': '2つ以上は複数形に -s を付ける。\'s（アポストロフィs）は所有格と混同しやすいので注意'
    },
    {
        'number': 67,
        'category': '複数形',
        'difficulty': '基礎',
        'question': 'This is a box. These are _____.',
        'options': ['box', 'boxs', 'boxes', 'boxez'],
        'answer_index': 2,
        'explanation': 'x で終わる単語は -es を付けて boxes になります。',
        'tips': 'box→boxes, bush→bushes, dish→dishes'
    },
    {
        'number': 68,
        'category': '複数形',
        'difficulty': '基礎',
        'question': 'I see a boy. I see five _____.',
        'options': ['boy', 'boies', 'boys', 'boyss'],
        'answer_index': 2,
        'explanation': '子音+y で終わる単語は y→ies に変わります。boys が正解。',
        'tips': 'boy→boys, day→days, family→families'
    },
    {
        'number': 69,
        'category': '複数形',
        'difficulty': '基礎',
        'question': 'I eat an apple. We eat _____.',
        'options': ['apple', 'apple\'s', 'applees', 'apples'],
        'answer_index': 3,
        'explanation': 'apple は単純に -s を付けて apples になります。「apple\'s」は所有格、「applees」は不要な e が入った誤りです。',
        'tips': '通常は -s を付けるだけ'
    },
    {
        'number': 70,
        'category': '複数形',
        'difficulty': '応用',
        'question': 'I have a book. They have many _____.',
        'options': ['books', 'book', 'book\'s', 'bookes'],
        'answer_index': 0,
        'explanation': 'book に -s を付けて books になります。「book\'s」は所有格、「bookes」は不要な e が入った誤りです。',
        'tips': '「多くの本」= many books'
    },
    {
        'number': 71,
        'category': '複数形',
        'difficulty': '応用',
        'question': 'There is one pen. There are two _____.',
        'options': ['pen', 'pen\'s', 'pens', 'penes'],
        'answer_index': 2,
        'explanation': 'There are two pens で「2本のペンがあります」と表現します。「pen\'s」は所有格、「penes」は不要な e が入った誤りです。',
        'tips': 'There are...で複数を表現'
    },
    {
        'number': 72,
        'category': '複数形',
        'difficulty': '基礎',
        'question': 'I see a bus. I see three _____.',
        'options': ['bus', 'buses', 'buss', 'busez'],
        'answer_index': 1,
        'explanation': 's で終わる単語は -es を付けて buses になります。',
        'tips': 'bus→buses, glass→glasses, class→classes'
    },
    {
        'number': 73,
        'category': '複数形',
        'difficulty': '基礎',
        'question': 'This is a watch. These are _____.',
        'options': ['watches', 'watch', 'watchs', 'watchez'],
        'answer_index': 0,
        'explanation': 'ch で終わる単語は -es を付けて watches になります。',
        'tips': 'watch→watches, church→churches, bench→benches'
    },
    # 所有代名詞
    {
        'number': 74,
        'category': '所有代名詞',
        'difficulty': '基礎',
        'question': 'This is _____ book. It\'s my book.',
        'options': ['me', 'my', 'mine', 'I'],
        'answer_index': 1,
        'explanation': '名詞の前には所有代名詞 my を使います。「これは私の本です。」',
        'tips': '名詞を修飾する場合は my/your/his/her 等'
    },
    {
        'number': 75,
        'category': '所有代名詞',
        'difficulty': '基礎',
        'question': 'That is _____ pen. It\'s his pen.',
        'options': ['him', 'hims', 'he', 'his'],
        'answer_index': 3,
        'explanation': '3人称単数男性の所有代名詞は his です。',
        'tips': '所有代名詞：my, your, his, her, its, our, their'
    },
    {
        'number': 76,
        'category': '所有代名詞',
        'difficulty': '基礎',
        'question': 'This is _____ bag. It\'s her bag.',
        'options': ['she', 'hers', 'hisses', 'her'],
        'answer_index': 3,
        'explanation': '3人称単数女性の所有代名詞は her です。',
        'tips': '女性は her を使う'
    },
    {
        'number': 77,
        'category': '所有代名詞',
        'difficulty': '基礎',
        'question': 'These are _____ books. They\'re our books.',
        'options': ['our', 'we', 'ours', 'us'],
        'answer_index': 0,
        'explanation': '1人称複数の所有代名詞は our です。「これらは私たちの本です。」',
        'tips': '複数は our/their を使う'
    },
    {
        'number': 78,
        'category': '所有代名詞',
        'difficulty': '応用',
        'question': 'Is this _____ dog? No, it\'s not _____ dog.',
        'options': ['yours...mine', 'your...my', 'your...mine', 'yours...my'],
        'answer_index': 1,
        'explanation': 'どちらの空所も直後に名詞 dog が続くため、名詞を修飾できる所有格 your / my を使います。mine や yours は名詞の直前には置けません（単独で使う形）。',
        'tips': 'my dog（名詞修飾）vs. mine（単独、名詞の前には置けない）'
    },
    {
        'number': 79,
        'category': '所有代名詞',
        'difficulty': '応用',
        'question': 'Ken has a sister. _____ sister is a nurse.',
        'options': ['He', 'Him', 'His', 'He\'s'],
        'answer_index': 2,
        'explanation': '名詞 sister を修飾するので所有格の His を使います。「ケンには姉（妹）がいます。彼の姉（妹）は看護師です。」',
        'tips': '所有代名詞は名詞の直前に置く：his sister, her sister'
    },
    {
        'number': 80,
        'category': '所有代名詞',
        'difficulty': '基礎',
        'question': 'Whose book is this? It\'s _____ book.',
        'options': ['she', 'her', 'hers', 'she\'s'],
        'answer_index': 1,
        'explanation': '名詞を修飾する場合は her。「これは誰の本ですか？彼女の本です。」',
        'tips': '「whose...?」に対しては名詞修飾の形で答える'
    },
    # 前置詞
    {
        'number': 81,
        'category': '前置詞',
        'difficulty': '基礎',
        'question': 'The pen is _____ the desk.',
        'options': ['in', 'at', 'to', 'on'],
        'answer_index': 3,
        'explanation': 'on は「上に」という意味です。「ペンは机の上にあります。」',
        'tips': 'on=上に、in=中に、at=そばに'
    },
    {
        'number': 82,
        'category': '前置詞',
        'difficulty': '基礎',
        'question': 'My book is _____ the bag.',
        'options': ['on', 'in', 'at', 'to'],
        'answer_index': 1,
        'explanation': 'in は「中に」という意味です。「私の本はバッグの中にあります。」',
        'tips': '中に入っている状態は in'
    },
    {
        'number': 83,
        'category': '前置詞',
        'difficulty': '基礎',
        'question': 'I go _____ school _____ 8 o\'clock.',
        'options': ['at...to', 'in...on', 'on...at', 'to...at'],
        'answer_index': 3,
        'explanation': 'to school で「学校へ」。at 8 o\'clock で「8時に」。',
        'tips': 'go to + 場所、at + 時間'
    },
    {
        'number': 84,
        'category': '前置詞',
        'difficulty': '基礎',
        'question': 'I study _____ the library.',
        'options': ['on', 'at', 'to', 'in'],
        'answer_index': 3,
        'explanation': 'in は場所を表します。「図書館で勉強します。」',
        'tips': '場所を表す前置詞は in/at'
    },
    {
        'number': 85,
        'category': '前置詞',
        'difficulty': '応用',
        'question': 'The cat is sleeping _____ the table, hidden from view.',
        'options': ['under', 'in', 'to', 'at'],
        'answer_index': 0,
        'explanation': '「隠れて見えない」という文脈から、テーブルの下にいることが分かります。under は「～の下に」という意味です。',
        'tips': 'under=下、over=上（越える）、between=間'
    },
    {
        'number': 86,
        'category': '前置詞',
        'difficulty': '応用',
        'question': 'I live _____ Tokyo.',
        'options': ['on', 'at', 'to', 'in'],
        'answer_index': 3,
        'explanation': 'in は都市を表します。「東京に住んでいます。」',
        'tips': '都市や国は in'
    },
    {
        'number': 87,
        'category': '前置詞',
        'difficulty': '基礎',
        'question': 'I go to school _____ Monday.',
        'options': ['in', 'on', 'at', 'to'],
        'answer_index': 1,
        'explanation': 'on は曜日を表します。「月曜日に学校に行きます。」',
        'tips': '曜日は on、月は in'
    },
    {
        'number': 88,
        'category': '前置詞',
        'difficulty': '応用',
        'question': 'The book is _____ the table and the chair.',
        'options': ['on', 'in', 'at', 'between'],
        'answer_index': 3,
        'explanation': 'between は「～と～の間に」という意味です。',
        'tips': 'between...and... で「間に」を表す'
    },
    {
        'number': 89,
        'category': '前置詞',
        'difficulty': '基礎',
        'question': 'She is _____ the classroom.',
        'options': ['on', 'in', 'at', 'to'],
        'answer_index': 1,
        'explanation': 'in は場所を表します。「彼女は教室にいます。」',
        'tips': '中に入っている場所は in'
    },
    {
        'number': 90,
        'category': '前置詞',
        'difficulty': '応用',
        'question': 'I study _____ 2 o\'clock _____ 4 o\'clock.',
        'options': ['from...to', 'at...at', 'in...in', 'on...on'],
        'answer_index': 0,
        'explanation': 'from 2 o\'clock to 4 o\'clock で「2時から4時まで」という意味です。',
        'tips': 'from...to で時間の範囲を表す'
    },
    # There is/are
    {
        'number': 91,
        'category': 'There is/are',
        'difficulty': '基礎',
        'question': '_____ a dog in the park.',
        'options': ['There are', 'There is', 'It is', 'There have'],
        'answer_index': 1,
        'explanation': 'a dog は単数なので There is を使います。「公園に犬がいます。」',
        'tips': '単数：There is、複数：There are'
    },
    {
        'number': 92,
        'category': 'There is/are',
        'difficulty': '基礎',
        'question': '_____ many books on the shelf.',
        'options': ['There is', 'It is', 'There have', 'There are'],
        'answer_index': 3,
        'explanation': 'many books は複数なので There are を使います。「棚の上に多くの本があります。」',
        'tips': '複数の名詞の後は are'
    },
    {
        'number': 93,
        'category': 'There is/are',
        'difficulty': '基礎',
        'question': '_____ some students in the library.',
        'options': ['There is', 'It is', 'There are', 'There have'],
        'answer_index': 2,
        'explanation': 'some students は複数なので There are を使います。「図書館に何人か学生がいます。」',
        'tips': 'students は複数なので are'
    },
    {
        'number': 94,
        'category': 'There is/are',
        'difficulty': '応用',
        'question': '_____ a cat and two dogs in the room.',
        'options': ['There are', 'There is', 'It is', 'There have'],
        'answer_index': 0,
        'explanation': 'and で接続された複数のもので複数扱い。「部屋に猫1匹と犬2匹がいます。」',
        'tips': 'and で接続された複数の名詞は複数扱い'
    },
    {
        'number': 95,
        'category': 'There is/are',
        'difficulty': '応用',
        'question': '_____ not any students in the classroom.',
        'options': ['There is', 'There are', 'It is', 'There have'],
        'answer_index': 1,
        'explanation': 'students は複数なので There are not を使います。「教室に学生がいません。」',
        'tips': 'There are not any... で「いない」を表す'
    },
    # 命令文
    {
        'number': 96,
        'category': '命令文',
        'difficulty': '基礎',
        'question': 'Please _____ the door.',
        'options': ['opens', 'opening', 'open', 'to open'],
        'answer_index': 2,
        'explanation': '命令文は動詞の原形で始まります。「ドアを開けてください。」',
        'tips': '命令文は動詞を原形で'
    },
    {
        'number': 97,
        'category': '命令文',
        'difficulty': '基礎',
        'question': '_____ your homework!',
        'options': ['Do', 'Does', 'Doing', 'Doings'],
        'answer_index': 0,
        'explanation': '命令文は動詞の原形で。「宿題をやりなさい！」',
        'tips': '命令文は主語を省略し動詞で始まる'
    },
    {
        'number': 98,
        'category': '命令文',
        'difficulty': '応用',
        'question': '_____ go to the park together.',
        'options': ['Let\'s', 'Let me', 'Let you', 'Let him'],
        'answer_index': 0,
        'explanation': 'Let\'s は「～しましょう」という提案。「一緒に公園に行きましょう。」',
        'tips': 'Let\'s で「～しましょう」'
    },
    {
        'number': 99,
        'category': '命令文',
        'difficulty': '応用',
        'question': '_____ play soccer!',
        'options': ['Let me', 'Do', 'Does', 'Let\'s'],
        'answer_index': 3,
        'explanation': 'Let\'s で「サッカーをしましょう！」',
        'tips': 'Let\'s + 動詞の原形'
    },
    {
        'number': 100,
        'category': '命令文',
        'difficulty': '応用',
        'question': 'Please _____ your books!',
        'options': ['closes', 'closing', 'to close', 'close'],
        'answer_index': 3,
        'explanation': '命令文は動詞の原形。「本を閉じてください。」',
        'tips': '丁寧な命令文でも please + 動詞の原形'
    },
]

# 単元ごとの問題数確認
CATEGORIES = {
    'be動詞': 15,
    '一般動詞': 15,
    '否定文': 10,
    '疑問文': 15,
    '代名詞': 10,
    '複数形': 8,
    '所有代名詞': 7,
    '前置詞': 10,
    'There is/are': 5,
    '命令文': 5,
}

assert len(PROBLEMS) == 100, f"問題数が{len(PROBLEMS)}です。100問でお願いします。"
