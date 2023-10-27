from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportActionModelAdmin

from .models import (
    User,
    Player,
    BonusBall,
    Draw
)


class BonusBallInlineAdmin(admin.TabularInline):
    model = BonusBall
    extra = 0


class PlayerResource(resources.ModelResource):
    """Class for filtering Player information in PlayerAdminFilter"""
    class Meta:  # pylint: disable=too-few-public-methods
        model = Player


# pylint:disable=too-many-ancestors
class PlayerAdminFilter(ImportExportActionModelAdmin, admin.ModelAdmin):
    inlines = [BonusBallInlineAdmin]
    list_display = ('name', 'active', 'email', 'datestamp_active_from', 'datestamp_active_until')
    resource_classes = [PlayerResource]
    ordering = ['name']


class BonusBallResource(resources.ModelResource):

    # pylint: disable=too-few-public-methods
    class Meta:
        model = BonusBall
        import_id_fields = ('ball_id',)


class BonusBallAdminFilter(ImportExportActionModelAdmin, admin.ModelAdmin):
    list_display = ('ball_id', 'player', 'player_id')
    resource_classes = [BonusBallResource]
    ordering = ['ball_id']


class DrawResource(resources.ModelResource):

    # pylint: disable=too-few-public-methods
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
