from django.shortcuts import render

def edit_profile(request):
    return render(request, 'edit_profile.html')
