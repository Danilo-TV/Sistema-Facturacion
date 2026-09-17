from django import forms
from django.contrib.auth.models import Group
from .models import Usuario


class UserForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name', 'rol', 'is_active']
        # Explicitly exclude: is_staff, is_superuser, groups, user_permissions

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields required as needed
        self.fields['email'].required = True
        self.fields['username'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

    def save(self, commit=True):
        user = super().save(commit=False)
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