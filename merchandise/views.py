from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from merchandise.forms import MerchandiseForm
from merchandise.models import Merchandise

def merchandise_list(request):
    merchandises = Merchandise.objects.all()
    context = {'merchandises': merchandises}
    return render(request, "merchandise_list.html", context)

def merchandise_detail(request, id):
    merchandise = get_object_or_404(Merchandise, pk=id)
    context = {'merchandise': merchandise}
    return render(request, "merchandise_detail.html", context)

def merchandise_create(request):
    form = MerchandiseForm(request.POST or None)
    if form.is_valid() and request.method == "POST":
        merchandise = form.save(commit=False)
        if request.user.is_authenticated:
            merchandise.organizer = request.user
        else:
            merchandise.organizer = None
        merchandise.save()
        return redirect('merchandise:merchandise_list')
    context = {
        'form': form,
        'title': 'Tambah Merchandise'
    }
    return render(request, "merchandise_form.html", context)


def merchandise_update(request, id):
    merchandise = get_object_or_404(Merchandise, pk=id)
    form = MerchandiseForm(request.POST or None, instance=merchandise)
    if form.is_valid() and request.method == 'POST':
        form.save()
        return redirect('merchandise:merchandise_detail', pk=id)
    context = {
        'form': form,
        'title': 'Edit Merchandise'
    }
    return render(request, "merchandise_form.html", context)

def merchandise_delete(request, id):
    merchandise = get_object_or_404(Merchandise, pk=id)
    if request.method == 'POST':
        merchandise.delete()
        return redirect('merchandise:merchandise_list')
    context = {'merchandise': merchandise}
    return render(request, "merchandise_confirm_delete.html", context)