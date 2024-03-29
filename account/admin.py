from django.contrib import admin
from .models import UserProfiles, UserInfo
# Register your models here.

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "birth", "phone")
    list_filter = ("phone",)


admin.site.register(UserProfiles, UserProfileAdmin)

class UserInfoAdmin(admin.ModelAdmin):
    list_display = ('user', 'school', 'company', 'profession', 'address', 'aboutme')
    list_filter = ('school', 'company', 'profession')
    

admin.site.register(UserInfo, UserInfoAdmin)
