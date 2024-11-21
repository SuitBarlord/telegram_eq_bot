import json
import telebot
import database.mysql_query as query
import re
import menu.menu as menu
import requests
import requests
from requests.auth import HTTPBasicAuth
import pytz
from async_request.request_task import RequestTask
from utils.utilities import Utilities
from transliterate import translit
import asyncio
import logging
from telebot.async_telebot import AsyncTeleBot
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

bot = AsyncTeleBot(str(config['bot']['key']))



username = config['portal']['user']
password = config['portal']['password']


filials_2 = {}
filials = {}
filials_adress = {}

@bot.callback_query_handler(func=lambda call: True)
async def callback_query(call):
    id = call.from_user.id
    if(call.data.rfind("Zapis'_v_")) > -1:
            filial = call.data.split("Zapis'_v_")[1]
            filial = filials_2[str(filial)]

            query.sql_init.update_last_id_menu(id, call.message.message_id)

            step = f"Запись в {filial}"

            query.sql_init.update_last_step(id, str(step))

            arr_menu = []
            query.sql_init.update_last_filial(id, filial)

            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)

            filial_id = filials[str(user[7])]

            api_endpoint = f'https://mfc-eq.loc/api/v1/search/vrepservicewindowviewes?search=%7B%22search%22:%5B%7B%22field%22:%22unitId%22,%22operator%22:%22eq%22,%22value%22:{filial_id}%7D%5D%7D&size=1000'

            headers = {"Accept": "application/json"}

            response = await RequestTask.async_fetch_get(api_endpoint, headers, username, password)

            res = response['_embedded']['vrepservicewindowviewes']
            arr_groups = []
            for item in res:
                arr_groups.append(f"Перейти к {item['groupName']}")

            arr_groups = list(set(arr_groups))
            arr_groups.append("Вернуться в главное меню")

            query.sql_init.update_last_filial(id, filial)

            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)

            text_message = f"Ваши выборы по текущей записи - {user[18]} --> {user[7]}.\nТеперь выберите группу из представленных ниже: "

            await menu.build_inline_menu_edit(arr_menu=[
                "Забрать готовый результат(категория) ",
                "Консультация(категория) ",
                "Прием документов(категория) ",
                "Вернуться в главное меню"
            ], id=id, bot=bot, message_id=user[15], text_message=text_message)

    elif(call.data.rfind("Otmenit'_talon_-_c_PIN_-_") > -1): 
            pin = call.data.split("Otmenit'_talon_-_c_PIN_-_")[1]
            ticket = query.sql_init.get_tickets_pin(pin)
            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)

            if str(ticket[0][2]) == str(id):
                json_data = {
                    "id": ticket[0][15],
                    "unit": {
                        "id": filials[str(ticket[0][10])]
                    }
                }
                api_endpoint = f'https://mfc-eq.loc/api/v1/cancel'

                headers = {"Accept": "application/json"}
                response = await RequestTask.async_fetch_post(api_endpoint, json_data, headers, username, password)

                if response['id'] != '':
                    msg=f"Талон - {ticket[0][5]}, {ticket[0][6]}, Дата - {ticket[0][8]}, Время - {Utilities.time_format(ticket[0][9])}, ПИН - {ticket[0][16]}, успешно <u><b>был Вами отменен</b></u>."
                    await bot.send_message(id, msg, parse_mode="HTML")
                    query.sql_init.update_status_ticket(id, "Отменен", ticket[0][16])
                    text_message = "Ваш талон успешно <u><b>был отменен</u></b>, теперь вы можете перейти к другим своим талонам или вернуться в главное меню:"
                    try:
                        await bot.delete_message(id,str(user[15]))
                    except Exception as e:
                        # Если сообщение с таким id не найдено, выводим соответствующее сообщение
                        if e.error_code == 400 and e.description == "Bad Request: message to delete not found":
                            pass
                        else:
                            pass
                    markup, res_message = await menu.build_inline_menu(arr_menu=[
                        "Мои талоны",
                        f"Вернуться в главное меню"
                    ], id=id, message="Выберите из доступного списка функции: ", bot=bot)
                    query.sql_init.update_last_id_menu(id, res_message.message_id)
            else:
                msg=f"У Вас нет талона с таким ПИН."
                await bot.send_message(id, msg)
                await menu.build_inline_menu_edit(arr_menu=[
                        f"Вернуться в главное меню"
                ], id=id, bot=bot, message_id=user[15])


    elif(call.data == "Vernut'sja_v_glavnoe_menju"):
            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)
            if(user[4] == 'yes'):
                try:
                    await bot.delete_message(id,str(user[15]))
                except Exception as e:
                    # Если сообщение с таким id не найдено, выводим соответствующее сообщение
                    if e.error_code == 400 and e.description == "Bad Request: message to delete not found":
                        pass
                    else:
                        pass
                markup, res_message = await menu.build_inline_menu(arr_menu=[
                    "Записаться на прием",
                    "Мои талоны",
                    "Обратная связь",
                    "Помощь",
                ], id=id, message="Выберите из доступного списка функции: ", bot=bot)
                query.sql_init.update_last_id_menu(id, res_message.message_id)

    elif((call.data == "Zapisat'sja_na_priem") or (call.data == "Записаться на прием в другой филиал") or (call.data == "Назад к выбору филиала")):
            await menu.remove_menu(id, "Message", bot)
            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)
            if(user[5] == 'yes' and user[4] == 'yes'):
                if query.sql_init.get_col_tickets(id)[0][0] >= 1:
                    msg=f"Вы записали сегодня 1 талон. Временно принемает только 1 талон на 24 часа. Пожалуйста, запишитесь завтра."
                    await bot.send_message(id, msg)
                else:
                    arr = []

                    api_endpoint = 'https://mfc-eq.loc/api/v1/units.json?size=1000&sort=shortName'

                    headers = {"Accept": "application/json"}

                    # response = await fetch_data(api_endpoint, headers, username, password)
                    response = await RequestTask.async_fetch_get(api_endpoint, headers, username, password)
                    res = response['_embedded']['units']
                    for item in res:
                        if (item['id'] == 1 or item['id'] == 21001 or item['id'] == 19801):
                             pass
                        else:
                            arr.append(f"Запись в {item['shortName']}")
                            filials_2.update({str(translit(str(item['shortName']).replace(' ', '_'), 'ru', reversed=True)): item['shortName']})
                            filials_adress.update({str(translit(str("Запись в " + item['shortName']).replace(' ', '_'), 'ru', reversed=True)): item['shortAddress']})

                    import json

                    with open("/var/test_tg/filials_key.json", "r") as json_file:
                        data = json.load(json_file)

                    dict_2 = {}
                    import string

                    with open("/var/test_tg/adress_filials.json", "r") as json_file:
                        data_2 = json.load(json_file)

                    for key, value in data_2.items():
                        print(f"Name: {value['name']}")
                        print(f"Data: {value['data']}")
                        dict_2.update({str(value['name']): str(value['data'])})

                    arr.append("Вернуться в главное меню")

                    dict_2.update({"Вернуться в главное меню": ""})

                    print(dict_2)

                    text_message = "Прелагаем Вам выбрать район и после филиал для предварительной записи талона.\nПри нажатии на 'Вернуться в главное меню', Ваши выборы сбрасываются.\nПожалуйста, выберите район:"
                    
                    markup, res_message = await menu.build_inline_menu_edit_filials_n(arr_menu=dict_2, id=id, bot=bot, message_id=user[15], text_message=text_message, filials_adress=data)
            else:
                msg = f"Сначала введите свое ФИО"
                await bot.send_message(id, msg)


    elif(call.data.rfind("Region_") > -1):
            
            region = call.data

            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)

            dict_2 = {}
            import json
            with open("/var/test_tg/adress_filials.json", "r") as json_file:
                data_2 = json.load(json_file)

            with open("/var/test_tg/filials_key.json", "r") as json_file:
                data = json.load(json_file)

            if region == 'Region_Zabaikalskiy':
                query.sql_init.update_last_region(id, region)
                query.sql_init.update_last_region_name(id, "Забайкальский край")
                for key, value in data.items():
                    dict_2.update({str(value): str(key)})
            else:
                for key, value in data_2.items():
                    if value['data'] == region:
                        query.sql_init.update_last_region(id, value['data'])
                        query.sql_init.update_last_region_name(id, value['name'])
                        for key_2, value_2 in value['local'].items():
                            dict_2.update({str(value_2['adress']): str(value_2['data'])})

                dict_2.update({"Вернуться в главное меню": ""})
                            
            data = {}

            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)

            text_message =  f"Ваши выборы по текущей записи - {user[18]}.\nТеперь выберите конкретный филиал из ниже представленных: "

            markup, res_message = await menu.build_inline_menu_edit_filials_n_p(arr_menu=dict_2, id=id, bot=bot, message_id=user[15], text_message=text_message, filials_adress=data)


    elif(call.data.rfind("pagef_") > -1):
            
            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)
            page = int(call.data.split("_")[1])
            
            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)

            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)

            region = user[17]

            dict_2 = {}
            import json
            with open("/var/test_tg/adress_filials.json", "r") as json_file:
                data_2 = json.load(json_file)

            with open("/var/test_tg/filials_key.json", "r") as json_file:
                data = json.load(json_file)

            if region == 'Region_Zabaikalskiy':
                for key, value in data.items():
                    dict_2.update({str(value): str(key)})
            else:
                for key, value in data_2.items():
                    print(value)
                    if value['data'] == region:
                        query.sql_init.update_last_region(id, value['name'])
                        for key_2, value_2 in value['local'].items():
                            dict_2.update({str(value_2['adress']): str(value_2['data'])})

            data = {}

            print(dict_2)

            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)

            text_message = f"Ваши выборы по текущей записи - {user[18]}\nТеперь выберите конкретный филиал из ниже представленных: "

            markup, res_message = await menu.build_inline_menu_edit_filials_n_p(arr_menu=dict_2, id=id, bot=bot, message_id=user[15], text_message=text_message, filials_adress=data, page=page)


    elif(call.data.rfind("Zabrat'_gotovyj_rezul'tat(kategorija)_") > -1):

            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)

            query.sql_init.update_last_step(id, str(user[7]))

            filial = user[7]

            filial_id = filials[str(filial)]

            query.sql_init.update_last_category(id, "Забрать готовый результат(категория)")

            api_endpoint = f'https://mfc-eq.loc/api/v1/search/vrepservicewindowviewes?search=%7B%22search%22:%5B%7B%22field%22:%22unitId%22,%22operator%22:%22eq%22,%22value%22:{filial_id}%7D%5D%7D&size=1000'

            headers = {"Accept": "application/json"}
            response = await RequestTask.async_fetch_get(api_endpoint, headers, username, password)
            res = response['_embedded']['vrepservicewindowviewes']
            arr_groups = []
            dict = {}
            for item in res:
                if item['groupName'] == 'Выдача документов':
                    arr_groups.append(f"Перейти к {item['groupName']}")
            arr_groups = list(set(arr_groups))

            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)

            text_message = f"Ваши выборы по текущей записи - {user[18]} --> {user[7]} --> {user[13]}\nТеперь выберите группу услуг из ниже представленных:"

            dict.update({"Назад": str("Zapis'_v_" + user[14])})
            await menu.build_inline_menu_edit_group(arr_menu=arr_groups, dict=dict, id=id, bot=bot, message_id=user[15], text_message=text_message)


    elif(call.data.rfind("Konsul'tatsija(kategorija)_") > -1):
            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)

            query.sql_init.update_last_step(id, str(user[7]))

            filial = user[7]

            filial_id = filials[str(filial)]

            query.sql_init.update_last_category(id, "Консультация(категория)")

            api_endpoint = f'https://mfc-eq.loc/api/v1/search/vrepservicewindowviewes?search=%7B%22search%22:%5B%7B%22field%22:%22unitId%22,%22operator%22:%22eq%22,%22value%22:{filial_id}%7D%5D%7D&size=1000'
            proxy = {
                "http" : "192.168.137.254:3128"
            }
            headers = {"Accept": "application/json"}
            # response = requests.get(api_endpoint, headers=headers, auth=HTTPBasicAuth(username, password), verify=False, proxies=proxy)
            response = await RequestTask.async_fetch_get(api_endpoint, headers, username, password)
            res = response['_embedded']['vrepservicewindowviewes']
            arr_groups = []
            dict = {}
            for item in res:
                category = re.search(r'\((.*?)\)', str(item['serviceName']))
                if category:
                    result = category.group(1)
                    if str(result) == 'Консультация':
                        if item['groupName'] != 'Консультация':
                            arr_groups.append(f"Перейти к {item['groupName']}")
                    if item['groupName'] == 'Консультация':
                        dict.update({str(f"Выбрать {item['serviceName']}"): item['id']})

            arr_groups = list(set(arr_groups))

            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)


            text_message = f"Ваши выборы по текущей записи - {user[18]} --> {user[7]} --> {user[13]}\nТеперь выберите группу услуг из ниже представленных:"

            dict.update({"Назад": str("Zapis'_v_" + user[14])})
            await menu.build_inline_menu_edit_group(arr_menu=arr_groups, dict=dict, id=id, bot=bot, message_id=user[15], text_message=text_message)


    elif(call.data.rfind("Priem_dokumentov(kategorija)_") > -1):

            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)

            query.sql_init.update_last_step(id, str(user[7]))

            filial = user[7]

            filial_id = filials[str(filial)]

            query.sql_init.update_last_category(id, "Прием документов(категория)")

            api_endpoint = f'https://mfc-eq.loc/api/v1/search/vrepservicewindowviewes?search=%7B%22search%22:%5B%7B%22field%22:%22unitId%22,%22operator%22:%22eq%22,%22value%22:{filial_id}%7D%5D%7D&size=1000'
            proxy = {
                "http" : "192.168.137.254:3128"
            }
            headers = {"Accept": "application/json"}
            response = requests.get(api_endpoint, headers=headers, auth=HTTPBasicAuth(username, password), verify=False, proxies=proxy)
            res = response.json()['_embedded']['vrepservicewindowviewes']

            arr_groups = []
            dict = {}
            for item in res:
                category = re.search(r'\((.*?)\)', str(item['serviceName']))
                if category:
                    result = category.group(1)
                    if str(result) == 'Прием документов':
                        if item['groupName'] != 'Приём документов':
                            arr_groups.append(f"Перейти к {item['groupName']}")
                    if item['groupName'] == 'Приём документов':
                        dict.update({str(f"Выбрать {item['serviceName']}"): item['id']})

            arr_groups = list(set(arr_groups))

            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)


            text_message = f"Ваши выборы по текущей записи - {user[18]} --> {user[7]} --> {user[13]}\nТеперь выберите группу услуг из ниже представленных:"

            dict.update({"Назад": str("Zapis'_v_" + user[14])})
            await menu.build_inline_menu_edit_group(arr_menu=arr_groups, dict=dict, id=id, bot=bot, message_id=user[15], text_message=text_message)


    elif(call.data.rfind("Perejti_k_") > -1):
            group = call.data.split("Perejti_k_")[1]
            group = str(translit(group, 'ru', reversed=False)).replace("_", " ").replace('Ь', 'ь')

            arr_services = []
            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)

            query.sql_init.update_last_group(id, group)

            filial = user[7]

            filial_id = filials[str(filial)]

            query.sql_init.update_last_step(id, str(user[13] + " "))

            api_endpoint = f'https://mfc-eq.loc/api/v1/search/vrepservicewindowviewes?search=%7B%22search%22:%5B%7B%22field%22:%22unitId%22,%22operator%22:%22eq%22,%22value%22:{filial_id}%7D%5D%7D&size=1000'
            proxy = {
                "http" : "192.168.137.254:3128"
            }
            headers = {"Accept": "application/json"}
            response = requests.get(api_endpoint, headers=headers, auth=HTTPBasicAuth(username, password), verify=False, proxies=proxy)
            res = response.json()['_embedded']['vrepservicewindowviewes']
            services = {}

            
            for item in res:
                if item['groupName'] == group:
                    if item['groupName'] == 'Выдача документов':
                        arr_services.append(f"Выбрать {item['serviceName']}")
                        services.update({item['serviceName']: item['id']})
                    else:
                        category = re.findall(r'\((.*?)\)', item['serviceName'])[-1]
                        if category:
                            last_category = str(user[13]).split("(")[0]
                            if str(user[13]).split("(")[0] == category:
                                arr_services.append(f"Выбрать {item['serviceName']}")
                                services.update({item['serviceName']: item['id']})


            arr_services = list(set(arr_services))
            arr_services.append("Вернуться в главное меню")
            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)


            text_message = f"Ваши выборы по текущей записи - {user[18]} --> {user[7]} --> {user[13]} --> {user[8]}\nТеперь выберите орган из ниже представленных:"

            services.update({"Назад": str(user[14])})
            await menu.build_inline_menu_edit_usluga(arr_menu=arr_services, dict=services, id=id, bot=bot, message_id=user[15], text_message=text_message)


    elif(call.data.rfind("Na_datu_") > -1):
            date = call.data.split("Na_datu_")[1]
            query.sql_init.update_last_date(id, date)
            date = date + "T00:00:00.000+0900"
            arr_times = []
            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)
            filial = user[7]

            filial_id = filials[str(filial)]

            data = {
                "servDay": str(user[10]),
                "service": {
                    "id": str(user[12])
                },    
                "countService": str(user[11]),
                "unit": {
                    "id": int(filial_id)
                }
            }

            api_endpoint = f'https://mfc-eq.loc/api/v1/getSlots'
            proxy = {
                "http" : "192.168.137.254:3128"
            }
            headers = {"Accept": "application/json"}
            response = requests.post(api_endpoint, headers=headers, auth=HTTPBasicAuth(username, password), json=data, verify=False, proxies=proxy)

            
            response_data = response.json()['_embedded']['timeSlots']

            arr_time = []

            for item in response_data:
                arr_time.append(f"Записаться на {Utilities.time_format(item['timeFrom'])}")


            arr_time.append("Вернуться в главное меню")

            text_message = f"Ваши шаги выборов по текущей записи - {user[18]} --> {user[7]} --> {user[13]} --> {user[8]} --> {user[9]} --> Количество {user[11]} -->{Utilities.date_format(user[10])}\nТеперь выберите свободное время для записи из ниже представленных:"

            await menu.build_inline_menu_edit_t_p(arr_menu=arr_time, id=id, bot=bot, message_id=user[15], text_message=text_message)


    elif(call.data.rfind("paget_") > -1):
            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)
            date = user[10]
            page = int(call.data.split("_")[1])
            # query.sql_init.update_last_date(id, date)
            date = date + "T00:00:00.000+0900"
            arr_times = []
            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)
            filial = user[7]

            filial_id = filials[str(filial)]

            data = {
                "servDay": str(user[10]),
                "service": {
                    "id": str(user[12])
                },    
                "countService": str(user[11]),
                "unit": {
                    "id": int(filial_id)
                }
            }

            api_endpoint = f'https://mfc-eq.loc/api/v1/getSlots'
            proxy = {
                "http" : "192.168.137.254:3128"
            }
            headers = {"Accept": "application/json"}
            response = requests.post(api_endpoint, headers=headers, auth=HTTPBasicAuth(username, password), json=data, verify=False, proxies=proxy)

            
            response_data = response.json()['_embedded']['timeSlots']

            arr_time = []

            for item in response_data:
                arr_time.append(f"Записаться на {Utilities.time_format(item['timeFrom'])}")

            text_message = f"Ваши шаги выборов по текущей записи - {user[18]} --> {user[7]} --> {user[13]} --> {user[8]} --> {user[9]} -->{user[11]} -->{user[10]}\nТеперь выберите свободное время для записи из ниже представленных:"

            await menu.build_inline_menu_edit_t_p(arr_menu=arr_time, id=id, bot=bot, message_id=user[15], text_message=text_message, page=page)


    elif(call.data.rfind("Zapisat'sja_na_") > -1):

            time = call.data.split("Zapisat'sja_na_")[1]

            query.sql_init.update_last_time(id, time)

            try:
                    await bot.delete_message(id,call.message.message_id)
            except Exception as e:
                    # Если сообщение с таким id не найдено, выводим соответствующее сообщение
                    if e.error_code == 400 and e.description == "Bad Request: message to delete not found":
                        pass
                    else:
                        pass

            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)

            msg = f"Записаться в филиал <u><b>{user[7]}</b></u>, на услугу <u><b>{user[9]}</b></u> на <u><b>{Utilities.date_format(user[10])}</b></u> в <u><b>{user[19]}</b></u> с количеством дел <u><b>{user[11]}</b></u>?\nЕсли хотите что-то изменить, нажмите 'Вернуться в главное меню' и заново сделайте выборы для записи талона."


            markup, res_message = await menu.build_inline_menu(arr_menu=[
                    "Да, записаться",
                    "Вернуться в главное меню",
                ], id=id, message=msg, bot=bot)
            query.sql_init.update_last_id_menu(id, res_message.message_id)


    elif(call.data == "Da,_zapisat'sja"):
            

            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)

            time = user[19]

            filial = user[7]

            filial_id = filials[str(filial)]

            service_data = []

            api_endpoint = f'https://mfc-eq.loc/api/v1/units.json/{filial_id}/services'
            proxy = {
                "http" : "192.168.137.254:3128"
            }
            headers = {"Accept": "application/json"}
            response = requests.get(api_endpoint, headers=headers, auth=HTTPBasicAuth(username, password), verify=False, proxies=proxy)

            res = response.json()['_embedded']['services']

            service_id = int(user[12])
            for item in res:
                if item['id'] == service_id:
                    service_data.append(item)


            from datetime import datetime
            # Создаем объект времени
            time_str = str(time)
            time_format = "%H:%M"
            time = datetime.strptime(time_str, time_format)

            # Устанавливаем часовой пояс
            timezone_str = "+0900"
            timezone = pytz.FixedOffset(int(timezone_str[1:3]) * 60 + int(timezone_str[3:5]))

            # Преобразуем время в нужный формат с часовым поясом
            time_with_timezone = time.replace(tzinfo=timezone)
            time_with_timezone_str = time_with_timezone.strftime("%H:%M:%S.%f%z")

            time_str = time_with_timezone_str
            parts = time_str.split(".")  # Разбиваем строку по точке
            time_without_zeros = parts[0] + "." + parts[1][:3] + parts[1][-5:]  # Соединяем части, оставляя только три цифры после точки


            reserve_time = user[10] + "T" + time_without_zeros

            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)

            date_order = user[10]
            
            import json
            with open('/var/test_tg/book_info.json', 'r') as file:
                data = json.load(file)

            # Копируем JSON объект в переменную
            json_data = data.copy()

            # Меняем значения по ключу в переменной
            json_data['service']['id'] = service_data[0]['id']
            json_data['service']['prefix'] = service_data[0]['prefix']
            json_data['service']['description'] = service_data[0]['description']
            json_data['service']['name'] = service_data[0]['name']
            json_data['service']['timeService'] = service_data[0]['timeServicePreRecord']

            json_data['countService'] = user[11]
            json_data['servDay'] = str(date_order)
            json_data['reserveTime'] = reserve_time
            json_data['fio'] = user[2]
            json_data['mobilePhone'] = user[3]

            filial = user[7]

            filial_id = filials[str(filial)]

            api_endpoint = f'https://mfc-eq.loc/api/v1/units.json/{filial_id}'
            proxy = {
                "http" : "192.168.137.254:3128"
            }
            headers = {"Accept": "application/json"}
            response_unit = requests.get(api_endpoint, headers=headers, auth=HTTPBasicAuth(username, password), verify=False, proxies=proxy)

            json_data['unit'] = response_unit.json()

            api_endpoint = f'https://mfc-eq.loc/api/v1/book'
            proxy = {
                "http" : "192.168.137.254:3128"
            }
            headers = {"Accept": "application/json"}
            response = requests.post(api_endpoint, headers=headers, auth=HTTPBasicAuth(username, password), json=json_data, verify=False, proxies=proxy)

            if response.json()['id'] != '':
                query.sql_init.create_ticket(id, response.json()['prefix'], response.json()['number'], response.json()['fullNumber'], user[9], user[11], user[10], response.json()['reserveTime'], user[7], 'no', 'no', 1, response.json()['id'] ,response.json()['pin'], "Зарезервирован")

                ticket = query.sql_init.get_ticket_l_id(id)

                date_time_obj = datetime.strptime(ticket[0][9], "%Y-%m-%dT%H:%M:%S.%f%z")

                date = date_time_obj.date().strftime("%d.%m.%Y")
                time = date_time_obj.time().strftime("%H:%M")

                msg=f"Ваш талон - <u><b>{ticket[0][5]}</b></u>, филиал - <u><b>{ticket[0][10]}</b></u>, услуга - <u><b>{ticket[0][6]}</b></u>, дата - <u><b>{date}</b></u>, время - <u><b>{time}</b></u> - <u><b>сохранен и занесен в очередь</b></u>. Свои талоны вы можете посмотреть в разделе главного меню - мои талоны."
                await bot.send_message(id, msg, parse_mode="HTML")
            else:
                msg=f"Ваш талон - <u><b>{ticket[0][5]}</b></u>, филиал - <u><b>{ticket[0][10]}</b></u>, услуга - <u><b>{ticket[0][6]}</b></u>, дата - <u><b>{date}</b></u>, время - <u><b>{time}</b></u> - <u><b>не был сохранен</b></u>. Пожалуйста, выберите другое время записи."
                await bot.send_message(id, msg, parse_mode="HTML")
            
            try:
                    await bot.delete_message(id,str(user[15]))
            except Exception as e:
                    # Если сообщение с таким id не найдено, выводим соответствующее сообщение
                    if e.error_code == 400 and e.description == "Bad Request: message to delete not found":
                        pass
                    else:
                        pass
            markup, res_message = await menu.build_inline_menu(arr_menu=[
                    "Записаться на прием",
                    "Мои талоны",
                    "Обратная связь",
                    "Помощь",
                ], id=id, message="Выберите из доступного списка функции: ", bot=bot)
            query.sql_init.update_last_id_menu(id, res_message.message_id)


    elif(call.data.rfind("PIN_-_") > -1): 

            pin = str(call.data.split("PIN_-_")[1])

            ticket = query.sql_init.get_tickets_pin_id(id, pin)
            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)
            if ticket[0][17] == 'Отменен':
                msg=f"Талон - {ticket[0][5]}, {ticket[0][6]}, Филиал-{ticket[0][10]}, {ticket[0][8]}, ПИН - {ticket[0][16]}, был отменен."
                await bot.send_message(id, msg)
                text_message = f"Вы перешли к талону {ticket[0][5]}."
                try:
                    await bot.delete_message(id,str(user[15]))
                except Exception as e:
                    # Если сообщение с таким id не найдено, выводим соответствующее сообщение
                    if e.error_code == 400 and e.description == "Bad Request: message to delete not found":
                        pass
                    else:
                        # Если это другая ошибка, выводим её описание
                        pass
                markup, res_message = await menu.build_inline_menu(arr_menu=[
                    "Записаться на прием",
                    "Мои талоны",
                    "Обратная связь",
                    "Помощь",
                ], id=id, message="Выберите из доступного списка функции: ", bot=bot)
                query.sql_init.update_last_id_menu(id, res_message.message_id)

            elif ticket[0][17] == 'Принят':
                msg=f"Талон - {ticket[0][5]}, {ticket[0][6]}, Филиал-{ticket[0][10]}, {ticket[0][8]}, ПИН - {ticket[0][16]}, был принят."
                await bot.send_message(id, msg)
                text_message = f"Вы перешли к талону {ticket[0][5]}."
                try:
                    await bot.delete_message(id,str(user[15]))
                except Exception as e:
                    # Если сообщение с таким id не найдено, выводим соответствующее сообщение
                    if e.error_code == 400 and e.description == "Bad Request: message to delete not found":
                        # await bot.reply_to(message, "Сообщение с таким id не найдено.")
                        pass
                    else:
                        # Если это другая ошибка, выводим её описание
                        # await bot.reply_to(message, f"Ошибка: {e.description}")
                        pass
                markup, res_message = await menu.build_inline_menu(arr_menu=[
                    "Записаться на прием",
                    "Мои талоны",
                    "Обратная связь",
                    "Помощь",
                ], id=id, message="Выберите из доступного списка функции: ", bot=bot)
                query.sql_init.update_last_id_menu(id, res_message.message_id)

            else:
                msg=f"Талон - {ticket[0][5]}, {ticket[0][6]}, Филиал-{ticket[0][10]}, Дата - {ticket[0][8]}, Время - {Utilities.time_format(ticket[0][9])}, ПИН - {ticket[0][16]}, Статус - {ticket[0][17]}."
                await bot.send_message(id, msg)
                
                try:
                    await bot.delete_message(id,str(user[15]))
                except Exception as e:
                    # Если сообщение с таким id не найдено, выводим соответствующее сообщение
                    if e.error_code == 400 and e.description == "Bad Request: message to delete not found":
                        # await bot.reply_to(message, "Сообщение с таким id не найдено.")
                        pass
                    else:
                        # Если это другая ошибка, выводим её описание
                        # await bot.reply_to(message, f"Ошибка: {e.description}")
                        pass
                markup, res_message = await menu.build_inline_menu(arr_menu=[
                    f"Отменить талон - c ПИН - {ticket[0][16]}",
                    "Вернуться в главное меню"
                ], id=id, message="Вы можете отменить выбранный талон, или вернуться в главное меню. Для того чтобы отменить талон нажмите 'Отменить талон - ПИН...': ", bot=bot)
                query.sql_init.update_last_id_menu(id, res_message.message_id)


    elif(call.data.rfind("Usluga_") > -1):
            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)
            service = call.data.split("Usluga_")[1]
            id_usluga = ""
            id_usluga = service.split("_")[-1]

            filial = user[7]

            filial_id = filials[str(filial)]

            api_endpoint = f'https://mfc-eq.loc/api/v1/search/vrepservicewindowviewes?search=%7B%22search%22:%5B%7B%22field%22:%22unitId%22,%22operator%22:%22eq%22,%22value%22:{filial_id}%7D%5D%7D&size=1000'
            proxy = {
                "http" : "192.168.137.254:3128"
            }
            headers = {"Accept": "application/json"}
            response_2 = requests.get(api_endpoint, headers=headers, auth=HTTPBasicAuth(username, password), verify=False, proxies=proxy)
            res_2 = response_2.json()['_embedded']['vrepservicewindowviewes']

            usluga = ""

            for item in res_2:
                if item['id'] == service:
                    usluga = item['serviceName']

            query.sql_init.update_last_usluga(id, usluga)

            query.sql_init.update_last_usluga_id(id, id_usluga)

            filial = user[7]

            filial_id = filials[str(filial)]

            query.sql_init.update_last_step(id, str(user[8]))

            api_endpoint = f'https://mfc-eq.loc/api/v1/units.json/{filial_id}/services'
            proxy = {
                "http" : "192.168.137.254:3128"
            }
            headers = {"Accept": "application/json"}
            response = requests.get(api_endpoint, headers=headers, auth=HTTPBasicAuth(username, password), verify=False, proxies=proxy)

            res = response.json()['_embedded']['services']

            arr_col = []

            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)

            for item in res:
                    if item['id'] == int(id_usluga):

                        if item['maxCountService'] == None:
                            arr_col = ['Количество дел 1']
                        else: 
                            # max_services = 10
                            max_services = int(item['maxCountService'])
                            if user[8] == "Выдача документов":
                                max_services = 10
                                arr_col = [f"Количество дел {i}" for i in range(1, max_services+1)]
                            # arr_col = [f"Кол-во дел {i}" for i in range(1, max_services+1)]
                            else:
                                arr_col = [f"Количество дел {i}" for i in range(1, max_services+1)]
                                # arr_col = ['Количество дел 1']


            query.sql_init.update_last_step(id, str(user[8]))

            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)

            group = user[14]

            arr_col.append("Назад")

            text_message = f"Ваши шаги выборов по текущей записи - {user[18]} --> {user[7]} --> {user[13]} --> {user[8]} --> {user[9]}\nТеперь выберите Количество дел из ниже представленных:"

            await menu.build_inline_menu_edit_col(arr_menu=arr_col, id=id, group=group, bot=bot, message_id=user[15], text_message=text_message)


    elif (call.data.rfind("Kolichestvo_del_") > -1):

            col_order = call.data.split("Kolichestvo_del_")[1]

            query.sql_init.update_last_col_order(id, col_order)
            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)
            filial = user[7]

            filial_id = filials[str(filial)]

            api_endpoint = f'https://mfc-eq.loc/api/v1/search/vrepservicewindowviewes?search=%7B%22search%22:%5B%7B%22field%22:%22unitId%22,%22operator%22:%22eq%22,%22value%22:{filial_id}%7D%5D%7D&size=1000'
            proxy = {
                "http" : "192.168.137.254:3128"
            }
            headers = {"Accept": "application/json"}
            response_2 = requests.get(api_endpoint, headers=headers, auth=HTTPBasicAuth(username, password), verify=False, proxies=proxy)
            res_2 = response_2.json()['_embedded']['vrepservicewindowviewes']

            id_usluga = ""

            id_usluga = int(user[12])

            filial = user[7]

            filial_id = filials[str(filial)]

            data = {
                "id": int(id_usluga),
                "unit": {
                    "id": int(filial_id)
                },
                "maxCountService": int(user[11])
            }

            arr_dates = []

            api_endpoint_2 = f'https://mfc-eq.loc/api/v1/getBookingDatesWithSlots'
            proxy = {
                "http" : "192.168.137.254:3128"
            }
            headers = {"Accept": "application/json"}
            response = requests.post(api_endpoint_2, headers=headers, auth=HTTPBasicAuth(username, password), json=data, verify=False, proxies=proxy)

            response_data = response.json()['content']

            for key, value in response_data.items():
                key = str(key).split("T", 1)[0]
                arr_dates.append(f"На дату {key}")
                
            arr_dates.append("Вернуться в главное меню")
            

            text_message = f"Ваши шаги выборов по текущей записи - {user[18]} --> {user[7]} --> {user[13]} --> {user[8]} --> {user[9]} --> Количество дел {user[11]}\nТеперь выберите свободную дату для записи из ниже представленных:"

            await menu.build_inline_menu_edit_date_p(arr_menu=arr_dates, id=id, bot=bot, message_id=user[15], text_message=text_message)


    elif (call.data.rfind("paged_") > -1):
            page = int(call.data.split("_")[1])

            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)
            filial = user[7]

            filial_id = filials[str(filial)]

            api_endpoint = f'https://mfc-eq.loc/api/v1/search/vrepservicewindowviewes?search=%7B%22search%22:%5B%7B%22field%22:%22unitId%22,%22operator%22:%22eq%22,%22value%22:{filial_id}%7D%5D%7D&size=1000'
            proxy = {
                "http" : "192.168.137.254:3128"
            }
            headers = {"Accept": "application/json"}
            response_2 = requests.get(api_endpoint, headers=headers, auth=HTTPBasicAuth(username, password), verify=False, proxies=proxy)
            res_2 = response_2.json()['_embedded']['vrepservicewindowviewes']

            id_usluga = ""

            id_usluga = int(user[12])

            filial = user[7]

            filial_id = filials[str(filial)]

            data = {
                "id": int(id_usluga),
                "unit": {
                    "id": int(filial_id)
                },
                "maxCountService": int(user[11])
            }

            arr_dates = []

            api_endpoint_2 = f'https://mfc-eq.loc/api/v1/getBookingDatesWithSlots'
            proxy = {
                "http" : "192.168.137.254:3128"
            }
            headers = {"Accept": "application/json"}
            response = requests.post(api_endpoint_2, headers=headers, auth=HTTPBasicAuth(username, password), json=data, verify=False, proxies=proxy)

            response_data = response.json()['content']

            for key, value in response_data.items():
                key = str(key).split("T", 1)[0]
                arr_dates.append(f"На дату {key}")
                

            text_message = f"Ваши шаги выборов по текущей записи - {user[18]} --> {user[7]} --> {user[13]} --> {user[8]} --> {user[9]} --> Количество дел - {user[11]}\nТеперь выберите свободную дату для записи из ниже представленных:"

            await menu.build_inline_menu_edit_date_p(arr_menu=arr_dates, id=id, bot=bot, message_id=user[15], text_message=text_message, page=page)


    elif(call.data == "Moi_talony"): 
            import time

            start_time = time.time()

            # tickets = query.sql_init.get_tickets_id(id)
            loop = asyncio.get_event_loop()
            tickets = await query.get_tickets_id(loop, id)

            arr_tickets = []
            for ticket in tickets:
                api_endpoint = f'https://mfc-eq.loc/api/v1/talons.json/{ticket[15]}/talonStatus'

                headers = {"Accept": "application/json"}
                # response = await fetch_data(api_endpoint, headers, username, password)
                response = await RequestTask.async_fetch_get(api_endpoint, headers, username, password)

                if (ticket[17]) == response['description']:
                    pass
                else:
                    query.sql_init.update_status_ticket(id, f"{response['description']}", ticket[16])
        

            loop = asyncio.get_event_loop()
            tickets = await query.get_tickets_id(loop, id)
            for ticket in tickets:
                arr_tickets.append(f"Талон-{ticket[5]}, Дата-{Utilities.date_format(ticket[8])}-{Utilities.time_format(ticket[9])},Статус-{ticket[17]}, ПИН - {ticket[16]}")


            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)

            text_message = "Здесь представленные Ваши талоны, которые были записаны через теллеграмм бота. Можете выбрать из данных талонов, чтобы узнать подробную информацию о талоне:"

            if arr_tickets == []:
                text_message = "У Вас пока нет талонов. Чтобы записаться - вернитесь в главное меню и перейдите к записи на прием."

            arr_tickets.append("Вернуться в главное меню")

            await menu.build_inline_menu_talons_edit(arr_menu=arr_tickets, id=id, message_id=user[15], bot=bot, text_message=text_message)
            end_time = time.time()
            execution_time = end_time - start_time
            print(execution_time)


    elif (call.data.rfind("page_") > -1):
        page = int(call.data.split("_")[1])

        import time

        start_time = time.time()

        # tickets = query.sql_init.get_tickets_id(id)
        loop = asyncio.get_event_loop()
        tickets = await query.get_tickets_id(loop, id)

        arr_tickets = []
        for ticket in tickets:
                api_endpoint = f'https://mfc-eq.loc/api/v1/talons.json/{ticket[15]}/talonStatus'

                headers = {"Accept": "application/json"}
                response = await RequestTask.async_fetch_get(api_endpoint, headers, username, password)
                # response = await fetch_data(api_endpoint, headers, username, password)

                if (ticket[17]) == response['description']:
                    pass
                else:
                    query.sql_init.update_status_ticket(id, f"{response['description']}", ticket[16])


        loop = asyncio.get_event_loop()
        tickets = await query.get_tickets_id(loop, id)
        for ticket in tickets:
                arr_tickets.append(f"Талон-{ticket[5]}, Дата-{Utilities.date_format(ticket[8])}-{Utilities.time_format(ticket[9])},Статус-{ticket[17]}, ПИН - {ticket[16]}")

        arr_tickets.append("Вернуться в главное меню")

        result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)

        text_message = "Номер текущей страницы талонов: "

        markup = await menu.build_inline_menu_talons_edit(arr_menu=arr_tickets, id=id, message_id=user[15], bot=bot, text_message=text_message, page=page)
        await bot.answer_callback_query(call.id)



    elif(call.data == "Da,_vse_verno."):
        try:
            await bot.delete_message(id, call.message.message_id)
        except Exception as e:
                # Если сообщение с таким id не найдено, выводим соответствующее сообщение
            if e.error_code == 400 and e.description == "Bad Request: message to delete not found":
                # await bot.reply_to(message, "Сообщение с таким id не найдено.")
                pass
            else:
                # Если это другая ошибка, выводим её описание
                # await bot.reply_to(message, f"Ошибка: {e.description}")
                pass

            
        msg = f"Уважаемый заявитель, для завершения регистрации нам необходимо получить Ваше согласие на обработку персональных данных.\nПожалуйста, подтвердите, что Вы даете согласие на обработку Ваших персональных данных в соответствии с нашей Политикой конфиденциальности."


        markup, res_message = await menu.build_inline_menu(arr_menu=[
                        "Да, я согласен",
                        "Нет, я не согласен",
                        "Подробнее о политике обработки персональных данных"
        ], id=id, message=msg, bot=bot)

        query.sql_init.update_last_id_menu(id, res_message.message_id)


    elif(call.data == "Da,_ja_soglasen"):

        try:
            await bot.delete_message(id, call.message.message_id)
        except Exception as e:
                # Если сообщение с таким id не найдено, выводим соответствующее сообщение
            if e.error_code == 400 and e.description == "Bad Request: message to delete not found":
                # await bot.reply_to(message, "Сообщение с таким id не найдено.")
                pass
            else:
                # Если это другая ошибка, выводим её описание
                # await bot.reply_to(message, f"Ошибка: {e.description}")
                pass
        
        result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)
        query.sql_init.update_status_sogl_yes(id)
        msg = f"<u><b>Регистрация завершена!</b></u> \n<u><b>ФИО: {user[2]}</b></u> \n<u><b>Телефон: {Utilities.format_phone_number(user[3])}</b></u> \n\nТеперь все функции бота доступны для вас. \nВыберите интересующую вас функцию:"
        await bot.send_message(id, msg, parse_mode="HTML")
        markup, res_message = await menu.build_inline_menu(arr_menu=[
            "Записаться на прием",
            "Мои талоны",
            "Обратная связь",
            "Помощь",
        ], id=id, message="Выберите из доступного списка функции: ", bot=bot)
        query.sql_init.update_last_id_menu(id, res_message.message_id)



    elif(call.data == "Net,_ja_ne_soglasen"):
        result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)
        try:
            await bot.delete_message(id, call.message.message_id)
        except Exception as e:
                # Если сообщение с таким id не найдено, выводим соответствующее сообщение
            if e.error_code == 400 and e.description == "Bad Request: message to delete not found":
                # await bot.reply_to(message, "Сообщение с таким id не найдено.")
                pass
            else:
                # Если это другая ошибка, выводим её описание
                # await bot.reply_to(message, f"Ошибка: {e.description}")
                pass
        msg = f"Спасибо, что Вы ознакомились с нашей Политикой конфиденциальности.\nК сожалению, без Вашего согласия на обработку персональных данных мы не можем предоставить Вам доступ к нашему сервису.\nКонфиденциальность и защита Ваших данных являются для нас важным приоритетом. Поэтому мы предлагаем Вам еще раз ознакомиться с нашей Политикой и рассмотреть возможность дать согласие на обработку персональных данных."
        await bot.send_message(id, msg, parse_mode="HTML")
        markup, res_message = await menu.build_inline_menu(arr_menu=[
            "Подробнее о политике обработки персональных данных",
        ], id=id, message="Выберите из доступного списка функции: ", bot=bot)
        query.sql_init.update_last_id_menu(id, res_message.message_id)



    elif(call.data == "Net,_izmenit'_dannye."):
        try:
            await bot.delete_message(id, call.message.message_id)
        except Exception as e:
                # Если сообщение с таким id не найдено, выводим соответствующее сообщение
            if e.error_code == 400 and e.description == "Bad Request: message to delete not found":
                # await bot.reply_to(message, "Сообщение с таким id не найдено.")
                pass
            else:
                # Если это другая ошибка, выводим её описание
                # await bot.reply_to(message, f"Ошибка: {e.description}")
                pass
        result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)
        query.sql_init.update_state_fio_correct(id)
        query.sql_init.update_state_phone_correct(id)
        msg = f"Введите верное ФИО полностью: "
        await bot.send_message(id, msg)


    elif(call.data == "Obratnaja_svjaz'"):
        result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)
        text_message = f'Любой гражданин, обратившийся в многофункциональный центр, может оставить своё мнение о качестве предоставления услуг. \n\nСпособов пройти эту процедуру несколько: \n-  на площадках МФЦ, в секторе пользовательского сопровождения, посредством гостевого компьютера; \n- оставив отзыв на сайте МФЦ (https://www.mfc-chita.ru/). Для этого вам необходимо авторизоваться на сайте, через ЕСИА и перейти в раздел "Оценка качества оказания услуг"(https://www.mfc-chita.ru/lk/vashkontrol/); \n- через сайт "Ваш контроль"(https://vashkontrol.ru/). \n\nТакже здесь Вы может оставить свой отзыв о нашем боте для предварительной записи талонов. \n\nУважаемый заявитель, напишите свой отзыв, критику или предложение по улучшению.\nКогда завершите отзыв, нажмите - "Завершить отзыв", и Ваш отзыв будет сохранен. \n Спасибо, что пользуетесь ботом!'
        await menu.build_inline_menu_edit(arr_menu=[
                        "Завершить отзыв"
                ], id=id, bot=bot, message_id=user[15], text_message=text_message)
        query.sql_init.update_last_comment_state(id)


    elif(call.data == "Zavershit'_otzyv"):
        result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)
        msg = f"Ваш отзыв сохранен. \nНам важно Ваше мнение, спасибо за обратную связь!"
        await bot.send_message(id, msg)
        # result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)
        try:
            await bot.delete_message(id,str(user[15]))
        except Exception as e:
            # Если сообщение с таким id не найдено, выводим соответствующее сообщение
            if e.error_code == 400 and e.description == "Bad Request: message to delete not found":
                # await bot.reply_to(message, "Сообщение с таким id не найдено.")
                pass
            else:
                # Если это другая ошибка, выводим её описание
                # await bot.reply_to(message, f"Ошибка: {e.description}")
                pass
        # text_message = f"Здесь Вы может оставить свой отзыв о нашем боте для предварительной записи талонов. \n Уважаемый заявитель, пожалуйста, напишите в одном сообщении свой отзыв, критику или предложение по улучшению. \n Спасибо, что пользуетесь ботом!"
        markup, res_message = await menu.build_inline_menu(arr_menu=[
                "Записаться на прием",
                "Мои талоны",
                "Обратная связь",
                "Помощь",
            ], id=id, message="Выберите из доступного списка функции: ", bot=bot)
        query.sql_init.update_last_id_menu(id, res_message.message_id)
        query.sql_init.update_comment_state(id)


    elif(call.data == "Podrobnee_o_politike_obrabotki_personal'nyh_dannyh"):
        result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)
        msg = f"Чтобы ознакомиться с полтикой обработки персональных данных, Вы можете перейти по следующим ссылкам:\nСсылка на раздел информации о защите персональных данных портала МФЦ Читы - https://www.mfc-chita.ru/zayavitelyam/info/zashita-personalnyh-dannyh-polzovatelej \nСсылка на документ Об утверждении политики обработки персональных данных в КГАУ МФЦ Забайкальского края в формате PDF - https://www.mfc-chita.ru/images/content_view/post9225/prikaz-237-ob-utverzhdenii-politiki-obrabotki-personalnyh-dannyh.pdf"
        await bot.send_message(id, msg)
        # result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)
        try:
            await bot.delete_message(id,str(user[15]))
        except Exception as e:
            # Если сообщение с таким id не найдено, выводим соответствующее сообщение
            if e.error_code == 400 and e.description == "Bad Request: message to delete not found":
                # await bot.reply_to(message, "Сообщение с таким id не найдено.")
                pass
            else:
                # Если это другая ошибка, выводим её описание
                # await bot.reply_to(message, f"Ошибка: {e.description}")
                pass
        # text_message = f"Здесь Вы может оставить свой отзыв о нашем боте для предварительной записи талонов. \n Уважаемый заявитель, пожалуйста, напишите в одном сообщении свой отзыв, критику или предложение по улучшению. \n Спасибо, что пользуетесь ботом!"
        markup, res_message = await menu.build_inline_menu(arr_menu=[
                "Да, я согласен",
                "Нет, я не согласен",
                "Подробнее о политике обработки персональных данных"
            ], id=id, message="Выберите из доступного списка функции: ", bot=bot)
        query.sql_init.update_last_id_menu(id, res_message.message_id)
        # query.sql_init.update_comment_state(id)


    elif(call.data == "Pomosch'"):
        result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)
        # text_message = f""
        msg = f"Если при осуществлении предварительной записи у Вас возникли трудности, рекомендуем позвонить по телефону: <u><b>8(3022) 21-10-10</b></u>."
        await bot.send_message(id, msg, parse_mode="HTML")


        try:
            await bot.delete_message(id,str(user[15]))
        except Exception as e:
            # Если сообщение с таким id не найдено, выводим соответствующее сообщение
            if e.error_code == 400 and e.description == "Bad Request: message to delete not found":
                # await bot.reply_to(message, "Сообщение с таким id не найдено.")
                pass
            else:
                # Если это другая ошибка, выводим её описание
                # await bot.reply_to(message, f"Ошибка: {e.description}")
                pass

        markup, res_message = await menu.build_inline_menu(arr_menu=[
                "Записаться на прием",
                "Мои талоны",
                "Обратная связь",
                "Помощь",
            ], id=id, message="Выберите из доступного списка функции: ", bot=bot)
        query.sql_init.update_last_id_menu(id, res_message.message_id)
        query.sql_init.update_comment_state(id)



@bot.message_handler(content_types=['text'])
async def get_text_messages(message):
    id = message.from_user.id
    text = message.text

    api_endpoint = 'https://mfc-eq.loc/api/v1/units.json?size=1000&sort=shortName'
    proxy = {
                    "http" : "192.168.137.254:3128"
        }
    headers = {"Accept": "application/json"}
    response = requests.get(api_endpoint, headers=headers, auth=HTTPBasicAuth(username, password), verify=False, proxies=proxy)
    res = response.json()['_embedded']['units']
    for item in res:
        filials.update({item['shortName']: item['id']})


    if text:

        result = query.sql_init.get_user_tg_id(id)
        if result == []:       
            query.sql_init.create_user(id)
            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)
        else:
            result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)

            query.sql_init.update_last_use_bot(id)

        result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)

        if user[4] == "correct":
            name = message.text
            if not(re.fullmatch(r'[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?', name)):
                msg = "Неправильный формат ФИО: "
                await bot.send_message(id, msg)
            else:
                query.sql_init.update_fio(id, name)
                if user[5] == 'yes':
                    print(user[5])


        result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)
        if (user[5] == "correct") and (user[4] == 'yes'):
                msg = "Введите Ваш мобильный номер телефона: "
                await bot.send_message(id, msg)
                query.sql_init.update_state_phone(id)
        elif user[5] == 'wait' and user[3] != '':
                phone = message.text
                if not(re.match(r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$', phone)):
                    msg = "Неправильный формат телефона: "
                    await bot.send_message(id, msg)
                else:
                    query.sql_init.update_phone(id, Utilities.format_phone_number(phone))
                    result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)
                    query.sql_init.update_phone_fio_pre_status(id)
                    msg = f"Вы ввели: \nФИО: {user[2]} \nТелефон: {Utilities.format_phone_number(user[3])}. \nПодтвердите указанные Вами данные: "
                    await bot.send_message(id, msg)
                    markup, res_message = await menu.build_inline_menu(arr_menu=[
                        "Да, все верно.",
                        "Нет, изменить данные.",
                    ], id=id, message="Выберите из доступного списка функции: ", bot=bot)
                    query.sql_init.update_last_id_menu(id, res_message.message_id)


        if fio == '':
            if user[4] == 'no':
                msg = "Здравствуйте! Вас приветствует автоматический помощник МФЦ Забайкальского края. Для начала использования бота необходима регистрация. "
                await bot.send_message(id, msg)
                msg = "Введите ФИО полностью: "
                await bot.send_message(id, msg)
                query.sql_init.update_state_fio(id)
            elif user[4] == 'wait':
                name = message.text
                if not(re.fullmatch(r'[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?', name)):
                    msg = "Неправильный формат ФИО: "
                    await bot.send_message(id, msg)
                else:
                    query.sql_init.update_fio(id, name)
                    if user[5] == 'yes':
                        print(user[5])
        result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)
        if (user[3] == '') and (user[4] == 'yes'):
            if user[5] == 'no':
                msg = "Введите Ваш мобильный номер телефона: "
                await bot.send_message(id, msg)
                query.sql_init.update_state_phone(id)
            elif user[5] == 'wait':
                phone = message.text
                if not(re.match(r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$', phone)):
                    msg = "Неправильный формат телефона: "
                    await bot.send_message(id, msg)
                else:
                    query.sql_init.update_phone(id, Utilities.format_phone_number(phone))
                    result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)
                    query.sql_init.update_phone_fio_pre_status(id)
                    msg = f"Вы ввели: \nФИО: {user[2]} \nТелефон: {Utilities.format_phone_number(user[3])}. \nПодтвердите указанные Вами данные: "
                    await bot.send_message(id, msg)
                    markup, res_message = await menu.build_inline_menu(arr_menu=[
                        "Да, все верно.",
                        "Нет, изменить данные.",
                    ], id=id, message="Выберите из доступного списка функции: ", bot=bot)
                    query.sql_init.update_last_id_menu(id, res_message.message_id)


        result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)
        if(text == "/start" or text == "Вернуться в главное меню" or text == "В главное меню"):
            if(user[4] == 'yes' and user[5] == 'yes'):
                result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)
                try:
                    await bot.delete_message(id,str(user[15]))
                except Exception as e:
                    # Если сообщение с таким id не найдено, выводим соответствующее сообщение
                    if e.error_code == 400 and e.description == "Bad Request: message to delete not found":
                        # await bot.reply_to(message, "Сообщение с таким id не найдено.")
                        pass
                    else:
                        # Если это другая ошибка, выводим её описание
                        # await bot.reply_to(message, f"Ошибка: {e.description}")
                        pass
                markup, res_message = await menu.build_inline_menu(arr_menu=[
                    "Записаться на прием",
                    "Мои талоны",
                    "Обратная связь",
                    "Помощь",
                ], id=id, message="Выберите из доступного списка функции: ", bot=bot)
                query.sql_init.update_last_id_menu(id, res_message.message_id)

        
        result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)
        if user[16] == 'wait':
            if message.text != '/start':
                comment = message.text
                # query.sql_init.update_last_comment(id, comment)
                query.sql_init.create_comment(id, comment)

                result, row_nums, user, fio = query.sql_init.get_user_tg_id(id)
                try:
                    await bot.delete_message(id,str(user[15]))
                except Exception as e:
                    # Если сообщение с таким id не найдено, выводим соответствующее сообщение
                    if e.error_code == 400 and e.description == "Bad Request: message to delete not found":
                        # await bot.reply_to(message, "Сообщение с таким id не найдено.")
                        pass
                    else:
                        # Если это другая ошибка, выводим её описание
                        # await bot.reply_to(message, f"Ошибка: {e.description}")
                        pass

                markup, res_message = await menu.build_inline_menu(arr_menu=[
                        "Завершить отзыв"
                ], id=id, message="Вы хотите продолжить отзыв или завершить?", bot=bot)
                query.sql_init.update_last_id_menu(id, res_message.message_id)


async def main():
    await bot.polling(timeout=40, non_stop=True, request_timeout=90)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
