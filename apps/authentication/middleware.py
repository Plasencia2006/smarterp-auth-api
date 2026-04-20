from apps.business.models import Business


class BusinessContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.business = None
        business_id = request.META.get('HTTP_X_BUSINESS_ID')
        if business_id:
            try:
                request.business = Business.objects.select_related('owner').get(
                    id=business_id, is_active=True
                )
            except Exception:
                pass
        return self.get_response(request)