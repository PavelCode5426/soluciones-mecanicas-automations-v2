from django import forms


class DatePickerInput(forms.DateInput):
    input_type = 'date'
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        # context["widget"]["attrs"]["class"] += " datepicker-input"
        # context["widget"]["attrs"]["type"] += "date"
        return context


class TimePickerInput(forms.TimeInput):
    input_type = 'time'


