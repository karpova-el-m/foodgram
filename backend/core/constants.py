MAX_LENGTH = 20
MAX_TITLE_LENGTH = 256
RECIPES_PER_PAGE = 6
MEASUREMENT_UNIT_CHOICES = [
    ('г', 'Грамм'),
    ('кг', 'Килограмм'),
    ('мг', 'Миллиграмм'),
    ('л', 'Литр'),
    ('мл', 'Миллилитр'),
    ('шт.', 'Штука'),
    ('ч. л.', 'Чайная ложка'),
    ('ст. л.', 'Столовая ложка'),
    ('капля', 'Капля'),
    ('кусок', 'Кусок'),
    ('банка', 'Банка'),
    ('стакан', 'Стакан'),
    ('щепотка', 'Щепотка'),
    ('горсть', 'Горсть'),
]
MAX_LENGTH_USERNAME = 150
USER_NAME_REGEX = r'^[\w.@+-]+\Z'
MAX_LENGTH_FIRST_AND_LAST_NAME = 150
NON_VALID_USERNAME = 'me'
MIN_COOK_TIME = 1
MAX_COOK_TIME = 1440
