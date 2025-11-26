from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods

from users.forms import UserRegisterForm, UserEditForm


@ensure_csrf_cookie
def csrf_token_view(request):
  """Issue a CSRF cookie for API clients (Flutter web)."""
  return JsonResponse({'success': True, 'csrfToken': get_token(request)})


@sensitive_post_parameters('password')
@require_http_methods(['POST'])
def login_view(request):
  username = request.POST.get('username', '').strip()
  password = request.POST.get('password', '')
  if not username or not password:
    return JsonResponse(
      {'success': False, 'message': 'Username dan password wajib diisi.'},
      status=400,
    )

  user = authenticate(request, username=username, password=password)
  if user is None:
    return JsonResponse(
      {'success': False, 'message': 'Username atau password salah.'},
      status=400,
    )

  login(request, user)
  return JsonResponse({'success': True})


@sensitive_post_parameters('password')
@require_http_methods(['POST'])
def register_view(request):
  form = UserRegisterForm(request.POST, request.FILES)
  if form.is_valid():
    form.save()
    return JsonResponse({
      'success': True,
      'message': 'Registrasi berhasil. Silakan login untuk melanjutkan.',
    })

  errors = {field: [str(err) for err in errs] for field, errs in form.errors.items()}
  return JsonResponse({'success': False, 'errors': errors}, status=400)


@require_http_methods(['POST'])
def logout_view(request):
  logout(request)
  return JsonResponse({'success': True})


def session_view(request):
  if not request.user.is_authenticated:
    return JsonResponse({'authenticated': False})

  user = request.user
  data = {
    'username': user.username,
    'first_name': user.first_name,
    'last_name': user.last_name,
    'email': user.email,
    'fakultas': getattr(user, 'fakultas', ''),
    'role': getattr(user, 'role', ''),
  }
  return JsonResponse({'authenticated': True, 'user': data})


@login_required
@sensitive_post_parameters('password')
@require_http_methods(['POST'])
def profile_update_view(request):
  form = UserEditForm(request.POST, request.FILES, instance=request.user)
  if form.is_valid():
    user = form.save(commit=False)
    new_password = form.cleaned_data.get('password')
    if new_password:
      user.set_password(new_password)
    user.save()
    if new_password:
      update_session_auth_hash(request, user)
    return JsonResponse({'success': True})

  errors = {field: [str(err) for err in errs] for field, errs in form.errors.items()}
  return JsonResponse({'success': False, 'errors': errors}, status=400)
