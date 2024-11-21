from datetime import datetime


class Utilities():

    def format_phone_number(phone_number):
        cleaned_number = ''.join(char for char in phone_number if char.isdigit())
        if cleaned_number.startswith('8'):
            cleaned_number = '+7' + cleaned_number[1:]
        elif not cleaned_number.startswith('7'):
            cleaned_number = '+7' + cleaned_number
        elif cleaned_number.startswith('7'):
            cleaned_number = '+' + cleaned_number
        elif cleaned_number.startswith('+7'):
            cleaned_number = cleaned_number

        if len(cleaned_number) == 12:
            formatted_number = cleaned_number[0:2] + ' (' + cleaned_number[2:5] + ') ' + cleaned_number[5:8] + '-' + cleaned_number[8:10] + '-' + cleaned_number[10:]
        else:
            formatted_number = cleaned_number

        return formatted_number
    
    def date_format(date):
        date_obj = datetime.strptime(str(date), "%Y-%m-%d")
        new_date_str = str(date_obj.strftime("%d.%m.%Y"))

        return new_date_str
    
    def time_format(time):
        datetime_obj = datetime.strptime(str(time), "%Y-%m-%dT%H:%M:%S.%f%z")
        time_only = datetime_obj.strftime("%H:%M")
        return time_only
    