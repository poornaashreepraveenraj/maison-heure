from django.contrib import messages
from django.shortcuts import redirect, render

from store.models import Brand

from .forms import ConsignmentForm


def sell(request):
    if request.method == "POST":
        form = ConsignmentForm(request.POST)
        if form.is_valid():
            consignment = form.save(commit=False)
            if request.user.is_authenticated:
                consignment.user = request.user
            consignment.save()
            messages.success(
                request,
                f"Thank you, {consignment.name}. We've received your {consignment.brand} {consignment.model} "
                "and a specialist will contact you within two business days.",
            )
            return redirect("sell:sell")
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {"name": request.user.get_full_name() or request.user.username, "email": request.user.email}
        # Values passed from the landing-page estimator ("Sell with us").
        for field in ("brand", "model", "year", "condition"):
            if request.GET.get(field):
                initial[field] = request.GET[field]
        if request.GET.get("papers") == "1":
            initial["box_and_papers"] = True
        form = ConsignmentForm(initial=initial)
    return render(request, "sell/sell.html", {"form": form, "brands": Brand.objects.all()})
