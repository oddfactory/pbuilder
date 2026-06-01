from django.db import models

class SystemSettings(models.Model):
    gemini_api_key = models.CharField(max_length=255, blank=True, null=True, help_text="Gemini API Key를 입력하세요. (비워두면 Rule-based Fallback 사용)")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "시스템 설정"
        verbose_name_plural = "시스템 설정"

    def save(self, *args, **kwargs):
        self.pk = 1 # 싱글톤 패턴 유지
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "시스템 설정"

class PromptHistory(models.Model):
    role = models.CharField(max_length=255, verbose_name="역할(Role)")
    data_spec = models.TextField(verbose_name="데이터 스펙(Data Spec)")
    core_layout = models.TextField(verbose_name="핵심 레이아웃(Core Layout)")
    tech_stack = models.CharField(max_length=255, verbose_name="기술 스택(Tech Stack)")
    generated_prompt = models.TextField(verbose_name="생성된 프롬프트")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")

    class Meta:
        verbose_name = "프롬프트 생성 이력"
        verbose_name_plural = "프롬프트 생성 이력"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.role} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
