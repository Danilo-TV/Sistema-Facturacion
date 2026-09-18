from django import forms
from django.contrib.auth.models import Group
from .models import Usuario


class UserForm(forms.ModelForm):
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        required=True,  # Required for creation
        help_text='Mínimo 8 caracteres'
    )

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name', 'rol', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['username'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        # Password only required for NEW users (not saved to DB yet)
        # Use _state.adding because UUID PK is assigned on instantiation
        if self.instance and not self.instance._state.adding:
            self.fields['password'].required = False
            self.fields['password'].help_text = 'Dejar en blanco para no cambiar la contraseña'

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password and password.strip():
            user.set_password(password)
        if commit:
            user.save()
            # Clear existing groups
            user.groups.clear()

            # Assign group based on rol
            rol = self.cleaned_data.get('rol')
            if rol == Usuario.Rol.ADMIN:
                group, _ = Group.objects.get_or_create(name='Administrador')
                user.groups.add(group)
                user.is_staff = True
                user.is_superuser = True
            elif rol == Usuario.Rol.VENDEDOR:
                group, _ = Group.objects.get_or_create(name='Cajeros')
                user.groups.add(group)
                user.is_staff = False
                user.is_superuser = False
            user.save()
        return user