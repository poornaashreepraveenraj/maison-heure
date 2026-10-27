from django import forms

from cart.pricing import DELIVERY_OPTIONS

from .models import phone_validator, pincode_validator

INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat", "Haryana",
    "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana",
    "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal", "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
]


class ShippingForm(forms.Form):
    name = forms.CharField(label="Full name", max_length=120, widget=forms.TextInput(attrs={"autocomplete": "name"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    phone = forms.CharField(
        max_length=20, validators=[phone_validator], widget=forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel"})
    )
    line1 = forms.CharField(label="Address line 1", max_length=200, widget=forms.TextInput(attrs={"autocomplete": "address-line1"}))
    line2 = forms.CharField(
        label="Address line 2", max_length=200, required=False, widget=forms.TextInput(attrs={"autocomplete": "address-line2"})
    )
    city = forms.CharField(max_length=80, widget=forms.TextInput(attrs={"autocomplete": "address-level2"}))
    state = forms.ChoiceField(choices=[("", "Select state")] + [(s, s) for s in INDIAN_STATES])
    pincode = forms.CharField(
        label="PIN code",
        max_length=6,
        validators=[pincode_validator],
        widget=forms.TextInput(attrs={"inputmode": "numeric", "pattern": "[1-9][0-9]{5}", "autocomplete": "postal-code", "data-pincode": ""}),
    )
    save_address = forms.BooleanField(label="Save this address to my account", required=False)


class DeliveryForm(forms.Form):
    delivery = forms.ChoiceField(
        choices=[(key, f"{opt['label']} ({opt['days']})") for key, opt in DELIVERY_OPTIONS.items()],
        widget=forms.RadioSelect,
        initial="standard",
    )


class TrackOrderForm(forms.Form):
    reference = forms.CharField(
        label="Order reference", max_length=20, widget=forms.TextInput(attrs={"placeholder": "MH-2026-000123"})
    )
    email = forms.EmailField(label="Email used at checkout")

    def clean_reference(self):
        return self.cleaned_data["reference"].strip().upper()
