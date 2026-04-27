from django import forms


class DatePickerInput(forms.DateInput):
    # input_type = 'date'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, format='%Y-%m-%d', **kwargs)

    # def get_context(self, name, value, attrs):
    #     context = super().get_context(name, value, attrs)
    #     context["widget"]["attrs"]["class"] += " datepicker-input"
    #     return context


class TimePickerInput(forms.TimeInput):
    input_type = 'time'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, format='%H:%M', **kwargs)
