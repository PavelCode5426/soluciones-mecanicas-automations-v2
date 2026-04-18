from django import forms


class DatePickerInput(forms.DateInput):
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["attrs"]["class"] += " datepicker-input"
        return context


class TimePickerInput(forms.TimeInput):
    input_type = 'time'


