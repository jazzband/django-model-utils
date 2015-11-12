from django import forms


class ModelChoiceForm(forms.Form):
    items = forms.ModelChoiceField(queryset=None, empty_label=None)

    def __init__(self, queryset, *args, **kwargs):
        super(ModelChoiceForm, self).__init__(*args, **kwargs)
        self.fields['items'].queryset = queryset
