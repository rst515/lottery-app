from django.contrib import admin
from .models import (
    User,
    Player,
    BonusBall,
    Draw
    )
from import_export import resources
from import_export.admin import ImportExportActionModelAdmin


class BonusBallInlineAdmin(admin.TabularInline):
    model = BonusBall
    extra = 0


class PlayerResource(resources.ModelResource):
    """Class for filtering Player information in PlayerAdminFilter"""
    class Meta:
        model = Player


class PlayerAdminFilter(ImportExportActionModelAdmin, admin.ModelAdmin):
    inlines = [BonusBallInlineAdmin]
    list_display = ('name', 'active', 'email', 'datestamp_active_from', 'datestamp_active_until')
    resource_classes = [PlayerResource]
    ordering = ['name']

    # def get_form(self, request, obj=None, **kwargs):
    #     # just save obj reference for future processing in Inline
    #     request._obj_ = obj
    #     return super(PlayerAdminFilter, self).get_form(request, obj, **kwargs)


class BonusBallResource(resources.ModelResource):

    class Meta:
        model = BonusBall
        import_id_fields = ('ball_id',)
        # fields = ('ball_id', 'player')


class BonusBallAdminFilter(ImportExportActionModelAdmin, admin.ModelAdmin):
    list_display = ('ball_id', 'player', 'player_id')
    resource_classes = [BonusBallResource]
    ordering = ['ball_id']


class DrawResource(resources.ModelResource):

    class Meta:
        model = Draw


class DrawAdminFilter(ImportExportActionModelAdmin, admin.ModelAdmin):
    list_display = ('draw_date', 'bonus_ball')
    resource_classes = [DrawResource]
    ordering = ['draw_date']


admin.site.register(User)
admin.site.register(Player, PlayerAdminFilter)
admin.site.register(BonusBall, BonusBallAdminFilter)
admin.site.register(Draw, DrawAdminFilter)
