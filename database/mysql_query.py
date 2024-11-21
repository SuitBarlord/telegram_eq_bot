import mysql.connector
from mysql.connector import Error
import datetime
import aiomysql
import configparser


config = configparser.ConfigParser()
config.read('config.ini')



class MySQL():      
    def __init__(self, host, db, user, password):
        self.host = host
        self.db = db
        self.user = user
        self.password = password

    def connect(self):
        try:
            connect = mysql.connector.connect(host = self.host, user = self.user, password = self.password, database = self.db, auth_plugin='mysql_native_password')
            print("Подключение к базе данных прошло успешно.")
            return connect
        except Error as e:          
            print(e)

    def get_user_tg_id(self, tg_id):
        connect = self.connect()
        sql = f"SELECT * FROM users WHERE tg_user_id='{tg_id}';"
        cursor = connect.cursor()
        result = False
        try:
            cursor.execute(sql)
            result = cursor.fetchall()
            if result != []:
                row_nums = cursor.rowcount
                user = result[0]
                fio = user[2]
                return result, row_nums, user, fio
            else:
                return result
        except Error as err:
            print(f"Error: '{err}'")

    def get_user_id(self, id):
        connect = self.connect()
        sql = f"SELECT * FROM users WHERE id='{id}';"
        cursor = connect.cursor()
        result = False
        try:
            cursor.execute(sql)
            result = cursor.fetchall()
            return result
        except Error as err:
            print(f"Error: '{err}'")

    def create_user(self, tg_id):
        connect = self.connect()
        sql = f"INSERT INTO users(tg_user_id, fio, phone, fio_reg, phone_reg, last_bot_use_unixtime, LastSelectMFC, LastSelectGroup, LastSelectUsluga, LastSelectDate, LastColOrder, LastStep, LastIdMenu, LastComment, LastRegion, LastRegionName, LastSelectTime) VALUES ('{tg_id}','','','no','no','{int(datetime.datetime.now().timestamp() * 1000)}','','','','','','','','','','','');"
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
            connect.close()
        except Error as err:
            print(f"Error: '{err}'")
    
    def update_last_use_bot(self, tg_id):
        connect = self.connect()
        sql = f"UPDATE users SET last_bot_use_unixtime='{int(datetime.datetime.now().timestamp() * 1000)}' WHERE tg_user_id ='{tg_id}'"
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
        except Error as err:
            print(f"Error: '{err}'")

    def update_fio(self, tg_id, fio):
        connect = self.connect()
        sql = f"UPDATE users SET fio='{fio}', fio_reg='yes' WHERE tg_user_id='{tg_id}'"
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
            # connect.close()
        except Error as err:
            print(f"Error: '{err}'")

    def update_state_fio(self, tg_id):
        connect = self.connect()
        sql = f"UPDATE users SET fio_reg='wait' WHERE tg_user_id='{tg_id}'"
        
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
        except Error as err:
            print(f"Error: '{err}'")

    def update_state_phone(self, tg_id):
        connect = self.connect()
        sql = f"UPDATE users SET phone_reg='wait' WHERE tg_user_id='{tg_id}'"
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
            # connect.close()
        except Error as err:
            print(f"Error: '{err}'")

    def update_phone(self, tg_id, phone):
        connect = self.connect()
        sql = f"UPDATE users SET phone='{phone}', phone_reg='yes' WHERE tg_user_id='{tg_id}'"
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
            # connect.close()
        except Error as err:
            print(f"Error: '{err}'")

    def update_last_filial(self, tg_id, filial):
        connect = self.connect()
        sql = f"UPDATE users SET LastSelectMFC='{filial}', LastSelectGroup='', LastSelectUsluga='' WHERE tg_user_id='{tg_id}'"
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
        except Error as err:
            print(f"Error:  '{err}'")

    def update_last_group(self, tg_id, group):
        connect = self.connect()
        sql = f"UPDATE users SET LastSelectGroup='{group}' WHERE tg_user_id='{tg_id}'"  
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
        except Error as err:
            print(f"Error: '{err}'")

    def update_last_usluga(self, tg_id, usluga):
        connect = self.connect()
        sql = f"UPDATE users SET LastSelectUsluga='{usluga}' WHERE tg_user_id='{tg_id}'" 
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
        except Error as err:
            print(f"Error : '{err}'")

    def update_last_date(self, tg_id, text):
        connect = self.connect()
        sql = f"UPDATE users SET LastSelectDate='{text}' WHERE tg_user_id='{tg_id}'"
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
        except Error as err:
            print(f"Error: '{err}'")

    def update_last_time(self, tg_id, text):
        connect = self.connect()
        sql = f"UPDATE users SET LastSelectTime='{text}' WHERE tg_user_id='{tg_id}'"
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
        except Error as err:
            print(f"Error: '{err}'")

    def update_last_col_order(self, tg_id, text):
        connect = self.connect()
        sql = f"UPDATE users SET LastColOrder='{text}' WHERE tg_user_id='{tg_id}'"
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
        except Error as err:
            print(f"Error: '{err}'")

    def update_last_usluga_id(self, tg_id, text):
        connect = self.connect()
        sql = f"UPDATE users SET LastSelectUslugaId='{text}' WHERE tg_user_id='{tg_id}'"
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
        except Error as err:
            print(f"Error: '{err}'")

    def update_last_category(self, tg_id, text):
        connect = self.connect()
        sql = f"UPDATE users SET LastSelectCategory='{text}' WHERE tg_user_id='{tg_id}'"
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
        except Error as err:
            print(f"Error: '{err}'")

    def create_ticket(self, tg_id, prefix, client_num, ticket_ru, serviceName, countOrders, date, time_t, filial,  notification_send, okno, img_create, queueUuid, serviceUuid, deleted):
        connect = self.connect()
        sql = f"INSERT INTO tickets(create_unixtime, tg_id_owner, prefix, clientNum, ticket_ru, serviceName, countOrders, date, time, filial, ticket_reg_unixtime, notification_send, okno, img_create, queueUuid, serviceUuid, deleted) VALUES ('{int(datetime.datetime.now().timestamp() * 1000)}', '{tg_id}', '{prefix}', '{client_num}', '{ticket_ru}', '{serviceName}', '{countOrders}', '{date}', '{time_t}', '{filial}', '{int(datetime.datetime.now().timestamp() * 1000)}', '{notification_send}', '{okno}', '{img_create}', '{queueUuid}', '{serviceUuid}', '{deleted}');"
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
            connect.close()
        except Error as err:
            print(f"Error: '{err}'")

    def get_tickets_id(self, tg_id):
        connect = self.connect()
        sql = f"SELECT * FROM mfc_tg_bot.tickets WHERE (tg_id_owner = '{tg_id}' AND ((deleted = 'Отменен' AND FROM_UNIXTIME(create_unixtime / 1000) >= DATE_SUB(NOW(), INTERVAL 1 DAY)) OR deleted != 'Отменен'));"
        cursor = connect.cursor()
        result = False
        print("Говый запрос по талонам.")
        try:
            cursor.execute(sql)
            result = cursor.fetchall()
            return result
        except Error as err:
            print(f"Error: '{err}'")

    def update_status_ticket(self, tg_id, text, pin):
        connect = self.connect()
        sql = f"UPDATE tickets SET deleted='{text}' WHERE tg_id_owner='{tg_id}' AND serviceUuid='{pin}'"
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
        except Error as err:
            print(f"Error: '{err}'")

    def update_last_step(self, tg_id, text):
        connect = self.connect()
        sql = f"UPDATE users SET LastStep='{text}' WHERE tg_user_id='{tg_id}'"
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
        except Error as err:
            print(f"Error: '{err}'")

    def update_last_id_menu(self, tg_id, text):
        connect = self.connect()
        sql = f"UPDATE users SET LastIdMenu='{text}' WHERE tg_user_id='{tg_id}'"
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
        except Error as err:
            print(f"Error: '{err}'")


    def get_tickets_pin_id(self, tg_id, pin):
        connect = self.connect()
        sql = f"SELECT * FROM tickets WHERE tg_id_owner='{tg_id}' AND serviceUuid='{pin}';"
        cursor = connect.cursor()
        result = False
        try:
            cursor.execute(sql)
            result = cursor.fetchall()
            return result
        except Error as err:
            print(f"Error: '{err}'")

    def get_tickets_pin(self, pin):
        connect = self.connect()
        sql = f"SELECT * FROM tickets WHERE serviceUuid='{pin}';"
        cursor = connect.cursor()
        result = False
        try:
            cursor.execute(sql)
            result = cursor.fetchall()
            return result
        except Error as err:
            print(f"Error: '{err}'")


    def get_col_tickets(self, id):
        connect = self.connect()
        sql = f"SELECT COUNT(*) AS count FROM mfc_tg_bot.tickets WHERE create_unixtime >= UNIX_TIMESTAMP(CURDATE()) * 1000 AND create_unixtime < UNIX_TIMESTAMP(NOW()) * 1000 and tg_id_owner='{id}' and deleted='Зарезервирован';"
        cursor = connect.cursor()
        result = False
        try:
            cursor.execute(sql)
            result = cursor.fetchall()
            return result
        except Error as err:
            print(f"Error: '{err}'")

    def update_state_fio_correct(self, tg_id):
        connect = self.connect()
        sql = f"UPDATE users SET fio_reg='correct' WHERE tg_user_id='{tg_id}'"
        
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
        except Error as err:
            print(f"Error: '{err}'")

    def update_state_phone_correct(self, tg_id):
        connect = self.connect()
        sql = f"UPDATE users SET phone_reg='correct' WHERE tg_user_id='{tg_id}'"
        
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
        except Error as err:
            print(f"Error: '{err}'")

    def get_ticket_l_id(self, tg_id):
        connect = self.connect()
        sql = f"SELECT * FROM mfc_tg_bot.tickets WHERE tg_id_owner='{tg_id}' ORDER BY id DESC LIMIT 1;"
        cursor = connect.cursor()
        result = False
        print("Говый запрос по талонам.")
        try:
            cursor.execute(sql)
            result = cursor.fetchall()
            return result
        except Error as err:
            print(f"Error: '{err}'")

    def update_last_comment(self, tg_id, comment):
        connect = self.connect()
        sql = f"UPDATE users SET LastComment='{comment}' WHERE tg_user_id='{tg_id}'"
        
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
        except Error as err:
            print(f"Error: '{err}'")

    def update_last_comment_state(self, tg_id):
        connect = self.connect()
        sql = f"UPDATE users SET LastComment='wait' WHERE tg_user_id='{tg_id}'"
        
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
        except Error as err:
            print(f"Error: '{err}'")

    
    def update_comment_state(self, tg_id):
        connect = self.connect()
        sql = f"UPDATE users SET LastComment='yes' WHERE tg_user_id='{tg_id}'"
        
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
        except Error as err:
            print(f"Error: '{err}'")


    def create_comment(self, tg_id, comment):
        import datetime
        connect = self.connect()
        sql = f"INSERT INTO reviews(tg_user_id, review, create_unixtime) VALUES ('{tg_id}', '{comment}', '{int(datetime.datetime.now().timestamp() * 1000)}');"
        
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
        except Error as err:
            print(f"Error: '{err}'") 

    def update_last_region(self, tg_id, region):
        connect = self.connect()
        sql = f"UPDATE users SET LastRegion='{region}' WHERE tg_user_id='{tg_id}'"  
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
        except Error as err:
            print(f"Error: '{err}'")

    def update_last_region_name(self, tg_id, region_name):
        connect = self.connect()
        sql = f"UPDATE users SET LastRegionName='{region_name}' WHERE tg_user_id='{tg_id}'"  
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
        except Error as err:
            print(f"Error: '{err}'")

    def update_user_pers_data(self, tg_id, region_name):
        connect = self.connect()
        sql = f"UPDATE users SET LastRegionName='{region_name}' WHERE tg_user_id='{tg_id}'"  
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
        except Error as err:
            print(f"Error: '{err}'")

    def update_phone_correct_num(self, tg_id):
        connect = self.connect()
        sql = f"UPDATE users SET phone='' WHERE tg_user_id='{tg_id}'"
        
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
        except Error as err:
            print(f"Error: '{err}'")


    def update_phone_fio_correct(self, tg_id):
        connect = self.connect()
        sql = f"UPDATE users SET fio_reg='wait', phone_reg='no' WHERE tg_user_id='{tg_id}'"
        
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
        except Error as err:
            print(f"Error: '{err}'")

    def update_phone_fio_del(self, tg_id):
        connect = self.connect()
        sql = f"UPDATE users SET fio=' ', phone=' ' WHERE tg_user_id='{tg_id}'"
        
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
        except Error as err:
            print(f"Error: '{err}'")

    def update_phone_fio_pre_status(self, tg_id):
        connect = self.connect()
        sql = f"UPDATE users SET fio_reg='sogl', phone_reg='sogl' WHERE tg_user_id='{tg_id}'"
        
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
        except Error as err:
            print(f"Error: '{err}'")

    def update_status_sogl_yes(self, tg_id):
        connect = self.connect()
        sql = f"UPDATE users SET fio_reg='yes', phone_reg='yes' WHERE tg_user_id='{tg_id}'"
        
        cursor = connect.cursor()
        try:
            cursor.execute(sql)
            connect.commit()
        except Error as err:
            print(f"Error: '{err}'")


async def update_status_ticket(loop, tg_id, text, pin):
    pool = await aiomysql.create_pool(host=config['mysql']['host'], port=3306,
                                      user=config['mysql']['user'], password=config['mysql']['password'],
                                      db=config['mysql']['database'], loop=loop, auth_plugin='mysql_native_password')
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(f"UPDATE tickets SET deleted='{text}' WHERE tg_id_owner='{tg_id}' AND serviceUuid='{pin}'")
            print(cur.description)
            # await cur.commit()

    pool.close()
    await pool.wait_closed()


async def get_tickets_id(loop, tg_id):
    pool = await aiomysql.create_pool(host=config['mysql']['host'], port=3306,
                                      user=config['mysql']['user'], password=config['mysql']['password'],
                                      db=config['mysql']['database'], loop=loop, auth_plugin='mysql_native_password')
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(f"SELECT * FROM mfc_tg_bot.tickets WHERE (tg_id_owner = '{tg_id}' AND ((deleted = 'Отменен' AND FROM_UNIXTIME(create_unixtime / 1000) >= DATE_SUB(NOW(), INTERVAL 2 DAY)) OR deleted != 'Отменен'));")
            result = await cur.fetchall()
            

    pool.close()
    await pool.wait_closed()
    return result



sql_init = MySQL(config['mysql']['host'], config['mysql']['database'], config['mysql']['user'], config['mysql']['password'])    # инициализируем класс для подключения к базе


