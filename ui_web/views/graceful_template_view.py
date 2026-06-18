import logging

from django.views.generic import TemplateView

logger = logging.getLogger("ui_web.views")


class GracefulTemplateView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            self.populate_context(context, **kwargs)
        except Exception as e:
            logger.exception("View component degraded: %s", type(self).__name__)
            context["error"] = str(e)
        return context

    def populate_context(self, context, **kwargs):
        raise NotImplementedError
