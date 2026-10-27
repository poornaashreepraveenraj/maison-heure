from datetime import date

from django import forms

from .models import Consignment


class ConsignmentForm(forms.ModelForm):
    class Meta:
        model = Consignment
        fields = ["name", "email", "phone", "brand", "model", "year", "condition", "box_and_papers", "asking_price", "photos"]
        widgets = {
            "phone": forms.TextInput(attrs={"inputmode": "tel", "autocomplete": "tel"}),
            "photos": forms.Textarea(attrs={"rows": 3, "placeholder": "https://…"}),
            "year": forms.NumberInput(attrs={"min": 1900}),
            "asking_price": forms.NumberInput(attrs={"min": 1, "step": 1000}),
        }

    def clean_year(self):
        year = self.cleaned_data["year"]
        if not 1900 <= year <= date.today().year:
            raise forms.ValidationError("Enter a year between 1900 and this year.")
        return year

    def clean_asking_price(self):
        price = self.cleaned_data["asking_price"]
        if price <= 0:
            raise forms.ValidationError("Asking price must be greater than zero.")
        return price
