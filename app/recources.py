from import_export import resources

from .models import ExamResult
class ExamResultResource(resources.ModelResource):

    class Meta:
        model = ExamResult