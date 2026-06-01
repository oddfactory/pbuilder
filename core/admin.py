from django.contrib import admin
from .models import SystemSettings, PromptHistory

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'updated_at']

    def has_add_permission(self, request):
        if self.model.objects.count() > 0:
            return False
        return super().has_add_permission(request)

@admin.register(PromptHistory)
class PromptHistoryAdmin(admin.ModelAdmin):
    list_display = ['role', 'tech_stack', 'created_at']
    readonly_fields = ['role', 'data_spec', 'core_layout', 'tech_stack', 'generated_prompt', 'created_at']

    def has_add_permission(self, request):
        return False
