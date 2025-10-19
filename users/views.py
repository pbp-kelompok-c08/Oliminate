from django.shortcuts import render

def edit_profile(request):
    return render(request, 'edit_profile.html')

def main_profile(request):
    return render(request, 'main_profile.html')
