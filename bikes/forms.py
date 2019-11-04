from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.contrib.auth.models import User

from .choices import MembershipType
from .models import UserProfile, Bikes,BikeRepairs, Location

# For registering new users
class RegistrationForm(forms.ModelForm):

    alphanumeric = RegexValidator(r'^[0-9a-zA-Z]*$', 'Only alphanumeric characters are allowed.')

    username = forms.CharField(min_length=4, max_length=50, validators=[alphanumeric], widget=forms.TextInput(attrs={'autofocus':'true'}))
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())
    password_confirm = forms.CharField(widget=forms.PasswordInput(), label="Confirm password")
    membership_type = forms.ChoiceField(choices=MembershipType.CHOICES) 

    class Meta:
        model = User
        fields = ('username', 'email', 'password',)
    
    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).count() > 0:
            raise ValidationError("Username already exists")
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).count() > 0:
            raise ValidationError("Email already exists")
        return email
    
    def clean_password_confirm(self):
        pw1 = self.cleaned_data['password']
        pw2 = self.cleaned_data['password_confirm']

        if pw1 and not pw1 == pw2:
            raise ValidationError("Passwords don't match")
        return pw2


    # Override to hash password by using the User model manager's 'create_user' method
    def save(self, *args, **kwargs):
        user = User.objects.create_user(
            self.cleaned_data['username'],
            self.cleaned_data['email'],
            self.cleaned_data['password']
        )
        user.userprofile.membership_type = self.cleaned_data['membership_type']
        user.userprofile.save()
        return user

class UserProfileForm(forms.ModelForm):
    """ Hidden form allowing profile picture uploads """
    class Meta:
        model = UserProfile
        fields = ('profile_pic',)

class ReturnBikeForm(forms.Form):
    hire_id = forms.IntegerField(widget=forms.HiddenInput())
    location = forms.ModelChoiceField(queryset=Location.objects.order_by('station_name'))
    discount = forms.CharField(required=False, label="Discount Code")

class MoveBikeForm(forms.Form):
    location = forms.ModelChoiceField(queryset=Location.objects.order_by('station_name')) # how do i make this list display bike count as well?
    new_location = forms.ModelChoiceField(queryset=Location.objects.order_by('station_name'), label = "New station")

class BikeHireForm(forms.Form):
    bike_id = forms.IntegerField()

class BikeRepairsForm(forms.ModelForm):

    class Meta:
        model= BikeRepairs
        fields=('bike',)