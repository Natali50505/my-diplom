# импорты
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
import re
from config import comunity_token, acces_token
from core import VkTools
import datetime
from data_base import  engine, add_user, check_user


# отправка сообщений


class BotInterface():
    def __init__(self, comunity_token, acces_token):
        self.vk = vk_api.VkApi(token=comunity_token)
        self.longpoll = VkLongPoll(self.vk)
        self.vk_tools = VkTools(acces_token)
        self.params = {}
        self.worksheets = []
        self.offset = 0
        self.keys = []

    def message_send(self, user_id, message, attachment=None):
        self.vk.method('messages.send',
                       {'user_id': user_id,
                        'message': message,
                        'attachment': attachment,
                        'random_id': get_random_id()}
                       )

    # обработка событий

    def event_handler(self):                          
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text.lower() == 'привет':
                    '''Логика для получения данных о пользователе'''
                    self.params = self.vk_tools.get_profile_info(event.user_id)
                    self.message_send(
                        event.user_id, f'Привет , {self.params["name"]}')

                    # обработка данных, которые не получили
                    self.keys = self.params.keys()
                    for i in self.keys:
                        if self.params[i] is None:
                            self.params[i] = self.name_sex_city_year(event)

                    self.message_send(event.user_id, 'Вы зарегистрировались! Напишите слово: поиск.')

                elif event.text.lower() == 'поиск':
                   
                                        
                    self.message_send(
                        event.user_id, 'Начинаем поиск')                    
                    

                    message = next(iter(self.get_file(self.worksheets, self.offset, event)))
                    if message:
                        photo_string = self.request_photo(message)
                        self.offset += 10

                        self.message_send(
                            event.user_id,
                            f'имя: {message["name"]} ссылка: vk.com/id{message["id"]}',
                            attachment=photo_string
                        )

                elif event.text.lower() == 'пока':
                    self.message_send(
                        event.user_id, 'Приходи еще')
                else:
                    self.message_send(
                        event.user_id, 'Неизвестная команда')            
                    
                    
    def name_sex_city_year(self, event):
        if self.params['name'] is None:
            self.message_send(event.user_id, 'Напишите имя и фамилию:')
            return self.new_message(0)
                    
        elif self.params['sex'] is None:
            self.message_send(event.user_id, 'Укажите свой пол (1 - М)б (2 - Ж):')
            return self.new_message(1)
                                    
        elif self.params['city'] is None:
            self.message_send(event.user_id, 'Напишите ваш город:')
            return self.new_message(2)
                                
        elif self.params['year'] is None:
            self.message_send(event.user_id, 'Укажите свою дату рождения в формате (дд.мм.гггг):')                                    
            return self.new_message(3)                

    # i - отличительный параметр, что именно None
    def new_message(self, i):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if i == 0:
                    # Проверка на числа
                    contains_digit = False
                    for x in event.text:
                        if x.isdigit():
                            contains_digit = True
                            break  # Прерываем цикл, если найдена цифра
                    if contains_digit:
                        self.message_send(event.user_id, 'Введите имя и фамилию без чисел:')
                    else:
                        return event.text

                if i == 1:
                    if event.text == "1" or event.text == "2":
                        return int(event.text)
                    else:
                        self.message_send(event.user_id, 'Неверный формат ввода пола. Введите 1 или 2:')

                if i == 2:
                    # Проверка на числа
                    contains_digit = False
                    for x in event.text:
                        if x.isdigit():
                            contains_digit = True
                            break  # Прерываем цикл, если найдена цифра
                    if contains_digit:
                        self.message_send(event.user_id, 'Неверно указан город. Введите название города без чисел:')
                    else:
                        return event.text

                if i == 3:
                    pattern = r'^\d{2}\.\d{2}\.\d{4}$'
                    if not re.match(pattern, event.text):
                        self.message_send(event.user_id, 'Пожалуйста, введите вашу дату '
                                                         'рождения в формате (дд.мм.гггг):')
                    else:
                        return self._bdate_toyear(event.text)
                    

    def _bdate_toyear(self, bdate):
        user_year = bdate.split('.')[2]
        now = datetime.now().year
        return now - int(user_year)


    def request_photo(self, worksheet):
        photos = self.vk_tools.get_photos(worksheet['id'])
        photo_string = ''
        for photo in photos:
            photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
        return photo_string    
        

    def get_file(self, worksheets, event):
        while True:
            if worksheets:
                worksheet = worksheets.pop()
            
                if not check_user(engine, event.user_id, worksheet['id']):
                    add_user(engine, event.user_id, worksheet['id'])
                
                    yield worksheet
            else:
                worksheets = self.vk_tools.search_worksheet(self.params, self.offset)
                if not worksheets:
                    yield None

    

if __name__ == '__main__':
    bot_interface = BotInterface(comunity_token, acces_token)
    bot_interface.event_handler()
